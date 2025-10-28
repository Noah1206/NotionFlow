import os
import json
import hmac
import hashlib
from flask import Blueprint, request, jsonify
from datetime import datetime
from backend.services.slack_service import SlackProvider
from backend.services.outlook_service import OutlookProvider
from backend.services.notion_service import NotionProvider
from supabase import create_client

webhooks_bp = Blueprint('webhooks', __name__, url_prefix='/webhooks')

# Supabase setup
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_API_KEY') or os.environ.get('SUPABASE_KEY')

# Initialize Supabase client only if credentials are available
supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("[SUCCESS] Supabase client initialized in webhook_handlers")
    except Exception as e:
        print(f"[WARNING] Failed to initialize Supabase client in webhook_handlers: {e}")
        supabase = None
else:
    print("[WARNING] Supabase credentials not found in webhook_handlers, webhook features disabled")

# If Supabase is not available, disable all webhook functionality
if not supabase:
    print("[INFO] Webhook handlers disabled due to missing Supabase connection")

# Webhook secrets
SLACK_SIGNING_SECRET = os.environ.get('SLACK_SIGNING_SECRET')
OUTLOOK_WEBHOOK_SECRET = os.environ.get('OUTLOOK_WEBHOOK_SECRET')

def verify_slack_signature(request):
    """Verify Slack webhook signature"""
    if not SLACK_SIGNING_SECRET:
        return True  # Skip verification in development
    
    timestamp = request.headers.get('X-Slack-Request-Timestamp', '')
    signature = request.headers.get('X-Slack-Signature', '')
    
    if not timestamp or not signature:
        return False
    
    # Check timestamp (prevent replay attacks)
    current_time = int(datetime.now().timestamp())
    if abs(current_time - int(timestamp)) > 300:  # 5 minutes
        return False
    
    # Verify signature
    sig_basestring = f"v0:{timestamp}:{request.get_data(as_text=True)}"
    expected_signature = 'v0=' + hmac.new(
        SLACK_SIGNING_SECRET.encode(),
        sig_basestring.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, signature)

def verify_outlook_signature(request):
    """Verify Outlook webhook signature"""
    if not OUTLOOK_WEBHOOK_SECRET:
        return True  # Skip verification in development
    
    signature = request.headers.get('X-Microsoft-Graph-ChangeType', '')
    # Implement Microsoft Graph webhook validation
    # This is a simplified version
    return True

def get_user_by_platform_id(platform, platform_user_id, team_id=None):
    """Get NotionFlow user ID by platform user ID"""
    try:
        if not supabase:
            return None
        result = supabase.table('platform_connections').select('user_id, raw_data').eq('platform', platform).execute()
        
        for connection in result.data:
            raw_data = connection.get('raw_data', {})
            
            if platform == 'slack':
                slack_team_id = raw_data.get('team', {}).get('id')
                slack_user_id = raw_data.get('authed_user', {}).get('id')
                if slack_team_id == team_id and slack_user_id == platform_user_id:
                    return connection['user_id']
            
            elif platform == 'outlook':
                outlook_user_id = raw_data.get('user_info', {}).get('id')
                if outlook_user_id == platform_user_id:
                    return connection['user_id']
        
        return None
    except Exception as e:
        print(f"Error getting user by platform ID: {e}")
        return None

@webhooks_bp.route('/slack/events', methods=['POST'])
def handle_slack_events():
    """Handle Slack Events API webhooks"""
    
    # Check if Supabase is available
    if not supabase:
        return jsonify({'error': 'Service temporarily unavailable'}), 503
    
    # Verify signature
    if not verify_slack_signature(request):
        return jsonify({'error': 'Invalid signature'}), 401
    
    data = request.get_json()
    
    # Handle URL verification challenge
    if data.get('type') == 'url_verification':
        return jsonify({'challenge': data.get('challenge')})
    
    # Handle events
    if data.get('type') == 'event_callback':
        event = data.get('event', {})
        team_id = data.get('team_id')
        
        return process_slack_event(event, team_id)
    
    return jsonify({'status': 'ok'})

