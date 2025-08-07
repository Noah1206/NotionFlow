"""
📊 Sync Status API Routes
Enhanced sync status tracking and management endpoints
"""

from flask import Blueprint, request, jsonify
from utils.auth_manager import AuthManager
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend'))
from services.sync_status_service import get_sync_status_service

sync_status_bp = Blueprint('sync_status', __name__, url_prefix='/api/sync-status')

@sync_status_bp.route('/overview', methods=['GET'])
def get_sync_overview():
    """Get complete sync status overview for current user"""
    try:
        user_id = AuthManager.get_current_user_id()
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        sync_service = get_sync_status_service()
        result = sync_service.get_user_sync_status(user_id)
        
        if not result['success']:
            return jsonify({'error': result.get('error')}), 500
        
        return jsonify({
            'success': True,
            'data': {
                'platforms': result['platforms'],
                'summary': result['summary']
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get sync overview: {str(e)}'}), 500

@sync_status_bp.route('/platform/<platform>', methods=['GET'])
def get_platform_status(platform):
    """Get sync status for specific platform"""
    try:
        user_id = AuthManager.get_current_user_id()
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        sync_service = get_sync_status_service()
        result = sync_service.get_user_sync_status(user_id)
        
        if not result['success']:
            return jsonify({'error': result.get('error')}), 500
        
        platform_data = result['platforms'].get(platform)
        if not platform_data:
            return jsonify({'error': f'No sync data found for platform: {platform}'}), 404
        
        return jsonify({
            'success': True,
            'platform': platform,
            'data': platform_data
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get platform status: {str(e)}'}), 500

@sync_status_bp.route('/platform/<platform>/connect', methods=['POST'])
def connect_platform(platform):
    """Update platform connection status"""
    try:
        user_id = AuthManager.get_current_user_id()
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json() or {}
        is_connected = data.get('is_connected', True)
        credentials = data.get('credentials')  # Optional encrypted credentials
        
        sync_service = get_sync_status_service()
        result = sync_service.update_platform_connection(
            user_id=user_id,
            platform=platform,
            is_connected=is_connected,
            credentials=credentials
        )
        
        if not result['success']:
            return jsonify({'error': result.get('error')}), 500
        
        return jsonify({
            'success': True,
            'message': result['message']
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to update platform connection: {str(e)}'}), 500

@sync_status_bp.route('/platform/<platform>/frequency', methods=['PUT'])
def update_sync_frequency(platform):
    """Update sync frequency for a platform"""
    try:
        user_id = AuthManager.get_current_user_id()
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json() or {}
        frequency_minutes = data.get('frequency_minutes')
        
        if not frequency_minutes:
            return jsonify({'error': 'frequency_minutes is required'}), 400
        
        sync_service = get_sync_status_service()
        result = sync_service.update_sync_frequency(
            user_id=user_id,
            platform=platform,
            frequency_minutes=frequency_minutes
        )
        
        if not result['success']:
            return jsonify({'error': result.get('error')}), 400
        
        return jsonify({
            'success': True,
            'message': result['message']
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to update sync frequency: {str(e)}'}), 500

@sync_status_bp.route('/platform/<platform>/toggle', methods=['PUT'])
def toggle_platform_sync(platform):
    """Enable or disable sync for a platform"""
    try:
        user_id = AuthManager.get_current_user_id()
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json() or {}
        is_active = data.get('is_active', True)
        
        sync_service = get_sync_status_service()
        result = sync_service.toggle_platform_sync(
            user_id=user_id,
            platform=platform,
            is_active=is_active
        )
        
        if not result['success']:
            return jsonify({'error': result.get('error')}), 500
        
        return jsonify({
            'success': True,
            'message': result['message']
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to toggle platform sync: {str(e)}'}), 500

@sync_status_bp.route('/history', methods=['GET'])
def get_sync_history():
    """Get sync history for current user"""
    try:
        user_id = AuthManager.get_current_user_id()
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        platform = request.args.get('platform')  # Optional filter
        limit = int(request.args.get('limit', 20))
        
        sync_service = get_sync_status_service()
        result = sync_service.get_sync_history(
            user_id=user_id,
            platform=platform,
            limit=limit
        )
        
        if not result['success']:
            return jsonify({'error': result.get('error')}), 500
        
        return jsonify({
            'success': True,
            'history': result['history']
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get sync history: {str(e)}'}), 500

@sync_status_bp.route('/manual-sync', methods=['POST'])
def trigger_manual_sync():
    """Trigger manual sync for specific platform or all platforms"""
    try:
        user_id = AuthManager.get_current_user_id()
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json() or {}
        platform = data.get('platform')  # Optional - sync specific platform
        
        # Import sync scheduler
        from utils.sync_scheduler import trigger_manual_sync
        
        # Trigger sync through existing scheduler
        result = trigger_manual_sync(user_id, platform)
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify({
            'success': True,
            'message': result.get('message', 'Sync triggered successfully'),
            'results': result.get('results')
        })
        
    except Exception as e:
        return jsonify({'error': f'Manual sync failed: {str(e)}'}), 500

# Error handlers
@sync_status_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Sync status endpoint not found'}), 404

@sync_status_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500