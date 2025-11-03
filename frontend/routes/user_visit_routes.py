"""
🚀 NodeFlow User Visit Tracking API Routes
REST API endpoints for managing user visits and popup display logic
"""

# OS 모듈을 가장 먼저 import (Railway 호환성)
import os
import sys
from functools import wraps

# 환경 변수 즉시 로드
from dotenv import load_dotenv
load_dotenv()

from flask import Blueprint, request, jsonify, session

# Add backend services to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend'))

# Flask 환경 설정 (전역) - Railway 호환성
try:
    FLASK_ENV = os.environ.get('FLASK_ENV', 'production')
except Exception as e:
    print(f"⚠️ Error loading environment variables: {e}")
    FLASK_ENV = 'production'

try:
    from services.user_visit_service import visit_service
except ImportError as e:
    print(f"Warning: Could not import visit_service: {e}")
    visit_service = None

visit_bp = Blueprint('user_visits', __name__, url_prefix='/api/visits')

def get_current_user_id():
    """Get current user ID from session"""
    return session.get('user_id')

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'Authentication required'
            }), 401
        return f(*args, **kwargs)
    return decorated_function

@visit_bp.route('/record', methods=['POST'])
@require_auth
def record_visit():
    """
    Record a user visit and get popup display decision
    
    POST /api/visits/record
    {
        "visit_type": "calendar_page"  # optional, defaults to calendar_page
    }
    """
    if not visit_service:
        return jsonify({
            'success': False,
            'error': 'Visit service not available',
            'should_show_popup': False  # Safe fallback
        }), 500
    
    try:
        user_id = get_current_user_id()
        data = request.get_json() or {}
        visit_type = data.get('visit_type', 'calendar_page')
        
        result = visit_service.record_visit(user_id, visit_type)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'should_show_popup': False  # Safe fallback
        }), 500

@visit_bp.route('/status', methods=['GET'])
@require_auth
def get_visit_status():
    """
    Get current visit status for user
    
    GET /api/visits/status?visit_type=calendar_page
    """
    if not visit_service:
        return jsonify({
            'success': False,
            'error': 'Visit service not available',
            'should_show_popup': False
        }), 500
    
    try:
        user_id = get_current_user_id()
        visit_type = request.args.get('visit_type', 'calendar_page')
        
        result = visit_service.get_user_visit_status(user_id, visit_type)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'should_show_popup': False
        }), 500

@visit_bp.route('/popup/shown', methods=['POST'])
@require_auth  
def mark_popup_shown():
    """
    Mark that popup has been shown to user
    
    POST /api/visits/popup/shown
    {
        "visit_type": "calendar_page"  # optional
    }
    """
    if not visit_service:
        return jsonify({
            'success': False,
            'error': 'Visit service not available'
        }), 500
    
    try:
        user_id = get_current_user_id()
        data = request.get_json() or {}
        visit_type = data.get('visit_type', 'calendar_page')
        
        result = visit_service.mark_popup_shown(user_id, visit_type)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@visit_bp.route('/popup/dismissed', methods=['POST'])
@require_auth
def mark_popup_dismissed():
    """
    Mark that user dismissed the popup (나중에 하기)
    
    POST /api/visits/popup/dismissed  
    {
        "visit_type": "calendar_page"  # optional
    }
    """
    if not visit_service:
        return jsonify({
            'success': False,
            'error': 'Visit service not available'
        }), 500
    
    try:
        user_id = get_current_user_id()
        data = request.get_json() or {}
        visit_type = data.get('visit_type', 'calendar_page')
        
        result = visit_service.mark_popup_dismissed(user_id, visit_type)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@visit_bp.route('/calendar/created', methods=['POST'])
@require_auth
def mark_calendar_created():
    """
    Mark that user has created a calendar
    
    POST /api/visits/calendar/created
    {
        "visit_type": "calendar_page"  # optional
    }
    """
    if not visit_service:
        return jsonify({
            'success': False,
            'error': 'Visit service not available'
        }), 500
    
    try:
        user_id = get_current_user_id()
        data = request.get_json() or {}
        visit_type = data.get('visit_type', 'calendar_page')
        
        result = visit_service.mark_calendar_created(user_id, visit_type)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@visit_bp.route('/debug/user/<user_id>', methods=['GET'])
def debug_user_visits(user_id):
    """
    Debug endpoint to view user visit data (development only)
    
    GET /api/visits/debug/user/<user_id>
    """
    # Only enable in development
    if not FLASK_ENV == 'development':
        return jsonify({'error': 'Debug endpoint only available in development'}), 403
    
    if not visit_service:
        return jsonify({'error': 'Visit service not available'}), 500
    
    try:
        result = visit_service.get_user_visit_status(user_id, 'calendar_page')
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Error handlers
@visit_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Visit endpoint not found'}), 404

@visit_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal visit tracking error'}), 500