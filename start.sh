#!/bin/bash

# Railway deployment startup script
echo "🚀 Starting NotionFlow on Railway..."

# Set default port if PORT environment variable is not set
if [ -z "$PORT" ]; then
    export PORT=5003
    echo "PORT not set, defaulting to 5003"
else
    echo "Using PORT: $PORT"
fi

# Environment check
echo "🔍 Environment check:"
echo "PORT: $PORT"
echo "FLASK_ENV: ${FLASK_ENV:-production}"

# Pre-flight checks
echo "📋 Pre-flight checks:"
python3 -c "import frontend.app; print('✅ App import successful')" || {
    echo "❌ App import failed"
    exit 1
}

# Start the application
echo "🔄 Starting gunicorn server..."
exec gunicorn frontend.app:app \
    --bind 0.0.0.0:$PORT \
    --timeout 300 \
    --workers 1 \
    --threads 4 \
    --worker-class sync \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    --preload