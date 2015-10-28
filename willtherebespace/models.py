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


class Place(_Base):
    __tablename__ = 'place'

    author = relationship('Author', backref=backref('places'))


class PlaceUpdate(_Base):
    __tablename__ = 'place_update'

    author = relationship('Author', backref=backref('place_updates'))
    place = relationship('Place', backref=backref('updates'))

    def __init__(self, used_spaces, free_spaces, author, place=None):
        self.used_spaces = used_spaces
        self.free_spaces = free_spaces
        self.author = author
        self.place = place
        self.date = datetime.datetime.now()
