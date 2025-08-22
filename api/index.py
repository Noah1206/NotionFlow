"""
Vercel Serverless Function Handler for NotionFlow
This file serves as the entry point for Vercel deployments
"""

import sys
import os
from pathlib import Path

# Add the project root and frontend directory to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'frontend'))

# Import the Flask app
try:
    from frontend.app import app
    
    # Vercel expects a handler named 'app' or needs to be explicitly exported
    handler = app
    
    # For local testing
    if __name__ == "__main__":
        app.run(debug=True, host='0.0.0.0', port=5000)
        
except ImportError as e:
    print(f"Error importing Flask app: {e}")
    print(f"Python path: {sys.path}")
    raise