from flask import Blueprint, request, jsonify, session
import os
import sys
import requests
from datetime import datetime, timedelta
from supabase import create_client
from dotenv import load_dotenv

# Add parent directory to path to import backend services
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from backend.services.slack_service import SlackProvider
from backend.services.outlook_service import OutlookProvider

# Load environment variables
load_dotenv()

integration_bp = Blueprint('integration', __name__, url_prefix='/api')

# Supabase setup
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_API_KEY')

if not SUPABASE_URL:
    raise Exception("SUPABASE_URL environment variable is required")
if not SUPABASE_KEY:
    raise Exception("SUPABASE_API_KEY environment variable is required")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_platform_connection(user_id: str, platform: str):
    """Get platform connection for user"""
    try:
        result = supabase.table('platform_connections').select('*').eq('user_id', user_id).eq('platform', platform).single().execute()
        return result.data if result.data else None
    except Exception as e:
        print(f"Error getting platform connection: {e}")
        return None

def is_token_expired(connection):
    """Check if access token is expired"""
    if not connection.get('expires_at'):
        return False  # Slack tokens don't expire
    
    expires_at = datetime.fromisoformat(connection['expires_at'])
    return datetime.utcnow() >= expires_at - timedelta(minutes=5)  # 5 minute buffer

@integration_bp.route('/connections/<platform>')
def get_connection_status(platform):
    """Get connection status for a platform"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({
            'connected': False,
            'message': 'Not authenticated'
        })
    
    try:
        connection = get_platform_connection(user_id, platform)
        
        if not connection:
            return jsonify({'connected': False})
        
        # Check if token is expired
        if is_token_expired(connection):
            return jsonify({
                'connected': True,
                'expired': True,
                'message': 'Token expired, please reconnect'
            })
        
        # Get additional info based on platform
        response_data = {'connected': True, 'expired': False}
        
        if platform == 'slack':
            if connection.get('team'):
                response_data['workspace'] = {
                    'name': connection['team'].get('name'),
                    'id': connection['team'].get('id')
                }
            
            if connection.get('authed_user'):
                response_data['user'] = {
                    'name': connection['authed_user'].get('name'),
                    'email': connection['authed_user'].get('email'),
                    'id': connection['authed_user'].get('id')
                }
        
        elif platform == 'outlook':
            if connection.get('user_info'):
                response_data['user'] = {
                    'name': connection['user_info'].get('displayName'),
                    'email': connection['user_info'].get('mail') or connection['user_info'].get('userPrincipalName'),
                    'id': connection['user_info'].get('id')
                }
        
        # Get sync settings
        settings_result = supabase.table('sync_settings').select('*').eq('user_id', user_id).eq('platform', platform).execute()
        if settings_result.data:
            response_data['settings'] = settings_result.data[0].get('settings', {})
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error getting connection status: {e}")
        return jsonify({'error': 'Failed to get connection status'}), 500

@integration_bp.route('/slack/channels')
def get_slack_channels():
    """Get Slack channels for connected workspace"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        connection = get_platform_connection(user_id, 'slack')
        if not connection:
            return jsonify({'error': 'Slack not connected'}), 404
        
        slack = SlackProvider(connection['access_token'], connection.get('team', {}).get('id'))
        
        # Test connection first
        test_result = slack.test_connection()
        if not test_result.get('success'):
            return jsonify({'error': 'Slack connection failed', 'details': test_result.get('error')}), 400
        
        # Get channels
        channels = slack.get_channels()
        
        # Get current sync settings to mark selected channels
        settings_result = supabase.table('sync_settings').select('*').eq('user_id', user_id).eq('platform', 'slack').execute()
        selected_channels = []
        if settings_result.data:
            settings = settings_result.data[0].get('settings', {})
            selected_channels = settings.get('selected_channels', [])
        
        # Format channels for response
        formatted_channels = []
        for channel in channels:
            formatted_channels.append({
                'id': channel['id'],
                'name': channel['name'],
                'is_private': channel.get('is_private', False),
                'is_member': channel.get('is_member', False),
                'selected': channel['id'] in selected_channels
            })
        
        return jsonify(formatted_channels)
        
    except Exception as e:
        print(f"Error getting Slack channels: {e}")
        return jsonify({'error': 'Failed to get channels'}), 500

