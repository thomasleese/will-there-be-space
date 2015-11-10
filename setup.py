#!/usr/bin/env python
from setuptools import setup, find_packages

from willtherebespace import __version__


setup(
    name='will-there-be-space',
    version=__version__,
    author='Thomas Leese',
    author_email='inbox@thomasleese.me',
    packages=find_packages(exclude=['tests*']),
    zip_safe=True,
    setup_requires=[
        'Sphinx >=1.3, <2'
    ],
    install_requires=[
        'alembic',
        'cerberus',
        'Flask',
        'gunicorn',
        'rollbar',
        'redis',
        'requests',
        'passlib',
        'psycopg2',
        'SQLAlchemy',
    ],
    test_suite='tests',
)
