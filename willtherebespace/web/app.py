import itertools
import logging
import os

from cerberus import Validator
import flask
import requests
from raven.contrib.flask import Sentry
from werkzeug.contrib.fixers import ProxyFix

from .. import database
from ..models import Author, Place, PlaceScale, PlaceUpdate, \
    _Session as SqlSession


app = flask.Flask('willtherebespace.web')
app.wsgi_app = ProxyFix(app.wsgi_app, num_proxies=2)  # Nginx and CloudFlare

try:
    sentry_dsn = os.environ['SENTRY_DSN']
except KeyError:
    pass
else:
    app.sentry = Sentry(app, dsn=sentry_dsn, logging=True,
                        level=logging.WARNING)

app.jinja_env.filters['islice'] = itertools.islice


@app.before_first_request
def configure_database():
    app.sql_engine = database.get_sql_engine()
    app.sql_connection = database.get_sql_connection()
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
