from flask import Blueprint, redirect, request, session, jsonify, url_for
import os
import secrets
import base64
import hashlib
import requests
import sys
import jwt
import time
import json
from datetime import datetime, timedelta
from urllib.parse import urlencode
from supabase import create_client
from dotenv import load_dotenv

# Add parent directory to path for backend services
sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend'))
from services.sync_tracking_service import sync_tracker, EventType, ActivityType

# Load environment variables
load_dotenv()

oauth_bp = Blueprint('oauth', __name__, url_prefix='/oauth')

# Supabase setup
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_API_KEY')

if not SUPABASE_URL:
    raise Exception("SUPABASE_URL environment variable is required")
if not SUPABASE_KEY:
    raise Exception("SUPABASE_API_KEY environment variable is required")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# OAuth Configuration
OAUTH_CONFIG = {
    'google': {
        'client_id': os.environ.get('GOOGLE_CLIENT_ID'),
        'client_secret': os.environ.get('GOOGLE_CLIENT_SECRET'),
        'authorize_url': 'https://accounts.google.com/o/oauth2/auth',
        'token_url': 'https://oauth2.googleapis.com/token',
        'scope': 'https://www.googleapis.com/auth/calendar openid email profile',
        'user_info_url': 'https://www.googleapis.com/oauth2/v2/userinfo'
    },
    'notion': {
        'client_id': os.environ.get('NOTION_CLIENT_ID'),
        'client_secret': os.environ.get('NOTION_CLIENT_SECRET'),
        'authorize_url': 'https://api.notion.com/v1/oauth/authorize',
        'token_url': 'https://api.notion.com/v1/oauth/token',
        'scope': '',
        'user_info_url': 'https://api.notion.com/v1/users/me'
    },
    'slack': {
        'client_id': os.environ.get('SLACK_CLIENT_ID'),
        'client_secret': os.environ.get('SLACK_CLIENT_SECRET'),
        'authorize_url': 'https://slack.com/oauth/v2/authorize',
        'token_url': 'https://slack.com/api/oauth.v2.access',
        'scope': 'channels:read,channels:write,chat:write,users:read,team:read',
        'user_scope': 'channels:read,channels:write,chat:write'
    },
    'outlook': {
        'client_id': os.environ.get('MICROSOFT_CLIENT_ID') or os.environ.get('OUTLOOK_CLIENT_ID'),
        'client_secret': os.environ.get('MICROSOFT_CLIENT_SECRET') or os.environ.get('OUTLOOK_CLIENT_SECRET'),
        'tenant_id': os.environ.get('MICROSOFT_TENANT_ID') or os.environ.get('OUTLOOK_TENANT_ID', 'common'),
        'authorize_url': 'https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize',
        'token_url': 'https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token',
        'scope': 'https://graph.microsoft.com/Calendars.ReadWrite offline_access',
        'user_info_url': 'https://graph.microsoft.com/v1.0/me'
    },
    'apple': {
        'client_id': os.environ.get('APPLE_CLIENT_ID'),
        'client_secret': None,  # Apple uses private key JWT
        'team_id': os.environ.get('APPLE_TEAM_ID'),
        'key_id': os.environ.get('APPLE_KEY_ID'),
        'private_key': os.environ.get('APPLE_PRIVATE_KEY'),
        'authorize_url': 'https://appleid.apple.com/auth/authorize',
        'token_url': 'https://appleid.apple.com/auth/token',
        'scope': 'name email',
        'user_info_url': None  # Apple doesn't provide user info endpoint
    }
}

def generate_pkce_codes():
    """Generate PKCE code verifier and challenge for OAuth 2.0"""
    code_verifier = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8').rstrip('=')
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('utf-8')).digest()
    ).decode('utf-8').rstrip('=')
    return code_verifier, code_challenge

