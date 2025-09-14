"""
🔗 Embedded OAuth Flow
Seamless OAuth integration for dashboard one-click connections
"""

import os
import uuid
import requests
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, redirect, session, render_template_string, url_for
from .base_oauth import register_oauth_service

# Environment configuration
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
MICROSOFT_CLIENT_ID = os.getenv('MICROSOFT_CLIENT_ID') 
MICROSOFT_CLIENT_SECRET = os.getenv('MICROSOFT_CLIENT_SECRET')

embedded_oauth_bp = Blueprint('embedded_oauth', __name__, url_prefix='/oauth/embedded')

# OAuth session storage
oauth_sessions = {}

@embedded_oauth_bp.route('/google/start', methods=['POST'])
def start_google_embedded():
    """Start embedded Google OAuth flow"""
    try:
        data = request.get_json() or {}
        user_id = data.get('user_id')
        session_id = str(uuid.uuid4())
        
        if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
            return jsonify({
                'success': False,
                'error': 'Google OAuth not configured'
            }), 500
        
        # Store session data
        oauth_sessions[session_id] = {
            'platform': 'google',
            'user_id': user_id,
            'created_at': datetime.utcnow().isoformat(),
            'status': 'started'
        }
        
        # Generate OAuth URL
        redirect_uri = url_for('embedded_oauth.google_embedded_callback', _external=True)
        
        auth_url = (
            f"https://accounts.google.com/o/oauth2/auth?"
            f"client_id={GOOGLE_CLIENT_ID}&"
            f"redirect_uri={redirect_uri}&"
            f"scope=email profile https://www.googleapis.com/auth/calendar&"
            f"response_type=code&"
            f"state={session_id}&"
            f"access_type=offline&"
            f"prompt=consent"
        )
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'auth_url': auth_url,
            'embedded_url': f'/oauth/embedded/google/popup?session={session_id}',
            'expires_in': 600  # 10 minutes
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to start Google OAuth: {str(e)}'
        }), 500

@embedded_oauth_bp.route('/google/popup')
def google_oauth_popup():
    """Display Google OAuth in popup window"""
    session_id = request.args.get('session')
    if not session_id or session_id not in oauth_sessions:
        return "Invalid OAuth session", 400
    
    session_data = oauth_sessions[session_id]
    redirect_uri = url_for('embedded_oauth.google_embedded_callback', _external=True)
    
    auth_url = (
        f"https://accounts.google.com/o/oauth2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={redirect_uri}&"
        f"scope=email profile https://www.googleapis.com/auth/calendar&"
        f"response_type=code&"
        f"state={session_id}&"
        f"access_type=offline&"
        f"prompt=consent"
    )
    
    # Redirect to Google OAuth
    return redirect(auth_url)

