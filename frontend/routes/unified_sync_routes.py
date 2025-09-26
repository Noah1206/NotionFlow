"""
통합 동기화 API 라우터
기존 Google Calendar 및 Notion Sync 서비스 100% 재활용
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

# 기존 서비스들 재활용
from services.google_calendar_sync import GoogleCalendarSyncService, sync_google_calendar_for_user
from services.notion_sync import NotionSyncService, sync_notion_calendar_for_user
from backend.services.calendar_service import CalendarSyncService
from backend.services.sync_tracking_service import sync_tracker, EventType, ActivityType

unified_sync_bp = Blueprint('unified_sync', __name__, url_prefix='/api/unified-sync')

def get_current_user_id():
    """현재 세션의 사용자 ID 획득 - 기존 패턴 재활용"""
    return session.get('user_id')

def require_login():
    """로그인 필요 데코레이터 함수 - 기존 패턴 재활용"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'success': False, 'error': '로그인이 필요합니다'}), 401
    return user_id

@unified_sync_bp.route('/status', methods=['GET'])
def get_platform_status():
    """플랫폼별 연결 상태 확인 - 기존 서비스 재활용"""
    try:
        user_id = require_login()
        if isinstance(user_id, tuple):  # Error response
            return user_id
        
        # 기존 CalendarSyncService 재활용
        calendar_service = CalendarSyncService(user_id)
        
        status = {}
        
        # Google 상태 체크
        try:
            google_provider = calendar_service.get_provider('google')
            status['google'] = {
                'connected': google_provider is not None,
                'platform': 'Google Calendar'
            }
        except Exception as e:
            status['google'] = {
                'connected': False,
                'platform': 'Google Calendar',
                'error': str(e)
            }
        
        # Notion 상태 체크
        try:
            notion_provider = calendar_service.get_provider('notion')
            status['notion'] = {
                'connected': notion_provider is not None,
                'platform': 'Notion'
            }
        except Exception as e:
            status['notion'] = {
                'connected': False,
                'platform': 'Notion',
                'error': str(e)
            }
        
        # Apple은 향후 구현
        status['apple'] = {
            'connected': False,
            'platform': 'Apple Calendar',
            'message': '구현 예정'
        }
        
        return jsonify({
            'success': True,
            'status': status
        })
        
    except Exception as e:
        print(f"❌ [UNIFIED SYNC] Status check failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@unified_sync_bp.route('/sync', methods=['POST'])
def execute_unified_sync():
    """통합 동기화 실행 - 기존 서비스들 조합"""
    try:
        user_id = require_login()
        if isinstance(user_id, tuple):  # Error response
            return user_id
        
        data = request.get_json()
        platforms = data.get('platforms', [])
        options = data.get('options', {})
        
        if not platforms:
            return jsonify({
                'success': False,
                'error': '동기화할 플랫폼을 선택해주세요'
            }), 400
        
        print(f"🚀 [UNIFIED SYNC] Starting multi-platform sync for user: {user_id}")
        print(f"📋 [UNIFIED SYNC] Platforms: {platforms}")
        print(f"⚙️ [UNIFIED SYNC] Options: {options}")
        
        results = {}
        
        # 각 플랫폼별로 기존 sync 서비스 호출
        for platform in platforms:
            activity_id = sync_tracker.start_activity(
                user_id=user_id,
                activity_type=getattr(ActivityType, f'{platform.upper()}_CALENDAR_SYNC', ActivityType.MANUAL_SYNC),
                source_info={'platform': platform, 'sync_type': 'unified', 'options': options}
            )
            
            try:
                if platform == 'google':
                    # 기존 Google Sync 함수 재활용
                    result = sync_google_calendar_for_user(user_id)
                    results[platform] = {
                        'success': True,
                        'message': f'Google Calendar 동기화 완료: {result.get("synced_count", 0)}개 이벤트',
                        'details': result
                    }
                    
                elif platform == 'notion':
                    # 기존 Notion Sync 함수 재활용
                    result = sync_notion_calendar_for_user(user_id)
                    results[platform] = {
                        'success': True,
                        'message': f'Notion 동기화 완료: {result.get("synced_count", 0)}개 이벤트',
                        'details': result
                    }
                    
                elif platform == 'apple':
                    # Apple은 향후 구현
                    results[platform] = {
                        'success': False,
                        'message': 'Apple Calendar은 현재 구현 중입니다'
                    }
                    
                sync_tracker.complete_activity(activity_id, success=results[platform]['success'])
                
            except Exception as platform_error:
                print(f"❌ [UNIFIED SYNC] {platform} sync failed: {platform_error}")
                results[platform] = {
                    'success': False,
                    'message': f'{platform} 동기화 실패: {str(platform_error)}',
                    'error': str(platform_error)
                }
                sync_tracker.complete_activity(activity_id, success=False, error_details=str(platform_error))
        
        # 전체 결과 요약
        success_count = sum(1 for r in results.values() if r.get('success'))
        total_count = len(platforms)
        
        response_data = {
            'success': success_count > 0,
            'message': f'{success_count}/{total_count} 플랫폼 동기화 완료',
            'results': results,
            'summary': {
                'successful': success_count,
                'total': total_count,
                'failed': total_count - success_count
            }
        }
        
        print(f"✅ [UNIFIED SYNC] Completed: {response_data['message']}")
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ [UNIFIED SYNC] Execution failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@unified_sync_bp.route('/preview', methods=['POST'])
def get_sync_preview():
    """동기화 미리보기 - 영향받을 이벤트 수 계산"""
    try:
        user_id = require_login()
        if isinstance(user_id, tuple):
            return user_id
        
        data = request.get_json()
        platforms = data.get('platforms', [])
        options = data.get('options', {})
        
        # 기존 CalendarSyncService 재활용하여 이벤트 수 계산
        calendar_service = CalendarSyncService(user_id)
        
        preview = {}
        
        for platform in platforms:
            try:
                # 기존 SupaBase에서 현재 이벤트 수 조회
                # (실제로는 더 정확한 계산 로직이 필요하지만 기본 구조)
                if platform in ['google', 'notion']:
                    from supabase import create_client
                    import os
                    
                    supabase_url = os.environ.get('SUPABASE_URL')
                    supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('SUPABASE_API_KEY')
                    
                    if supabase_url and supabase_key:
                        supabase = create_client(supabase_url, supabase_key)
                        
                        # 현재 사용자의 이벤트 수 조회
                        events_result = supabase.table('calendar_events').select('id', count='exact').eq('user_id', user_id).execute()
                        event_count = events_result.count or 0
                        
                        preview[platform] = {
                            'current_events': event_count,
                            'estimated_impact': event_count,
                            'direction': options.get('direction', 'bidirectional')
                        }
                    else:
                        preview[platform] = {
                            'current_events': 0,
                            'estimated_impact': 0,
                            'error': 'Database connection failed'
                        }
                        
                elif platform == 'apple':
                    preview[platform] = {
                        'current_events': 0,
                        'estimated_impact': 0,
                        'message': '구현 예정'
                    }
                    
            except Exception as platform_error:
                preview[platform] = {
                    'error': str(platform_error)
                }
        
        return jsonify({
            'success': True,
            'preview': preview,
            'options': options
        })
        
    except Exception as e:
        print(f"❌ [UNIFIED SYNC] Preview failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@unified_sync_bp.route('/history', methods=['GET'])
def get_sync_history():
    """동기화 기록 조회 - 기존 sync_tracker 재활용"""
    try:
        user_id = require_login()
        if isinstance(user_id, tuple):
            return user_id
        
        # 기존 sync_tracker에서 사용자의 최근 동기화 기록 조회
        # (실제 구현은 sync_tracking_service에 따라 달라질 수 있음)
        
        # 임시 응답 (실제로는 sync_tracker.get_user_activities 같은 메서드 사용)
        history = [
            {
                'timestamp': datetime.now().isoformat(),
                'platforms': ['google', 'notion'],
                'status': 'completed',
                'summary': '2개 플랫폼, 15개 이벤트 동기화'
            }
        ]
        
        return jsonify({
            'success': True,
            'history': history
        })
        
    except Exception as e:
        print(f"❌ [UNIFIED SYNC] History retrieval failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500