#!/bin/sh
set -e

# Wait for DB to be ready and run migrations (retry loop)
echo "Running migrations..."
until python manage.py makemigrations --noinput; do
  echo "Database unavailable - sleeping"
  sleep 2
done

until python manage.py migrate --noinput; do
  echo "Database unavailable - sleeping"
  sleep 2
done

echo "Collecting static files..."
python manage.py collectstatic --noinput || true

echo "Starting container command: $@"
exec "$@"
