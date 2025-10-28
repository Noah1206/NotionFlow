"""
Google Calendar API 라우터
프론트엔드 호환을 위한 추가 API 엔드포인트
"""

from flask import Blueprint, request, jsonify, session
import os
import sys
from datetime import datetime

# Add parent directories to path for backend services
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../../services'))

from backend.services.google_calendar_service import get_google_calendar_service

# Import Supabase for fallback data
try:
    from supabase import create_client
    import os

    # Initialize Supabase client for fallback queries
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY')
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
except ImportError:
    supabase = None
    print("⚠️ [GOOGLE-CALENDARS API] Supabase not available for fallback")

google_calendar_api_bp = Blueprint('google_calendar_api', __name__)

def get_current_user_id():
    """현재 세션의 사용자 ID 획득"""
    return session.get('user_id')

def require_login():
    """로그인 필요 데코레이터 함수"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'success': False, 'error': '로그인이 필요합니다'}), 401
    return user_id

@google_calendar_api_bp.route('/api/google-calendars', methods=['GET'])
def get_google_calendars_list():
    """Google Calendar 목록 조회 - 프론트엔드 호환 엔드포인트"""
    try:
        user_id = require_login()
        if isinstance(user_id, tuple):  # Error response
            return user_id

        print(f"📅 [GOOGLE-CALENDARS API] Loading calendars for user: {user_id}")

        # Try Google Calendar 서비스 first
        calendars = []
        try:
            calendar_service = get_google_calendar_service()
            calendars = calendar_service.get_calendar_list(user_id)
            print(f"✅ [GOOGLE-CALENDARS API] Retrieved {len(calendars)} Google calendars")
        except Exception as google_error:
            error_str = str(google_error)
            print(f"⚠️ [GOOGLE-CALENDARS API] Google service failed: {error_str}")

            # OAuth refresh 에러인 경우 더 구체적인 메시지
            if 'refresh the access token' in error_str or 'credentials do not contain' in error_str:
                return jsonify({
                    'success': False,
                    'error': 'Google 인증이 만료되었습니다. Google Calendar 연결을 해제한 후 다시 연결해주세요.',
                    'calendars': [],
                    'reconnect_required': True
                }), 400
            else:
                return jsonify({
                    'success': False,
                    'error': 'Google Calendar에 연결할 수 없습니다. 네트워크를 확인하거나 잠시 후 다시 시도해주세요.',
                    'calendars': []
                }), 400

        # Check if we got actual Google calendars
        if not calendars:
            print(f"⚠️ [GOOGLE-CALENDARS API] No Google calendars found for user {user_id}")
            return jsonify({
                'success': False,
                'error': 'Google Calendar에서 캘린더를 찾을 수 없습니다. Google 계정에 캘린더가 있는지 확인해주세요.',
                'calendars': []
            }), 404


        # Return successful Google calendars
        print(f"✅ [GOOGLE-CALENDARS API] Found {len(calendars)} calendars for user {user_id}")

        return jsonify({
            'success': True,
            'calendars': calendars,
            'total_count': len(calendars)
        }), 200

    except Exception as e:
        error_msg = f"Google Calendar 목록 조회 오류: {str(e)}"
        print(f"❌ [GOOGLE-CALENDARS API] Error: {error_msg}")

        return jsonify({
            'success': False,
            'error': error_msg,
            'calendars': []
        }), 500

@google_calendar_api_bp.route('/api/google-calendar/disconnect', methods=['POST'])
def disconnect_google_calendar():
    """Disconnect Google Calendar - 안전한 Google 전용 연결해제"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401

    try:
        from utils.config import config
        supabase = config.get_client_for_user(user_id)

        print(f"🔗 [GOOGLE DISCONNECT] 사용자 {user_id} Google Calendar 연결해제 시작")

        # 1. calendar_sync_configs에서 Google 연결 비활성화
        config_result = supabase.table('calendar_sync_configs').select('*').eq('user_id', user_id).eq('platform', 'google').execute()

        if config_result.data:
            # 연결 비활성화 (실제 테이블 구조에 맞게 is_enabled만 수정)
            update_result = supabase.table('calendar_sync_configs').update({
                'is_enabled': False
            }).eq('user_id', user_id).eq('platform', 'google').execute()
            print(f"✅ [GOOGLE DISCONNECT] calendar_sync_configs 비활성화 완료: {len(update_result.data)} 행 업데이트")

        # 2. oauth_tokens에서 Google OAuth 토큰 제거 (선택사항)
        oauth_result = supabase.table('oauth_tokens').select('*').eq('user_id', user_id).eq('platform', 'google').execute()

        if oauth_result.data:
            # OAuth 토큰 삭제로 완전 연결해제
            delete_result = supabase.table('oauth_tokens').delete().eq('user_id', user_id).eq('platform', 'google').execute()
            print(f"✅ [GOOGLE DISCONNECT] oauth_tokens 삭제 완료: {len(delete_result.data)} 행 삭제")
        else:
            print(f"ℹ️ [GOOGLE DISCONNECT] Google OAuth 토큰이 없습니다")

        print(f"🔗 [GOOGLE DISCONNECT] 사용자 {user_id} Google Calendar 연결해제 완료")

        return jsonify({
            'success': True,
            'message': 'Google Calendar 연결이 해제되었습니다.'
        })

    except Exception as e:
        print(f"❌ [GOOGLE DISCONNECT] 연결해제 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@google_calendar_api_bp.route('/api/google-calendar/enable', methods=['POST'])
def enable_google_calendar():
    """Enable Google Calendar - Google 전용 재활성화"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401

    try:
        from utils.config import config
        supabase = config.get_client_for_user(user_id)

        print(f"🔗 [GOOGLE ENABLE] 사용자 {user_id} Google Calendar 재활성화 시작")

        # calendar_sync_configs에서 Google 연결 활성화
        config_result = supabase.table('calendar_sync_configs').select('*').eq('user_id', user_id).eq('platform', 'google').execute()

        if config_result.data:
            # 연결 활성화 (is_enabled를 True로 변경하고 실패 카운터 리셋)
            update_result = supabase.table('calendar_sync_configs').update({
                'is_enabled': True,
                'consecutive_failures': 0,  # 실패 카운터 리셋
                'sync_errors': []  # 에러 로그 클리어
            }).eq('user_id', user_id).eq('platform', 'google').execute()
            print(f"✅ [GOOGLE ENABLE] calendar_sync_configs 활성화 완료: {len(update_result.data)} 행 업데이트")
        else:
            print(f"ℹ️ [GOOGLE ENABLE] Google 연결 설정이 없습니다")

        print(f"🔗 [GOOGLE ENABLE] 사용자 {user_id} Google Calendar 재활성화 완료")

        return jsonify({
            'success': True,
            'message': 'Google Calendar가 다시 활성화되었습니다.'
        })

    except Exception as e:
        print(f"❌ [GOOGLE ENABLE] 재활성화 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@google_calendar_api_bp.route('/sync', methods=['POST'])
def sync_google_calendar():
    """Google Calendar 이벤트를 SupaBase에 동기화"""
    try:
        # 로그인 확인
        user_id = require_login()
        if isinstance(user_id, tuple):  # Error response
            return user_id

        print(f"🚀 [GOOGLE SYNC] Starting sync for user: {user_id}")

        # Google Calendar 동기화 서비스 실행
        sys.path.append(os.path.join(os.path.dirname(__file__), '../../services'))
        from google_calendar_sync import sync_google_calendar_for_user

        result = sync_google_calendar_for_user(user_id)

        # 동기화 결과 로깅
        print(f"📊 [GOOGLE SYNC] Sync result for user {user_id}: {result}")

        if result.get('success'):
            return jsonify({
                'success': True,
                'message': result.get('message', 'Google Calendar 동기화 완료'),
                'events_found': result.get('events_found', 0),
                'events_processed': result.get('events_processed', 0),
                'sync_time': datetime.now().isoformat()
            }), 200

        else:
            # 실패한 경우
            error_msg = result.get('error', 'Google Calendar 동기화 실패')
            return jsonify({
                'success': False,
                'error': error_msg,
                'events_processed': result.get('events_processed', 0)
            }), 400

    except Exception as e:
        error_msg = f"Google Calendar 동기화 오류: {str(e)}"
        print(f"❌ [GOOGLE SYNC] Error: {error_msg}")

        return jsonify({
            'success': False,
            'error': error_msg
        }), 500

@google_calendar_api_bp.route('/connect-calendar', methods=['POST'])
def connect_google_to_calendar():
    """Connect Google Calendar to a specific calendar chosen by user"""
    try:
        print(f"🔗 [GOOGLE-CONNECT] Request received")
        user_id = get_current_user_id()
        if not user_id:
            print(f"❌ [GOOGLE-CONNECT] No user authentication")
            return jsonify({'error': 'User not authenticated'}), 401

        data = request.get_json()
        calendar_id = data.get('calendar_id')
        google_calendar_id = data.get('google_calendar_id')

        print(f"🔗 [GOOGLE-CONNECT] User: {user_id}")
        print(f"🔗 [GOOGLE-CONNECT] Received calendar_id: {calendar_id}")
        print(f"🔗 [GOOGLE-CONNECT] Google calendar_id: {google_calendar_id}")

        if not calendar_id:
            print(f"❌ [GOOGLE-CONNECT] Missing calendar_id")
            return jsonify({'error': 'Calendar ID is required'}), 400

        from utils.config import config
        supabase = config.get_client_for_user(user_id)

        # Convert user_id to the format used in database (with hyphens)
        if len(user_id) == 32 and '-' not in user_id:
            formatted_user_id = f"{user_id[:8]}-{user_id[8:12]}-{user_id[12:16]}-{user_id[16:20]}-{user_id[20:]}"
            print(f"🔗 [GOOGLE-CONNECT] Converted user_id: {user_id} -> {formatted_user_id}")
        else:
            formatted_user_id = user_id

        # Check if calendar_id looks like a Google Calendar ID (contains @ or very long)
        if '@' in calendar_id or len(calendar_id) > 36:
            print(f"🔗 [GOOGLE-CONNECT] Detected Google Calendar ID, finding user's calendar...")

            # This is a Google Calendar ID, find the user's first available calendar
            calendar_check = supabase.table('calendars').select('*').eq('owner_id', formatted_user_id).eq('is_active', True).execute()

            if calendar_check.data:
                # Use the first available calendar
                user_calendar = calendar_check.data[0]
                actual_calendar_id = user_calendar['id']
                google_calendar_id = calendar_id  # Store the Google Calendar ID
                print(f"🔗 [GOOGLE-CONNECT] Using user calendar: {actual_calendar_id} for Google Calendar: {google_calendar_id}")
            else:
                print(f"❌ [GOOGLE-CONNECT] No calendars found for user {user_id}")
                return jsonify({'error': 'No calendars found for user. Please create a calendar first.'}), 404
        else:
            # This is a NotionFlow calendar ID
            actual_calendar_id = calendar_id
            print(f"🔗 [GOOGLE-CONNECT] Checking calendar ownership...")
            calendar_check = supabase.table('calendars').select('*').eq('id', actual_calendar_id).eq('owner_id', formatted_user_id).execute()

            if not calendar_check.data:
                print(f"❌ [GOOGLE-CONNECT] Calendar not found - calendar_id: {actual_calendar_id}, user_id: {user_id}")
                return jsonify({'error': 'Calendar not found or access denied'}), 404

        print(f"✅ [GOOGLE-CONNECT] Calendar ownership verified")

        # Get existing credentials to preserve OAuth tokens
        existing_config = supabase.table('calendar_sync_configs').select('credentials').eq('user_id', user_id).eq('platform', 'google').execute()
        existing_credentials = existing_config.data[0].get('credentials', {}) if existing_config.data else {}

        # Merge with new calendar information (preserve OAuth data)
        credentials_data = {
            **existing_credentials,  # Keep existing OAuth tokens and info
            'oauth_connected': True,
            'calendar_id': actual_calendar_id,
            'connected_at': datetime.now().isoformat(),
            'real_time_sync': True,
            'needs_calendar_selection': False  # Calendar has been selected
        }

        # Include Google calendar ID if provided
        if google_calendar_id:
            credentials_data['google_calendar_id'] = google_calendar_id

        update_result = supabase.table('calendar_sync_configs').update({
            'credentials': credentials_data,
            'is_enabled': True,
            'updated_at': datetime.now().isoformat()
        }).eq('user_id', user_id).eq('platform', 'google').execute()

        if not update_result.data:
            return jsonify({'error': 'Google Calendar configuration not found. Please reconnect Google Calendar first.'}), 404

        # 🚀 IMMEDIATE SYNC
        try:
            print(f"🚀 [GOOGLE CONNECT] Starting immediate Google Calendar sync for calendar {actual_calendar_id}")

            # Import sync function
            sys.path.append(os.path.join(os.path.dirname(__file__), '../../services'))
            from google_calendar_sync import sync_google_calendar_for_user

            # Trigger immediate Google Calendar sync
            sync_result = sync_google_calendar_for_user(user_id)

            if sync_result.get('success'):
                synced_count = sync_result.get('events_processed', 0)
                print(f"✅ [GOOGLE CONNECT] Immediate sync completed: {synced_count} events synced")

                return jsonify({
                    'success': True,
                    'message': f'Google Calendar connected successfully. {synced_count} events synced to calendar.',
                    'calendar_id': actual_calendar_id,
                    'google_calendar_id': google_calendar_id,
                    'synced_count': synced_count,
                    'trigger_calendar_refresh': True,
                    'clear_disconnected_flag': True
                })
            else:
                return jsonify({
                    'success': True,
                    'message': f'Google Calendar connected successfully, but sync had issues: {sync_result.get("error", "Unknown error")}',
                    'calendar_id': actual_calendar_id,
                    'google_calendar_id': google_calendar_id,
                    'sync_warning': sync_result.get('error'),
                    'trigger_calendar_refresh': True,
                    'clear_disconnected_flag': True
                })

        except Exception as sync_error:
            print(f"❌ [GOOGLE CONNECT] Immediate sync failed: {sync_error}")

            return jsonify({
                'success': True,
                'message': f'Google Calendar connected successfully, but immediate sync failed: {str(sync_error)}',
                'calendar_id': actual_calendar_id,
                'google_calendar_id': google_calendar_id,
                'sync_error': str(sync_error),
                'trigger_calendar_refresh': True,
                'clear_disconnected_flag': True
            })

    except Exception as e:
        print(f"Error connecting Google Calendar to calendar: {e}")
        return jsonify({'error': f'Failed to connect: {str(e)}'}), 500