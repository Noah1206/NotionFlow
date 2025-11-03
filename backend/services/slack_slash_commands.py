import os
import json
import requests
from flask import Blueprint, request, jsonify
from datetime import datetime
from backend.services.slack_service import SlackProvider
from backend.services.notion_service import NotionProvider
from supabase import create_client

slash_commands_bp = Blueprint('slack_slash', __name__, url_prefix='/slack')

# Supabase setup
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_API_KEY') or os.environ.get('SUPABASE_KEY')

# Initialize Supabase client only if credentials are available
supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("[SUCCESS] Supabase client initialized in slack_slash_commands")
    except Exception as e:
        print(f"[WARNING] Failed to initialize Supabase client in slack_slash_commands: {e}")
        supabase = None
else:
    print("[WARNING] Supabase credentials not found in slack_slash_commands, slash commands disabled")

def verify_slack_request(request):
    """Verify that the request came from Slack"""
    # In production, you should verify the request signature
    # For now, we'll just check if it has the required fields
    required_fields = ['token', 'team_id', 'user_id', 'command']
    return all(field in request.form for field in required_fields)

def get_user_by_slack_team_user(team_id, user_id):
    """Get NodeFlow user by Slack team and user ID"""
    try:
        if not supabase:
            return None
        result = supabase.table('platform_connections').select('user_id').eq('platform', 'slack').execute()
        
        for connection in result.data:
            raw_data = connection.get('raw_data', {})
            if (raw_data.get('team', {}).get('id') == team_id and 
                raw_data.get('authed_user', {}).get('id') == user_id):
                return connection['user_id']
        
        return None
    except Exception as e:
        print(f"Error getting user: {e}")
        return None

@slash_commands_bp.route('/commands/notion', methods=['POST'])
def handle_notion_command():
    """Handle /notion slash command"""
    
    # Check if Supabase is available
    if not supabase:
        return jsonify({'text': 'Service temporarily unavailable'}), 503
    
    # Verify request is from Slack
    if not verify_slack_request(request):
        return jsonify({'text': 'Unauthorized request'}), 401
    
    # Get form data
    token = request.form.get('token')
    team_id = request.form.get('team_id')
    team_domain = request.form.get('team_domain')
    channel_id = request.form.get('channel_id')
    channel_name = request.form.get('channel_name')
    user_id = request.form.get('user_id')
    user_name = request.form.get('user_name')
    command = request.form.get('command')
    text = request.form.get('text', '').strip()
    response_url = request.form.get('response_url')
    
    # Get NodeFlow user
    notionflow_user = get_user_by_slack_team_user(team_id, user_id)
    if not notionflow_user:
        return jsonify({
            'response_type': 'ephemeral',
            'text': 'You need to connect your Slack account to NodeFlow first. Visit your NodeFlow dashboard to set up the integration.'
        })
    
    # Parse command text
    if not text:
        return show_help()
    
    parts = text.split(' ', 2)
    action = parts[0].lower()
    
    if action == 'help':
        return show_help()
    elif action == 'create':
        return handle_create_command(parts[1:], notionflow_user, channel_id, user_id, response_url)
    elif action == 'save':
        return handle_save_command(parts[1:], notionflow_user, channel_id, user_id, response_url)
    elif action == 'search':
        return handle_search_command(parts[1:], notionflow_user, user_id, response_url)
    elif action == 'status':
        return handle_status_command(notionflow_user, user_id)
    else:
        return jsonify({
            'response_type': 'ephemeral',
            'text': f'Unknown command: `{action}`. Type `/notion help` for available commands.'
        })

def show_help():
    """Show help message for /notion command"""
    help_text = """
*NodeFlow Slack Commands*

• `/notion create [page|database] [title]` - Create a new Notion page or database
• `/notion save [message_link]` - Save a Slack message to Notion
• `/notion search [query]` - Search your Notion pages
• `/notion status` - Check your NodeFlow connection status
• `/notion help` - Show this help message

*Examples:*
• `/notion create page "Meeting Notes"`
• `/notion create database "Project Tasks"`
• `/notion save` (saves current message thread)
• `/notion search "project alpha"`
    """
    
    return jsonify({
        'response_type': 'ephemeral',
        'text': help_text
    })