def generate_apple_client_secret():
    """Generate Apple Sign In client secret using JWT"""
    try:
        config = OAUTH_CONFIG['apple']
        team_id = config.get('team_id')
        key_id = config.get('key_id')
        client_id = config.get('client_id')
        private_key = config.get('private_key')
        
        if not all([team_id, key_id, client_id, private_key]):
            print("Missing Apple OAuth configuration")
            return None
        
        # Clean private key format
        if '\\n' in private_key:
            private_key = private_key.replace('\\n', '\n')
        
        # JWT headers
        headers = {
            'kid': key_id,
            'alg': 'ES256'
        }
        
        # JWT payload
        now = int(time.time())
        payload = {
            'iss': team_id,
            'iat': now,
            'exp': now + 3600,  # 1 hour expiration
            'aud': 'https://appleid.apple.com',
            'sub': client_id
        }
        
        # Generate JWT
        client_secret = jwt.encode(payload, private_key, algorithm='ES256', headers=headers)
        return client_secret
        
    except Exception as e:
        print(f"Error generating Apple client secret: {e}")
        return None

def store_oauth_state(user_id, provider, state, code_verifier=None):
    """Store OAuth state - always use session for simplicity"""
    try:
        # Always use session storage for reliability
        session[f'oauth_state_{state}'] = {
            'user_id': user_id,
            'provider': provider,
            'code_verifier': code_verifier,
            'created_at': datetime.utcnow().isoformat()
        }
        print(f"OAuth state stored in session for {provider}: {state[:8]}...")
        return True
            
    except Exception as e:
        print(f"Error storing OAuth state for {provider}: {e}")
        print(f"User ID: {user_id}, Provider: {provider}")
        print(f"Session keys: {list(session.keys())}")
        return False

def verify_oauth_state(state, provider):
    """Verify OAuth state from session"""
    try:
        # Only use session for simplicity
        session_key = f'oauth_state_{state}'
        if session_key in session:
            state_data = session[session_key]
            if state_data['provider'] == provider:
                # Check if not expired (10 minute timeout)
                created_at = datetime.fromisoformat(state_data['created_at'])
                if datetime.utcnow() - created_at < timedelta(minutes=10):
                    # Clean up after use
                    del session[session_key]
                    return state_data
                else:
                    # Clean up expired session state
                    del session[session_key]
        
        print(f"OAuth state not found for {provider}: {state[:8]}...")
        return None
    except Exception as e:
        print(f"Error verifying OAuth state: {e}")
        return None

def get_user_info_from_provider(platform, access_token):
    """Get user information from OAuth provider"""
    try:
        config = OAUTH_CONFIG[platform]
        headers = {'Authorization': f'Bearer {access_token}'}
        
        if platform == 'notion':
            headers['Notion-Version'] = '2022-06-28'
        
        user_info_url = config.get('user_info_url')
        if not user_info_url:
            return None
            
        response = requests.get(user_info_url, headers=headers)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error getting user info from {platform}: {e}")
        return None

def store_platform_registration(user_id, platform, token_data, user_info=None):
    """Store platform registration in registered_platforms table"""
    try:
        # Get user info if not provided
        if not user_info and token_data.get('access_token'):
            user_info = get_user_info_from_provider(platform, token_data['access_token'])
        
        # Calculate token expiration
        expires_at = None
        if token_data.get('expires_in'):
            expires_at = (datetime.utcnow() + timedelta(seconds=int(token_data['expires_in']))).isoformat()
        
        # Prepare registration data
        registration_data = {
            'user_id': user_id,
            'platform': platform,
            'platform_name': platform.title(),
            'encrypted_credentials': json.dumps({
                'access_token': token_data.get('access_token'),
                'refresh_token': token_data.get('refresh_token'),
                'token_type': token_data.get('token_type', 'Bearer'),
                'scope': token_data.get('scope'),
                'expires_at': expires_at
            }),
            'platform_user_id': get_platform_user_id(platform, user_info) if user_info else None,
            'platform_user_email': get_platform_user_email(platform, user_info) if user_info else None,
            'platform_user_name': get_platform_user_name(platform, user_info) if user_info else None,
            'is_active': True,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'expires_at': expires_at
        }
        
        # Upsert registration
        result = supabase.table('registered_platforms').upsert(
            registration_data,
            on_conflict='user_id,platform'
        ).execute()
        
        return bool(result.data)
    except Exception as e:
        print(f"Error storing platform registration: {e}")
        return False

def get_platform_user_id(platform, user_info):
    """Extract user ID from platform-specific user info"""
    if not user_info:
        return None
    if platform == 'google':
        return user_info.get('id')
    elif platform == 'notion':
        return user_info.get('id')
    elif platform == 'slack':
        return user_info.get('authed_user', {}).get('id')
    elif platform == 'outlook':
        return user_info.get('id')
    elif platform == 'apple':
        return user_info.get('sub')  # Apple uses 'sub' field
    return None

