"""
Vercel Serverless Function Handler for NotionFlow
This file serves as the entry point for Vercel deployments
"""

import sys
import os
from pathlib import Path

# Add the project root and utils directory to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'utils'))

# Set up minimal environment if needed
os.environ.setdefault('FLASK_ENV', 'production')

# Import the Flask app with error handling
try:
    # First try to import from the main app.py
    from app import app
except ImportError:
    try:
        # If that fails, try from frontend
        from frontend.app import app
    except ImportError as e:
        # Create a minimal Flask app if import fails
        from flask import Flask, jsonify
        app = Flask(__name__)
        
        @app.route('/')
        def index():
            return jsonify({
                "error": "Application failed to load",
                "details": str(e),
                "python_path": sys.path
            }), 500
        
        @app.route('/health')
        def health():
            return jsonify({"status": "error", "message": str(e)}), 500

# Vercel expects the Flask app to be named 'app'
# No need to rename it

# For local testing
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)