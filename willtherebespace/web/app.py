import datetime
import itertools

from cerberus import Validator
import flask
from werkzeug.contrib.fixers import ProxyFix
import sqlalchemy.sql

from .. import database
from ..models import Author, Place, PlaceUpdate, _Session as SqlSession


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


@app.route('/in/<slug>')
def place(slug):
    place = flask.g.sql_session.query(Place) \
        .filter(Place.slug == slug) \
        .one()

    sql = """
        SELECT
            to_char(date, 'ID') AS day,
            to_char(date, 'HH24') as hour,
            AVG(free_spaces) AS frees,
            AVG(used_spaces) AS useds
        FROM
            place_update
        WHERE
            place_update.place_id = :place_id
        GROUP BY
            to_char(date, 'ID'),
            to_char(date, 'HH24')
    """

    free_results = {}
    used_results = {}

    for row in app.sql_engine.execute(sqlalchemy.sql.text(sql), place_id=place.id):
        free_results[(int(row[0]) - 1, int(row[1]))] = row[2]
        used_results[(int(row[0]) - 1, int(row[1]))] = row[3]

    results = []
    dict_results = {}

    if free_results and used_results:
        free_average = sum(x for x in free_results.values()) / len(free_results)
        used_average = sum(x for x in used_results.values()) / len(used_results)

        results = []
        for day in range(7):
            for hour in range(24):
                free = free_results.get((day, hour))
                used = used_results.get((day, hour))

                if free is None:
                    assert used is None
                if used is None:
                    assert free is None

                if free is None or used is None:
                    # try the day before
                    day_before = day - 1
                    while day_before != day:
                        free_before = free_results.get((day_before, hour))
                        used_before = used_results.get((day_before, hour))
                        if free_before is not None and used_before is not None:
                            free = free_before
                            used = used_before
                            break

                        day_before -= 1
                        if day_before < 0:
                            day_before = 6

                    if free is None or used is None:
                        # average
                        free = free_average
                        used = used_average

                dict_results[(day, hour)] = (free, used)
                results.append((day, hour, free, used))

    now = datetime.datetime.now()
    now_results = dict_results.get((now.weekday(), now.hour), (None, None))

    return flask.render_template('place.html', place=place, chart=results,
                                 now_free=now_results[0],
                                 now_used=now_results[1])


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
            flask.g.sql_session.add(place)
            flask.g.sql_session.commit()
            return flask.redirect(flask.url_for('.place', slug=place.slug))
        else:
            return flask.render_template('place/new.html', errors=v.errors)
    return flask.render_template('place/new.html')


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