@embedded_oauth_bp.route('/google/callback')
def google_embedded_callback():
    """Handle Google OAuth callback for embedded flow"""
    try:
        code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')
        
        if error:
            return render_oauth_result('error', f'OAuth error: {error}', state)
        
        if not code or not state or state not in oauth_sessions:
            return render_oauth_result('error', 'Invalid OAuth callback', state)
        
        session_data = oauth_sessions[state]
        session_data['status'] = 'processing'
        
        # Exchange code for tokens
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            'client_id': GOOGLE_CLIENT_ID,
            'client_secret': GOOGLE_CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': url_for('embedded_oauth.google_embedded_callback', _external=True)
        }
        
        token_response = requests.post(token_url, data=token_data)
        
        if not token_response.ok:
            return render_oauth_result('error', 'Failed to exchange code for tokens', state)
        
        tokens = token_response.json()
        
        # Get user info
        user_info_response = requests.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f"Bearer {tokens['access_token']}"}
        )
        
        if not user_info_response.ok:
            return render_oauth_result('error', 'Failed to get user info', state)
        
        user_info = user_info_response.json()
        
        # Store successful result
        session_data.update({
            'status': 'completed',
            'tokens': tokens,
            'user_info': user_info,
            'completed_at': datetime.utcnow().isoformat()
        })
        
        # Save to auto-connect system
        from routes.auto_connect_routes import save_platform_credentials
        
        credentials = {
            'access_token': tokens['access_token'],
            'refresh_token': tokens.get('refresh_token'),
            'client_id': GOOGLE_CLIENT_ID,
            'client_secret': GOOGLE_CLIENT_SECRET,
            'setup_type': 'embedded_oauth',
            'account_email': user_info['email'],
            'account_name': user_info['name']
        }
        
        save_result = save_platform_credentials(session_data['user_id'], 'google', credentials)
        
        # ALSO save OAuth tokens to oauth_tokens table for GoogleCalendarService
        try:
            import os
            SUPABASE_URL = os.getenv('SUPABASE_URL')
            SUPABASE_API_KEY = os.getenv('SUPABASE_API_KEY')
            
            if SUPABASE_URL and SUPABASE_API_KEY:
                headers = {
                    "apikey": SUPABASE_API_KEY,
                    "Authorization": f"Bearer {SUPABASE_API_KEY}",
                    "Content-Type": "application/json",
                    "Prefer": "return=representation,resolution=merge-duplicates"
                }
                
                # Calculate expiry time
                expires_at = None
                if tokens.get('expires_in'):
                    expires_at = (datetime.utcnow() + timedelta(seconds=tokens['expires_in'])).isoformat()
                
                oauth_token_data = {
                    "user_id": session_data['user_id'],
                    "platform": "google",
                    "access_token": tokens['access_token'],
                    "refresh_token": tokens.get('refresh_token'),
                    "token_type": tokens.get('token_type', 'Bearer'),
                    "expires_at": expires_at,
                    "scope": "email profile https://www.googleapis.com/auth/calendar",
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
                
                oauth_resp = requests.post(
                    f"{SUPABASE_URL}/rest/v1/oauth_tokens",
                    headers=headers,
                    json=oauth_token_data
                )
                
                if oauth_resp.ok:
                    print(f"OAuth tokens saved successfully for user {session_data['user_id']}")
                    
                    # Trigger auto-import after successful token save
                    try:
                        import threading
                        import sys
                        import os
                        
                        def auto_import_async():
                            try:
                                # Import Google Calendar service
                                sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend'))
                                from services.google_calendar_service import GoogleCalendarService
                                
                                # Get Supabase client
                                SUPABASE_URL = os.getenv('SUPABASE_URL')
                                SUPABASE_API_KEY = os.getenv('SUPABASE_API_KEY')
                                if not SUPABASE_URL or not SUPABASE_API_KEY:
                                    print("Database credentials not available for auto-import")
                                    return
                                
                                from supabase import create_client
                                supabase_client = create_client(SUPABASE_URL, SUPABASE_API_KEY)
                                
                                user_id = session_data['user_id']
                                
                                # Check/create default calendar
                                user_calendars = supabase_client.table('calendars').select('*').eq('owner_id', user_id).execute()
                                
                                if not user_calendars.data:
                                    new_calendar = {
                                        'owner_id': user_id,
                                        'name': 'My Calendar',
                                        'description': 'Default calendar for imported events',
                                        'color': '#4285F4',
                                        'platform': 'custom',
                                        'is_shared': False,
                                        'is_enabled': True,
                                        'created_at': datetime.utcnow().isoformat(),
                                        'updated_at': datetime.utcnow().isoformat()
                                    }
                                    create_result = supabase_client.table('calendars').insert(new_calendar).execute()
                                    calendar_data = create_result.data[0] if create_result.data else None
                                else:
                                    calendar_data = user_calendars.data[0]
                                
                                if not calendar_data:
                                    print("Failed to get/create calendar for auto-import")
                                    return
                                
                                calendar_id = calendar_data.get('id')
                                print(f"Starting embedded auto-import for user {user_id}, calendar {calendar_id}")
                                
                                # Import Google Calendar events
                                google_service = GoogleCalendarService()
                                google_events = google_service.get_events(user_id, calendar_id='primary')
                                
                                if not google_events:
                                    print(f"No Google events found for user {user_id}")
                                    return
                                
                                # Import events to NotionFlow calendar
                                imported_count = 0
                                for event in google_events:
                                    try:
                                        start_datetime = event.get('start', {})
                                        end_datetime = event.get('end', {})
                                        
                                        start_time = start_datetime.get('dateTime') or start_datetime.get('date')
                                        end_time = end_datetime.get('dateTime') or end_datetime.get('date')
                                        
                                        if not start_time:
                                            continue
                                        
                                        event_data = {
                                            'user_id': user_id,
                                            'calendar_id': calendar_id,
                                            'title': event.get('summary', 'Untitled Event'),
                                            'description': event.get('description', ''),
                                            'location': event.get('location', ''),
                                            'platform': 'google',
                                            'external_event_id': event.get('id'),
                                            'html_link': event.get('htmlLink', ''),
                                            'sync_status': 'synced',
                                            'last_synced_at': datetime.utcnow().isoformat(),
                                            'status': event.get('status', 'confirmed')
                                        }
                                        
                                        if 'date' in start_datetime:
                                            event_data.update({
                                                'start_date': start_time,
                                                'end_date': end_time or start_time,
                                                'is_all_day': True
                                            })
                                        else:
                                            event_data.update({
                                                'start_datetime': start_time,
                                                'end_datetime': end_time or start_time,
                                                'is_all_day': False
                                            })
                                        
                                        # Check if event already exists
                                        existing = supabase_client.table('calendar_events').select('id').eq('user_id', user_id).eq('external_event_id', event.get('id')).execute()
                                        
                                        if not existing.data:
                                            result = supabase_client.table('calendar_events').insert(event_data).execute()
                                            if result.data:
                                                imported_count += 1
                                        
                                    except Exception as e:
                                        print(f"Failed to import single event in embedded flow: {str(e)}")
                                
                                print(f"Embedded auto-import completed: {imported_count} events imported for user {user_id}")
                                
                            except Exception as e:
                                print(f"Embedded auto-import thread error: {str(e)}")
                        
                        # Run auto-import in background thread
                        thread = threading.Thread(target=auto_import_async)
                        thread.daemon = True
                        thread.start()
                        
                    except Exception as e:
                        print(f"Failed to start embedded auto-import thread: {str(e)}")
                    
                else:
                    print(f"Failed to save OAuth tokens: {oauth_resp.text}")
        except Exception as e:
            print(f"Error saving OAuth tokens in embedded flow: {str(e)}")
        
        return render_oauth_result('success', 'Google Calendar connected successfully!', state, {
            'user_info': user_info,
            'credentials_saved': save_result['success']
        })
        
    except Exception as e:
        return render_oauth_result('error', f'OAuth callback failed: {str(e)}', state)

@embedded_oauth_bp.route('/microsoft/start', methods=['POST'])
def start_microsoft_embedded():
    """Start embedded Microsoft OAuth flow"""
    try:
        data = request.get_json() or {}
        user_id = data.get('user_id')
        session_id = str(uuid.uuid4())
        
        if not MICROSOFT_CLIENT_ID or not MICROSOFT_CLIENT_SECRET:
            return jsonify({
                'success': False,
                'error': 'Microsoft OAuth not configured'
            }), 500
        
        # Store session data
        oauth_sessions[session_id] = {
            'platform': 'microsoft',
            'user_id': user_id,
            'created_at': datetime.utcnow().isoformat(),
            'status': 'started'
        }
        
        # Generate OAuth URL
        redirect_uri = url_for('embedded_oauth.microsoft_embedded_callback', _external=True)
        
        auth_url = (
            f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?"
            f"client_id={MICROSOFT_CLIENT_ID}&"
            f"redirect_uri={redirect_uri}&"
            f"scope=User.Read Calendars.ReadWrite&"
            f"response_type=code&"
            f"state={session_id}&"
            f"response_mode=query"
        )
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'auth_url': auth_url,
            'embedded_url': f'/oauth/embedded/microsoft/popup?session={session_id}',
            'expires_in': 600  # 10 minutes
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to start Microsoft OAuth: {str(e)}'
        }), 500