def get_platform_user_email(platform, user_info):
    """Extract user email from platform-specific user info"""
    if not user_info:
        return None
    if platform == 'google':
        return user_info.get('email')
    elif platform == 'notion':
        person = user_info.get('person', {})
        return person.get('email') if person else user_info.get('email')
    elif platform == 'slack':
        return user_info.get('authed_user', {}).get('email')
    elif platform == 'outlook':
        return user_info.get('mail') or user_info.get('userPrincipalName')
    elif platform == 'apple':
        return user_info.get('email')
    return None

def get_platform_user_name(platform, user_info):
    """Extract user name from platform-specific user info"""
    if not user_info:
        return None
    if platform == 'google':
        return user_info.get('name')
    elif platform == 'notion':
        return user_info.get('name')
    elif platform == 'slack':
        return user_info.get('authed_user', {}).get('name')
    elif platform == 'outlook':
        return user_info.get('displayName')
    elif platform == 'apple':
        # Apple provides name in a different structure
        name_obj = user_info.get('name', {})
        if isinstance(name_obj, dict):
            first_name = name_obj.get('firstName', '')
            last_name = name_obj.get('lastName', '')
            return f"{first_name} {last_name}".strip() if first_name or last_name else None
        return None
    return None

@oauth_bp.route('/<platform>/authorize')
def generic_oauth_authorize(platform):
    """Generic OAuth authorization for supported platforms"""
    if platform not in OAUTH_CONFIG:
        print(f"Unsupported platform requested: {platform}")
        return jsonify({'error': f'Unsupported platform: {platform}'}), 400
    
    user_id = session.get('user_id')
    if not user_id:
        print(f"OAuth authorization attempt without authentication for {platform}")
        print(f"Session data: {dict(session)}")
        # Try to get user_id from different possible session keys
        user_id = session.get('user') or session.get('user_email') or session.get('email')
        if not user_id:
            return jsonify({'error': 'Not authenticated - Please login first'}), 401
    
    config = OAUTH_CONFIG[platform]
    
    # Check if OAuth is properly configured (skip for Apple which uses JWT)
    if platform != 'apple':
        if not config.get('client_id') or not config.get('client_secret'):
            print(f"OAuth not configured for {platform}")
            print(f"Client ID: {config.get('client_id')[:10]}..." if config.get('client_id') else "Missing")
            print(f"Client Secret: {'Set' if config.get('client_secret') else 'Missing'}")
            error_msg = f'OAuth not configured for {platform}. Client ID: {"Set" if config.get("client_id") else "Missing"}, Secret: {"Set" if config.get("client_secret") else "Missing"}'
            return jsonify({'error': error_msg}), 500
    
    state = secrets.token_urlsafe(32)
    
    # Generate PKCE for platforms that support it
    code_verifier = None
    code_challenge = None
    if platform in ['google', 'notion', 'apple', 'outlook']:
        code_verifier, code_challenge = generate_pkce_codes()
        success = store_oauth_state(user_id, platform, state, code_verifier)
    else:
        success = store_oauth_state(user_id, platform, state)
    
    if not success:
        print(f"Failed to store OAuth state for {platform}")
        return jsonify({'error': 'Failed to initiate OAuth flow - Database connection issue'}), 500
    
    # Build authorization parameters
    params = {
        'client_id': config['client_id'],
        'response_type': 'code',
        'redirect_uri': url_for('oauth.generic_oauth_callback', platform=platform, _external=True),
        'state': state,
        'scope': config['scope']
    }
    
    # Platform-specific parameters
    if platform == 'google':
        params['access_type'] = 'offline'
        params['prompt'] = 'consent'
        if code_verifier:
            params['code_challenge'] = code_challenge
            params['code_challenge_method'] = 'S256'
    elif platform == 'notion':
        params['response_type'] = 'code'
        # Notion doesn't use PKCE in practice, but we'll include it
    elif platform == 'slack':
        params['user_scope'] = config.get('user_scope', '')
    elif platform == 'outlook':
        auth_url = config['authorize_url'].format(tenant=config['tenant_id'])
        params['response_mode'] = 'query'
        if code_verifier:
            params['code_challenge'] = code_challenge
            params['code_challenge_method'] = 'S256'
    elif platform == 'apple':
        params['response_mode'] = 'form_post'
        params['response_type'] = 'code id_token'
        if code_verifier:
            params['code_challenge'] = code_challenge
            params['code_challenge_method'] = 'S256'
    
    # Build final URL
    if platform == 'outlook':
        auth_url = config['authorize_url'].format(tenant=config['tenant_id'])
    else:
        auth_url = config['authorize_url']
    
    final_url = f"{auth_url}?{urlencode(params)}"
    
    # Return popup-friendly HTML
    popup_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Connect {platform.title()}</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif;
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
                margin: 0;
                background: #f9fafb;
                color: #374151;
            }}
            .loading {{
                text-align: center;
                max-width: 400px;
                padding: 40px;
                background: white;
                border-radius: 12px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }}
            .spinner {{
                width: 40px;
                height: 40px;
                border: 3px solid #e5e7eb;
                border-top: 3px solid #3b82f6;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 0 auto 20px;
            }}
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
            .platform-name {{
                font-size: 18px;
                font-weight: 600;
                margin-bottom: 8px;
                color: #111827;
            }}
            .redirect-info {{
                color: #6b7280;
                font-size: 14px;
                margin-bottom: 20px;
            }}
            .manual-link {{
                display: inline-block;
                padding: 10px 20px;
                background: #3b82f6;
                color: white;
                text-decoration: none;
                border-radius: 8px;
                font-weight: 500;
                transition: background 0.2s;
            }}
            .manual-link:hover {{
                background: #2563eb;
            }}
        </style>
        <script>
            // Redirect to OAuth provider
            setTimeout(function() {{
                window.location.href = '{final_url}';
            }}, 1000);
        </script>
    </head>
    <body>
        <div class="loading">
            <div class="spinner"></div>
            <div class="platform-name">Connecting to {platform.title()}</div>
            <div class="redirect-info">Redirecting to {platform.title()} for authorization...</div>
            <a href="{final_url}" class="manual-link">Continue manually if not redirected</a>
        </div>
    </body>
    </html>
    """
    return popup_html

@oauth_bp.route('/<platform>/callback')
def generic_oauth_callback(platform):
    """Generic OAuth callback handler"""
    if platform not in OAUTH_CONFIG:
        return handle_callback_error('Unsupported platform')
    
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')
    
    if error:
        return handle_callback_error(f'OAuth error: {error}')
    
    if not code or not state:
        return handle_callback_error('Missing authorization code or state')
    
    # Verify state
    state_data = verify_oauth_state(state, platform)
    if not state_data:
        return handle_callback_error('Invalid or expired state')
    
    try:
        # Exchange code for tokens
        token_data = exchange_code_for_tokens(platform, code, state_data)
        if not token_data:
            return handle_callback_error('Failed to exchange authorization code for tokens')
        
        # Get user info
        user_info = None
        if platform == 'apple':
            # Apple provides user info in ID token
            id_token = token_data.get('id_token')
            if id_token:
                try:
                    # Decode JWT (Apple ID token is signed, but we can extract payload for basic info)
                    # Note: In production, you should verify the signature
                    import base64
                    payload = id_token.split('.')[1]
                    # Add padding if needed
                    payload += '=' * (4 - len(payload) % 4)
                    decoded = base64.urlsafe_b64decode(payload)
                    user_info = json.loads(decoded.decode('utf-8'))
                except Exception as e:
                    print(f"Error decoding Apple ID token: {e}")
                    user_info = {'sub': 'apple_user', 'email': 'unknown@apple.com'}
        elif token_data.get('access_token'):
            user_info = get_user_info_from_provider(platform, token_data['access_token'])
        
        # Store platform registration
        success = store_platform_registration(state_data['user_id'], platform, token_data, user_info)
        if not success:
            return handle_callback_error('Failed to save platform registration')
        
        # Track the connection event
        sync_tracker.track_sync_event(
            user_id=state_data['user_id'],
            event_type=EventType.PLATFORM_CONNECTED,
            platform=platform,
            status='success',
            metadata={
                'user_email': get_platform_user_email(platform, user_info),
                'user_name': get_platform_user_name(platform, user_info),
                'connection_method': 'oauth'
            }
        )
        
        # Clean up OAuth state
        supabase.table('oauth_states').delete().eq('state', state).execute()
        
        return handle_callback_success(platform, user_info)
        
    except Exception as e:
        print(f"OAuth callback error for {platform}: {e}")
        return handle_callback_error(f'OAuth processing failed: {str(e)}')

def exchange_code_for_tokens(platform, code, state_data):
    """Exchange authorization code for access tokens"""
    config = OAUTH_CONFIG[platform]
    
    # Prepare token request data
    token_data = {
        'client_id': config['client_id'],
        'client_secret': config['client_secret'],
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': url_for('oauth.generic_oauth_callback', platform=platform, _external=True)
    }
    
    # Platform-specific modifications
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    
    if platform == 'google':
        # Google supports PKCE
        if state_data.get('code_verifier'):
            token_data['code_verifier'] = state_data['code_verifier']
    elif platform == 'notion':
        # Notion uses JSON format
        headers = {'Content-Type': 'application/json'}
        token_data = json.dumps(token_data)
    elif platform == 'outlook':
        # Outlook with PKCE
        token_url = config['token_url'].format(tenant=config['tenant_id'])
        if state_data.get('code_verifier'):
            token_data['code_verifier'] = state_data['code_verifier']
        config = {**config, 'token_url': token_url}
    elif platform == 'apple':
        # Apple uses client secret JWT
        client_secret = generate_apple_client_secret()
        if not client_secret:
            return None
        token_data['client_secret'] = client_secret
        if state_data.get('code_verifier'):
            token_data['code_verifier'] = state_data['code_verifier']
    
    # Make token request
    response = requests.post(config['token_url'], data=token_data, headers=headers)
    
    if response.status_code != 200:
        print(f"Token exchange failed for {platform}: {response.status_code} {response.text}")
        return None
    
    result = response.json()
    
    # Check for errors in response
    if platform == 'slack' and not result.get('ok'):
        print(f"Slack token exchange error: {result.get('error')}")
        return None
    elif 'error' in result:
        print(f"Token exchange error for {platform}: {result.get('error')}")
        return None
    
    return result

def handle_callback_success(platform, user_info):
    """Handle successful OAuth callback"""
    user_name = get_platform_user_name(platform, user_info) or get_platform_user_email(platform, user_info) or 'Unknown User'
    
    success_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Connected Successfully</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif;
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
                margin: 0;
                background: #f9fafb;
            }}
            .success {{
                text-align: center;
                background: white;
                padding: 40px;
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.05);
                max-width: 400px;
                width: 90%;
            }}
            .success-icon {{
                width: 64px;
                height: 64px;
                margin: 0 auto 24px;
                background: linear-gradient(135deg, #10b981, #059669);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 28px;
                font-weight: bold;
            }}
            .success-title {{
                margin: 0 0 8px;
                color: #111827;
                font-size: 24px;
                font-weight: 600;
            }}
            .success-subtitle {{
                margin: 0 0 16px;
                color: #6b7280;
                font-size: 16px;
            }}
            .user-info {{
                padding: 16px;
                background: #f3f4f6;
                border-radius: 8px;
                margin: 20px 0;
            }}
            .user-name {{
                font-weight: 600;
                color: #111827;
                font-size: 16px;
                margin: 0;
            }}
            .close-info {{
                margin-top: 24px;
                font-size: 14px;
                color: #6b7280;
                padding: 12px;
                background: #f9fafb;
                border-radius: 6px;
                border: 1px solid #e5e7eb;
            }}
        </style>
        <script>
            // Notify parent window of success
            if (window.opener && !window.opener.closed) {{
                window.opener.postMessage({{
                    type: 'oauth_success',
                    platform: '{platform}',
                    user_info: {json.dumps(user_info) if user_info else 'null'}
                }}, '*');
            }}
            
            // Auto-close after delay
            let countdown = 3;
            const countdownElement = document.getElementById('countdown');
            const timer = setInterval(() => {{
                countdown--;
                if (countdownElement) {{
                    countdownElement.textContent = countdown;
                }}
                if (countdown <= 0) {{
                    clearInterval(timer);
                    window.close();
                }}
            }}, 1000);
        </script>
    </head>
    <body>
        <div class="success">
            <div class="success-icon">✓</div>
            <h1 class="success-title">{platform.title()} Connected!</h1>
            <p class="success-subtitle">Successfully connected your {platform.title()} account.</p>
            <div class="user-info">
                <div class="user-name">{user_name}</div>
            </div>
            <div class="close-info">
                This window will close automatically in <span id="countdown">3</span> seconds.
            </div>
        </div>
    </body>
    </html>
    """
    return success_html

