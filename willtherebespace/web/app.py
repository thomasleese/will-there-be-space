import itertools

from cerberus import Validator
import flask
from werkzeug.contrib.fixers import ProxyFix

from .. import database
from ..models import Author, Place, PlaceScale, PlaceUpdate, \
    _Session as SqlSession


app = flask.Flask('willtherebespace.web')
app.wsgi_app = ProxyFix(app.wsgi_app)

app.jinja_env.filters['islice'] = itertools.islice


@app.before_first_request
def configure_database():
    app.sql_engine = database.get_sql_engine()
    app.sql_connection = database.get_sql_connection()


@app.before_request
def configure_session(*args, **kwargs):
    flask.g.sql_session = SqlSession()


@app.teardown_request
def remove_session(*args, **kwargs):
    SqlSession.remove()


@app.route('/')
def home():
    places = flask.g.sql_session.query(Place).all()
    return flask.render_template('places.html', places=places)


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
        if v.validate(form):
            author = make_author()
            update = PlaceUpdate(v.document['busyness'], author, place=place)

            flask.g.sql_session.add(update)
            flask.g.sql_session.commit()
            return flask.redirect(flask.url_for('.place', slug=place.slug))
        else:
            return flask.render_template('place.html', place=place,
                                         errors=v.errors)
    else:
        chart = place.busyness_chart

        return flask.render_template('place.html', place=place,
                                     chart=chart.results,
                                     now_busyness=chart.now_results)


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
        if v.validate(form):
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
