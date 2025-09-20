"""
Session Cleanup Routes
세션에서 오래된 OAuth 및 동기화 데이터를 정리
"""

from flask import Blueprint, session, jsonify
from datetime import datetime

session_cleanup_bp = Blueprint('session_cleanup', __name__, url_prefix='/api/session')

@session_cleanup_bp.route('/cleanup-notion', methods=['POST'])
def cleanup_notion_session():
    """Clean up Notion-related session data"""
    try:
        keys_to_remove = []
        
        # Find all Notion-related session keys
        for key in session.keys():
            if any(keyword in key.lower() for keyword in ['notion', '3e7f438e', 'calendar_sync']):
                keys_to_remove.append(key)
        
        # Remove the keys
        for key in keys_to_remove:
            session.pop(key, None)
            
        # Also clear specific Notion flags
        session.pop('notion_connected', None)
        session.pop('notion_oauth_completed', None)
        session.pop('notion_needs_calendar_selection', None)
        session.pop('notion_calendar_id', None)
        
        return jsonify({
            'success': True,
            'message': f'Cleaned up {len(keys_to_remove)} Notion session entries',
            'removed_keys': keys_to_remove
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to cleanup session: {str(e)}'
        }), 500

@session_cleanup_bp.route('/status', methods=['GET'])
def get_session_status():
    """Get current session status for debugging"""
    try:
        notion_keys = []
        calendar_keys = []
        oauth_keys = []
        
        for key in session.keys():
            if 'notion' in key.lower():
                notion_keys.append(key)
            elif 'calendar' in key.lower():
                calendar_keys.append(key)
            elif 'oauth' in key.lower():
                oauth_keys.append(key)
                
        return jsonify({
            'success': True,
            'user_id': session.get('user_id'),
            'notion_keys': notion_keys,
            'calendar_keys': calendar_keys,
            'oauth_keys': len(oauth_keys),  # Don't expose sensitive data
            'total_session_keys': len(session.keys())
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get session status: {str(e)}'
        }), 500