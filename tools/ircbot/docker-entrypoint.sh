#!/bin/bash
set -e

if [ "$1" = 'node' ]; then
    chown -R willtherebespace .
    exec gosu willtherebespace "$@"
fi

exec "$@"
