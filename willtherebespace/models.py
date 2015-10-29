"""Models."""

import datetime
import hashlib
import os

from sqlalchemy.orm import backref, scoped_session, sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base, DeferredReflection
from passlib.context import CryptContext

from .chart import BusynessChart


_Base = declarative_base(cls=DeferredReflection)
_Session = scoped_session(sessionmaker())


password_context = CryptContext(
    schemes=['pbkdf2_sha256'],
    default='pbkdf2_sha256',
    all__vary_rounds=0.1,
    pbkdf2_sha256__default_rounds=8000
)


def generate_key(length=512):
    h = hashlib.sha256()
    h.update(os.urandom(length))
    return h.hexdigest()


class Author(_Base):
    __tablename__ = 'author'

    def __init__(self, ip_address, account=None):
        self.account = account
        self.ip_address = ip_address


def slugify(string):
    string = string.replace('_', '-')
    return string.replace(' ', '-').lower()


class Place(_Base):
    __tablename__ = 'place'

    author = relationship('Author', backref=backref('places'))

    def __init__(self, name, description, location, author):
        self.name = name
        self.description = description
        self.location = location
        self.slug = slugify(name)
        self.author = author

    @property
    def busyness_chart(self):
        sql = """
            SELECT
                to_char(date, 'ID') AS day,
                to_char(date, 'HH24') as hour,
                AVG(busyness) AS busyness
            FROM
                place_update
            WHERE
                place_update.place_id = :place_id
            GROUP BY
                to_char(date, 'ID'),
                to_char(date, 'HH24')
        """

        session = _Session.object_session(self)
        raw_results = session.execute(sql, {'place_id': self.id})

        try:
            return BusynessChart(raw_results)
        except ValueError:
            return None


class PlaceScale(_Base):
    __tablename__ = 'place_scale'

    place = relationship('Place', backref=backref('scale', uselist=False))

    def __init__(self):
        self.text_0 = 'empty'
        self.text_1 = 'very empty'
        self.text_2 = 'fairly empty'
        self.text_3 = 'reasonably empty'
        self.text_4 = 'almost half full'
        self.text_5 = 'half full'
        self.text_6 = 'just over half full'
        self.text_7 = 'reasonably full'
        self.text_8 = 'fairly full'
        self.text_9 = 'almost full'
        self.text_10 = 'full'

    def get_text(self, index):
        if index < 0 or index > 10:
            raise IndexError(index)
        return getattr(self, 'text_{}'.format(index))

    def get_colour(self, index):
        if 0 <= index <= 5:
            return '#5cb85c'
        elif 5 < index <= 8:
            return '#f0ad4e'
        elif 8 < index <= 10:
            return '#d9534f'
        else:
            raise IndexError(index)


class PlaceUpdate(_Base):
    __tablename__ = 'place_update'

    author = relationship('Author', backref=backref('place_updates'))
    place = relationship('Place', backref=backref('updates', order_by='desc(PlaceUpdate.date)'))

    def __init__(self, busyness, author, place=None):
        self.busyness = busyness
        self.author = author
        self.place = place
        self.date = datetime.datetime.now()
