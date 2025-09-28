"""
플랫폼 캘린더 연동 API 엔드포인트
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
from utils.auth_manager import AuthManager
from utils.config import config

def check_auth():
    """Check if user is authenticated and return user_id or error response"""
    user_id = AuthManager.get_current_user_id()
    if not user_id:
        return None, jsonify({'error': 'Authentication required', 'code': 'AUTH_REQUIRED'}), 401
    return user_id, None, None

def get_current_user_id():
    return AuthManager.get_current_user_id()

platform_connect_bp = Blueprint('platform_connect', __name__)

@platform_connect_bp.route('/calendar/connect-platform', methods=['POST'])
def connect_platform():
    """플랫폼과 사용자 캘린더 연동"""
    user_id, error_response, status_code = check_auth()
    if error_response:
        return error_response, status_code
    
    try:
        data = request.get_json()
        platform = data.get('platform')
        calendar_id = data.get('calendar_id')
        import_existing = data.get('import_existing', False)
        real_time_sync = data.get('real_time_sync', True)
        
        if not platform or not calendar_id:
            return jsonify({
                'success': False,
                'error': 'Platform and calendar_id are required'
            }), 400
            
        # 지원되는 플랫폼 확인
        supported_platforms = ['notion', 'google', 'apple', 'outlook']
        if platform not in supported_platforms:
            return jsonify({
                'success': False,
                'error': f'Unsupported platform: {platform}'
            }), 400
        
        # 사용자 캘린더 존재 확인
        supabase = config.get_client_for_user(user_id)
        calendar_result = supabase.table('calendars').select('*').eq('id', calendar_id).eq('owner_id', user_id).execute()
        
        if not calendar_result.data:
            return jsonify({
                'success': False,
                'error': 'Calendar not found or access denied'
            }), 404
            
        calendar_info = calendar_result.data[0]
        
        # 플랫폼 연결 상태 확인
        platform_result = supabase.table('calendar_sync_configs').select('*').eq('user_id', user_id).eq('platform', platform).execute()
        
        if not platform_result.data:
            return jsonify({
                'success': False,
                'error': f'{platform} is not connected. Please connect the platform first.'
            }), 400
            
        platform_config = platform_result.data[0]
        
        # 이미 다른 캘린더와 연동되어 있는지 확인
        if platform_config.get('calendar_id') and platform_config['calendar_id'] != calendar_id:
            # 기존 연동 해제 후 새로운 캘린더와 연동
            print(f"🔄 Switching {platform} sync from {platform_config['calendar_id']} to {calendar_id}")
        
        # 연동 설정 업데이트
        update_data = {
            'sync_direction': 'bidirectional' if real_time_sync else 'import_only',
            'is_enabled': True,
            'updated_at': datetime.now().isoformat(),
            'credentials': {
                'calendar_id': calendar_id,
                'import_existing': import_existing,
                'real_time_sync': real_time_sync,
                'calendar_name': calendar_info['name'],
                'connected_at': datetime.now().isoformat()
            }
        }
        
        supabase.table('calendar_sync_configs').update(update_data).eq('user_id', user_id).eq('platform', platform).execute()
        
        print(f"✅ Platform {platform} connected to calendar {calendar_id} for user {user_id}")
        
        # 기존 일정 가져오기 (선택한 경우)
        synced_events = 0
        if import_existing:
            try:
                synced_events = await_import_existing_events(platform, user_id, calendar_id)
            except Exception as e:
                print(f"⚠️ Failed to import existing events: {e}")
                # 연동은 성공했지만 기존 일정 가져오기는 실패
        
        return jsonify({
            'success': True,
            'message': f'{platform} calendar sync enabled',
            'calendar_id': calendar_id,
            'calendar_name': calendar_info['name'],
            'synced_events': synced_events,
            'import_existing': import_existing,
            'real_time_sync': real_time_sync
        })
        
    except Exception as e:
        print(f"❌ Error connecting platform: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@platform_connect_bp.route('/calendar/disconnect-platform', methods=['POST'])
def disconnect_platform():
    """플랫폼 캘린더 연동 해제"""
    user_id, error_response, status_code = check_auth()
    if error_response:
        return error_response, status_code
    
    try:
        data = request.get_json()
        platform = data.get('platform')
        
        if not platform:
            return jsonify({
                'success': False,
                'error': 'Platform is required'
            }), 400
        
        supabase = config.get_client_for_user(user_id)
        
        # 연동 설정 업데이트 (연동 해제)
        update_data = {
            'is_enabled': False,
            'updated_at': datetime.now().isoformat(),
            'credentials': {
                'disconnected': True,
                'disconnected_at': datetime.now().isoformat()
            }
        }
        
        result = supabase.table('calendar_sync_configs').update(update_data).eq('user_id', user_id).eq('platform', platform).execute()
        
        if not result.data:
            return jsonify({
                'success': False,
                'error': f'{platform} connection not found'
            }), 404
        
        print(f"✅ Platform {platform} disconnected for user {user_id}")
        
        return jsonify({
            'success': True,
            'message': f'{platform} calendar sync disabled'
        })
        
    except Exception as e:
        print(f"❌ Error disconnecting platform: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def await_import_existing_events(platform: str, user_id: str, calendar_id: str) -> int:
    """기존 이벤트 가져오기 (동기 함수로 처리)"""
    try:
        if platform == 'notion':
            from services.notion_sync import NotionCalendarSync
            notion_sync = NotionCalendarSync()
            # Let the sync service determine the correct calendar_id from database
            result = notion_sync.sync_to_calendar(user_id)
            return result.get('synced_events', 0)
        elif platform == 'google':
            # Google Calendar 동기화 로직 (향후 구현)
            return 0
        elif platform == 'apple':
            # Apple Calendar 동기화 로직 (향후 구현)
            return 0
        elif platform == 'outlook':
            # Outlook 동기화 로직 (향후 구현)
            return 0
        else:
            print(f"⚠️ Unsupported platform for import: {platform}")
            return 0
            
    except Exception as e:
        print(f"❌ Error importing events from {platform}: {e}")
        return 0

@platform_connect_bp.route('/api/platform/google/connect', methods=['POST'])
def connect_google_calendar():
    """Google Calendar 연결 상태 저장 (클라이언트 localStorage와 동기화)"""
    try:
        print(f"🔍 Google Calendar connect request received")

        user_id, error_response, status_code = check_auth()
        if error_response:
            print(f"❌ Auth error: {error_response}")
            return error_response, status_code

        print(f"✅ User authenticated: {user_id}")

        data = request.get_json() or {}
        calendar_id = data.get('calendar_id')
        print(f"📅 Calendar ID received: {calendar_id}")

        if not calendar_id:
            error_response = {
                'success': False,
                'error': 'calendar_id is required'
            }
            print(f"❌ Missing calendar_id: {error_response}")
            return jsonify(error_response), 400

        try:
            from utils.config import config
            supabase = config.get_client_for_user(user_id)
            print(f"✅ Supabase client obtained")
        except Exception as e:
            print(f"❌ Failed to get Supabase client: {e}")
            return jsonify({
                'success': False,
                'error': f'Database connection error: {str(e)}'
            }), 500

        try:
            # Google Calendar 연결 정보 저장 또는 업데이트
            existing = supabase.table('calendar_sync_configs').select('*').eq('user_id', user_id).eq('platform', 'google').execute()
            print(f"✅ Checked existing config: {len(existing.data) if existing.data else 0} records found")
        except Exception as e:
            print(f"❌ Database query error: {e}")
            return jsonify({
                'success': False,
                'error': f'Database query error: {str(e)}'
            }), 500

        # Store OAuth info in credentials JSON field (no calendar_id yet)
        connection_data = {
            'user_id': user_id,
            'platform': 'google',
            'is_enabled': False,  # Not enabled until calendar is selected
            'sync_direction': 'bidirectional',
            'updated_at': datetime.now().isoformat(),
            'credentials': {
                'oauth_connected': True,
                'google_calendar_id': calendar_id,  # Store Google calendar email here
                'connected_at': datetime.now().isoformat(),
                'real_time_sync': True,
                'needs_calendar_selection': True  # Flag that calendar selection is needed
            }
        }

        try:
            if existing.data:
                # Update existing record
                result = supabase.table('calendar_sync_configs').update(connection_data).eq('user_id', user_id).eq('platform', 'google').execute()
                print(f"✅ Updated existing config")
            else:
                # Insert new record
                connection_data['created_at'] = datetime.now().isoformat()
                result = supabase.table('calendar_sync_configs').insert(connection_data).execute()
                print(f"✅ Inserted new config")

            print(f"✅ Google Calendar {calendar_id} connected for user {user_id}")
        except Exception as e:
            print(f"❌ Database operation error: {e}")
            return jsonify({
                'success': False,
                'error': f'Database operation error: {str(e)}'
            }), 500

        return jsonify({
            'success': True,
            'message': 'Google Calendar OAuth connected successfully. Please select a calendar to sync with.',
            'google_calendar_id': calendar_id,
            'needs_calendar_selection': True
        })

    except Exception as e:
        print(f"❌ Unexpected error connecting Google Calendar: {e}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500

@platform_connect_bp.route('/api/platform/google/disconnect', methods=['POST'])
def disconnect_google_calendar():
    """Google Calendar 연결 해제"""
    user_id, error_response, status_code = check_auth()
    if error_response:
        return error_response, status_code

    try:
        supabase = config.get_client_for_user(user_id)

        # Google Calendar 연결 정보 삭제 또는 비활성화
        update_data = {
            'is_enabled': False,
            'updated_at': datetime.now().isoformat(),
            'credentials': {
                'oauth_connected': False,
                'disconnected_at': datetime.now().isoformat()
            }
        }

        result = supabase.table('calendar_sync_configs').update(update_data).eq('user_id', user_id).eq('platform', 'google').execute()

        print(f"✅ Google Calendar disconnected for user {user_id}")

        return jsonify({
            'success': True,
            'message': 'Google Calendar disconnected successfully'
        })

    except Exception as e:
        print(f"❌ Error disconnecting Google Calendar: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@platform_connect_bp.route('/calendar/platform-status', methods=['GET'])
def get_calendar_platform_status():
    """플랫폼 연동 상태 조회"""
    user_id, error_response, status_code = check_auth()
    if error_response:
        return error_response, status_code

    try:
        supabase = config.get_client_for_user(user_id)

        # 모든 플랫폼 연동 상태 조회
        result = supabase.table('calendar_sync_configs').select('''
            platform, is_enabled, credentials, updated_at
        ''').eq('user_id', user_id).execute()

        platform_status = {}
        for config in result.data:
            platform = config['platform']
            credentials = config.get('credentials', {})
            platform_status[platform] = {
                'connected': credentials.get('oauth_connected', False) or credentials.get('calendar_id') is not None,
                'calendar_id': credentials.get('calendar_id'),
                'enabled': config.get('is_enabled', False),
                'real_time_sync': credentials.get('real_time_sync', False),
                'last_sync_at': config.get('updated_at'),
                'calendar_name': credentials.get('calendar_name')
            }

        return jsonify({
            'success': True,
            'platforms': platform_status
        })

    except Exception as e:
        print(f"❌ Error getting platform status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@platform_connect_bp.route('/api/google-calendar/calendar-state', methods=['GET'])
def get_google_calendar_state():
    """Google Calendar 캘린더 선택 상태 조회 (노션과 동일한 패턴)"""
    try:
        user_id, error_response, status_code = check_auth()
        if error_response:
            return error_response, status_code

        supabase = config.get_client_for_user(user_id)

        # Google Calendar 연동 상태 확인
        result = supabase.table('calendar_sync_configs').select('*').eq('user_id', user_id).eq('platform', 'google').execute()

        if not result.data:
            return jsonify({
                'success': True,
                'needs_calendar_selection': False,
                'oauth_connected': False,
                'message': 'Google Calendar not connected'
            })

        config_data = result.data[0]
        credentials = config_data.get('credentials', {})
        oauth_connected = credentials.get('oauth_connected', False)
        has_calendar_id = credentials.get('calendar_id') is not None
        is_enabled = config_data.get('is_enabled', False)

        # OAuth는 연결되었지만 캘린더 선택이 안된 경우
        needs_selection = oauth_connected and not (has_calendar_id and is_enabled)

        return jsonify({
            'success': True,
            'needs_calendar_selection': needs_selection,
            'oauth_connected': oauth_connected,
            'calendar_connected': has_calendar_id and is_enabled,
            'message': 'Calendar selection needed' if needs_selection else 'Ready'
        })

    except Exception as e:
        print(f"❌ Error getting Google Calendar state: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500