import itertools
import os

from cerberus import Validator
import flask
import requests
import rollbar
import rollbar.contrib.flask
from werkzeug.contrib.fixers import ProxyFix

from .. import database
from ..models import Author, Place, PlaceScale, PlaceUpdate, \
    _Session as SqlSession


app = flask.Flask('willtherebespace.web')
app.wsgi_app = ProxyFix(app.wsgi_app, num_proxies=2)  # Nginx and CloudFlare

app.jinja_env.filters['islice'] = itertools.islice


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
    places = flask.g.sql_session.query(Place) \
        .outerjoin(PlaceUpdate) \
        .order_by(PlaceUpdate.date.desc()) \
        .all()

    return flask.render_template('place/index.html', places=places)


@app.route('/about')
def about():
    return flask.render_template('about.html')


def check_recaptcha():
    payload = {
        'secret': os.environ['RECAPTCHA_SECRET'],
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
    place = flask.g.sql_session.query(Place) \
        .filter(Place.slug == slug) \
        .one()

    if flask.request.method == 'POST':
        v = Validator({
            'busyness': {'type': 'integer', 'coerce': int, 'required': True,
                         'min': 0, 'max': 10},
        })

        form = dict(flask.request.form.items())
        del form['g-recaptcha-response']

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
        del form['g-recaptcha-response']

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