def handle_create_command(parts, user_id, channel_id, slack_user_id, response_url):
    """Handle creating new Notion content"""
    if len(parts) < 2:
        return jsonify({
            'response_type': 'ephemeral',
            'text': 'Usage: `/notion create [page|database] [title]`'
        })
    
    content_type = parts[0].lower()
    title = parts[1] if len(parts) > 1 else 'Untitled'
    
    if content_type not in ['page', 'database']:
        return jsonify({
            'response_type': 'ephemeral',
            'text': 'Content type must be "page" or "database"'
        })
    
    # Send immediate response
    response = {
        'response_type': 'in_channel',
        'text': f'Creating {content_type}: "{title}"...'
    }
    
    # Process creation asynchronously
    try:
        create_notion_content_async(user_id, content_type, title, channel_id, slack_user_id, response_url)
    except Exception as e:
        print(f"Error creating content: {e}")
        return jsonify({
            'response_type': 'ephemeral',
            'text': f'Error creating {content_type}. Please try again.'
        })
    
    return jsonify(response)

def handle_save_command(parts, user_id, channel_id, slack_user_id, response_url):
    """Handle saving Slack messages to Notion"""
    
    # Send immediate response
    response = {
        'response_type': 'ephemeral',
        'text': 'Saving to Notion...'
    }
    
    # Process saving asynchronously
    try:
        save_slack_content_async(user_id, channel_id, slack_user_id, response_url, parts)
    except Exception as e:
        print(f"Error saving content: {e}")
        return jsonify({
            'response_type': 'ephemeral',
            'text': 'Error saving to Notion. Please try again.'
        })
    
    return jsonify(response)

def handle_search_command(parts, user_id, slack_user_id, response_url):
    """Handle searching Notion content"""
    if not parts:
        return jsonify({
            'response_type': 'ephemeral',
            'text': 'Usage: `/notion search [query]`'
        })
    
    query = ' '.join(parts)
    
    # Send immediate response
    response = {
        'response_type': 'ephemeral',
        'text': f'Searching for: "{query}"...'
    }
    
    # Process search asynchronously
    try:
        search_notion_async(user_id, query, slack_user_id, response_url)
    except Exception as e:
        print(f"Error searching: {e}")
        return jsonify({
            'response_type': 'ephemeral',
            'text': 'Error searching Notion. Please try again.'
        })
    
    return jsonify(response)

def handle_status_command(user_id, slack_user_id):
    """Handle status check command"""
    try:
        if not supabase:
            return {
                'text': 'Status: Service temporarily unavailable',
                'response_type': 'ephemeral'
            }
        # Check Notion connection
        notion_connection = supabase.table('platform_connections').select('*').eq('user_id', user_id).eq('platform', 'notion').execute()
        slack_connection = supabase.table('platform_connections').select('*').eq('user_id', user_id).eq('platform', 'slack').execute()
        
        notion_status = "✅ Connected" if notion_connection.data else "❌ Not connected"
        slack_status = "✅ Connected" if slack_connection.data else "❌ Not connected"
        
        # Get recent sync info
        recent_syncs = supabase.table('sync_jobs').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(3).execute()
        
        sync_info = ""
        if recent_syncs.data:
            sync_info = "\n\n*Recent Syncs:*\n"
            for sync in recent_syncs.data[:3]:
                status_emoji = "✅" if sync['status'] == 'completed' else "⏳" if sync['status'] == 'running' else "❌"
                sync_info += f"• {status_emoji} {sync['platform'].title()} - {sync['created_at'][:10]}\n"
        
        status_text = f"""
*NodeFlow Connection Status*

Notion: {notion_status}
Slack: {slack_status}
{sync_info}
        """
        
        return jsonify({
            'response_type': 'ephemeral',
            'text': status_text
        })
        
    except Exception as e:
        print(f"Error getting status: {e}")
        return jsonify({
            'response_type': 'ephemeral',
            'text': 'Error checking status. Please try again.'
        })

