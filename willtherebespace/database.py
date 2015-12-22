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


# http://docs.sqlalchemy.org/en/latest/core/pooling.html#dealing-with-disconnects
def sql_ping_connection(connection, branch):
    if branch:
        # "branch" refers to a sub-connection of a connection,
        # we don't want to bother pinging on these.
        return

    try:
        # run a SELECT 1.   use a core select() so that
        # the SELECT of a scalar value without a table is
        # appropriately formatted for the backend
        connection.scalar(sqlalchemy.select([1]))
    except sqlalchemy.exc.DBAPIError as err:
        # catch SQLAlchemy's DBAPIError, which is a wrapper
        # for the DBAPI's exception.  It includes a .connection_invalidated
        # attribute which specifies if this connection is a "disconnect"
        # condition, which is based on inspection of the original exception
        # by the dialect in use.
        if err.connection_invalidated:
            # run the same SELECT again - the connection will re-validate
            # itself and establish a new connection.  The disconnect detection
            # here also causes the whole connection pool to be invalidated
            # so that all stale connections are discarded.
            connection.scalar(sqlalchemy.select([1]))
        else:
            raise


def connect_to_sql():
    global _sql_engine, _sql_connection

    if _sql_engine is not None or \
            (_sql_connection is not None and not _sql_connection.closed):
        raise RuntimeError('Attempted to connect, but already connected.')

    uri = get_sql_database_uri()

    logger.info('Connecting to SQL database.')

    engine = sqlalchemy.create_engine(uri)
    sqlalchemy.event.listen(engine, 'engine_connect', sql_ping_connection)

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