@integration_bp.route('/slack/settings', methods=['POST'])
def save_slack_settings():
    """Save Slack sync settings"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        
        settings_data = {
            'user_id': user_id,
            'platform': 'slack',
            'settings': data,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        # Upsert settings
        supabase.table('sync_settings').upsert(
            settings_data,
            on_conflict='user_id,platform'
        ).execute()
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Error saving Slack settings: {e}")
        return jsonify({'error': 'Failed to save settings'}), 500

@integration_bp.route('/outlook/calendars')
def get_outlook_calendars():
    """Get Outlook calendars for connected account"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        connection = get_platform_connection(user_id, 'outlook')
        if not connection:
            return jsonify({'error': 'Outlook not connected'}), 404
        
        # Check if token needs refresh
        if is_token_expired(connection):
            return jsonify({'error': 'Token expired, please reconnect'}), 401
        
        outlook = OutlookProvider(connection['access_token'], connection.get('refresh_token'))
        
        # Test connection first
        test_result = outlook.test_connection()
        if not test_result.get('success'):
            return jsonify({'error': 'Outlook connection failed', 'details': test_result.get('error')}), 400
        
        # Get calendars
        calendars = outlook.get_calendars()
        
        # Get current sync settings to mark selected calendars
        settings_result = supabase.table('sync_settings').select('*').eq('user_id', user_id).eq('platform', 'outlook').execute()
        selected_calendars = []
        if settings_result.data:
            settings = settings_result.data[0].get('settings', {})
            selected_calendars = settings.get('selected_calendars', [])
        
        # Format calendars for response
        formatted_calendars = []
        for calendar in calendars:
            formatted_calendars.append({
                'id': calendar['id'],
                'name': calendar['name'],
                'color': calendar.get('color'),
                'is_default': calendar.get('isDefault', False),
                'can_edit': calendar.get('canEdit', False),
                'selected': calendar['id'] in selected_calendars
            })
        
        return jsonify(formatted_calendars)
        
    except Exception as e:
        print(f"Error getting Outlook calendars: {e}")
        return jsonify({'error': 'Failed to get calendars'}), 500

@integration_bp.route('/outlook/events')
def get_outlook_events():
    """Get Outlook events for a date range"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        connection = get_platform_connection(user_id, 'outlook')
        if not connection:
            return jsonify({'error': 'Outlook not connected'}), 404
        
        # Check if token needs refresh
        if is_token_expired(connection):
            return jsonify({'error': 'Token expired, please reconnect'}), 401
        
        # Get query parameters
        start_date = request.args.get('start')
        end_date = request.args.get('end')
        calendar_id = request.args.get('calendar_id')
        
        outlook = OutlookProvider(connection['access_token'], connection.get('refresh_token'))
        
        # Get events
        events = outlook.get_events(calendar_id, start_date, end_date)
        
        return jsonify(events)
        
    except Exception as e:
        print(f"Error getting Outlook events: {e}")
        return jsonify({'error': 'Failed to get events'}), 500

@integration_bp.route('/outlook/settings', methods=['POST'])
def save_outlook_settings():
    """Save Outlook sync settings"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        
        settings_data = {
            'user_id': user_id,
            'platform': 'outlook',
            'settings': data,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        # Upsert settings
        supabase.table('sync_settings').upsert(
            settings_data,
            on_conflict='user_id,platform'
        ).execute()
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Error saving Outlook settings: {e}")
        return jsonify({'error': 'Failed to save settings'}), 500

@integration_bp.route('/sync/manual/<platform>')
def trigger_manual_sync(platform):
    """Trigger manual sync for a platform"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        connection = get_platform_connection(user_id, platform)
        if not connection:
            return jsonify({'error': f'{platform.title()} not connected'}), 404
        
        # Get sync settings
        settings_result = supabase.table('sync_settings').select('*').eq('user_id', user_id).eq('platform', platform).execute()
        if not settings_result.data:
            return jsonify({'error': 'No sync settings found'}), 404
        
        settings = settings_result.data[0].get('settings', {})
        
        # Create sync job
        sync_job = {
            'user_id': user_id,
            'platform': platform,
            'type': 'manual',
            'status': 'pending',
            'settings': settings,
            'created_at': datetime.utcnow().isoformat()
        }
        
        result = supabase.table('sync_jobs').insert(sync_job).execute()
        job_id = result.data[0]['id']
        
        # Here you would trigger your sync worker
        # For now, we'll just return the job ID
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': f'{platform.title()} sync started'
        })
        
    except Exception as e:
        print(f"Error triggering sync: {e}")
        return jsonify({'error': 'Failed to trigger sync'}), 500

@integration_bp.route('/sync/status/<job_id>')
def get_sync_status(job_id):
    """Get status of a sync job"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        result = supabase.table('sync_jobs').select('*').eq('id', job_id).eq('user_id', user_id).single().execute()
        
        if not result.data:
            return jsonify({'error': 'Sync job not found'}), 404
        
        job = result.data
        
        return jsonify({
            'id': job['id'],
            'platform': job['platform'],
            'type': job['type'],
            'status': job['status'],
            'progress': job.get('progress', 0),
            'message': job.get('message', ''),
            'created_at': job['created_at'],
            'completed_at': job.get('completed_at'),
            'error': job.get('error')
        })
        
    except Exception as e:
        print(f"Error getting sync status: {e}")
        return jsonify({'error': 'Failed to get sync status'}), 500