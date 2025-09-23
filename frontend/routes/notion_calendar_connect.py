"""
Notion Calendar Connection Routes
사용자가 Notion과 연결할 캘린더를 선택하는 API
"""

from flask import Blueprint, request, jsonify, session
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from utils.config import config

notion_calendar_bp = Blueprint('notion_calendar', __name__, url_prefix='/api/notion')

@notion_calendar_bp.route('/connect-calendar', methods=['POST'])
def connect_notion_to_calendar():
    """Connect Notion to a specific calendar chosen by user"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
            
        data = request.get_json()
        calendar_id = data.get('calendar_id')
        
        if not calendar_id:
            return jsonify({'error': 'Calendar ID is required'}), 400
            
        # Check if user owns this calendar
        supabase = config.get_client_for_user(user_id)
        calendar_check = supabase.table('calendars').select('*').eq('id', calendar_id).eq('owner_id', user_id).execute()
        
        if not calendar_check.data:
            return jsonify({'error': 'Calendar not found or access denied'}), 404
            
        # Update calendar_sync_configs with the selected calendar_id and enable sync
        update_result = supabase.table('calendar_sync_configs').update({
            'calendar_id': calendar_id,
            'sync_status': 'active',
            'is_enabled': True,
            'updated_at': datetime.now().isoformat()
        }).eq('user_id', user_id).eq('platform', 'notion').execute()
        
        if not update_result.data:
            return jsonify({'error': 'Notion configuration not found. Please reconnect Notion first.'}), 404
            
        # Create or update calendar_sync entry
        sync_data = {
            'user_id': user_id,
            'platform': 'notion',
            'calendar_id': calendar_id,
            'is_active': True,
            'sync_status': 'active',
            'synced_at': datetime.now().isoformat(),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Check if sync entry exists
        existing_sync = supabase.table('calendar_sync').select('*').eq('user_id', user_id).eq('platform', 'notion').eq('calendar_id', calendar_id).execute()
        
        if existing_sync.data:
            # Update existing
            supabase.table('calendar_sync').update({
                'is_active': True,
                'sync_status': 'active',
                'synced_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }).eq('id', existing_sync.data[0]['id']).execute()
        else:
            # Create new
            supabase.table('calendar_sync').insert(sync_data).execute()
            
        # Clear the session flag
        session.pop('notion_needs_calendar_selection', None)
        
        # 🚀 IMMEDIATE SYNC & GRID BLOCK GENERATION
        # Import here to avoid circular imports
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
        from services.notion_sync import sync_notion_events
        
        try:
            print(f"🚀 [CONNECT] Starting immediate Notion sync for calendar {calendar_id}")
            
            # Trigger immediate Notion sync
            sync_result = sync_notion_events(user_id, calendar_id)
            
            if sync_result.get('success'):
                synced_count = sync_result.get('synced_count', 0)
                print(f"✅ [CONNECT] Immediate sync completed: {synced_count} events synced")
                
                return jsonify({
                    'success': True,
                    'message': f'Notion connected successfully. {synced_count} events synced to calendar.',
                    'calendar_id': calendar_id,
                    'synced_count': synced_count,
                    'trigger_calendar_refresh': True,  # 프론트엔드에서 캘린더 새로고침 트리거
                    'clear_disconnected_flag': True
                })
            else:
                print(f"⚠️ [CONNECT] Sync completed with issues: {sync_result.get('error', 'Unknown error')}")
                
                return jsonify({
                    'success': True,
                    'message': f'Notion connected successfully, but sync had issues: {sync_result.get("error", "Unknown error")}',
                    'calendar_id': calendar_id,
                    'sync_warning': sync_result.get('error'),
                    'trigger_calendar_refresh': True,
                    'clear_disconnected_flag': True
                })
                
        except Exception as sync_error:
            print(f"❌ [CONNECT] Immediate sync failed: {sync_error}")
            
            return jsonify({
                'success': True,
                'message': f'Notion connected successfully, but immediate sync failed: {str(sync_error)}',
                'calendar_id': calendar_id,
                'sync_error': str(sync_error),
                'trigger_calendar_refresh': True,
                'clear_disconnected_flag': True
            })
        
    except Exception as e:
        print(f"Error connecting Notion to calendar: {e}")
        return jsonify({'error': f'Failed to connect: {str(e)}'}), 500

@notion_calendar_bp.route('/disconnect-calendar', methods=['POST'])
def disconnect_notion_from_calendar():
    """Disconnect Notion from calendar"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
            
        data = request.get_json()
        calendar_id = data.get('calendar_id')
        
        supabase = config.get_client_for_user(user_id)
        
        # Update calendar_sync_configs to remove calendar_id and set selection needed status
        supabase.table('calendar_sync_configs').update({
            'calendar_id': None,
            'sync_status': 'needs_calendar_selection',
            'is_enabled': False,
            'updated_at': datetime.now().isoformat()
        }).eq('user_id', user_id).eq('platform', 'notion').execute()
        
        # Deactivate calendar_sync entry
        if calendar_id:
            supabase.table('calendar_sync').update({
                'is_active': False,
                'sync_status': 'inactive',
                'updated_at': datetime.now().isoformat()
            }).eq('user_id', user_id).eq('platform', 'notion').eq('calendar_id', calendar_id).execute()
        
        return jsonify({
            'success': True,
            'message': 'Notion disconnected from calendar'
        })
        
    except Exception as e:
        print(f"Error disconnecting Notion from calendar: {e}")
        return jsonify({'error': f'Failed to disconnect: {str(e)}'}), 500