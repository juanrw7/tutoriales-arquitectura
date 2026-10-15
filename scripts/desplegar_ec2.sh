#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [ ! -f .env ]; then
  echo "Primero cree .env y defina DJANGO_ALLOWED_HOSTS con la IP publica." >&2
  exit 1
fi
docker compose config --quiet
docker compose up -d --build --remove-orphans
docker compose ps
echo "Revise 'docker compose logs web nginx' y abra http://IP-PUBLICA/api/v1/comprar/"
