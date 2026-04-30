#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "Waiting for postgres..."

# Use a simple loop to check if the port is open
# 'db' is the service name from your docker-compose
#while ! nc -z db 5432; do
#  sleep 0.1
#done

echo "PostgreSQL started"

# Run migrations
#echo "Applying database migrations..."
#alembic -c app/alembic.ini stamp head
#alembic -c app/alembic.ini upgrade head

uv run uvicorn app.main:app --host 0.0.0.0 --port 7860 --reload &

# 2. Start Celery Worker
# Note the module path syntax
uv run celery -A app.core.celery:celery_app worker --loglevel=info --concurrency=1 &

# 3. Start Celery Beat
uv run celery -A app.core.celery:celery_app beat --loglevel=info --schedule=/tmp/celerybeat-schedule &

# Start the actual application
echo "Starting FastAPI..."
exec "$@"