def process_slack_event(event, team_id):
    """Process individual Slack events"""
    event_type = event.get('type')
    
    try:
        if event_type == 'message':
            return handle_slack_message(event, team_id)
        elif event_type == 'reaction_added':
            return handle_slack_reaction_added(event, team_id)
        elif event_type == 'reaction_removed':
            return handle_slack_reaction_removed(event, team_id)
        elif event_type == 'channel_created':
            return handle_slack_channel_created(event, team_id)
        elif event_type == 'channel_deleted':
            return handle_slack_channel_deleted(event, team_id)
        elif event_type == 'member_joined_channel':
            return handle_slack_member_joined(event, team_id)
        
        return jsonify({'status': 'ignored'})
        
    except Exception as e:
        print(f"Error processing Slack event {event_type}: {e}")
        return jsonify({'error': 'Processing failed'}), 500

def handle_slack_message(event, team_id):
    """Handle new Slack messages"""
    user_id = event.get('user')
    channel = event.get('channel')
    text = event.get('text', '')
    ts = event.get('ts')
    
    # Skip bot messages and messages without user
    if not user_id or event.get('bot_id'):
        return jsonify({'status': 'ignored'})
    
    # Get NotionFlow user
    notionflow_user = get_user_by_platform_id('slack', user_id, team_id)
    if not notionflow_user:
        return jsonify({'status': 'no_user'})
    
    # Get sync settings
    sync_settings = get_sync_settings(notionflow_user, 'slack')
    if not sync_settings or not sync_settings.get('realtime_sync'):
        return jsonify({'status': 'sync_disabled'})
    
    # Check if channel is in selected channels
    selected_channels = sync_settings.get('selected_channels', [])
    if selected_channels and channel not in selected_channels:
        return jsonify({'status': 'channel_not_selected'})
    
    # Check for sync triggers (keywords, reactions, etc.)
    sync_triggers = sync_settings.get('sync_triggers', {})
    
    # Keyword triggers
    keywords = sync_triggers.get('keywords', [])
    if keywords:
        has_keyword = any(keyword.lower() in text.lower() for keyword in keywords)
        if not has_keyword:
            return jsonify({'status': 'no_trigger_keyword'})
    
    # Schedule message sync
    schedule_slack_message_sync(notionflow_user, event, team_id)
    
    return jsonify({'status': 'scheduled'})

def handle_slack_reaction_added(event, team_id):
    """Handle reaction added to Slack messages"""
    user_id = event.get('user')
    reaction = event.get('reaction')
    item = event.get('item', {})
    
    if item.get('type') != 'message':
        return jsonify({'status': 'ignored'})
    
    # Get NotionFlow user
    notionflow_user = get_user_by_platform_id('slack', user_id, team_id)
    if not notionflow_user:
        return jsonify({'status': 'no_user'})
    
    # Get sync settings
    sync_settings = get_sync_settings(notionflow_user, 'slack')
    if not sync_settings or not sync_settings.get('reaction_sync'):
        return jsonify({'status': 'reaction_sync_disabled'})
    
    # Check if reaction is a sync trigger
    sync_reactions = sync_settings.get('sync_reactions', ['bookmark', 'pushpin', 'star'])
    if reaction not in sync_reactions:
        return jsonify({'status': 'not_sync_reaction'})
    
    # Get the original message and sync it
    channel = item.get('channel')
    ts = item.get('ts')
    
    schedule_slack_message_sync_by_reaction(notionflow_user, channel, ts, reaction, team_id)
    
    return jsonify({'status': 'scheduled'})

def handle_slack_reaction_removed(event, team_id):
    """Handle reaction removed from Slack messages"""
    # Similar to reaction_added but might trigger unsync if configured
    return jsonify({'status': 'ok'})

def handle_slack_channel_created(event, team_id):
    """Handle new Slack channel creation"""
    # Update channel list for users in this team
    update_team_channel_cache(team_id)
    return jsonify({'status': 'ok'})

def handle_slack_channel_deleted(event, team_id):
    """Handle Slack channel deletion"""
    # Update channel list and clean up sync settings
    channel_id = event.get('channel')
    update_team_channel_cache(team_id)
    clean_up_deleted_channel_settings(team_id, channel_id)
    return jsonify({'status': 'ok'})

