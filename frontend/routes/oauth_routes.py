from flask import Blueprint, redirect, request, session, jsonify, url_for
import os
import secrets
import base64
import hashlib
import requests
import sys
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
    'slack': {
        'client_id': os.environ.get('SLACK_CLIENT_ID'),
        'client_secret': os.environ.get('SLACK_CLIENT_SECRET'),
        'authorize_url': 'https://slack.com/oauth/v2/authorize',
        'token_url': 'https://slack.com/api/oauth.v2.access',
        'scope': 'channels:read,channels:write,chat:write,users:read,team:read',
        'user_scope': 'channels:read,channels:write,chat:write'
    },
    'outlook': {
        'client_id': os.environ.get('OUTLOOK_CLIENT_ID'),
        'client_secret': os.environ.get('OUTLOOK_CLIENT_SECRET'),
        'tenant_id': os.environ.get('OUTLOOK_TENANT_ID', 'common'),
        'authorize_url': 'https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize',
        'token_url': 'https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token',
        'scope': 'https://graph.microsoft.com/Calendars.ReadWrite offline_access'
    }
}

def generate_pkce_codes():
    """Generate PKCE code verifier and challenge for OAuth 2.0"""
    code_verifier = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8').rstrip('=')
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('utf-8')).digest()
    ).decode('utf-8').rstrip('=')
    return code_verifier, code_challenge

def store_oauth_state(user_id, provider, state, code_verifier=None):
    """Store OAuth state in database for security"""
    try:
        data = {
            'user_id': user_id,
            'provider': provider,
            'state': state,
            'code_verifier': code_verifier,
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(minutes=10)).isoformat()
        }
        supabase.table('oauth_states').insert(data).execute()
        return True
    except Exception as e:
        print(f"Error storing OAuth state: {e}")
        return False

