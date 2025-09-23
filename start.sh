#!/bin/bash

# Railway deployment startup script - Simplified version
echo "Starting NotionFlow..."

# Use Railway's PORT or default to 8080
PORT=${PORT:-8080}
echo "PORT: $PORT"

# Start gunicorn with optimized configuration for Railway
exec gunicorn frontend.app:app \
    --bind 0.0.0.0:$PORT \
    --workers 1 \
    --timeout 300 \
    --graceful-timeout 30 \
    --keep-alive 2 \
    --max-requests 500 \
    --max-requests-jitter 50 \
    --preload \
    --worker-class sync \
    --worker-connections 500 \
    --log-level info \
    --access-logfile - \
    --error-logfile -