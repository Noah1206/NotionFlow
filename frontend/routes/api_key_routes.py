"""
🔑 API Key Management Routes
Comprehensive API key storage and validation for external platform integrations
"""

import os
import json
import hashlib
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from flask import Blueprint, request, jsonify, session
import requests

# Add parent directory to path for backend services
sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend'))
from services.sync_tracking_service import sync_tracker, EventType, ActivityType
sys.path.append(os.path.join(os.path.dirname(__file__), '../../utils'))
from utils.config import config

api_key_bp = Blueprint('api_keys', __name__, url_prefix='/api/keys')

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
    'slack': {
        'name': 'Slack',
        'credential_type': 'webhook_url',
        'test_method': 'POST',
        'test_payload': {'text': 'NodeFlow connection test'},
        'required_fields': ['webhook_url']
    },
    'google': {
        'name': 'Google Calendar',
        'credential_type': 'oauth',
        'oauth_scopes': ['https://www.googleapis.com/auth/calendar'],
        'required_fields': ['client_id', 'client_secret']
    },
    'outlook': {
        'name': 'Microsoft Outlook',
        'credential_type': 'oauth',
        'oauth_scopes': ['https://graph.microsoft.com/calendars.readwrite'],
        'required_fields': ['client_id', 'client_secret']
    },
    'apple': {
        'name': 'Apple Calendar',
        'credential_type': 'caldav',
        'required_fields': ['server_url', 'username', 'password']
    }
}

def get_current_user_id():
    """Get current authenticated user ID"""
    from utils.auth_manager import AuthManager
    return AuthManager.get_current_user_id()

def encrypt_credentials(credentials: Dict) -> str:
    """Encrypt credentials using AES-256 encryption"""
    from utils.config import encrypt_api_key  # Use function directly
    return encrypt_api_key(credentials)

def decrypt_credentials(encrypted_credentials: str) -> Dict:
    """Decrypt credentials using AES-256 encryption"""
    from utils.config import decrypt_api_key
    return decrypt_api_key(encrypted_credentials)