def verify_oauth_state(state, provider):
    """Verify OAuth state from database"""
    try:
        result = supabase.table('oauth_states').select('*').eq('state', state).eq('provider', provider).single().execute()
        if result.data:
            # Check if state is expired
            expires_at = datetime.fromisoformat(result.data['expires_at'])
            if datetime.utcnow() > expires_at:
                # Clean up expired state
                supabase.table('oauth_states').delete().eq('state', state).execute()
                return None
            return result.data
        return None
    except Exception as e:
        print(f"Error verifying OAuth state: {e}")
        return None

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
            return redirect(f'/setup/slack?error={token_data.get("error", "token_exchange_failed")}')
        
        # Store tokens in database
        connection_data = {
            'user_id': state_data['user_id'],
            'platform': 'slack',
            'access_token': token_data.get('access_token'),
            'refresh_token': token_data.get('refresh_token'),
            'token_type': token_data.get('token_type', 'Bearer'),
            'scope': token_data.get('scope'),
            'team': token_data.get('team'),
            'authed_user': token_data.get('authed_user'),
            'expires_at': None,  # Slack tokens don't expire
            'raw_data': token_data,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        # Upsert connection
        supabase.table('platform_connections').upsert(
            connection_data,
            on_conflict='user_id,platform'
        ).execute()
        
        # Track platform connection event
        sync_tracker.track_sync_event(
            user_id=state_data['user_id'],
            event_type=EventType.PLATFORM_CONNECTED,
            platform='slack',
            status='success',
            metadata={
                'team_name': token_data.get('team', {}).get('name'),
                'team_id': token_data.get('team', {}).get('id')
            }
        )
        
        # Track user activity
        sync_tracker.track_user_activity(
            user_id=state_data['user_id'],
            activity_type=ActivityType.PLATFORM_CONNECTED,
            platform='slack',
            details={
                'team_name': token_data.get('team', {}).get('name'),
                'connection_method': 'oauth'
            },
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        # Clean up OAuth state
        supabase.table('oauth_states').delete().eq('state', state).execute()
        
        return redirect('/setup/slack?success=true')
        
    except Exception as e:
        print(f"Slack OAuth error: {e}")
        return redirect('/setup/slack?error=token_exchange_error')

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
            return redirect(f'/setup/outlook?error={token_data.get("error")}')
        
        # Calculate token expiration
        expires_in = token_data.get('expires_in', 3600)
        expires_at = (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()
        
        # Get user info from Microsoft Graph
        user_info = None
        try:
            headers = {'Authorization': f"Bearer {token_data['access_token']}"}
            user_response = requests.get('https://graph.microsoft.com/v1.0/me', headers=headers)
            if user_response.status_code == 200:
                user_info = user_response.json()
        except:
            pass
        
        # Store tokens in database
        connection_data = {
            'user_id': state_data['user_id'],
            'platform': 'outlook',
            'access_token': token_data.get('access_token'),
            'refresh_token': token_data.get('refresh_token'),
            'token_type': token_data.get('token_type', 'Bearer'),
            'scope': token_data.get('scope'),
            'expires_at': expires_at,
            'user_info': user_info,
            'raw_data': token_data,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        # Upsert connection
        supabase.table('platform_connections').upsert(
            connection_data,
            on_conflict='user_id,platform'
        ).execute()
        
        # Track platform connection event
        sync_tracker.track_sync_event(
            user_id=state_data['user_id'],
            event_type=EventType.PLATFORM_CONNECTED,
            platform='outlook',
            status='success',
            metadata={
                'user_email': user_info.get('mail') if user_info else None,
                'user_name': user_info.get('displayName') if user_info else None,
                'tenant_id': user_info.get('id') if user_info else None
            }
        )
        
        # Track user activity
        sync_tracker.track_user_activity(
            user_id=state_data['user_id'],
            activity_type=ActivityType.PLATFORM_CONNECTED,
            platform='outlook',
            details={
                'user_email': user_info.get('mail') if user_info else None,
                'connection_method': 'oauth'
            },
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        # Clean up OAuth state
        supabase.table('oauth_states').delete().eq('state', state).execute()
        
        return redirect('/setup/outlook?success=true')
        
    except Exception as e:
        print(f"Outlook OAuth error: {e}")
        return redirect('/setup/outlook?error=token_exchange_error')

@oauth_bp.route('/refresh/<platform>')
def refresh_token(platform):
    """Refresh OAuth tokens for a platform"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    if platform not in ['outlook']:  # Slack doesn't use refresh tokens
        return jsonify({'error': 'Invalid platform'}), 400
    
    try:
        # Get current connection
        result = supabase.table('platform_connections').select('*').eq('user_id', user_id).eq('platform', platform).single().execute()
        if not result.data:
            return jsonify({'error': 'No connection found'}), 404
        
        connection = result.data
        refresh_token = connection.get('refresh_token')
        
        if not refresh_token:
            return jsonify({'error': 'No refresh token available'}), 400
        
        config = OAUTH_CONFIG[platform]
        token_url = config['token_url'].format(tenant=config.get('tenant_id', 'common'))
        
        # Request new tokens
        response = requests.post(token_url, data={
            'client_id': config['client_id'],
            'client_secret': config['client_secret'],
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token'
        })
        
        token_data = response.json()
        
        if 'error' in token_data:
            return jsonify({'error': token_data.get('error_description', 'Token refresh failed')}), 400
        
        # Update tokens
        expires_in = token_data.get('expires_in', 3600)
        expires_at = (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()
        
        update_data = {
            'access_token': token_data.get('access_token'),
            'refresh_token': token_data.get('refresh_token', refresh_token),  # May get new refresh token
            'expires_at': expires_at,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        supabase.table('platform_connections').update(update_data).eq('user_id', user_id).eq('platform', platform).execute()
        
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
        # Delete connection
        supabase.table('platform_connections').delete().eq('user_id', user_id).eq('platform', platform).execute()
        
        # Clean up any related data (sync settings, etc.)
        supabase.table('sync_settings').delete().eq('user_id', user_id).eq('platform', platform).execute()
        
        return jsonify({'success': True})
        
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
        # Get all platform connections for user
        result = supabase.table('platform_connections').select('platform,expires_at,team,user_info').eq('user_id', user_id).execute()
        
        connections = {}
        for conn in result.data:
            platform = conn['platform']
            connections[platform] = {
                'connected': True,
                'expires_at': conn.get('expires_at'),
                'user_info': conn.get('team') or conn.get('user_info')
            }
        
        return jsonify({
            'authenticated': True,
            'user_id': user_id,
            'connections': connections
        })
        
    except Exception as e:
        print(f"OAuth status error: {e}")
        return jsonify({'authenticated': False, 'error': str(e)}), 500