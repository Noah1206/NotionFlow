"""
NotionFlow Main Application Entry Point
Imports and runs the Flask app from frontend/app.py
"""

import sys
import os

# Add frontend directory to Python path
frontend_path = os.path.join(os.path.dirname(__file__), 'frontend')
sys.path.insert(0, frontend_path)

# Import the Flask app directly from frontend
from frontend.app import app

# Health check is handled in frontend/app.py

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))