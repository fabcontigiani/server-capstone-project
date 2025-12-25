#!/bin/sh
set -e

# Ensure media directory exists and has correct permissions
echo "Setting up media directory..."
mkdir -p /app/media/images /app/media/processed_images
chmod -R 755 /app/media || true

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