def handle_slack_member_joined(event, team_id):
    """Handle member joining Slack channel"""
    # Could trigger welcome message or auto-sync setup
    return jsonify({'status': 'ok'})

@webhooks_bp.route('/outlook/notifications', methods=['POST'])
def handle_outlook_notifications():
    """Handle Microsoft Graph webhooks for Outlook calendar changes"""
    
    # Check if Supabase is available
    if not supabase:
        return jsonify({'error': 'Service temporarily unavailable'}), 503
    
    # Verify signature
    if not verify_outlook_signature(request):
        return jsonify({'error': 'Invalid signature'}), 401
    
    # Microsoft Graph sends validation tokens
    validation_token = request.args.get('validationToken')
    if validation_token:
        return validation_token, 200, {'Content-Type': 'text/plain'}
    
    data = request.get_json()
    
    # Handle notification array
    notifications = data.get('value', [])
    
    for notification in notifications:
        process_outlook_notification(notification)
    
    return jsonify({'status': 'ok'})

def process_outlook_notification(notification):
    """Process individual Outlook notifications"""
    try:
        resource = notification.get('resource')
        change_type = notification.get('changeType')
        client_state = notification.get('clientState')
        
        # Extract user ID from client state or resource
        user_id = extract_user_from_resource(resource, client_state)
        if not user_id:
            return
        
        # Get sync settings
        sync_settings = get_sync_settings(user_id, 'outlook')
        if not sync_settings or not sync_settings.get('realtime_sync'):
            return
        
        if change_type in ['created', 'updated']:
            schedule_outlook_event_sync(user_id, resource, change_type)
        elif change_type == 'deleted':
            schedule_outlook_event_deletion(user_id, resource)
            
    except Exception as e:
        print(f"Error processing Outlook notification: {e}")

def get_sync_settings(user_id, platform):
    """Get sync settings for user and platform"""
    try:
        if not supabase:
            return None
        result = supabase.table('sync_settings').select('settings').eq('user_id', user_id).eq('platform', platform).single().execute()
        return result.data.get('settings', {}) if result.data else None
    except Exception as e:
        print(f"Error getting sync settings: {e}")
        return None

def schedule_slack_message_sync(user_id, event, team_id):
    """Schedule Slack message sync job"""
    try:
        if not supabase:
            return
        job_data = {
            'user_id': user_id,
            'platform': 'slack',
            'type': 'message_sync',
            'status': 'pending',
            'data': {
                'event': event,
                'team_id': team_id,
                'sync_type': 'realtime'
            },
            'created_at': datetime.utcnow().isoformat()
        }
        
        supabase.table('sync_jobs').insert(job_data).execute()
        
        # Trigger sync worker (you could use Celery, RQ, or similar)
        # For now, we'll just log it
        print(f"Scheduled Slack message sync for user {user_id}")
        
    except Exception as e:
        print(f"Error scheduling Slack message sync: {e}")

def schedule_slack_message_sync_by_reaction(user_id, channel, ts, reaction, team_id):
    """Schedule Slack message sync triggered by reaction"""
    try:
        if not supabase:
            return
        job_data = {
            'user_id': user_id,
            'platform': 'slack',
            'type': 'reaction_sync',
            'status': 'pending',
            'data': {
                'channel': channel,
                'ts': ts,
                'reaction': reaction,
                'team_id': team_id,
                'sync_type': 'reaction_trigger'
            },
            'created_at': datetime.utcnow().isoformat()
        }
        
        supabase.table('sync_jobs').insert(job_data).execute()
        print(f"Scheduled Slack reaction sync for user {user_id}")
        
    except Exception as e:
        print(f"Error scheduling Slack reaction sync: {e}")

def schedule_outlook_event_sync(user_id, resource, change_type):
    """Schedule Outlook event sync job"""
    try:
        if not supabase:
            return
        job_data = {
            'user_id': user_id,
            'platform': 'outlook',
            'type': 'event_sync',
            'status': 'pending',
            'data': {
                'resource': resource,
                'change_type': change_type,
                'sync_type': 'realtime'
            },
            'created_at': datetime.utcnow().isoformat()
        }
        
        supabase.table('sync_jobs').insert(job_data).execute()
        print(f"Scheduled Outlook event sync for user {user_id}")
        
    except Exception as e:
        print(f"Error scheduling Outlook event sync: {e}")

