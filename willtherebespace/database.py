"""Module for connecting to the various databases."""

import logging
import os

import redis
import sqlalchemy

from . import models


DATABASE_URI_KEY = 'DATABASE_URL'
REDIS_URI_KEY = 'REDIS_URL'


logger = logging.getLogger(__name__)


_sql_engine = None
_sql_connection = None
_redis = None


def get_sql_database_uri(key=DATABASE_URI_KEY):
    try:
        return os.environ[key]
    except KeyError:
        msg = 'SQL database URI is not configured. ' \
              'Please set {key} environment variable.'.format(key=key)
        raise RuntimeError(msg)


def connect_to_sql():
    global _sql_engine, _sql_connection

    if _sql_engine is not None or \
            (_sql_connection is not None and not _sql_connection.closed):
        raise RuntimeError('Attempted to connect, but already connected.')

    uri = get_sql_database_uri()

    logger.info('Connecting to SQL database.')

    engine = sqlalchemy.create_engine(uri)
    connection = engine.connect()

    models._Base.prepare(engine)
    models._Session.configure(bind=connection)

    _sql_engine = engine
    _sql_connection = connection

    return engine, connection


def get_sql_engine():
    if _sql_engine is None:
        connect_to_sql()
    return _sql_engine


def get_sql_connection():
    if _sql_connection is None or _sql_connection.closed:
        connect_to_sql()
    return _sql_connection


def get_redis_uri(key=REDIS_URI_KEY):
    try:
        return os.environ[key]
    except KeyError:
        msg = 'Redis URI is not configured. ' \
              'Please set {key} environment variable.'.format(key=key)
        raise RuntimeError(msg)


def connect_to_redis():
    global _redis

    if _redis is not None:
        raise RuntimeError('Attempted to connect, but already connected.')

    uri = get_redis_uri()

    logger.info('Connecting to Redis.')

    connection = redis.Redis.from_url(uri)

    _redis = connection

    return connection


def get_redis():
    if _redis is None:
        connect_to_redis()
    return _redis
