#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "Waiting for postgres..."

# Use a simple loop to check if the port is open
# 'db' is the service name from your docker-compose
while ! nc -z db 5432; do
  sleep 0.1
done

echo "PostgreSQL started"

# Run migrations
echo "Applying database migrations..."
alembic -c app/alembic.ini upgrade head

# Start the actual application
echo "Starting FastAPI..."
exec "$@"