"""
Google Calendar API 라우터
프론트엔드 호환을 위한 추가 API 엔드포인트
"""

from flask import Blueprint, request, jsonify, session
import os
import sys

# Add parent directories to path for backend services
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend'))

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