def create_notion_content_async(user_id, content_type, title, channel_id, slack_user_id, response_url):
    """Asynchronously create Notion content and send response"""
    try:
        if not supabase:
            send_delayed_response(response_url, 'Service temporarily unavailable')
            return
        # Get Notion connection
        notion_connection = supabase.table('platform_connections').select('*').eq('user_id', user_id).eq('platform', 'notion').execute()
        
        if not notion_connection.data:
            send_delayed_response(response_url, {
                'response_type': 'ephemeral',
                'text': 'Notion not connected. Please connect Notion in your NodeFlow dashboard.'
            })
            return
        
        # Create NotionProvider instance
        notion = NotionProvider(notion_connection.data[0]['access_token'])
        
        if content_type == 'page':
            # Create a new page
            result = notion.create_page({
                'title': title,
                'content': f'Created from Slack via /notion command\nChannel: #{channel_id}\nCreated by: <@{slack_user_id}>',
                'created_from': 'slack_command'
            })
        else:  # database
            # Create a new database
            result = notion.create_database({
                'title': title,
                'properties': {
                    'Name': {'title': {}},
                    'Status': {'select': {'options': [{'name': 'Not started'}, {'name': 'In progress'}, {'name': 'Done'}]}},
                    'Created': {'created_time': {}},
                    'From Slack': {'checkbox': {}}
                },
                'created_from': 'slack_command'
            })
        
        if result.get('success'):
            url = result.get('url', '#')
            send_delayed_response(response_url, {
                'response_type': 'in_channel',
                'text': f'✅ {content_type.title()} "{title}" created successfully!',
                'attachments': [{
                    'color': 'good',
                    'fields': [{
                        'title': f'View {content_type.title()}',
                        'value': f'<{url}|Open in Notion>',
                        'short': False
                    }]
                }]
            })
        else:
            send_delayed_response(response_url, {
                'response_type': 'ephemeral',
                'text': f'❌ Failed to create {content_type}: {result.get("error", "Unknown error")}'
            })
            
    except Exception as e:
        print(f"Error in create_notion_content_async: {e}")
        send_delayed_response(response_url, {
            'response_type': 'ephemeral',
            'text': f'❌ Error creating {content_type}. Please try again.'
        })

def save_slack_content_async(user_id, channel_id, slack_user_id, response_url, parts):
    """Asynchronously save Slack content to Notion"""
    try:
        # Get both Notion and Slack connections
        notion_connection = supabase.table('platform_connections').select('*').eq('user_id', user_id).eq('platform', 'notion').execute()
        slack_connection = supabase.table('platform_connections').select('*').eq('user_id', user_id).eq('platform', 'slack').execute()
        
        if not notion_connection.data or not slack_connection.data:
            send_delayed_response(response_url, {
                'response_type': 'ephemeral',
                'text': 'Both Notion and Slack must be connected to save content.'
            })
            return
        
        # Create provider instances
        notion = NotionProvider(notion_connection.data[0]['access_token'])
        slack = SlackProvider(slack_connection.data[0]['access_token'])
        
        # If message link provided, parse it; otherwise get recent messages from channel
        if parts and parts[0].startswith('https://'):
            # Parse message link to get channel and timestamp
            # This is a simplified version - you might want to use Slack's permalink format
            message_data = {'text': 'Message saved from link', 'user': slack_user_id}
        else:
            # Get recent messages from current channel
            messages = slack.get_messages(channel_id, limit=1)
            if not messages:
                send_delayed_response(response_url, {
                    'response_type': 'ephemeral',
                    'text': 'No messages found to save.'
                })
                return
            message_data = messages[0]
        
        # Create Notion page from Slack message
        result = notion.create_page({
            'title': f'Slack Message - {datetime.now().strftime("%Y-%m-%d %H:%M")}',
            'content': f"""**Message:** {message_data.get('text', 'No content')}
**From:** <@{message_data.get('user', 'Unknown')}>
**Channel:** #{channel_id}
**Saved by:** <@{slack_user_id}>
**Timestamp:** {message_data.get('ts', 'Unknown')}""",
            'source': 'slack_message',
            'slack_data': message_data
        })
        
        if result.get('success'):
            url = result.get('url', '#')
            send_delayed_response(response_url, {
                'response_type': 'in_channel',
                'text': '✅ Message saved to Notion!',
                'attachments': [{
                    'color': 'good',
                    'fields': [{
                        'title': 'View in Notion',
                        'value': f'<{url}|Open Page>',
                        'short': False
                    }]
                }]
            })
        else:
            send_delayed_response(response_url, {
                'response_type': 'ephemeral',
                'text': f'❌ Failed to save message: {result.get("error", "Unknown error")}'
            })
            
    except Exception as e:
        print(f"Error in save_slack_content_async: {e}")
        send_delayed_response(response_url, {
            'response_type': 'ephemeral',
            'text': '❌ Error saving message. Please try again.'
        })