@embedded_oauth_bp.route('/microsoft/popup')
def microsoft_oauth_popup():
    """Display Microsoft OAuth in popup window"""
    session_id = request.args.get('session')
    if not session_id or session_id not in oauth_sessions:
        return "Invalid OAuth session", 400
    
    session_data = oauth_sessions[session_id]
    redirect_uri = url_for('embedded_oauth.microsoft_embedded_callback', _external=True)
    
    auth_url = (
        f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?"
        f"client_id={MICROSOFT_CLIENT_ID}&"
        f"redirect_uri={redirect_uri}&"
        f"scope=User.Read Calendars.ReadWrite&"
        f"response_type=code&"
        f"state={session_id}&"
        f"response_mode=query"
    )
    
    # Redirect to Microsoft OAuth
    return redirect(auth_url)

@embedded_oauth_bp.route('/microsoft/callback')
def microsoft_embedded_callback():
    """Handle Microsoft OAuth callback for embedded flow"""
    try:
        code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')
        
        if error:
            return render_oauth_result('error', f'OAuth error: {error}', state)
        
        if not code or not state or state not in oauth_sessions:
            return render_oauth_result('error', 'Invalid OAuth callback', state)
        
        session_data = oauth_sessions[state]
        session_data['status'] = 'processing'
        
        # Exchange code for tokens
        token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        token_data = {
            'client_id': MICROSOFT_CLIENT_ID,
            'client_secret': MICROSOFT_CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': url_for('embedded_oauth.microsoft_embedded_callback', _external=True)
        }
        
        token_response = requests.post(token_url, data=token_data)
        
        if not token_response.ok:
            return render_oauth_result('error', 'Failed to exchange code for tokens', state)
        
        tokens = token_response.json()
        
        # Get user info
        user_info_response = requests.get(
            'https://graph.microsoft.com/v1.0/me',
            headers={'Authorization': f"Bearer {tokens['access_token']}"}
        )
        
        if not user_info_response.ok:
            return render_oauth_result('error', 'Failed to get user info', state)
        
        user_info = user_info_response.json()
        
        # Store successful result
        session_data.update({
            'status': 'completed',
            'tokens': tokens,
            'user_info': user_info,
            'completed_at': datetime.utcnow().isoformat()
        })
        
        # Save to auto-connect system
        from routes.auto_connect_routes import save_platform_credentials
        
        credentials = {
            'access_token': tokens['access_token'],
            'refresh_token': tokens.get('refresh_token'),
            'client_id': MICROSOFT_CLIENT_ID,
            'client_secret': MICROSOFT_CLIENT_SECRET,
            'setup_type': 'embedded_oauth',
            'account_email': user_info['mail'] or user_info['userPrincipalName'],
            'account_name': user_info['displayName']
        }
        
        save_result = save_platform_credentials(session_data['user_id'], 'outlook', credentials)
        
        return render_oauth_result('success', 'Microsoft Outlook connected successfully!', state, {
            'user_info': user_info,
            'credentials_saved': save_result['success']
        })
        
    except Exception as e:
        return render_oauth_result('error', f'OAuth callback failed: {str(e)}', state)

