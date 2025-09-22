#!/bin/bash

# Railway deployment startup script
echo "🚀 Starting NotionFlow on Railway..."

# Railway provides PORT environment variable
export PORT=${PORT:-8080}
echo "Using PORT: $PORT"

# Environment check
echo "🔍 Environment check:"
echo "PORT: $PORT"
echo "FLASK_ENV: ${FLASK_ENV:-production}"
echo "PWD: $(pwd)"
echo "Python version: $(python3 --version)"

# Pre-flight checks
echo "📋 Pre-flight checks:"
python3 -c "
import sys
import os
print(f'Python path: {sys.path}')
print(f'Working directory: {os.getcwd()}')
print(f'Directory contents: {os.listdir(\".\")}')

try:
    import frontend.app
    print('✅ App import successful')
except Exception as e:
    print(f'❌ App import failed: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
" || exit 1

# Start the application
echo "🔄 Starting gunicorn server..."
exec gunicorn frontend.app:app \
    --bind 0.0.0.0:$PORT \
    --timeout 120 \
    --workers 2 \
    --threads 4 \
    --worker-class sync \
    --log-level debug \
    --access-logfile - \
    --error-logfile - \
    --preload