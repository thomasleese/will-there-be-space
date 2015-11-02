#!/bin/bash
set -e

if [ "$1" = 'willtherebespace-backup.sh' ]; then
    chown -R willtherebespace .
    exec gosu willtherebespace "$@"
fi

exec "$@"
