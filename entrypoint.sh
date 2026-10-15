#!/bin/sh
set -eu
: "${DJANGO_SECRET_KEY:?Defina DJANGO_SECRET_KEY en .env}"
: "${DB_PASSWORD:?Defina DB_PASSWORD en .env}"
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py sembrar_tutorial
exec "$@"
