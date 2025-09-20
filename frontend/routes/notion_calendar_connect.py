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
            
        # Update calendar_sync_configs with the selected calendar_id
        update_result = supabase.table('calendar_sync_configs').update({
            'calendar_id': calendar_id,
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
        
        return jsonify({
            'success': True,
            'message': f'Notion connected to calendar successfully',
            'calendar_id': calendar_id
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
        
        # Update calendar_sync_configs to remove calendar_id
        supabase.table('calendar_sync_configs').update({
            'calendar_id': None,
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