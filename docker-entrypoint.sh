#!/bin/bash
set -e

if [ "$1" = 'gunicorn' ]; then
    chown -R willtherebespace .
    exec gosu willtherebespace "$@"
fi

if [ "$1" = 'python' ]; then
    chown -R willtherebespace .
    exec gosu willtherebespace "$@"
fi

exec "$@"
