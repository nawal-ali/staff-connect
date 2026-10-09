#!/bin/sh
set -e

# Create/upgrade the database tables, then start the server (the CMD)
python manage.py migrate --noinput

exec "$@"
