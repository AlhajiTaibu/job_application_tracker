#!/bin/bash

set -e

echo "Waiting for postgres..."
echo "PostgreSQL started"

echo "Applying database migrations..."
#alembic -c app/alembic.ini upgrade head

echo "Starting FastAPI..."
uvicorn app.main:app --host 0.0.0.0 --port 7860 &

echo "Starting Celery Worker..."
celery -A app.core.celery:celery_app worker --loglevel=info --concurrency=1 --pool=threads &

echo "Starting Celery Beat..."
celery -A app.core.celery:celery_app beat --loglevel=info --schedule=/tmp/celerybeat-schedule &

# Keep container alive and wait for all background processes
wait