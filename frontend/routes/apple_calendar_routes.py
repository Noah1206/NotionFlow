"""
Apple Calendar Sync Routes
Handles Apple Calendar synchronization endpoints
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend'))
try:
    from backend.services.apple_calendar_service import apple_calendar_sync
    print("✅ [APPLE ROUTE] Apple calendar service imported successfully")
except ImportError as e:
    print(f"❌ [APPLE ROUTE] Failed to import apple_calendar_service: {e}")
    try:
        from services.apple_calendar_service import apple_calendar_sync
        print("✅ [APPLE ROUTE] Apple calendar service imported (fallback)")
    except ImportError as e2:
        print(f"❌ [APPLE ROUTE] Fallback import also failed: {e2}")
        apple_calendar_sync = None

from utils.auth_manager import AuthManager
from utils.config import config

apple_calendar_bp = Blueprint('apple_calendar', __name__, url_prefix='/api/apple-calendar')

def get_current_user_id():
    """Get current authenticated user ID"""
    return AuthManager.get_current_user_id()

@apple_calendar_bp.route('/sync', methods=['POST'])
def sync_apple_calendar():
    """Trigger Apple Calendar synchronization"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401

    try:
        data = request.get_json() or {}
        calendar_id = data.get('calendar_id')
        date_range = data.get('date_range', {})

        print(f"🍎 [APPLE ROUTE] Starting sync for user {user_id}, calendar {calendar_id}")
        if date_range:
            print(f"🍎 [APPLE ROUTE] Date range: {date_range.get('start_date')} to {date_range.get('end_date')}")

        # Check if service is available
        if apple_calendar_sync is None:
            print(f"❌ [APPLE ROUTE] Apple calendar sync service not available")
            return jsonify({
                'success': False,
                'error': 'Apple Calendar sync service not available'
            }), 500

        # Trigger sync
        result = apple_calendar_sync.sync_to_calendar(user_id, calendar_id, date_range)

        if result.get('success'):
            print(f"✅ [APPLE ROUTE] Sync completed: {result.get('synced_events')} events")
            return jsonify({
                'success': True,
                'message': f"Successfully synced {result.get('synced_events')} events from Apple Calendar",
                'synced_events': result.get('synced_events'),
                'total_events': result.get('total_events'),
                'calendar_id': result.get('calendar_id')
            })
        else:
            print(f"❌ [APPLE ROUTE] Sync failed: {result.get('error')}")
            return jsonify({
                'success': False,
                'error': result.get('error', 'Sync failed'),
                'synced_events': 0
            }), 400

    except Exception as e:
        print(f"❌ [APPLE ROUTE] Error in sync endpoint: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@apple_calendar_bp.route('/test-fetch', methods=['POST'])
def test_fetch_events():
    """Test fetching events from Apple Calendar"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401

    try:
        # Get Apple credentials
        supabase = config.get_client_for_user(user_id)
        result = supabase.table('calendar_sync_configs').select('*').eq('user_id', user_id).eq('platform', 'apple').execute()

        if not result.data:
            return jsonify({
                'success': False,
                'error': 'Apple Calendar not connected'
            }), 400

        credentials = result.data[0].get('credentials', {})

        # Test fetching events
        from services.apple_calendar_service import AppleCalendarSync
        sync_service = AppleCalendarSync()

        apple_creds = {
            'server_url': credentials.get('server_url', 'https://caldav.icloud.com'),
            'username': credentials.get('username'),
            'password': credentials.get('password')
        }

        events = sync_service._fetch_apple_events(apple_creds)

        return jsonify({
            'success': True,
            'event_count': len(events),
            'events': events[:10]  # Return first 10 events as sample
        })

    except Exception as e:
        print(f"❌ [APPLE ROUTE] Error testing fetch: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@apple_calendar_bp.route('/status', methods=['GET'])
def get_apple_sync_status():
    """Get Apple Calendar sync status"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401

    try:
        supabase = config.get_client_for_user(user_id)

        # Check Apple connection status
        config_result = supabase.table('calendar_sync_configs').select('*').eq('user_id', user_id).eq('platform', 'apple').execute()

        if not config_result.data:
            return jsonify({
                'success': True,
                'connected': False,
                'message': 'Apple Calendar not connected'
            })

        config_data = config_result.data[0]
        credentials = config_data.get('credentials', {})

        return jsonify({
            'success': True,
            'connected': credentials.get('connected', False),
            'enabled': config_data.get('is_enabled', False),
            'calendar_selected': bool(config_data.get('calendar_id')),
            'calendar_id': config_data.get('calendar_id'),
            'last_sync': config_data.get('last_sync_at'),
            'sync_status': config_data.get('sync_status', 'disconnected'),
            'credentials_available': bool(credentials.get('username') and credentials.get('password'))
        })

    except Exception as e:
        print(f"❌ [APPLE ROUTE] Error getting status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@apple_calendar_bp.route('/disconnect', methods=['POST'])
def disconnect_apple_calendar():
    """Disconnect Apple Calendar - 안전한 Apple 전용 연결해제"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401

    try:
        supabase = config.get_client_for_user(user_id)

        print(f"🍎 [APPLE DISCONNECT] 사용자 {user_id} Apple Calendar 연결해제 시작")

        # calendar_sync_configs에서 Apple 연결 비활성화
        config_result = supabase.table('calendar_sync_configs').select('*').eq('user_id', user_id).eq('platform', 'apple').execute()

        if config_result.data:
            # 연결 비활성화 (데이터는 보존하되 is_enabled와 sync_status 업데이트)
            update_result = supabase.table('calendar_sync_configs').update({
                'is_enabled': False,
                'sync_status': 'disconnected',
                'updated_at': datetime.now().isoformat()
            }).eq('user_id', user_id).eq('platform', 'apple').execute()
            print(f"✅ [APPLE DISCONNECT] calendar_sync_configs 비활성화 완료: {len(update_result.data)} 행 업데이트")
        else:
            print(f"ℹ️ [APPLE DISCONNECT] Apple 연결 설정이 없습니다 - 이미 연결해제된 상태일 수 있습니다")

        print(f"🍎 [APPLE DISCONNECT] 사용자 {user_id} Apple Calendar 연결해제 완료")

        return jsonify({
            'success': True,
            'message': 'Apple Calendar 연결이 해제되었습니다.'
        })

    except Exception as e:
        print(f"❌ [APPLE DISCONNECT] 연결해제 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500