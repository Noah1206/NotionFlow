"""
캘린더 선택 관리 API Routes
사용자가 동기화할 캘린더를 선택/해제하는 API
"""

from flask import Blueprint, request, jsonify, session
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

# Add parent directory to path for backend services
sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend'))
from services.sync_tracking_service import sync_tracker, EventType, ActivityType

# Add utils path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../utils'))
from utils.config import get_supabase_admin
from utils.auth_manager import get_current_user_id

calendar_selection_bp = Blueprint('calendar_selection', __name__, url_prefix='/api/calendar-selection')

@calendar_selection_bp.route('/user/<user_id>/calendars', methods=['GET'])
def get_user_calendars_with_selection(user_id):
    """사용자의 캘린더 목록과 선택 상태 조회"""
    try:
        # 인증 확인
        current_user = get_current_user_id()
        if not current_user or current_user != user_id:
            return jsonify({'error': 'Authentication required'}), 401

        supabase = get_supabase_admin()

        # 사용자의 모든 캘린더 조회
        calendars_result = supabase.table('calendars').select('*').eq('owner_id', user_id).execute()

        if not calendars_result.data:
            return jsonify({
                'success': True,
                'calendars': [],
                'message': 'No calendars found'
            })

        # 활성화된 캘린더 정보 조회 (is_active=true인 캘린더들)
        selected_calendar_ids = {cal['id'] for cal in calendars_result.data if cal.get('is_active', True)}

        # 캘린더 목록에 선택 상태 추가
        calendars_with_selection = []
        for calendar in calendars_result.data:
            calendar_info = {
                'id': calendar['id'],
                'name': calendar['name'],
                'color': calendar.get('color', '#4285f4'),
                'google_calendar_id': calendar.get('google_calendar_id'),
                'is_selected': calendar['id'] in selected_calendar_ids,
                'created_at': calendar.get('created_at'),
                'event_count': 0  # 추후 이벤트 수 계산 추가
            }
            calendars_with_selection.append(calendar_info)

        return jsonify({
            'success': True,
            'user_id': user_id,
            'calendars': calendars_with_selection,
            'total_calendars': len(calendars_with_selection),
            'selected_count': len(selected_calendar_ids)
        })

    except Exception as e:
        print(f"Error getting user calendars: {e}")
        return jsonify({'error': f'Failed to get calendars: {str(e)}'}), 500

@calendar_selection_bp.route('/user/<user_id>/select', methods=['POST'])
def select_calendars(user_id):
    """캘린더 선택/해제"""
    try:
        # 인증 확인
        current_user = get_current_user_id()
        if not current_user or current_user != user_id:
            return jsonify({'error': 'Authentication required'}), 401

        data = request.get_json()
        calendar_ids = data.get('calendar_ids', [])

        if not isinstance(calendar_ids, list):
            return jsonify({'error': 'calendar_ids must be a list'}), 400

        supabase = get_supabase_admin()

        # 모든 캘린더를 비활성화
        supabase.table('calendars').update({'is_active': False}).eq('owner_id', user_id).execute()

        # 선택된 캘린더들을 활성화
        if calendar_ids:
            for calendar_id in calendar_ids:
                # 캘린더가 실제로 존재하는지 확인 후 활성화
                calendar_check = supabase.table('calendars').select('id').eq('owner_id', user_id).eq('id', calendar_id).execute()

                if calendar_check.data:
                    supabase.table('calendars').update({
                        'is_active': True,
                        'updated_at': datetime.now().isoformat()
                    }).eq('id', calendar_id).execute()

        # 동기화 추적
        sync_tracker.track_user_activity(
            user_id=user_id,
            activity_type=ActivityType.SETTINGS_CHANGED,
            platform='google',
            details={
                'action': 'calendar_selection_updated',
                'selected_calendars': calendar_ids,
                'calendar_count': len(calendar_ids)
            },
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )

        return jsonify({
            'success': True,
            'message': f'{len(calendar_ids)} calendars selected for sync',
            'selected_calendars': calendar_ids
        })

    except Exception as e:
        print(f"Error selecting calendars: {e}")
        return jsonify({'error': f'Failed to select calendars: {str(e)}'}), 500

@calendar_selection_bp.route('/user/<user_id>/toggle/<calendar_id>', methods=['POST'])
def toggle_calendar_selection(user_id, calendar_id):
    """개별 캘린더 선택 상태 토글"""
    try:
        # 인증 확인
        current_user = get_current_user_id()
        if not current_user or current_user != user_id:
            return jsonify({'error': 'Authentication required'}), 401

        supabase = get_supabase_admin()

        # 캘린더 존재 확인
        calendar_check = supabase.table('calendars').select('*').eq('owner_id', user_id).eq('id', calendar_id).execute()

        if not calendar_check.data:
            return jsonify({'error': 'Calendar not found'}), 404

        calendar_info = calendar_check.data[0]

        # 현재 활성화 상태 확인
        current_status = calendar_info.get('is_active', True)

        if current_status:
            # 이미 활성화된 경우 - 비활성화
            supabase.table('calendars').update({
                'is_active': False,
                'updated_at': datetime.now().isoformat()
            }).eq('id', calendar_id).execute()
            is_selected = False
            action = 'deselected'
        else:
            # 비활성화된 경우 - 활성화
            supabase.table('calendars').update({
                'is_active': True,
                'updated_at': datetime.now().isoformat()
            }).eq('id', calendar_id).execute()
            is_selected = True
            action = 'selected'

        # 동기화 추적
        sync_tracker.track_user_activity(
            user_id=user_id,
            activity_type=ActivityType.SETTINGS_CHANGED,
            platform='google',
            details={
                'action': f'calendar_{action}',
                'calendar_id': calendar_id,
                'calendar_name': calendar_info.get('name', 'Unknown')
            },
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )

        return jsonify({
            'success': True,
            'calendar_id': calendar_id,
            'calendar_name': calendar_info.get('name'),
            'is_selected': is_selected,
            'action': action
        })

    except Exception as e:
        print(f"Error toggling calendar selection: {e}")
        return jsonify({'error': f'Failed to toggle calendar: {str(e)}'}), 500

@calendar_selection_bp.route('/user/<user_id>/selected', methods=['GET'])
def get_selected_calendars(user_id):
    """선택된 캘린더 목록 조회"""
    try:
        # 인증 확인
        current_user = get_current_user_id()
        if not current_user or current_user != user_id:
            return jsonify({'error': 'Authentication required'}), 401

        supabase = get_supabase_admin()

        # 활성화된 캘린더 정보 조회
        selected_result = supabase.table('calendars').select('*').eq('owner_id', user_id).eq('is_active', True).execute()

        selected_calendars = []
        for calendar in selected_result.data:
            selected_calendars.append({
                'id': calendar['id'],
                'name': calendar['name'],
                'color': calendar.get('color', '#4285f4'),
                'google_calendar_id': calendar.get('google_calendar_id'),
                'selected_at': calendar.get('updated_at', calendar.get('created_at')),
                'created_at': calendar.get('created_at')
            })

        return jsonify({
            'success': True,
            'user_id': user_id,
            'selected_calendars': selected_calendars,
            'count': len(selected_calendars)
        })

    except Exception as e:
        print(f"Error getting selected calendars: {e}")
        return jsonify({'error': f'Failed to get selected calendars: {str(e)}'}), 500

# Error handlers
@calendar_selection_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Calendar selection API endpoint not found'}), 404

@calendar_selection_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500