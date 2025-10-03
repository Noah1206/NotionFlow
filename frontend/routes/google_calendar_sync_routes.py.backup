"""
Google Calendar 동기화 라우터
Notion과 동일한 패턴으로 구현된 Google Calendar 동기화 엔드포인트
"""

from flask import Blueprint, request, jsonify, session
import os
import sys
import json
from datetime import datetime, timezone

# Add parent directories to path for backend services
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../../services'))

from services.google_calendar_sync import GoogleCalendarSyncService, sync_google_calendar_for_user
from backend.services.sync_tracking_service import sync_tracker, EventType, ActivityType

google_calendar_bp = Blueprint('google_calendar', __name__, url_prefix='/api/google-calendar')

def get_current_user_id():
    """현재 세션의 사용자 ID 획득"""
    return session.get('user_id')

def require_login():
    """로그인 필요 데코레이터 함수"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'success': False, 'error': '로그인이 필요합니다'}), 401
    return user_id

@google_calendar_bp.route('/sync', methods=['POST'])
def sync_google_calendar():
    """Google Calendar 이벤트를 SupaBase에 동기화"""
    try:
        # 로그인 확인
        user_id = require_login()
        if isinstance(user_id, tuple):  # Error response
            return user_id
        
        print(f"🚀 [GOOGLE SYNC ROUTE] Starting sync for user: {user_id}")
        
        # 동기화 시작 이벤트 추적
        sync_tracker.track_sync_event(
            user_id=user_id,
            event_type=EventType.SYNC_STARTED,
            platform='google',
            status='pending',
            metadata={'sync_type': 'manual'}
        )

        try:
            # Google Calendar 동기화 서비스 실행
            result = sync_google_calendar_for_user(user_id)

            # 동기화 결과 로깅
            print(f"📊 [GOOGLE SYNC ROUTE] Sync result for user {user_id}: {result}")

            if result.get('success'):
                # 성공한 경우
                sync_tracker.track_sync_event(
                    user_id=user_id,
                    event_type=EventType.SYNC_COMPLETED,
                    platform='google',
                    status='success',
                    metadata={
                        'events_found': result.get('events_found', 0),
                        'events_processed': result.get('events_processed', 0),
                        'errors': result.get('errors', [])
                    }
                )
                
                return jsonify({
                    'success': True,
                    'message': result.get('message', 'Google Calendar 동기화 완료'),
                    'events_found': result.get('events_found', 0),
                    'events_processed': result.get('events_processed', 0),
                    'sync_time': datetime.now(timezone.utc).isoformat()
                }), 200
                
            else:
                # 실패한 경우
                error_msg = result.get('error', 'Google Calendar 동기화 실패')

                sync_tracker.track_sync_event(
                    user_id=user_id,
                    event_type=EventType.SYNC_ERROR,
                    platform='google',
                    status='failed',
                    metadata={'error': error_msg}
                )

                return jsonify({
                    'success': False,
                    'error': error_msg,
                    'events_processed': result.get('events_processed', 0)
                }), 400
        
        except Exception as sync_error:
            # 예외 발생한 경우
            error_msg = f"Google Calendar 동기화 중 오류: {str(sync_error)}"
            print(f"❌ [GOOGLE SYNC ROUTE] Sync error for user {user_id}: {error_msg}")

            sync_tracker.track_sync_event(
                user_id=user_id,
                event_type=EventType.SYNC_ERROR,
                platform='google',
                status='failed',
                metadata={'error': error_msg, 'exception': str(sync_error)}
            )

            return jsonify({
                'success': False,
                'error': error_msg
            }), 500
        
    except Exception as e:
        error_msg = f"Google Calendar 동기화 라우터 오류: {str(e)}"
        print(f"❌ [GOOGLE SYNC ROUTE] Route error: {error_msg}")
        
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500

@google_calendar_bp.route('/status', methods=['GET'])
def get_sync_status():
    """Google Calendar 동기화 상태 조회"""
    try:
        user_id = require_login()
        if isinstance(user_id, tuple):  # Error response
            return user_id
        
        print(f"📊 [GOOGLE SYNC STATUS] Checking status for user: {user_id}")
        
        # SupaBase에서 Google Calendar 이벤트 통계 조회
        sync_service = GoogleCalendarSyncService()
        
        # 사용자의 Google Calendar 이벤트 수 조회
        events_response = sync_service.supabase.table('events').select('*').eq('user_id', user_id).eq('source', 'google_calendar').execute()
        events_count = len(events_response.data) if events_response.data else 0
        
        # 마지막 동기화 시간 조회
        last_sync_response = sync_service.supabase.table('events').select('updated_at').eq('user_id', user_id).eq('source', 'google_calendar').order('updated_at', desc=True).limit(1).execute()
        last_sync = None
        if last_sync_response.data:
            last_sync = last_sync_response.data[0]['updated_at']
        
        # OAuth 토큰 상태 확인
        token_response = sync_service.supabase.table('oauth_tokens').select('*').eq('user_id', user_id).eq('platform', 'google').execute()
        sync_enabled = bool(token_response.data)
        
        return jsonify({
            'success': True,
            'events_count': events_count,
            'last_sync': last_sync,
            'sync_enabled': sync_enabled,
            'user_id': user_id
        }), 200
        
    except Exception as e:
        error_msg = f"Google Calendar 상태 조회 오류: {str(e)}"
        print(f"❌ [GOOGLE SYNC STATUS] Status error: {error_msg}")
        
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500

@google_calendar_bp.route('/events', methods=['GET'])
def get_google_events():
    """사용자의 Google Calendar 이벤트 목록 조회 (SupaBase에서)"""
    try:
        user_id = require_login()
        if isinstance(user_id, tuple):  # Error response
            return user_id
        
        # 쿼리 파라미터 처리
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        calendar_id = request.args.get('calendar_id')  # 특정 캘린더 필터
        
        print(f"📋 [GOOGLE EVENTS] Loading events for user: {user_id} (limit: {limit}, offset: {offset})")
        
        # SupaBase에서 Google Calendar 이벤트 조회
        sync_service = GoogleCalendarSyncService()
        
        query = sync_service.supabase.table('events').select('*').eq('user_id', user_id).eq('source', 'google_calendar')
        
        # 특정 캘린더 필터 적용
        if calendar_id:
            query = query.eq('google_calendar_id', calendar_id)
        
        # 날짜 정렬 및 페이징
        events_response = query.order('date', desc=False).order('start_time', desc=False).range(offset, offset + limit - 1).execute()
        
        events = events_response.data if events_response.data else []
        
        print(f"✅ [GOOGLE EVENTS] Found {len(events)} Google Calendar events for user {user_id}")
        
        return jsonify({
            'success': True,
            'events': events,
            'total_count': len(events),
            'limit': limit,
            'offset': offset
        }), 200
        
    except Exception as e:
        error_msg = f"Google Calendar 이벤트 조회 오류: {str(e)}"
        print(f"❌ [GOOGLE EVENTS] Events query error: {error_msg}")
        
        return jsonify({
            'success': False,
            'error': error_msg,
            'events': []
        }), 500

@google_calendar_bp.route('/calendars', methods=['GET'])
def get_google_calendars():
    """사용자의 Google Calendar 목록 조회 (Google API에서 직접)"""
    try:
        user_id = require_login()
        if isinstance(user_id, tuple):  # Error response
            return user_id
        
        print(f"📋 [GOOGLE CALENDARS] Loading calendars for user: {user_id}")
        
        # Google Calendar 동기화 서비스 사용
        sync_service = GoogleCalendarSyncService()
        
        # 사용자 인증 정보 획득
        credentials = sync_service.get_user_credentials(user_id)
        if not credentials:
            return jsonify({
                'success': False,
                'error': 'Google OAuth 토큰을 찾을 수 없습니다',
                'calendars': []
            }), 404
        
        # Google Calendar API 초기화
        from services.google_calendar_sync import GoogleCalendarAPI
        google_api = GoogleCalendarAPI(credentials)
        
        if not google_api.service:
            return jsonify({
                'success': False,
                'error': 'Google Calendar API 서비스를 초기화할 수 없습니다',
                'calendars': []
            }), 500
        
        # 캘린더 목록 조회
        calendars = google_api.list_calendars()
        
        # 캘린더 정보 정리
        calendar_list = []
        for calendar in calendars:
            calendar_info = {
                'id': calendar.get('id'),
                'summary': calendar.get('summary', 'Unknown Calendar'),
                'description': calendar.get('description', ''),
                'primary': calendar.get('primary', False),
                'access_role': calendar.get('accessRole', 'reader'),
                'selected': calendar.get('selected', True),
                'color_id': calendar.get('colorId', ''),
                'background_color': calendar.get('backgroundColor', '#1976D2'),
                'foreground_color': calendar.get('foregroundColor', '#FFFFFF')
            }
            calendar_list.append(calendar_info)
        
        print(f"✅ [GOOGLE CALENDARS] Found {len(calendar_list)} calendars for user {user_id}")
        
        return jsonify({
            'success': True,
            'calendars': calendar_list,
            'total_count': len(calendar_list)
        }), 200
        
    except Exception as e:
        error_msg = f"Google Calendar 목록 조회 오류: {str(e)}"
        print(f"❌ [GOOGLE CALENDARS] Calendars query error: {error_msg}")
        
        return jsonify({
            'success': False,
            'error': error_msg,
            'calendars': []
        }), 500

@google_calendar_bp.route('/test', methods=['GET'])
def test_google_sync():
    """Google Calendar 동기화 테스트 엔드포인트 (개발용)"""
    try:
        user_id = require_login()
        if isinstance(user_id, tuple):  # Error response
            return user_id
        
        print(f"🧪 [GOOGLE TEST] Testing sync for user: {user_id}")
        
        # 간단한 연결 테스트
        sync_service = GoogleCalendarSyncService()
        credentials = sync_service.get_user_credentials(user_id)
        
        if not credentials:
            return jsonify({
                'success': False,
                'message': 'Google OAuth 토큰이 없습니다',
                'test_result': 'FAILED - No OAuth Token'
            }), 404
        
        # Google API 연결 테스트
        from services.google_calendar_sync import GoogleCalendarAPI
        google_api = GoogleCalendarAPI(credentials)
        
        if not google_api.service:
            return jsonify({
                'success': False,
                'message': 'Google Calendar API 서비스 초기화 실패',
                'test_result': 'FAILED - API Service Init'
            }), 500
        
        # 기본 캘린더 조회 테스트
        calendars = google_api.list_calendars()
        calendar_count = len(calendars)
        
        # 이벤트 조회 테스트 (최근 5개만)
        events = google_api.get_events('primary', max_results=5)
        event_count = len(events)
        
        return jsonify({
            'success': True,
            'message': 'Google Calendar 연결 테스트 성공',
            'test_result': 'PASSED',
            'details': {
                'user_id': user_id,
                'calendars_found': calendar_count,
                'recent_events': event_count,
                'credentials_valid': True,
                'api_service_ok': True
            }
        }), 200
        
    except Exception as e:
        error_msg = f"Google Calendar 테스트 오류: {str(e)}"
        print(f"❌ [GOOGLE TEST] Test error: {error_msg}")
        
        return jsonify({
            'success': False,
            'message': error_msg,
            'test_result': 'FAILED - Exception',
            'details': {'error': error_msg}
        }), 500

# 라우터 등록을 위한 함수
def register_google_calendar_routes(app):
    """Flask 앱에 Google Calendar 라우터 등록"""
    app.register_blueprint(google_calendar_bp)
    print("✅ [GOOGLE CALENDAR ROUTES] Registered Google Calendar sync routes")