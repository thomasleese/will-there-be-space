import datetime
import itertools
import os

from cerberus import Validator
import flask
import requests
import rollbar
import rollbar.contrib.flask
import sqlalchemy
from werkzeug.contrib.fixers import ProxyFix

from .. import database
from ..models import Author, Place, PlaceScale, PlaceUpdate, \
    _Session as SqlSession


app = flask.Flask('willtherebespace.web')
app.wsgi_app = ProxyFix(app.wsgi_app, num_proxies=2)  # Nginx and CloudFlare

app.jinja_env.filters['islice'] = itertools.islice

app.config['PREFERRED_URL_SCHEME'] = 'https'


@app.before_first_request
def configure_recaptcha():
    try:
        app.config['RECAPTCHA_SITE_KEY'] = os.environ['RECAPTCHA_SITE_KEY']
        app.config['RECAPTCHA_SECRET_KEY'] = os.environ['RECAPTCHA_SECRET_KEY']
        app.config['RECAPTCHA_ENABLED'] = True
    except KeyError:
        if not app.debug:
            raise
        else:
            app.config['RECAPTCHA_ENABLED'] = False


@app.before_first_request
def initialise_rollbar():
    try:
        access_token = os.environ['ROLLBAR_ACCESS_TOKEN']
    except KeyError:
        return

    rollbar.init(access_token, 'will-there-be-space',
                 root=os.path.dirname(os.path.realpath(__file__)),
                 allow_logging_basic_config=False)

    flask.got_request_exception.connect(rollbar.contrib.flask.report_exception,
                                        app)


@app.before_first_request
def configure_database():
    app.sql_engine = database.get_sql_engine()
    app.sql_connection = database.get_sql_connection()
    app.redis = database.get_redis()
    app.logger.info('Connected to database.')


@app.before_request
def configure_session(*args, **kwargs):
    flask.g.sql_session = SqlSession()


@app.teardown_request
def remove_session(*args, **kwargs):
    SqlSession.remove()


@app.route('/')
def home():
    query = flask.g.sql_session.query(Place) \
        .outerjoin(PlaceUpdate) \
        .order_by(PlaceUpdate.date.desc())

    if 'q' in flask.request.args:
        q = flask.request.args['q']
        query = query.filter(sqlalchemy.or_(
            Place.name.ilike('%' + q + '%'),
            Place.description.ilike('%' + q + '%'),
            Place.location.ilike('%' + q + '%')
        ))

    places = query.all()

    return flask.render_template('place/index.html', places=places)


@app.route('/about')
def about():
    return flask.render_template('about.html')


def check_recaptcha():
    if not app.config['RECAPTCHA_ENABLED']:
        return True

    payload = {
        'secret': app.config['RECAPTCHA_SECRET_KEY'],
        'response': flask.request.form['g-recaptcha-response'],
    }
    app.logger.debug('Testing Recaptcha response.')
    req = requests.post('https://www.google.com/recaptcha/api/siteverify',
                        data=payload)
    json = req.json()
    app.logger.debug(str(json))
    return json['success']


@app.route('/in/<slug>', methods=['GET', 'POST'])
def place(slug):
    try:
        place = flask.g.sql_session.query(Place) \
            .filter(Place.slug == slug) \
            .one()
    except sqlalchemy.orm.exc.NoResultFound:
        flask.abort(404)

    if flask.request.method == 'POST':
        v = Validator({
            'busyness': {'type': 'integer', 'coerce': int, 'required': True,
                         'min': 0, 'max': 10},
        })

        form = dict(flask.request.form.items())

        try:
            del form['g-recaptcha-response']
        except KeyError:
            pass

        if check_recaptcha() and v.validate(form):
            author = make_author()
            update = PlaceUpdate(v.document['busyness'], author, place=place)

            app.redis.publish('updates', '{} has set {} to {}.'.format(
                author.ip_address, place.name,
                place.scale.get_text(v.document['busyness'])
            ))

            flask.g.sql_session.add(update)
            flask.g.sql_session.commit()
            return flask.redirect(flask.url_for('.place', slug=place.slug))
        else:
            return flask.render_template('place/view.html', place=place,
                                         errors=v.errors)
    else:
        return flask.render_template('place/view.html', place=place)


def make_author():
    return Author(flask.request.remote_addr)


@app.route('/new_place', methods=['GET', 'POST'])
def new_place():
    if flask.request.method == 'POST':
        v = Validator({
            'name': {'type': 'string', 'minlength': 3},
            'description': {'type': 'string', 'required': True},
            'location': {'type': 'string', 'required': True},
        })

        form = dict(flask.request.form.items())

        try:
            del form['g-recaptcha-response']
        except KeyError:
            pass

        if check_recaptcha() and v.validate(form):
            author = make_author()
            place = Place(v.document['name'], v.document['description'],
                          v.document['location'], author)
            place.scale = PlaceScale()
            flask.g.sql_session.add(place)
            flask.g.sql_session.commit()
            return flask.redirect(flask.url_for('.place', slug=place.slug))
        else:
            return flask.render_template('place/new.html', errors=v.errors)
    return flask.render_template('place/new.html')


@app.route('/robots.txt')
def robots():
    text = flask.render_template('robots.txt')
    return flask.Response(text, mimetype='text/plain')


@app.route('/sitemap.xml')
def sitemap():
    pages = []

    ten_days_ago = (datetime.datetime.now() -
                    datetime.timedelta(days=10)).date().isoformat()

    # static pages
    for rule in app.url_map.iter_rules():
        if 'GET' in rule.methods and not rule.arguments:
            pages.append([flask.url_for(rule.endpoint, _external=True),
                          ten_days_ago, 'weekly', 1])

    # place pages
    places = flask.g.sql_session.query(Place) \
        .outerjoin(PlaceUpdate) \
        .order_by(PlaceUpdate.date.desc()) \
        .all()

    for place in places:
        url = flask.url_for('.place', slug=place.slug, _external=True)
        if place.last_update:
            modified_time = place.last_update.date.date().isoformat()
        else:
            modified_time = ten_days_ago
        pages.append([url, modified_time, 'daily', 0.8])

    sitemap = flask.render_template('sitemap.xml', pages=pages)
    return flask.Response(sitemap, mimetype='application/xml')


@app.errorhandler(404)
def page_not_found(e):
    return flask.render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return flask.render_template('500.html'), 500
