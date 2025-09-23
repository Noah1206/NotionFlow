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
    --timeout 600 \
    --keep-alive 2 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --preload \
    --worker-class sync \
    --worker-connections 1000 \
    --log-level info