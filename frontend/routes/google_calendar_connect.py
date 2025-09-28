"""
Google Calendar Connection Routes
사용자가 Google Calendar와 연결할 캘린더를 선택하는 API (Notion 패턴과 동일)
"""

from flask import Blueprint, request, jsonify, session
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from utils.config import config
from utils.auth_manager import AuthManager

google_calendar_connect_bp = Blueprint('google_calendar_connect', __name__, url_prefix='/api/google-calendar')

@google_calendar_connect_bp.route('/connect-calendar', methods=['POST'])
def connect_google_to_calendar():
    """Connect Google Calendar to a specific calendar chosen by user"""
    try:
        print(f"🔗 [GOOGLE-CONNECT] Request received")
        user_id = AuthManager.get_current_user_id()
        if not user_id:
            print(f"❌ [GOOGLE-CONNECT] No user authentication")
            return jsonify({'error': 'User not authenticated'}), 401

        data = request.get_json()
        calendar_id = data.get('calendar_id')
        google_calendar_id = data.get('google_calendar_id')

        print(f"🔗 [GOOGLE-CONNECT] User: {user_id}")
        print(f"🔗 [GOOGLE-CONNECT] NotionFlow calendar_id: {calendar_id}")
        print(f"🔗 [GOOGLE-CONNECT] Google calendar_id: {google_calendar_id}")

        if not calendar_id:
            print(f"❌ [GOOGLE-CONNECT] Missing calendar_id")
            return jsonify({'error': 'Calendar ID is required'}), 400

        # Convert user_id to the format used in database (with hyphens)
        if len(user_id) == 32 and '-' not in user_id:
            # Convert from 87875eda6797f839f8c70aa90efb1352 to 87875eda-6797-f839-f8c7-0aa90efb1352
            formatted_user_id = f"{user_id[:8]}-{user_id[8:12]}-{user_id[12:16]}-{user_id[16:20]}-{user_id[20:]}"
            print(f"🔗 [GOOGLE-CONNECT] Converted user_id: {user_id} -> {formatted_user_id}")
        else:
            formatted_user_id = user_id

        # Check if user owns this calendar
        supabase = config.get_client_for_user(user_id)
        print(f"🔗 [GOOGLE-CONNECT] Checking calendar ownership...")
        calendar_check = supabase.table('calendars').select('*').eq('id', calendar_id).eq('owner_id', formatted_user_id).execute()

        print(f"🔗 [GOOGLE-CONNECT] Calendar check result: {calendar_check.data}")

        if not calendar_check.data:
            print(f"❌ [GOOGLE-CONNECT] Calendar not found - calendar_id: {calendar_id}, user_id: {user_id}")
            return jsonify({'error': 'Calendar not found or access denied'}), 404

        print(f"✅ [GOOGLE-CONNECT] Calendar ownership verified")

        # Update calendar_sync_configs with the selected calendar_id and enable sync
        credentials_data = {
            'oauth_connected': True,
            'calendar_id': calendar_id,
            'connected_at': datetime.now().isoformat(),
            'real_time_sync': True
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

        # Create or update calendar_sync entry
        sync_data = {
            'user_id': user_id,
            'platform': 'google',
            'calendar_id': calendar_id,
            'sync_status': 'active',
            'synced_at': datetime.now().isoformat(),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

        # Check if sync entry exists
        existing_sync = supabase.table('calendar_sync').select('*').eq('user_id', user_id).eq('platform', 'google').eq('calendar_id', calendar_id).execute()

        if existing_sync.data:
            # Update existing
            supabase.table('calendar_sync').update({
                'sync_status': 'active',
                'synced_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }).eq('id', existing_sync.data[0]['id']).execute()
        else:
            # Create new
            supabase.table('calendar_sync').insert(sync_data).execute()

        # Clear the session flag
        session.pop('google_needs_calendar_selection', None)

        # 🚀 IMMEDIATE SYNC & GRID BLOCK GENERATION
        # Import here to avoid circular imports
        from services.google_calendar_sync import sync_google_calendar_for_user

        try:
            print(f"🚀 [GOOGLE CONNECT] Starting immediate Google Calendar sync for calendar {calendar_id}")

            # Trigger immediate Google Calendar sync
            sync_result = sync_google_calendar_for_user(user_id)

            if sync_result.get('success'):
                synced_count = sync_result.get('events_processed', 0)
                print(f"✅ [GOOGLE CONNECT] Immediate sync completed: {synced_count} events synced")

                return jsonify({
                    'success': True,
                    'message': f'Google Calendar connected successfully. {synced_count} events synced to calendar.',
                    'calendar_id': calendar_id,
                    'synced_count': synced_count,
                    'trigger_calendar_refresh': True,  # 프론트엔드에서 캘린더 새로고침 트리거
                    'clear_disconnected_flag': True
                })
            else:
                print(f"⚠️ [GOOGLE CONNECT] Sync completed with issues: {sync_result.get('error', 'Unknown error')}")

                return jsonify({
                    'success': True,
                    'message': f'Google Calendar connected successfully, but sync had issues: {sync_result.get("error", "Unknown error")}',
                    'calendar_id': calendar_id,
                    'sync_warning': sync_result.get('error'),
                    'trigger_calendar_refresh': True,
                    'clear_disconnected_flag': True
                })

        except Exception as sync_error:
            print(f"❌ [GOOGLE CONNECT] Immediate sync failed: {sync_error}")

            return jsonify({
                'success': True,
                'message': f'Google Calendar connected successfully, but immediate sync failed: {str(sync_error)}',
                'calendar_id': calendar_id,
                'sync_error': str(sync_error),
                'trigger_calendar_refresh': True,
                'clear_disconnected_flag': True
            })

    except Exception as e:
        print(f"Error connecting Google Calendar to calendar: {e}")
        return jsonify({'error': f'Failed to connect: {str(e)}'}), 500

@google_calendar_connect_bp.route('/disconnect-calendar', methods=['POST'])
def disconnect_google_from_calendar():
    """Disconnect Google Calendar from calendar"""
    try:
        user_id = AuthManager.get_current_user_id()
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401

        data = request.get_json()
        calendar_id = data.get('calendar_id')

        supabase = config.get_client_for_user(user_id)

        # Update calendar_sync_configs to remove calendar_id and set selection needed status
        supabase.table('calendar_sync_configs').update({
            'credentials': {
                'oauth_connected': True,
                'needs_calendar_selection': True,
                'disconnected_at': datetime.now().isoformat()
            },
            'is_enabled': False,
            'updated_at': datetime.now().isoformat()
        }).eq('user_id', user_id).eq('platform', 'google').execute()

        # Deactivate calendar_sync entry
        if calendar_id:
            supabase.table('calendar_sync').update({
                'sync_status': 'inactive',
                'updated_at': datetime.now().isoformat()
            }).eq('user_id', user_id).eq('platform', 'google').eq('calendar_id', calendar_id).execute()

        return jsonify({
            'success': True,
            'message': 'Google Calendar disconnected from calendar'
        })

    except Exception as e:
        print(f"Error disconnecting Google Calendar from calendar: {e}")
        return jsonify({'error': f'Failed to disconnect: {str(e)}'}), 500