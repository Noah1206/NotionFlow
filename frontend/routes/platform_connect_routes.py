"""
플랫폼 캘린더 연동 API 엔드포인트
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
from utils.auth import require_auth, get_current_user_id
from utils.config import config

platform_connect_bp = Blueprint('platform_connect', __name__)

@platform_connect_bp.route('/calendar/connect-platform', methods=['POST'])
def connect_platform():
    """플랫폼과 사용자 캘린더 연동"""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    user_id = get_current_user_id()
    
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
            'calendar_id': calendar_id,
            'sync_direction': 'bidirectional' if real_time_sync else 'import_only',
            'is_enabled': True,
            'real_time_sync': real_time_sync,
            'last_sync_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'sync_settings': {
                'import_existing': import_existing,
                'real_time_sync': real_time_sync,
                'calendar_name': calendar_info['name']
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
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    user_id = get_current_user_id()
    
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
            'calendar_id': None,
            'is_enabled': False,
            'real_time_sync': False,
            'updated_at': datetime.now().isoformat(),
            'sync_settings': None
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
            result = notion_sync.sync_to_calendar(user_id, calendar_id)
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

@platform_connect_bp.route('/calendar/platform-status', methods=['GET'])
def get_platform_status():
    """플랫폼 연동 상태 조회"""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    user_id = get_current_user_id()
    
    try:
        supabase = config.get_client_for_user(user_id)
        
        # 모든 플랫폼 연동 상태 조회
        result = supabase.table('calendar_sync_configs').select('''
            platform, calendar_id, is_enabled, real_time_sync, 
            last_sync_at, sync_settings
        ''').eq('user_id', user_id).execute()
        
        platform_status = {}
        for config in result.data:
            platform = config['platform']
            platform_status[platform] = {
                'connected': bool(config.get('calendar_id')),
                'calendar_id': config.get('calendar_id'),
                'enabled': config.get('is_enabled', False),
                'real_time_sync': config.get('real_time_sync', False),
                'last_sync_at': config.get('last_sync_at'),
                'calendar_name': config.get('sync_settings', {}).get('calendar_name') if config.get('sync_settings') else None
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