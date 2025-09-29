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
        except Exception as google_error:
            print(f"⚠️ [GOOGLE-CALENDARS API] Google service failed: {str(google_error)}")
            calendars = []

        # Fallback: 기존 캘린더가 있으면 calendars 테이블에서 가져오기
        if not calendars and supabase:
            try:
                print(f"🔄 [GOOGLE-CALENDARS API] Trying fallback from calendars table for user {user_id}")

                # calendars 테이블에서 Google 타입 캘린더 가져오기
                calendars_result = supabase.table('calendars').select('id, name, type, is_active').eq('owner_id', user_id).eq('type', 'google').eq('is_active', True).execute()

                if calendars_result.data:
                    calendars = []
                    for cal in calendars_result.data:
                        calendar_data = {
                            'id': cal['id'],
                            'summary': cal['name'],
                            'name': cal['name'],
                            'platform': 'google',
                            'selected': True,  # 이미 생성된 캘린더는 선택된 상태
                            'primary': True
                        }
                        calendars.append(calendar_data)

                    print(f"✅ [GOOGLE-CALENDARS API] Found {len(calendars)} calendars from fallback table")
                else:
                    print(f"⚠️ [GOOGLE-CALENDARS API] No Google-type calendars found in fallback table")

                    # 2차 fallback: 기존 개인 캘린더가 있고 Google OAuth 토큰이 있으면 변환
                    personal_calendars = supabase.table('calendars').select('id, name, type, is_active').eq('owner_id', user_id).eq('is_active', True).execute()
                    oauth_tokens = supabase.table('oauth_tokens').select('*').eq('user_id', user_id).eq('platform', 'google').execute()

                    if personal_calendars.data and oauth_tokens.data:
                        print(f"💡 [GOOGLE-CALENDARS API] Found {len(personal_calendars.data)} personal calendars and valid Google OAuth token")
                        print(f"🔄 [GOOGLE-CALENDARS API] Converting first personal calendar to Google type...")

                        # 첫 번째 개인 캘린더를 Google 타입으로 변환
                        first_calendar = personal_calendars.data[0]
                        update_result = supabase.table('calendars').update({
                            'type': 'google',
                            'description': f"Converted to Google Calendar - {first_calendar['name']}"
                        }).eq('id', first_calendar['id']).execute()

                        if update_result.data:
                            calendar_data = {
                                'id': first_calendar['id'],
                                'summary': first_calendar['name'],
                                'name': first_calendar['name'],
                                'platform': 'google',
                                'selected': True,
                                'primary': True
                            }
                            calendars = [calendar_data]
                            print(f"✅ [GOOGLE-CALENDARS API] Successfully converted calendar '{first_calendar['name']}' to Google type")
                        else:
                            print(f"❌ [GOOGLE-CALENDARS API] Failed to convert calendar to Google type")

            except Exception as fallback_error:
                print(f"❌ [GOOGLE-CALENDARS API] Fallback failed: {str(fallback_error)}")

        if not calendars:
            print(f"⚠️ [GOOGLE-CALENDARS API] No calendars found for user {user_id}")
            return jsonify({
                'success': False,
                'error': 'Google 계정에 캘린더가 없습니다',
                'calendars': []
            }), 404

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