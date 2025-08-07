"""
NotionFlow Main Application Entry Point
Imports and runs the Flask app from frontend/app.py
"""

import sys
import os
import datetime

# Add frontend directory to Python path
frontend_path = os.path.join(os.path.dirname(__file__), 'frontend')
sys.path.insert(0, frontend_path)

# Import the Flask app from frontend/app.py (avoid circular import)
import importlib.util
spec = importlib.util.spec_from_file_location("frontend_app", os.path.join(frontend_path, "app.py"))
frontend_app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(frontend_app)

# Get the Flask app instance
app = frontend_app.app

# Add health check endpoint for Render
@app.route('/health')
def health_check():
    """Health check endpoint for deployment monitoring"""
    return {
        'status': 'healthy',
        'message': 'NotionFlow is running successfully',
        'timestamp': str(datetime.datetime.now())
    }

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))