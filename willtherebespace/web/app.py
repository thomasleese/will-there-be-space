from cerberus import Validator
import flask
from werkzeug.contrib.fixers import ProxyFix

from .. import database
from ..models import Author, Place, PlaceUpdate, _Session as SqlSession


app = flask.Flask('willtherebespace.web')
app.wsgi_app = ProxyFix(app.wsgi_app)


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


@app.route('/in/<slug>')
def place(slug):
    place = flask.g.sql_session.query(Place) \
        .filter(Place.slug == slug) \
        .one()
    return flask.render_template('place.html', place=place)


def make_author():
    return Author(flask.request.remote_addr)


@app.route('/in/<slug>/update', methods=['GET', 'POST'])
def update_place(slug):
    place = flask.g.sql_session.query(Place) \
        .filter(Place.slug == slug) \
        .one()

    if flask.request.method == 'POST':
        # TODO add >0 checking
        v = Validator({
            'free': {'type': 'integer', 'coerce': int, 'required': True},
            'used': {'type': 'integer', 'coerce': int, 'required': True},
        })

        form = dict(flask.request.form.items())
        if v.validate(form):
            author = make_author()
            update = PlaceUpdate(v.document['used'], v.document['free'],
                                 author, place=place)

            flask.g.sql_session.add(update)
            flask.g.sql_session.commit()
            return flask.redirect(flask.url_for('.place', slug=place.slug))
        else:
            print(v.errors)
            return flask.render_template('place/update.html', place=place)

    return flask.render_template('place/update.html', place=place)