def search_notion_async(user_id, query, slack_user_id, response_url):
    """Asynchronously search Notion and send results"""
    try:
        # Get Notion connection
        notion_connection = supabase.table('platform_connections').select('*').eq('user_id', user_id).eq('platform', 'notion').execute()
        
        if not notion_connection.data:
            send_delayed_response(response_url, {
                'response_type': 'ephemeral',
                'text': 'Notion not connected. Please connect Notion in your NodeFlow dashboard.'
            })
            return
        
        # Create NotionProvider instance
        notion = NotionProvider(notion_connection.data[0]['access_token'])
        
        # Search Notion
        results = notion.search(query, limit=5)
        
        if results and len(results) > 0:
            attachments = []
            for result in results[:5]:  # Limit to 5 results
                attachments.append({
                    'color': 'good',
                    'title': result.get('title', 'Untitled'),
                    'title_link': result.get('url', '#'),
                    'text': result.get('excerpt', 'No preview available'),
                    'footer': f"Type: {result.get('type', 'page').title()}",
                    'ts': int(datetime.now().timestamp())
                })
            
            send_delayed_response(response_url, {
                'response_type': 'ephemeral',
                'text': f'🔍 Found {len(results)} result(s) for "{query}":',
                'attachments': attachments
            })
        else:
            send_delayed_response(response_url, {
                'response_type': 'ephemeral',
                'text': f'🔍 No results found for "{query}"'
            })
            
    except Exception as e:
        print(f"Error in search_notion_async: {e}")
        send_delayed_response(response_url, {
            'response_type': 'ephemeral',
            'text': '❌ Error searching Notion. Please try again.'
        })

def send_delayed_response(response_url, message):
    """Send a delayed response to Slack"""
    try:
        requests.post(response_url, json=message, timeout=10)
    except Exception as e:
        print(f"Error sending delayed response: {e}")

# Interactive component handlers
@slash_commands_bp.route('/interactive', methods=['POST'])
def handle_interactive():
    """Handle interactive components (buttons, modals, etc.)"""
    
    # Check if Supabase is available
    if not supabase:
        return jsonify({'text': 'Service temporarily unavailable'}), 503
    
    payload = json.loads(request.form.get('payload', '{}'))
    
    if payload.get('type') == 'block_actions':
        return handle_block_actions(payload)
    elif payload.get('type') == 'view_submission':
        return handle_modal_submission(payload)
    elif payload.get('type') == 'view_closed':
        return handle_modal_closed(payload)
    
    return jsonify({'response_action': 'clear'})

def handle_block_actions(payload):
    """Handle button clicks and other block actions"""
    actions = payload.get('actions', [])
    
    for action in actions:
        action_id = action.get('action_id')
        
        if action_id == 'create_notion_page':
            # Handle create page button
            return trigger_page_creation_modal(payload)
        elif action_id == 'save_to_notion':
            # Handle save to notion button
            return trigger_save_action(payload)
    
    return jsonify({'response_action': 'clear'})

def handle_modal_submission(payload):
    """Handle modal form submissions"""
    view = payload.get('view', {})
    callback_id = view.get('callback_id')
    
    if callback_id == 'create_page_modal':
        return process_page_creation(payload)
    elif callback_id == 'save_content_modal':
        return process_content_save(payload)
    
    return jsonify({'response_action': 'clear'})

def handle_modal_closed(payload):
    """Handle modal close events"""
    return jsonify({'response_action': 'clear'})