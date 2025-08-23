"""
🔄 Manual Sync Routes
Enhanced sync management with scheduler integration and activity tracking
"""

from flask import Blueprint, request, jsonify
from utils.auth_manager import AuthManager
from utils.sync_scheduler import trigger_manual_sync, get_sync_status
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from backend.services.sync_tracking_service import sync_tracker, EventType, ActivityType

# Supabase 설정 (전역) - Railway 호환성
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_API_KEY') or os.getenv('SUPABASE_ANON_KEY')

sync_bp = Blueprint('sync', __name__, url_prefix='/api/sync')

@sync_bp.route('/trigger', methods=['POST'])
def trigger_sync():
    """Trigger manual sync for current user"""
    try:
        user_id = AuthManager.get_current_user_id()
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json() or {}
        platform = data.get('platform')  # Optional - sync specific platform
        
        # Track sync trigger activity
        sync_tracker.track_user_activity(
            user_id=user_id,
            activity_type=ActivityType.SYNC_TRIGGERED,
            platform=platform,
            details={'manual': True, 'source': 'web_ui'},
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        # Trigger sync
        result = trigger_manual_sync(user_id, platform)
        
        if 'error' in result:
            # Track failed sync
            sync_tracker.track_sync_event(
                user_id=user_id,
                event_type=EventType.SYNC_FAILED,
                platform=platform or 'all',
                status='failed',
                error_message=result.get('error')
            )
            return jsonify(result), 400
        
        # Track successful sync start
        sync_tracker.track_sync_event(
            user_id=user_id,
            event_type=EventType.SYNC_STARTED,
            platform=platform or 'all',
            status='pending',
            metadata={'sync_type': 'manual'}
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Sync trigger failed: {str(e)}'}), 500

@sync_bp.route('/status', methods=['GET'])
def sync_status():
    """Get sync scheduler status"""
    try:
        status = get_sync_status()
        return jsonify({
            'success': True,
            'status': status
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get sync status: {str(e)}'}), 500

@sync_bp.route('/user-status', methods=['GET'])
def user_sync_status():
    """Get sync status for current user"""
    try:
        user_id = AuthManager.get_current_user_id()
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Import here to avoid circular imports
        from supabase import create_client
        
        if not SUPABASE_URL or not SUPABASE_KEY:
            return jsonify({'error': 'Database configuration error'}), 500
            
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Get user's sync configurations
        result = supabase.table('calendar_sync_configs').select('''
            platform, is_enabled, last_sync_at, consecutive_failures,
            sync_frequency_minutes, sync_errors
        ''').eq('user_id', user_id).execute()
        
        platforms = {}
        for config in result.data:
            platform = config['platform']
            platforms[platform] = {
                'enabled': config['is_enabled'],
                'last_sync': config['last_sync_at'],
                'sync_frequency': config['sync_frequency_minutes'],
                'health': 'healthy' if config['consecutive_failures'] == 0 else 'error',
                'consecutive_failures': config['consecutive_failures'],
                'recent_errors': config.get('sync_errors', [])[-3:] if config.get('sync_errors') else []
            }
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'platforms': platforms,
            'summary': {
                'total_platforms': len(platforms),
                'enabled_platforms': len([p for p in platforms.values() if p['enabled']]),
                'healthy_platforms': len([p for p in platforms.values() if p['health'] == 'healthy'])
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get user sync status: {str(e)}'}), 500

@sync_bp.route('/history', methods=['GET'])
def sync_history():
    """Get sync history for current user"""
    try:
        user_id = AuthManager.get_current_user_id()
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Import here to avoid circular imports
        from supabase import create_client
        
        if not SUPABASE_URL or not SUPABASE_KEY:
            return jsonify({'error': 'Database configuration error'}), 500
            
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Get sync configurations with error history
        result = supabase.table('calendar_sync_configs').select('''
            platform, last_sync_at, sync_errors, consecutive_failures
        ''').eq('user_id', user_id).execute()
        
        history = []
        for config in result.data:
            platform = config['platform']
            errors = config.get('sync_errors', [])
            
            # Add recent sync attempts to history
            for error in errors[-10:]:  # Last 10 errors
                history.append({
                    'platform': platform,
                    'timestamp': error['timestamp'],
                    'status': 'error',
                    'message': error['error']
                })
            
            # Add last successful sync if available
            if config['last_sync_at'] and config['consecutive_failures'] == 0:
                history.append({
                    'platform': platform,
                    'timestamp': config['last_sync_at'],
                    'status': 'success',
                    'message': 'Sync completed successfully'
                })
        
        # Sort by timestamp (newest first)
        history.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({
            'success': True,
            'history': history[:20]  # Return last 20 events
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get sync history: {str(e)}'}), 500

@sync_bp.route('/activity/recent', methods=['GET'])
def get_recent_activity():
    """Get recent sync activity with detailed tracking"""
    try:
        user_id = AuthManager.get_current_user_id()
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Get query parameters
        limit = request.args.get('limit', 20, type=int)
        platform = request.args.get('platform')
        activity_type = request.args.get('type')
        
        # Get recent activities
        activities = sync_tracker.get_recent_activity(
            user_id=user_id,
            limit=limit,
            activity_type=activity_type,
            platform=platform
        )
        
        return jsonify({
            'success': True,
            'activities': activities
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get recent activity: {str(e)}'}), 500

@sync_bp.route('/events/recent', methods=['GET'])
def get_recent_sync_events():
    """Get recent sync events"""
    try:
        user_id = AuthManager.get_current_user_id()
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Get query parameters
        limit = request.args.get('limit', 20, type=int)
        platform = request.args.get('platform')
        status = request.args.get('status')
        
        # Get recent sync events
        events = sync_tracker.get_recent_sync_events(
            user_id=user_id,
            limit=limit,
            platform=platform,
            status=status
        )
        
        return jsonify({
            'success': True,
            'events': events
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get sync events: {str(e)}'}), 500

@sync_bp.route('/coverage', methods=['GET'])
def get_platform_coverage():
    """Get platform coverage statistics"""
    try:
        user_id = AuthManager.get_current_user_id()
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Get platform coverage
        coverage = sync_tracker.get_platform_coverage(user_id)
        
        # Calculate overall statistics
        total_platforms = len(coverage)
        connected_platforms = sum(1 for p in coverage.values() if p['is_connected'])
        total_synced = sum(p['total_synced_items'] for p in coverage.values())
        total_failed = sum(p['total_failed_items'] for p in coverage.values())
        
        return jsonify({
            'success': True,
            'platforms': coverage,
            'summary': {
                'total_platforms': total_platforms,
                'connected_platforms': connected_platforms,
                'total_synced_items': total_synced,
                'total_failed_items': total_failed,
                'overall_success_rate': round((total_synced / (total_synced + total_failed) * 100) if (total_synced + total_failed) > 0 else 0, 2)
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get platform coverage: {str(e)}'}), 500

@sync_bp.route('/analytics', methods=['GET'])
def get_sync_analytics():
    """Get sync analytics"""
    try:
        user_id = AuthManager.get_current_user_id()
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Get query parameters
        period = request.args.get('period', 'daily')
        limit = request.args.get('limit', 7, type=int)
        
        # Get analytics data
        analytics = sync_tracker.get_sync_analytics(
            user_id=user_id,
            period_type=period,
            limit=limit
        )
        
        return jsonify({
            'success': True,
            'analytics': analytics,
            'period': period
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get sync analytics: {str(e)}'}), 500

@sync_bp.route('/summary', methods=['GET'])
def get_platform_sync_summary():
    """Get comprehensive platform sync summary"""
    try:
        user_id = AuthManager.get_current_user_id()
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Get platform summary
        summary = sync_tracker.get_platform_sync_summary(user_id)
        
        return jsonify({
            'success': True,
            'summary': summary
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get platform summary: {str(e)}'}), 500

# Error handlers
@sync_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Sync endpoint not found'}), 404

@sync_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Sync internal error'}), 500