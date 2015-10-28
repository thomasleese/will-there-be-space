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
        'nose >=1.3, <2',
        'Sphinx >=1.3, <2'
    ],
    install_requires=[
        'alembic',
        'Flask',
        'gunicorn',
        'passlib',
        'psycopg2',
        'SQLAlchemy',
    ],
    test_suite='nose.collector',
)
