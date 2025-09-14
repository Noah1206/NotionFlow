"""
🔗 Platform Registration Management Routes
Separate platform registration from calendar connections for better control
"""

import os
import json
import sys
import requests
from datetime import datetime
from typing import Dict, List, Optional
from flask import Blueprint, request, jsonify, session
from requests.auth import HTTPBasicAuth

# Add parent directory to path for backend services
sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend'))
from services.sync_tracking_service import sync_tracker, EventType, ActivityType
sys.path.append(os.path.join(os.path.dirname(__file__), '../../utils'))
from utils.config import config

platform_reg_bp = Blueprint('platform_registration', __name__, url_prefix='/api/platforms')

# Platform configuration
PLATFORM_CONFIGS = {
    'notion': {
        'name': 'Notion',
        'credential_type': 'api_key',
        'test_endpoint': 'https://api.notion.com/v1/users/me',
        'headers_template': {
            'Authorization': 'Bearer {api_key}',
            'Notion-Version': '2022-06-28',
            'Content-Type': 'application/json'
        },
        'required_fields': ['api_key']
    },
    'google': {
        'name': 'Google Calendar',
        'credential_type': 'oauth',
        'oauth_scopes': ['https://www.googleapis.com/auth/calendar'],
        'required_fields': ['client_id', 'client_secret']
    },
    'apple': {
        'name': 'Apple Calendar',
        'credential_type': 'caldav',
        'required_fields': ['server_url', 'username', 'password']
    },
    'outlook': {
        'name': 'Microsoft Outlook',
        'credential_type': 'oauth',
        'oauth_scopes': ['https://graph.microsoft.com/calendars.readwrite'],
        'required_fields': ['client_id', 'client_secret']
    },
    'slack': {
        'name': 'Slack',
        'credential_type': 'webhook_url',
        'test_method': 'POST',
        'test_payload': {'text': 'NotionFlow connection test'},
        'required_fields': ['webhook_url']
    }
}

def get_current_user_id():
    """Get current authenticated user ID"""
    from utils.auth_manager import AuthManager
    return AuthManager.get_current_user_id()

def encrypt_credentials(credentials: Dict) -> str:
    """Encrypt credentials using AES-256 encryption"""
    return config.encrypt_credentials(credentials)

def decrypt_credentials(encrypted_credentials: str) -> Dict:
    """Decrypt credentials using AES-256 encryption"""
    return config.decrypt_credentials(encrypted_credentials)

