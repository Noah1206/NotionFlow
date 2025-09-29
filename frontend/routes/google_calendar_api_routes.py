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