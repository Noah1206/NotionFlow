#!/bin/bash

# Railway deployment startup script - Simplified version
echo "Starting NotionFlow..."

# Use Railway's PORT or default to 8080
PORT=${PORT:-8080}
echo "PORT: $PORT"

# Start gunicorn with minimal configuration
exec gunicorn frontend.app:app \
    --bind 0.0.0.0:$PORT \
    --workers 1 \
    --log-level info