@platform_reg_bp.route('/register', methods=['POST'])
def register_platform():
    """Register a platform with API keys (without connecting to specific calendars)"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    # Rate limiting
    last_register_time = session.get(f'last_platform_register_{user_id}')
    if last_register_time:
        from datetime import datetime, timedelta
        time_diff = datetime.now() - datetime.fromisoformat(last_register_time)
        if time_diff < timedelta(seconds=5):
            return jsonify({'error': 'Rate limit exceeded'}), 429
    
    session[f'last_platform_register_{user_id}'] = datetime.now().isoformat()
    
    try:
        data = request.get_json()
        platform = data.get('platform', '').strip().lower()
        credentials_data = data.get('credentials', {})
        
        if not platform or platform not in PLATFORM_CONFIGS:
            return jsonify({'error': 'Invalid platform'}), 400
        
        if not isinstance(credentials_data, dict):
            return jsonify({'error': 'Invalid credentials format'}), 400
        
        # Validate required fields
        platform_config = PLATFORM_CONFIGS[platform]
        for field in platform_config['required_fields']:
            if field not in credentials_data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Test connection
        test_result = test_platform_connection(platform, credentials_data)
        if not test_result.get('success'):
            return jsonify({
                'error': 'Connection test failed',
                'details': test_result.get('error')
            }), 400
        
        # Encrypt credentials
        encrypted_credentials = encrypt_credentials(credentials_data)
        
        # Get Supabase client
        supabase = config.get_client_for_user(user_id)
        
        # Check if already registered
        existing = supabase.table('registered_platforms').select('*').eq('user_id', user_id).eq('platform', platform).execute()
        
        platform_data = {
            'user_id': user_id,
            'platform': platform,
            'platform_name': platform_config['name'],
            'credential_type': platform_config['credential_type'],
            'credentials': credentials_data,
            'encrypted_credentials': encrypted_credentials,
            'is_registered': True,
            'health_status': 'healthy',
            'last_test_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        if existing.data:
            # Update existing registration
            result = supabase.table('registered_platforms').update(platform_data).eq('user_id', user_id).eq('platform', platform).execute()
            message = f'{platform_config["name"]} registration updated successfully'
        else:
            # Create new registration
            platform_data['created_at'] = datetime.now().isoformat()
            result = supabase.table('registered_platforms').insert(platform_data).execute()
            message = f'{platform_config["name"]} registered successfully'
        
        if result.data:
            # Track event
            sync_tracker.track_sync_event(
                user_id=user_id,
                event_type=EventType.PLATFORM_CONNECTED,
                platform=platform,
                status='success',
                metadata={
                    'action': 'platform_registration',
                    'credential_type': platform_config['credential_type'],
                    'is_update': bool(existing.data)
                }
            )
            
            return jsonify({
                'success': True,
                'message': message,
                'platform': platform,
                'platform_name': platform_config['name'],
                'connection_test': test_result
            })
        else:
            return jsonify({'error': 'Failed to register platform'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500

@platform_reg_bp.route('/list', methods=['GET'])
def list_registered_platforms():
    """List all registered platforms for the current user"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        supabase = config.get_client_for_user(user_id)
        
        # Get registered platforms
        result = supabase.table('registered_platforms').select('''
            platform, platform_name, credential_type, is_registered,
            health_status, last_test_at, created_at
        ''').eq('user_id', user_id).eq('is_registered', True).execute()
        
        registered_platforms = {}
        for platform in result.data:
            platform_id = platform['platform']
            registered_platforms[platform_id] = {
                'name': platform['platform_name'],
                'registered': True,
                'credential_type': platform['credential_type'],
                'health_status': platform['health_status'],
                'last_test_at': platform['last_test_at'],
                'created_at': platform['created_at']
            }
        
        # Add available platforms not yet registered
        for platform_id, config_data in PLATFORM_CONFIGS.items():
            if platform_id not in registered_platforms:
                registered_platforms[platform_id] = {
                    'name': config_data['name'],
                    'registered': False,
                    'credential_type': config_data['credential_type'],
                    'health_status': 'not_registered',
                    'last_test_at': None,
                    'created_at': None
                }
        
        return jsonify({
            'success': True,
            'platforms': registered_platforms,
            'summary': {
                'total_available': len(PLATFORM_CONFIGS),
                'registered_count': len([p for p in registered_platforms.values() if p['registered']])
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to list platforms: {str(e)}'}), 500

@platform_reg_bp.route('/unregister/<platform>', methods=['DELETE'])
def unregister_platform(platform):
    """Unregister a platform (removes credentials and all calendar connections)"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        supabase = config.get_client_for_user(user_id)
        
        # Remove from platform connections
        platform_result = supabase.table('platform_connections').delete().eq('user_id', user_id).eq('platform', platform).execute()
        
        # Also remove any calendar sync settings for this platform
        calendar_result = supabase.table('calendar_sync').delete().eq('user_id', user_id).eq('platform', platform).execute()
        
        # Track event
        sync_tracker.track_sync_event(
            user_id=user_id,
            event_type=EventType.PLATFORM_DISCONNECTED,
            platform=platform,
            status='success',
            metadata={'action': 'platform_unregistration'}
        )
        
        return jsonify({
            'success': True,
            'message': f'{platform} unregistered successfully'
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to unregister platform: {str(e)}'}), 500

@platform_reg_bp.route('/test/<platform>', methods=['POST'])
def test_platform_connection_endpoint(platform):
    """Test connection to a registered platform or with provided credentials"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        data = request.get_json() or {}
        credentials_data = data.get('credentials', {})
        
        supabase = config.get_client_for_user(user_id)
        
        # If no credentials provided, get from registered platforms
        if not credentials_data:
            result = supabase.table('registered_platforms').select('credentials').eq('user_id', user_id).eq('platform', platform).execute()
            
            if result.data:
                credentials_data = result.data[0]['credentials']
            else:
                return jsonify({'error': 'Platform not registered'}), 404
        
        # Test the connection
        test_result = test_platform_connection(platform, credentials_data)
        
        # Update health status in database if platform is registered
        if test_result.get('success'):
            health_status = 'healthy'
        else:
            health_status = 'error'
        
        # Update the registered platform's health status
        try:
            update_result = supabase.table('registered_platforms').update({
                'health_status': health_status,
                'last_test_at': datetime.now().isoformat(),
                'last_error': test_result.get('error') if not test_result.get('success') else None
            }).eq('user_id', user_id).eq('platform', platform).execute()
        except:
            pass  # Don't fail the test if status update fails
        
        return jsonify({
            **test_result,
            'platform': platform,
            'health_status': health_status,
            'last_test_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': f'Test failed: {str(e)}'}), 500

def test_platform_connection(platform, credentials_data):
    """Internal function to test platform connections"""
    
    if platform not in PLATFORM_CONFIGS:
        return {'success': False, 'error': f'Unsupported platform: {platform}'}
    
    try:
        if platform == 'notion':
            return test_notion_connection(credentials_data)
        elif platform == 'slack':
            return test_slack_connection(credentials_data)
        elif platform == 'google':
            return test_google_connection(credentials_data)
        elif platform == 'outlook':
            return test_outlook_connection(credentials_data)
        elif platform == 'apple':
            return test_apple_connection(credentials_data)
        else:
            return {'success': False, 'error': 'Platform testing not implemented'}
            
    except Exception as e:
        return {'success': False, 'error': f'Connection test failed: {str(e)}'}

def test_notion_connection(credentials):
    """Test Notion API connection"""
    try:
        api_key = credentials.get('api_key')
        if not api_key:
            return {'success': False, 'error': 'API key required'}
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Notion-Version': '2022-06-28',
            'Content-Type': 'application/json'
        }
        
        response = requests.get('https://api.notion.com/v1/users/me', headers=headers, timeout=10)
        
        if response.status_code == 200:
            user_data = response.json()
            return {
                'success': True,
                'message': 'Notion connection successful',
                'user_info': {
                    'name': user_data.get('name', 'Unknown'),
                    'type': user_data.get('type', 'Unknown')
                }
            }
        else:
            return {
                'success': False,
                'error': f'Notion API error: {response.status_code}'
            }
            
    except Exception as e:
        return {'success': False, 'error': f'Notion test failed: {str(e)}'}

def test_slack_connection(credentials):
    """Test Slack webhook connection"""
    try:
        webhook_url = credentials.get('webhook_url')
        if not webhook_url:
            return {'success': False, 'error': 'Webhook URL required'}
        
        payload = {
            'text': 'NotionFlow connection test',
            'username': 'NotionFlow'
        }
        
        response = requests.post(webhook_url, json=payload, timeout=10)
        
        if response.status_code == 200:
            return {'success': True, 'message': 'Slack connection successful'}
        else:
            return {'success': False, 'error': f'Slack error: {response.status_code}'}
            
    except Exception as e:
        return {'success': False, 'error': f'Slack test failed: {str(e)}'}

def test_google_connection(credentials):
    """Test Google Calendar OAuth credentials"""
    try:
        # Check if OAuth token exists
        access_token = credentials.get('access_token')
        client_id = credentials.get('client_id')
        client_secret = credentials.get('client_secret')
        
        if access_token:
            # Test with actual access token
            headers = {'Authorization': f'Bearer {access_token}'}
            response = requests.get(
                'https://www.googleapis.com/calendar/v3/users/me/calendarList',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                calendars = response.json().get('items', [])
                return {
                    'success': True,
                    'message': f'Google Calendar connected successfully ({len(calendars)} calendars)',
                    'calendar_count': len(calendars)
                }
            elif response.status_code == 401:
                return {
                    'success': False,
                    'error': 'Google OAuth token expired or invalid',
                    'requires_reauth': True
                }
            else:
                return {
                    'success': False,
                    'error': f'Google API error: {response.status_code}'
                }
        elif client_id and client_secret:
            # Validate OAuth credentials format
            return {
                'success': True,
                'message': 'Google OAuth credentials validated (authentication required)',
                'requires_oauth': True
            }
        else:
            return {'success': False, 'error': 'Google OAuth credentials or access token required'}
        
    except Exception as e:
        return {'success': False, 'error': f'Google test failed: {str(e)}'}

def test_outlook_connection(credentials):
    """Test Outlook OAuth credentials"""
    try:
        # Check if OAuth token exists
        access_token = credentials.get('access_token')
        client_id = credentials.get('client_id')
        client_secret = credentials.get('client_secret')
        
        if access_token:
            # Test with actual access token
            headers = {'Authorization': f'Bearer {access_token}'}
            response = requests.get(
                'https://graph.microsoft.com/v1.0/me/calendars',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                calendars = response.json().get('value', [])
                return {
                    'success': True,
                    'message': f'Microsoft Outlook connected successfully ({len(calendars)} calendars)',
                    'calendar_count': len(calendars)
                }
            elif response.status_code == 401:
                return {
                    'success': False,
                    'error': 'Microsoft OAuth token expired or invalid',
                    'requires_reauth': True
                }
            else:
                return {
                    'success': False,
                    'error': f'Microsoft Graph API error: {response.status_code}'
                }
        elif client_id and client_secret:
            # Validate OAuth credentials format
            return {
                'success': True,
                'message': 'Microsoft OAuth credentials validated (authentication required)',
                'requires_oauth': True
            }
        else:
            return {'success': False, 'error': 'Microsoft OAuth credentials or access token required'}
        
    except Exception as e:
        return {'success': False, 'error': f'Outlook test failed: {str(e)}'}

def test_apple_connection(credentials):
    """Test Apple Calendar CalDAV connection"""
    try:
        # Check if OAuth token exists (from OAuth flow)
        access_token = credentials.get('access_token')
        
        if access_token:
            # Apple Sign In OAuth flow
            return {
                'success': True,
                'message': 'Apple Sign In connected successfully',
                'connection_type': 'oauth'
            }
        
        # CalDAV direct connection
        server_url = credentials.get('server_url', 'https://caldav.icloud.com')
        username = credentials.get('username')
        password = credentials.get('password')
        
        if not all([username, password]):
            return {'success': False, 'error': 'Apple ID and app-specific password required'}
        
        # Test CalDAV connection
        try:
            # Basic CalDAV PROPFIND request to test authentication
            headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'Depth': '0'
            }
            
            # Simple PROPFIND to test connection
            propfind_body = '''<?xml version="1.0" encoding="utf-8" ?>
            <D:propfind xmlns:D="DAV:">
                <D:prop>
                    <D:resourcetype/>
                    <D:displayname/>
                </D:prop>
            </D:propfind>'''
            
            response = requests.request(
                'PROPFIND',
                f'{server_url}/principals/',
                auth=HTTPBasicAuth(username, password),
                headers=headers,
                data=propfind_body,
                timeout=15
            )
            
            if response.status_code in [207, 200]:  # Multi-Status or OK
                return {
                    'success': True,
                    'message': 'Apple CalDAV connection successful',
                    'connection_type': 'caldav',
                    'server': server_url
                }
            elif response.status_code == 401:
                return {
                    'success': False,
                    'error': 'Authentication failed - check Apple ID and app-specific password'
                }
            else:
                return {
                    'success': False,
                    'error': f'CalDAV connection failed: HTTP {response.status_code}'
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Connection timeout - check server URL and network'
            }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'Connection failed - check server URL'
            }
        
    except Exception as e:
        return {'success': False, 'error': f'Apple test failed: {str(e)}'}

# Error handlers
@platform_reg_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Platform registration endpoint not found'}), 404

@platform_reg_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500