def schedule_outlook_event_deletion(user_id, resource):
    """Schedule Outlook event deletion sync"""
    try:
        if not supabase:
            return
        job_data = {
            'user_id': user_id,
            'platform': 'outlook',
            'type': 'event_deletion',
            'status': 'pending',
            'data': {
                'resource': resource,
                'sync_type': 'realtime_deletion'
            },
            'created_at': datetime.utcnow().isoformat()
        }
        
        supabase.table('sync_jobs').insert(job_data).execute()
        print(f"Scheduled Outlook event deletion for user {user_id}")
        
    except Exception as e:
        print(f"Error scheduling Outlook event deletion: {e}")

def update_team_channel_cache(team_id):
    """Update channel cache for a Slack team"""
    # Implementation would update cached channel list
    pass

def clean_up_deleted_channel_settings(team_id, channel_id):
    """Clean up sync settings for deleted channel"""
    try:
        if not supabase:
            return
        # Find users with this channel in their settings
        result = supabase.table('sync_settings').select('*').eq('platform', 'slack').execute()
        
        for setting in result.data:
            settings = setting.get('settings', {})
            selected_channels = settings.get('selected_channels', [])
            
            if channel_id in selected_channels:
                selected_channels.remove(channel_id)
                settings['selected_channels'] = selected_channels
                
                supabase.table('sync_settings').update({
                    'settings': settings,
                    'updated_at': datetime.utcnow().isoformat()
                }).eq('id', setting['id']).execute()
                
    except Exception as e:
        print(f"Error cleaning up deleted channel settings: {e}")

def extract_user_from_resource(resource, client_state):
    """Extract user ID from Outlook webhook resource"""
    # This would parse the resource URL or client state to get the user ID
    # Implementation depends on how you structure your webhooks
    if client_state:
        try:
            return json.loads(client_state).get('user_id')
        except:
            pass
    
    # Fallback: extract from resource URL
    # Example: /users/{user-id}/events/{event-id}
    if resource and '/users/' in resource:
        parts = resource.split('/users/')
        if len(parts) > 1:
            user_part = parts[1].split('/')[0]
            # Look up NotionFlow user by Outlook user ID
            return get_user_by_platform_id('outlook', user_part)
    
    return None

# Background job processor (you might want to move this to a separate worker)
def process_sync_jobs():
    """Process pending sync jobs"""
    try:
        if not supabase:
            return
        # Get pending jobs
        result = supabase.table('sync_jobs').select('*').eq('status', 'pending').order('created_at').limit(10).execute()
        
        for job in result.data:
            try:
                # Mark as running
                supabase.table('sync_jobs').update({
                    'status': 'running',
                    'started_at': datetime.utcnow().isoformat()
                }).eq('id', job['id']).execute()
                
                # Process based on platform and type
                if job['platform'] == 'slack':
                    process_slack_sync_job(job)
                elif job['platform'] == 'outlook':
                    process_outlook_sync_job(job)
                
                # Mark as completed
                supabase.table('sync_jobs').update({
                    'status': 'completed',
                    'completed_at': datetime.utcnow().isoformat()
                }).eq('id', job['id']).execute()
                
            except Exception as e:
                # Mark as failed
                supabase.table('sync_jobs').update({
                    'status': 'failed',
                    'error': str(e),
                    'completed_at': datetime.utcnow().isoformat()
                }).eq('id', job['id']).execute()
                
                print(f"Error processing sync job {job['id']}: {e}")
                
    except Exception as e:
        print(f"Error processing sync jobs: {e}")

def process_slack_sync_job(job):
    """Process a Slack sync job"""
    # Implementation would handle the actual syncing
    print(f"Processing Slack sync job: {job['type']}")

def process_outlook_sync_job(job):
    """Process an Outlook sync job"""
    # Implementation would handle the actual syncing
    print(f"Processing Outlook sync job: {job['type']}")