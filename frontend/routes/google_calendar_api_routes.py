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

        # Google Calendar 서비스 사용
        calendar_service = get_google_calendar_service()

        # 캘린더 목록 조회
        calendars = calendar_service.get_calendar_list(user_id)

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