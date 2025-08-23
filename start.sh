#!/bin/bash

# Set default port if PORT environment variable is not set
if [ -z "$PORT" ]; then
    export PORT=8080
    echo "PORT not set, defaulting to 8080"
else
    echo "Using PORT: $PORT"
fi

echo "Starting server on port $PORT"

# Start gunicorn with the configured port
gunicorn frontend.app:app --bind 0.0.0.0:$PORT --timeout 120 --workers 2 --threads 4