def handle_callback_error(error_message):
    """Handle OAuth callback error"""
    error_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Connection Failed</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif;
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
                margin: 0;
                background: #f9fafb;
            }}
            .error {{
                text-align: center;
                background: white;
                padding: 40px;
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.05);
                max-width: 400px;
                width: 90%;
            }}
            .error-icon {{
                width: 64px;
                height: 64px;
                margin: 0 auto 24px;
                background: linear-gradient(135deg, #ef4444, #dc2626);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 28px;
                font-weight: bold;
            }}
            .error-title {{
                margin: 0 0 8px;
                color: #111827;
                font-size: 24px;
                font-weight: 600;
            }}
            .error-subtitle {{
                margin: 0 0 16px;
                color: #6b7280;
                font-size: 16px;
            }}
            .error-details {{
                margin: 20px 0;
                padding: 16px;
                background: #fef2f2;
                border-radius: 8px;
                font-size: 14px;
                color: #991b1b;
                border: 1px solid #fecaca;
                word-break: break-word;
            }}
            .close-info {{
                margin-top: 24px;
                font-size: 14px;
                color: #6b7280;
            }}
        </style>
        <script>
            // Notify parent window of error
            if (window.opener && !window.opener.closed) {{
                window.opener.postMessage({{
                    type: 'oauth_error',
                    error: '{error_message}'
                }}, '*');
            }}
            
            // Auto-close after delay
            setTimeout(() => {{
                window.close();
            }}, 5000);
        </script>
    </head>
    <body>
        <div class="error">
            <div class="error-icon">✗</div>
            <h1 class="error-title">Connection Failed</h1>
            <p class="error-subtitle">Unable to connect your account.</p>
            <div class="error-details">
                {error_message}
            </div>
            <div class="close-info">
                This window will close automatically in 5 seconds.
            </div>
        </div>
    </body>
    </html>
    """
    return error_html

@oauth_bp.route('/<platform>/check')
def check_oauth_config(platform):
    """Check if OAuth is configured for a platform"""
    if platform not in OAUTH_CONFIG:
        return jsonify({'configured': False, 'error': 'Unsupported platform'})
    
    config = OAUTH_CONFIG[platform]
    
    # Check required configuration
    if platform == 'apple':
        required_fields = ['client_id', 'team_id', 'key_id', 'private_key']
        configured = all(config.get(field) and config[field] != f'your_{platform}_{field}_here' for field in required_fields)
    else:
        required_fields = ['client_id', 'client_secret']
        configured = all(config.get(field) and config[field] != f'your_{platform}_{field}_here' for field in required_fields)
    
    return jsonify({
        'configured': configured,
        'platform': platform,
        'missing_fields': [field for field in required_fields if not config.get(field) or config[field] == f'your_{platform}_{field}_here']
    })

@oauth_bp.route('/slack/authorize')
def slack_authorize():
    """Initiate Slack OAuth flow"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    config = OAUTH_CONFIG['slack']
    state = secrets.token_urlsafe(32)
    
    # Store state for verification
    if not store_oauth_state(user_id, 'slack', state):
        return jsonify({'error': 'Failed to initiate OAuth flow'}), 500
    
    params = {
        'client_id': config['client_id'],
        'scope': config['scope'],
        'user_scope': config['user_scope'],
        'state': state,
        'redirect_uri': url_for('oauth.slack_callback', _external=True)
    }
    
    auth_url = f"{config['authorize_url']}?{urlencode(params)}"
    return redirect(auth_url)

@oauth_bp.route('/slack/callback')
def slack_callback():
    """Handle Slack OAuth callback"""
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')
    
    if error:
        return redirect(f'/setup/slack?error={error}')
    
    if not code or not state:
        return redirect('/setup/slack?error=missing_params')
    
    # Verify state
    state_data = verify_oauth_state(state, 'slack')
    if not state_data:
        return redirect('/setup/slack?error=invalid_state')
    
    config = OAUTH_CONFIG['slack']
    
    # Exchange code for tokens
    try:
        response = requests.post(config['token_url'], data={
            'client_id': config['client_id'],
            'client_secret': config['client_secret'],
            'code': code,
            'redirect_uri': url_for('oauth.slack_callback', _external=True)
        })
        
        token_data = response.json()
        
        if not token_data.get('ok'):
            return redirect(f'/dashboard?oauth_error={token_data.get("error", "token_exchange_failed")}')
        
        # Store platform registration using new integrated system
        success = store_platform_registration(state_data['user_id'], 'slack', token_data, token_data)
        
        if success:
            # Track platform connection event
            sync_tracker.track_sync_event(
                user_id=state_data['user_id'],
                event_type=EventType.PLATFORM_CONNECTED,
                platform='slack',
                status='success',
                metadata={
                    'team_name': token_data.get('team', {}).get('name'),
                    'team_id': token_data.get('team', {}).get('id'),
                    'connection_method': 'oauth'
                }
            )
            
            # Clean up OAuth state
            supabase.table('oauth_states').delete().eq('state', state).execute()
            return redirect('/dashboard?oauth_success=slack')
        else:
            return redirect('/dashboard?oauth_error=registration_failed')
        
    except Exception as e:
        print(f"Slack OAuth error: {e}")
        return redirect('/dashboard?oauth_error=token_exchange_error')

@oauth_bp.route('/outlook/authorize')
def outlook_authorize():
    """Initiate Outlook OAuth flow with PKCE"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    config = OAUTH_CONFIG['outlook']
    state = secrets.token_urlsafe(32)
    code_verifier, code_challenge = generate_pkce_codes()
    
    # Store state and code verifier
    if not store_oauth_state(user_id, 'outlook', state, code_verifier):
        return jsonify({'error': 'Failed to initiate OAuth flow'}), 500
    
    auth_url = config['authorize_url'].format(tenant=config['tenant_id'])
    params = {
        'client_id': config['client_id'],
        'response_type': 'code',
        'redirect_uri': url_for('oauth.outlook_callback', _external=True),
        'response_mode': 'query',
        'scope': config['scope'],
        'state': state,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256'
    }
    
    return redirect(f"{auth_url}?{urlencode(params)}")

@oauth_bp.route('/outlook/callback')
def outlook_callback():
    """Handle Outlook OAuth callback"""
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')
    
    if error:
        return redirect(f'/setup/outlook?error={error}')
    
    if not code or not state:
        return redirect('/setup/outlook?error=missing_params')
    
    # Verify state and get code verifier
    state_data = verify_oauth_state(state, 'outlook')
    if not state_data:
        return redirect('/setup/outlook?error=invalid_state')
    
    config = OAUTH_CONFIG['outlook']
    token_url = config['token_url'].format(tenant=config['tenant_id'])
    
    # Exchange code for tokens
    try:
        response = requests.post(token_url, data={
            'client_id': config['client_id'],
            'client_secret': config['client_secret'],
            'code': code,
            'redirect_uri': url_for('oauth.outlook_callback', _external=True),
            'grant_type': 'authorization_code',
            'code_verifier': state_data['code_verifier']
        })
        
        token_data = response.json()
        
        if 'error' in token_data:
            return redirect(f'/dashboard?oauth_error={token_data.get("error")}')
        
        # Store platform registration using new integrated system
        user_info = get_user_info_from_provider('outlook', token_data['access_token'])
        success = store_platform_registration(state_data['user_id'], 'outlook', token_data, user_info)
        
        if success:
            # Track platform connection event
            sync_tracker.track_sync_event(
                user_id=state_data['user_id'],
                event_type=EventType.PLATFORM_CONNECTED,
                platform='outlook',
                status='success',
                metadata={
                    'user_email': get_platform_user_email('outlook', user_info),
                    'user_name': get_platform_user_name('outlook', user_info),
                    'connection_method': 'oauth'
                }
            )
            
            # Clean up OAuth state
            supabase.table('oauth_states').delete().eq('state', state).execute()
            return redirect('/dashboard?oauth_success=outlook')
        else:
            return redirect('/dashboard?oauth_error=registration_failed')
        
    except Exception as e:
        print(f"Outlook OAuth error: {e}")
        return redirect('/dashboard?oauth_error=token_exchange_error')

@oauth_bp.route('/refresh/<platform>')
def refresh_token(platform):
    """Refresh OAuth tokens for a platform"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    if platform not in OAUTH_CONFIG:
        return jsonify({'error': 'Invalid platform'}), 400
    
    # Slack tokens don't expire, skip refresh
    if platform == 'slack':
        return jsonify({'success': True, 'message': 'Slack tokens do not expire'})
    
    try:
        # Get current registration
        result = supabase.table('registered_platforms').select('*').eq('user_id', user_id).eq('platform', platform).single().execute()
        if not result.data:
            return jsonify({'error': 'No platform registration found'}), 404
        
        # Decrypt credentials
        credentials = json.loads(result.data['encrypted_credentials'])
        refresh_token_value = credentials.get('refresh_token')
        
        if not refresh_token_value:
            return jsonify({'error': 'No refresh token available'}), 400
        
        config = OAUTH_CONFIG[platform]
        token_url = config['token_url']
        
        if platform == 'outlook':
            token_url = token_url.format(tenant=config.get('tenant_id', 'common'))
        
        # Request new tokens
        response = requests.post(token_url, data={
            'client_id': config['client_id'],
            'client_secret': config['client_secret'],
            'refresh_token': refresh_token_value,
            'grant_type': 'refresh_token'
        })
        
        token_data = response.json()
        
        if 'error' in token_data:
            return jsonify({'error': token_data.get('error_description', 'Token refresh failed')}), 400
        
        # Update credentials
        expires_in = token_data.get('expires_in', 3600)
        expires_at = (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()
        
        updated_credentials = {
            **credentials,
            'access_token': token_data.get('access_token'),
            'refresh_token': token_data.get('refresh_token', refresh_token_value),
            'expires_at': expires_at
        }
        
        # Update registration
        supabase.table('registered_platforms').update({
            'encrypted_credentials': json.dumps(updated_credentials),
            'expires_at': expires_at,
            'updated_at': datetime.utcnow().isoformat()
        }).eq('user_id', user_id).eq('platform', platform).execute()
        
        return jsonify({'success': True, 'expires_at': expires_at})
        
    except Exception as e:
        print(f"Token refresh error: {e}")
        return jsonify({'error': 'Token refresh failed'}), 500

@oauth_bp.route('/disconnect/<platform>')
def disconnect_platform(platform):
    """Disconnect a platform OAuth connection"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # Delete platform registration
        supabase.table('registered_platforms').delete().eq('user_id', user_id).eq('platform', platform).execute()
        
        # Delete platform connections
        supabase.table('platform_connections').delete().eq('user_id', user_id).eq('platform', platform).execute()
        
        # Clean up calendar connections
        supabase.table('calendar_connections').delete().eq('user_id', user_id).eq('platform', platform).execute()
        
        # Clean up sync settings
        supabase.table('sync_settings').delete().eq('user_id', user_id).eq('platform', platform).execute()
        
        return jsonify({'success': True, 'message': f'{platform.title()} disconnected successfully'})
        
    except Exception as e:
        print(f"Disconnect error: {e}")
        return jsonify({'error': 'Failed to disconnect'}), 500

@oauth_bp.route('/status')
def oauth_status():
    """Get OAuth status for all platforms"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'authenticated': False}), 200
    
    try:
        # Get all platform registrations for user
        result = supabase.table('registered_platforms').select('*').eq('user_id', user_id).eq('is_active', True).execute()
        
        platforms = {}
        for registration in result.data:
            platform = registration['platform']
            platforms[platform] = {
                'registered': True,
                'platform_name': registration.get('platform_name'),
                'user_name': registration.get('platform_user_name'),
                'user_email': registration.get('platform_user_email'),
                'expires_at': registration.get('expires_at'),
                'created_at': registration.get('created_at')
            }
        
        return jsonify({
            'authenticated': True,
            'user_id': user_id,
            'platforms': platforms,
            'total_registered': len(platforms)
        })
        
    except Exception as e:
        print(f"OAuth status error: {e}")
        return jsonify({'authenticated': False, 'error': str(e)}), 500