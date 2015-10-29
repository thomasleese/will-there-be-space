"""Models."""

import datetime
import hashlib
import os

from sqlalchemy import event, Column, String
from sqlalchemy.orm import backref, scoped_session, sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base, DeferredReflection
from sqlalchemy.ext.hybrid import hybrid_property
from passlib.context import CryptContext


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


class PlaceScale(_Base):
    __tablename__ = 'place_scale'

    place = relationship('Place', backref=backref('scale', uselist=False))

    def __init__(self):
        self.text_0 = 'Empty'
        self.text_1 = 'Very empty'
        self.text_2 = 'Fairly empty'
        self.text_3 = 'Reasonably empty'
        self.text_4 = 'Almost half full'
        self.text_5 = 'Half full'
        self.text_6 = 'Just over half full'
        self.text_7 = 'Reasonably full'
        self.text_8 = 'Fairly full'
        self.text_9 = 'Very full'
        self.text_10 = 'Full'

class PlaceUpdate(_Base):
    __tablename__ = 'place_update'

    author = relationship('Author', backref=backref('place_updates'))
    place = relationship('Place', backref=backref('updates', order_by='desc(PlaceUpdate.date)'))

    def __init__(self, busyness, author, place=None):
        self.busyness = busyness
        self.author = author
        self.place = place
        self.date = datetime.datetime.now()
