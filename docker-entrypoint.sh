#!/bin/bash
set -e

if [ "$1" = 'gunicorn' ]; then
    chown -R willtherebespace .
    exec gosu willtherebespace "$@"
fi

exec "$@"
