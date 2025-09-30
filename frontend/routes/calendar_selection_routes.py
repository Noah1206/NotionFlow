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

        # 선택된 캘린더 정보 조회
        selected_result = supabase.table('selected_calendars').select('*').eq('user_id', user_id).eq('is_selected', True).execute()

        selected_calendar_ids = {item['calendar_id'] for item in selected_result.data}

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

        # 기존 선택 상태 모두 삭제
        supabase.table('selected_calendars').delete().eq('user_id', user_id).execute()

        # 새로운 선택 상태 저장
        if calendar_ids:
            selection_data = []
            for calendar_id in calendar_ids:
                # 캘린더가 실제로 존재하는지 확인
                calendar_check = supabase.table('calendars').select('id').eq('owner_id', user_id).eq('id', calendar_id).execute()

                if calendar_check.data:
                    selection_data.append({
                        'user_id': user_id,
                        'calendar_id': calendar_id,
                        'is_selected': True,
                        'selected_at': datetime.now().isoformat()
                    })

            if selection_data:
                supabase.table('selected_calendars').insert(selection_data).execute()

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

        # 현재 선택 상태 확인
        selection_check = supabase.table('selected_calendars').select('*').eq('user_id', user_id).eq('calendar_id', calendar_id).execute()

        if selection_check.data:
            # 이미 선택된 경우 - 선택 해제
            supabase.table('selected_calendars').delete().eq('user_id', user_id).eq('calendar_id', calendar_id).execute()
            is_selected = False
            action = 'deselected'
        else:
            # 선택되지 않은 경우 - 선택
            supabase.table('selected_calendars').insert({
                'user_id': user_id,
                'calendar_id': calendar_id,
                'is_selected': True,
                'selected_at': datetime.now().isoformat()
            }).execute()
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

        # 선택된 캘린더 정보 조회 (JOIN 사용)
        selected_result = supabase.table('selected_calendars').select('''
            calendar_id,
            selected_at,
            user_calendars (
                id,
                name,
                color,
                google_calendar_id,
                created_at
            )
        ''').eq('user_id', user_id).eq('is_selected', True).execute()

        selected_calendars = []
        for item in selected_result.data:
            calendar_data = item.get('user_calendars')
            if calendar_data:
                selected_calendars.append({
                    'id': calendar_data['id'],
                    'name': calendar_data['name'],
                    'color': calendar_data.get('color', '#4285f4'),
                    'google_calendar_id': calendar_data.get('google_calendar_id'),
                    'selected_at': item['selected_at'],
                    'created_at': calendar_data.get('created_at')
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