@embedded_oauth_bp.route('/status/<session_id>')
def get_oauth_status(session_id):
    """Get OAuth session status for polling"""
    if session_id not in oauth_sessions:
        return jsonify({
            'success': False,
            'error': 'Session not found'
        }), 404
    
    session_data = oauth_sessions[session_id]
    
    # Clean up old sessions
    created_at = datetime.fromisoformat(session_data['created_at'])
    if datetime.utcnow() - created_at > timedelta(minutes=15):
        del oauth_sessions[session_id]
        return jsonify({
            'success': False,
            'error': 'Session expired'
        }), 410
    
    return jsonify({
        'success': True,
        'status': session_data['status'],
        'platform': session_data['platform'],
        'created_at': session_data['created_at'],
        'completed': session_data['status'] == 'completed',
        'user_info': session_data.get('user_info', {}),
        'error': session_data.get('error')
    })

def render_oauth_result(status, message, session_id, data=None):
    """Render OAuth result page that communicates with parent window"""
    template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>OAuth Result</title>
        <meta charset="UTF-8">
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
                background: linear-gradient(135deg, #0000 0%, #764ba2 100%);
                color: white;
            }
            .result-container {
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border-radius: 16px;
                padding: 2rem;
                text-align: center;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            }
            .icon {
                font-size: 3rem;
                margin-bottom: 1rem;
            }
            .message {
                font-size: 1.2rem;
                margin-bottom: 1rem;
            }
            .closing-message {
                font-size: 0.9rem;
                opacity: 0.8;
            }
        </style>
    </head>
    <body>
        <div class="result-container">
            <div class="icon">{{ icon }}</div>
            <div class="message">{{ message }}</div>
            <div class="closing-message">This window will close automatically...</div>
        </div>
        
        <script>
            // Send result to parent window
            const result = {
                status: '{{ status }}',
                message: '{{ message }}',
                session_id: '{{ session_id }}',
                data: {{ data | tojson }}
            };
            
            if (window.opener) {
                window.opener.postMessage({
                    type: 'oauth_result',
                    result: result
                }, '*');
            }
            
            // Close window after a short delay
            setTimeout(() => {
                window.close();
            }, 2000);
        </script>
    </body>
    </html>
    """
    
    icon = '✅' if status == 'success' else '❌'
    
    return render_template_string(
        template, 
        status=status, 
        message=message, 
        session_id=session_id or '', 
        data=data or {},
        icon=icon
    )

def cleanup_expired_sessions():
    """Clean up expired OAuth sessions"""
    now = datetime.utcnow()
    expired_sessions = []
    
    for session_id, session_data in oauth_sessions.items():
        created_at = datetime.fromisoformat(session_data['created_at'])
        if now - created_at > timedelta(minutes=15):
            expired_sessions.append(session_id)
    
    for session_id in expired_sessions:
        del oauth_sessions[session_id]

# Register cleanup function to run periodically
import atexit
atexit.register(cleanup_expired_sessions)