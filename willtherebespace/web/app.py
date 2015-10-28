import flask

from .. import database
from ..models import Place, _Session as SqlSession


app = flask.Flask('willtherebespace.web')


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
def hello():
    places = flask.g.sql_session.query(Place).all()
    return flask.render_template('places.html', places=places)


@app.route('/in/<slug>')
def place(slug):
    place = flask.g.sql_session.query(Place) \
        .filter(Place.slug == slug) \
        .one()
    return flask.render_template('place.html', place=place)