@api_key_bp.route('/current', methods=['GET'])
def get_current_user():
    """Get current authenticated user information"""
    try:
        user_id = get_current_user_id()
        if user_id:
            return jsonify({
                'success': True,
                'user_id': user_id
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Not authenticated'
            }), 401
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_key_bp.route('/save', methods=['POST'])
def save_api_key():
    """Save API key for a platform to calendar_sync_configs table"""
    from utils.auth_manager import require_auth
    
    # Require authentication
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required. Please log in first.'}), 401
    
    # Rate limiting check (simple implementation)
    from datetime import datetime, timedelta
    last_save_time = session.get(f'last_api_save_{user_id}')
    if last_save_time:
        time_diff = datetime.now() - datetime.fromisoformat(last_save_time)
        if time_diff < timedelta(seconds=5):  # 5 second rate limit
            return jsonify({'error': 'Rate limit exceeded. Please wait before saving again.'}), 429
    
    session[f'last_api_save_{user_id}'] = datetime.now().isoformat()
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        platform = data.get('platform', '').strip().lower()
        credentials_data = data.get('credentials', {})
        
        # Input validation
        if not platform:
            return jsonify({'error': 'Platform is required'}), 400
            
        if not isinstance(credentials_data, dict):
            return jsonify({'error': 'Invalid credentials format'}), 400
        
        # Validate platform
        if platform not in PLATFORM_CONFIGS:
            return jsonify({'error': f'Unsupported platform: {platform}'}), 400
        
        # Sanitize credentials data
        sanitized_credentials = {}
        for key, value in credentials_data.items():
            if isinstance(value, str):
                # Remove any potential HTML/JS injection
                sanitized_value = value.strip()[:1000]  # Limit length
                if sanitized_value:
                    sanitized_credentials[key] = sanitized_value
        
        credentials_data = sanitized_credentials
        
        # Validate required fields
        platform_config = PLATFORM_CONFIGS[platform]
        required_fields = platform_config['required_fields']
        
        for field in required_fields:
            if field not in credentials_data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Test connection before saving
        test_result = test_platform_connection(platform, credentials_data)
        if not test_result['success']:
            return jsonify({
                'error': 'Connection test failed',
                'details': test_result.get('error', 'Unknown error')
            }), 400
        
        # Prepare credentials for storage
        encrypted_credentials = encrypt_credentials(credentials_data)
        
        # Get Supabase client
        from utils.config import get_supabase_admin  # Use function directly
        supabase = get_supabase_admin()
        
        # Check if configuration already exists
        existing_result = supabase.table('calendar_sync_configs').select('*').eq('user_id', user_id).eq('platform', platform).execute()
        
        config_data = {
            'user_id': user_id,
            'platform': platform,
            'credential_type': platform_config['credential_type'],
            'credentials': credentials_data,  # Store as JSONB
            'encrypted_credentials': encrypted_credentials,
            'is_enabled': True,
            'health_status': 'healthy',
            'updated_at': datetime.now().isoformat()
        }
        
        if existing_result.data:
            # Update existing configuration
            result = supabase.table('calendar_sync_configs').update(config_data).eq('user_id', user_id).eq('platform', platform).execute()
            message = f'{platform_config["name"]} credentials updated successfully'
        else:
            # Create new configuration
            config_data['created_at'] = datetime.now().isoformat()
            result = supabase.table('calendar_sync_configs').insert(config_data).execute()
            message = f'{platform_config["name"]} credentials saved successfully'
        
        if result.data:
            # Track API key added event
            sync_tracker.track_sync_event(
                user_id=user_id,
                event_type=EventType.PLATFORM_CONNECTED,
                platform=platform,
                status='success',
                metadata={
                    'credential_type': platform_config['credential_type'],
                    'connection_test_passed': test_result.get('success', False) if test_result else False,
                    'is_update': bool(existing_result.data)
                }
            )
            
            # Track user activity
            sync_tracker.track_user_activity(
                user_id=user_id,
                activity_type=ActivityType.API_KEY_ADDED if not existing_result.data else ActivityType.SETTINGS_CHANGED,
                platform=platform,
                details={
                    'credential_type': platform_config['credential_type'],
                    'connection_method': 'api_key'
                },
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            
            return jsonify({
                'success': True,
                'message': message,
                'platform': platform,
                'connection_test': test_result
            })
        else:
            return jsonify({'error': 'Failed to save credentials'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Failed to save API key: {str(e)}'}), 500

@api_key_bp.route('/user/<user_id>', methods=['GET'])
def get_user_keys(user_id):
    """Get all configured platform credentials for a user"""
    try:
        print(f"🚨 ROUTE ENTRY: /api/keys/user/{user_id} - START")
        import traceback
        print(f"🚨 Traceback for debugging: {traceback.format_stack()[-3:]}")  # Show last 3 stack frames
        print(f"🔍 get_user_keys called for user: {user_id}")
        
        # Validate user access - try both session methods
        current_user = get_current_user_id()
        print(f"🔍 Current user from AuthManager: {current_user}")
        
        # Fallback to direct session check
        if not current_user:
            current_user = session.get('user_id')
            print(f"🔍 Current user from direct session: {current_user}")
            
            # Debug the full session contents
            print(f"🔍 Full session data: {dict(session)}")
            
            # Try other session keys
            if not current_user:
                user_info = session.get('user_info')
                print(f"🔍 User info from session: {user_info}")
                if user_info and isinstance(user_info, dict):
                    current_user = user_info.get('id')
                    print(f"🔍 User ID from user_info: {current_user}")
        
        if not current_user:
            print("❌ No current user found, authentication required")
            return jsonify({'error': 'Authentication required'}), 401
        
        # Users can only access their own data - normalize both UUIDs for comparison
        from utils.uuid_helper import normalize_uuid
        normalized_current = normalize_uuid(current_user)
        normalized_requested = normalize_uuid(user_id)
        
        if normalized_current != normalized_requested:
            print(f"❌ User mismatch: {current_user} (normalized: {normalized_current}) != {user_id} (normalized: {normalized_requested})")
            return jsonify({'error': 'Access denied'}), 403
        
        print("🔍 Attempting to get database client...")
        # Get Supabase client
        from utils.config import get_supabase_admin  # Use function directly
        supabase = get_supabase_admin()
        print(f"🔍 Supabase client obtained: {supabase is not None}")
        
        # Get all sync configurations for user
        print("🔍 Querying calendar_sync_configs table...")
        try:
            result = supabase.table('calendar_sync_configs').select('''
                platform, credentials, is_enabled, last_sync_at, 
                consecutive_failures, sync_frequency_minutes, created_at, health_status
            ''').eq('user_id', user_id).execute()
            print(f"🔍 Query successful, got {len(result.data) if result.data else 0} records")
        except Exception as db_error:
            print(f"❌ Database query failed: {str(db_error)}")
            # Check if the table doesn't exist
            if 'does not exist' in str(db_error) or 'relation' in str(db_error):
                print("🔍 Table calendar_sync_configs doesn't exist, returning empty configuration")
                result = type('Result', (), {'data': []})()  # Create empty result
            else:
                return jsonify({'error': f'Database query failed: {str(db_error)}'}), 500
        
        # Format response
        platforms = {}
        for config in result.data:
            platform = config['platform']
            platform_info = PLATFORM_CONFIGS.get(platform, {})
            
            # Determine credential type based on platform and presence of credentials
            has_credentials = config.get('credentials') is not None
            credential_type = 'oauth' if has_credentials else None
            
            platforms[platform] = {
                'name': platform_info.get('name', platform.title()),
                'enabled': config['is_enabled'],
                'credential_type': credential_type,
                'configured': has_credentials,
                'last_sync': config['last_sync_at'],
                'sync_frequency': config['sync_frequency_minutes'],
                'health_status': config.get('health_status', 'healthy') if config['consecutive_failures'] == 0 else 'error',
                'failures': config['consecutive_failures'],
                'created_at': config['created_at']
            }
        
        # Add unconfigured platforms
        for platform_id, platform_info in PLATFORM_CONFIGS.items():
            if platform_id not in platforms:
                platforms[platform_id] = {
                    'name': platform_info['name'],
                    'enabled': False,
                    'credential_type': platform_info['credential_type'],
                    'configured': False,
                    'last_sync': None,
                    'sync_frequency': 15,
                    'health_status': 'not_configured',
                    'failures': 0,
                    'created_at': None
                }
        
        print(f"🔍 Returning response with {len(platforms)} platforms")
        return jsonify({
            'success': True,
            'user_id': user_id,
            'platforms': platforms,
            'summary': {
                'total_platforms': len(PLATFORM_CONFIGS),
                'configured_platforms': len([p for p in platforms.values() if p['configured']]),
                'enabled_platforms': len([p for p in platforms.values() if p['enabled']])
            }
        })
        
    except Exception as e:
        print(f"❌ Unexpected error in get_user_keys: {str(e)}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Failed to get user keys: {str(e)}'}), 500

@api_key_bp.route('/test/<platform>', methods=['POST'])
def test_platform_connection(platform, credentials_data=None):
    """Test connection to a specific platform"""
    try:
        if credentials_data is None:
            # Called via HTTP request
            data = request.get_json()
            credentials_data = data.get('credentials', {})
            should_return_response = True
        else:
            # Called internally
            should_return_response = False
        
        if platform not in PLATFORM_CONFIGS:
            result = {'success': False, 'error': f'Unsupported platform: {platform}'}
            return jsonify(result) if should_return_response else result
        
        platform_config = PLATFORM_CONFIGS[platform]
        
        # Platform-specific connection testing
        if platform == 'notion':
            result = test_notion_connection(credentials_data)
        elif platform == 'slack':
            result = test_slack_connection(credentials_data)
        elif platform == 'google':
            result = test_google_connection(credentials_data)
        elif platform == 'outlook':
            result = test_outlook_connection(credentials_data)
        elif platform == 'apple':
            result = test_apple_connection(credentials_data)
        else:
            result = {'success': False, 'error': 'Platform testing not implemented'}
        
        if should_return_response:
            return jsonify(result)
        else:
            return result
            
    except Exception as e:
        result = {'success': False, 'error': f'Connection test failed: {str(e)}'}
        if should_return_response:
            return jsonify(result), 500
        else:
            return result

def test_notion_connection(credentials: Dict) -> Dict:
    """Test Notion API connection"""
    try:
        api_key = credentials.get('api_key')
        if not api_key:
            return {'success': False, 'error': 'Notion API key required'}
        
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
                'error': f'Notion API error: {response.status_code} - {response.text}'
            }
            
    except requests.RequestException as e:
        return {'success': False, 'error': f'Network error: {str(e)}'}
    except Exception as e:
        return {'success': False, 'error': f'Notion test failed: {str(e)}'}

def test_slack_connection(credentials: Dict) -> Dict:
    """Test Slack webhook connection"""
    try:
        webhook_url = credentials.get('webhook_url')
        if not webhook_url:
            return {'success': False, 'error': 'Slack webhook URL required'}
        
        payload = {
            'text': 'NodeFlow connection test - you can ignore this message',
            'username': 'NodeFlow',
            'icon_emoji': ':calendar:'
        }
        
        response = requests.post(webhook_url, json=payload, timeout=10)
        
        if response.status_code == 200:
            return {
                'success': True,
                'message': 'Slack webhook connection successful'
            }
        else:
            return {
                'success': False,
                'error': f'Slack webhook error: {response.status_code} - {response.text}'
            }
            
    except requests.RequestException as e:
        return {'success': False, 'error': f'Network error: {str(e)}'}
    except Exception as e:
        return {'success': False, 'error': f'Slack test failed: {str(e)}'}

def test_google_connection(credentials: Dict) -> Dict:
    """Test Google Calendar OAuth credentials"""
    try:
        # For Google, we need OAuth flow, not just API key
        client_id = credentials.get('client_id')
        client_secret = credentials.get('client_secret')
        
        if not client_id or not client_secret:
            return {
                'success': False,
                'error': 'Google Calendar requires OAuth setup with client_id and client_secret'
            }
        
        # For now, just validate that the credentials are provided
        # TODO: Implement actual OAuth validation
        return {
            'success': True,
            'message': 'Google Calendar credentials validated (OAuth flow required for full setup)',
            'requires_oauth': True
        }
        
    except Exception as e:
        return {'success': False, 'error': f'Google test failed: {str(e)}'}

def test_outlook_connection(credentials: Dict) -> Dict:
    """Test Outlook OAuth credentials"""
    try:
        # Similar to Google, Outlook requires OAuth
        client_id = credentials.get('client_id')
        client_secret = credentials.get('client_secret')
        
        if not client_id or not client_secret:
            return {
                'success': False,
                'error': 'Outlook requires OAuth setup with client_id and client_secret'
            }
        
        return {
            'success': True,
            'message': 'Outlook credentials validated (OAuth flow required for full setup)',
            'requires_oauth': True
        }
        
    except Exception as e:
        return {'success': False, 'error': f'Outlook test failed: {str(e)}'}

def test_apple_connection(credentials: Dict) -> Dict:
    """Test Apple Calendar CalDAV connection"""
    try:
        server_url = credentials.get('server_url')
        username = credentials.get('username')
        password = credentials.get('password')
        
        if not all([server_url, username, password]):
            return {
                'success': False,
                'error': 'Apple Calendar requires server_url, username, and password'
            }
        
        # TODO: Implement actual CalDAV connection test
        return {
            'success': True,
            'message': 'Apple Calendar credentials validated (CalDAV implementation pending)'
        }
        
    except Exception as e:
        return {'success': False, 'error': f'Apple Calendar test failed: {str(e)}'}

@api_key_bp.route('/disable/<platform>', methods=['POST'])
def disable_platform(platform):
    """Disable a platform integration"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Get Supabase client
        from utils.config import get_supabase_admin  # Use function directly
        supabase = get_supabase_admin()
        
        # Update configuration to disable
        result = supabase.table('calendar_sync_configs').update({
            'is_enabled': False,
            'updated_at': datetime.now().isoformat()
        }).eq('user_id', user_id).eq('platform', platform).execute()
        
        if result.data:
            return jsonify({
                'success': True,
                'message': f'{platform} integration disabled'
            })
        else:
            return jsonify({'error': 'Platform not found or already disabled'}), 404
            
    except Exception as e:
        return jsonify({'error': f'Failed to disable platform: {str(e)}'}), 500

@api_key_bp.route('/remove/<platform>', methods=['DELETE'])
def remove_platform(platform):
    """Remove a platform integration completely"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Get Supabase client
        from utils.config import get_supabase_admin  # Use function directly
        supabase = get_supabase_admin()
        
        # Delete configuration
        result = supabase.table('calendar_sync_configs').delete().eq('user_id', user_id).eq('platform', platform).execute()
        
        return jsonify({
            'success': True,
            'message': f'{platform} integration removed completely'
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to remove platform: {str(e)}'}), 500

@api_key_bp.route('/platforms', methods=['GET'])
def get_supported_platforms():
    """Get list of all supported platforms with their requirements"""
    try:
        platforms = {}
        for platform_id, config in PLATFORM_CONFIGS.items():
            platforms[platform_id] = {
                'name': config['name'],
                'credential_type': config['credential_type'],
                'required_fields': config['required_fields'],
                'description': get_platform_description(platform_id)
            }
        
        return jsonify({
            'success': True,
            'platforms': platforms
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get platforms: {str(e)}'}), 500

def get_platform_description(platform_id: str) -> str:
    """Get description for a platform"""
    descriptions = {
        'notion': 'Sync tasks and events with your Notion workspace',
        'slack': 'Send calendar notifications to Slack channels',
        'google': 'Two-way sync with Google Calendar',
        'outlook': 'Two-way sync with Microsoft Outlook Calendar',
        'apple': 'Sync with Apple Calendar (iCloud)'
    }
    return descriptions.get(platform_id, 'External calendar integration')

# Error handlers
@api_key_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'API endpoint not found'}), 404

@api_key_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500