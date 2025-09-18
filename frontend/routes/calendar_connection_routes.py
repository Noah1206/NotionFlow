"""
📅 Calendar Platform Connection Routes
Manage calendar-specific platform connections separately from platform registration
"""

import os
import json
import sys
from datetime import datetime
from typing import Dict, List, Optional
from flask import Blueprint, request, jsonify, session, current_app

# Add parent directory to path for backend services
sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend'))
from services.sync_tracking_service import sync_tracker, EventType, ActivityType
from services.google_calendar_service import GoogleCalendarService
sys.path.append(os.path.join(os.path.dirname(__file__), '../../utils'))
from utils.config import config

calendar_conn_bp = Blueprint('calendar_connections', __name__, url_prefix='/api/calendars')

def get_current_user_id():
    """Get current authenticated user ID"""
    from utils.auth_manager import AuthManager
    return AuthManager.get_current_user_id()

@calendar_conn_bp.route('/<calendar_id>/connect', methods=['POST'])
def connect_platform_to_calendar(calendar_id):
    """Connect a registered platform to a specific calendar"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    # Rate limiting
    last_connect_time = session.get(f'last_calendar_connect_{user_id}')
    if last_connect_time:
        from datetime import datetime, timedelta
        time_diff = datetime.now() - datetime.fromisoformat(last_connect_time)
        if time_diff < timedelta(seconds=3):
            return jsonify({'error': 'Rate limit exceeded'}), 429
    
    session[f'last_calendar_connect_{user_id}'] = datetime.now().isoformat()
    
    try:
        data = request.get_json()
        platform = data.get('platform', '').strip().lower()
        sync_config = data.get('sync_config', {})
        
        if not platform:
            return jsonify({'error': 'Platform is required'}), 400
        
        supabase = config.get_client_for_user(user_id)
        
        # Check if platform is registered
        platform_result = supabase.table('registered_platforms').select('*').eq('user_id', user_id).eq('platform', platform).execute()
        
        if not platform_result.data:
            return jsonify({'error': 'Platform not registered. Please register the platform first.'}), 400
        
        # Check if calendar exists
        calendar_result = supabase.table('user_calendars').select('*').eq('user_id', user_id).eq('calendar_id', calendar_id).execute()
        
        if not calendar_result.data:
            return jsonify({'error': 'Calendar not found'}), 404
        
        calendar_data = calendar_result.data[0]
        
        # Simple success response - OAuth tokens are already saved by OAuth flow
        result = {'success': True}
        message = f'{platform} connected to {calendar_data["name"]}'
        
        if result.get('success'):
            # Track event
            sync_tracker.track_sync_event(
                user_id=user_id,
                event_type=EventType.CALENDAR_CONNECTED,
                platform=platform,
                status='success',
                metadata={
                    'calendar_id': calendar_id,
                    'calendar_name': calendar_data['name'],
                    'sync_direction': connection_data['sync_direction'],
                    'is_reconnection': bool(existing_conn.data)
                }
            )
            
            # Auto-import Google Calendar events - with loop prevention
            auto_import_result = None
            
            # Only auto-import if this is a new connection or explicit user action
            should_auto_import = (
                platform == 'google' and 
                connection_data.get('sync_direction') in ['both', 'from_platform'] and
                not existing_conn.data  # Only for NEW connections, not existing ones
            )
            
            if should_auto_import:
                try:
                    print(f"[CALENDAR-CONNECTION] Auto-importing Google events for new connection - user: {user_id}, calendar: {calendar_id}")
                    auto_import_result = auto_import_google_events(user_id, calendar_id)
                    print(f"[CALENDAR-CONNECTION] Auto-import result: {auto_import_result}")
                except Exception as e:
                    print(f"[CALENDAR-CONNECTION] Auto-import error: {e}")
                    auto_import_result = {'error': str(e)}
            else:
                reason = "existing connection" if existing_conn.data else "wrong sync direction or platform"
                print(f"[CALENDAR-CONNECTION] Skipping auto-import - reason: {reason}")
            
            response_data = {
                'success': True,
                'message': message,
                'connection': result.data[0]
            }
            
            # Include auto-import results if attempted
            if auto_import_result:
                response_data['auto_import'] = auto_import_result
            
            return jsonify(response_data)
        else:
            return jsonify({'error': 'Failed to connect platform to calendar'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Connection failed: {str(e)}'}), 500

@calendar_conn_bp.route('/<calendar_id>/disconnect/<platform>', methods=['DELETE'])
def disconnect_platform_from_calendar(calendar_id, platform):
    """Disconnect a platform from a specific calendar"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    print(f"=== Disconnect Debug Info ===")
    print(f"User ID: {user_id}")
    print(f"Calendar ID: {calendar_id}")
    print(f"Platform: {platform}")
    
    try:
        print("Getting Supabase client...")
        supabase = config.get_client_for_user(user_id)
        print(f"Supabase client obtained: {supabase is not None}")
        
        if not supabase:
            print("ERROR: Supabase client is None!")
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Step 1: Delete registered platform (완전한 OAuth 연결 해제)
        try:
            print("Step 1: Deleting registered platform...")
            platform_result = supabase.table('registered_platforms').delete().eq('user_id', user_id).eq('platform', platform).execute()
            print(f"Platform delete result: {platform_result}")
            
            # Step 2: Delete OAuth tokens
            print("Step 2: Deleting OAuth tokens...")
            oauth_result = supabase.table('oauth_tokens').delete().eq('user_id', user_id).eq('platform', platform).execute()
            print(f"OAuth delete result: {oauth_result}")
            
            # Step 3: Delete platform connections
            print("Step 3: Deleting platform connections...")
            try:
                connection_result = supabase.table('platform_connections').delete().eq('user_id', user_id).eq('platform', platform).execute()
                print(f"Connection delete result: {connection_result}")
            except Exception as conn_error:
                print(f"Connection deletion failed (ignoring): {conn_error}")
            
            # Step 4: Try to delete imported events (optional, ignore errors)
            print("Step 4: Deleting imported events...")
            try:
                events_result = supabase.table('calendar_events').delete().eq('user_id', user_id).eq('platform', platform).execute()
                print(f"Events delete result: {events_result}")
            except Exception as events_error:
                print(f"Events deletion failed (ignoring): {events_error}")
            
            print("Complete OAuth disconnection completed successfully!")
            
            # Clear all session data related to this platform
            from flask import session
            session_keys_to_remove = [
                f'platform_{platform}_connected',
                f'{platform}_access_token',
                f'{platform}_refresh_token',
                f'{platform}_user_info',
                f'{platform}_oauth_state'
            ]
            
            for session_key in session_keys_to_remove:
                if session_key in session:
                    session.pop(session_key)
                    print(f"Removed {session_key} from session")
            
            result = {'success': True}
            
        except Exception as e:
            print(f"=== CRITICAL ERROR ===")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            print(f"Error details: {repr(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return jsonify({'error': f'Disconnect failed: {str(e)}'}), 500
        
        # Track event (optional, ignore errors)
        try:
            print("Step 3: Tracking disconnect event...")
            sync_tracker.track_sync_event(
                user_id=user_id,
                event_type=EventType.CALENDAR_DISCONNECTED,
                platform=platform,
                status='success',
                metadata={
                    'calendar_id': calendar_id,
                }
            )
            print("Event tracking completed!")
        except Exception as track_error:
            print(f"Event tracking failed (ignoring): {track_error}")
        
        print("Returning success response...")
        return jsonify({
            'success': True,
            'message': f'{platform} OAuth 연결이 완전히 해제되었습니다. 다시 연결하려면 원클릭 연결을 해주세요.',
            'requires_reauth': True  # 프론트엔드에서 재인증 필요함을 알림
        })
        
    except Exception as e:
        return jsonify({'error': f'Disconnection failed: {str(e)}'}), 500

@calendar_conn_bp.route('/<calendar_id>/connections', methods=['GET'])
def get_calendar_connections(calendar_id):
    """Get all platform connections for a specific calendar"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        supabase = config.get_client_for_user(user_id)
        
        # Get calendar info
        calendar_result = supabase.table('user_calendars').select('*').eq('user_id', user_id).eq('calendar_id', calendar_id).execute()
        
        if not calendar_result.data:
            return jsonify({'error': 'Calendar not found'}), 404
        
        calendar_data = calendar_result.data[0]
        
        # Get platform connections
        connections_result = supabase.table('platform_connections').select('*').eq('user_id', user_id).execute()
        
        # Build connections data - simplified version
        connections = {}
        for conn in connections_result.data:
            platform_id = conn['platform']
            connections[platform_id] = {
                'platform_name': platform_id.title(),
                'is_connected': conn.get('is_connected', True),
                'sync_enabled': True,
                'sync_direction': 'both',
                'sync_frequency': 15,
                'auto_sync_enabled': True,
                'last_sync': conn.get('updated_at'),
                'next_sync': None,
                'health_status': 'healthy',
                'failures': 0,
                'created_at': conn['created_at'],
                'updated_at': conn['updated_at']
            }
        
        # Add registered platforms not yet connected to this calendar
        available_platforms = {}
        for platform_id, platform_name in registered_platforms.items():
            if platform_id not in connections:
                available_platforms[platform_id] = {
                    'platform_name': platform_name,
                    'is_connected': False,
                    'can_connect': True
                }
        
        return jsonify({
            'success': True,
            'calendar': {
                'id': calendar_data['calendar_id'],
                'name': calendar_data['name'],
                'description': calendar_data.get('description', ''),
                'color': calendar_data.get('color', '#3B82F6')
            },
            'connected_platforms': connections,
            'available_platforms': available_platforms,
            'summary': {
                'total_connections': len(connections),
                'active_connections': len([c for c in connections.values() if c['is_connected']]),
                'available_to_connect': len(available_platforms)
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get connections: {str(e)}'}), 500

@calendar_conn_bp.route('/<calendar_id>/connections/<platform>/config', methods=['PUT'])
def update_connection_config(calendar_id, platform):
    """Update sync configuration for a calendar-platform connection"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        data = request.get_json()
        
        supabase = config.get_client_for_user(user_id)
        
        # Validate connection exists
        connection_result = supabase.table('platform_connections').select('*').eq('user_id', user_id).eq('calendar_id', calendar_id).eq('platform', platform).execute()
        
        if not connection_result.data:
            return jsonify({'error': 'Connection not found'}), 404
        
        # Update configuration
        update_data = {
            'updated_at': datetime.now().isoformat()
        }
        
        # Update allowed fields
        if 'sync_enabled' in data:
            update_data['sync_enabled'] = bool(data['sync_enabled'])
        
        if 'sync_direction' in data:
            valid_directions = ['both', 'to_platform', 'from_platform']
            if data['sync_direction'] in valid_directions:
                update_data['sync_direction'] = data['sync_direction']
        
        if 'sync_frequency' in data:
            frequency = int(data['sync_frequency'])
            if 5 <= frequency <= 1440:  # 5 minutes to 24 hours
                update_data['sync_frequency_minutes'] = frequency
        
        if 'auto_sync_enabled' in data:
            update_data['auto_sync_enabled'] = bool(data['auto_sync_enabled'])
        
        result = supabase.table('platform_connections').update(update_data).eq('user_id', user_id).eq('calendar_id', calendar_id).eq('platform', platform).execute()
        
        if result.data:
            return jsonify({
                'success': True,
                'message': 'Connection configuration updated',
                'updated_config': update_data
            })
        else:
            return jsonify({'error': 'Failed to update configuration'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Update failed: {str(e)}'}), 500

@calendar_conn_bp.route('/connections/summary', methods=['GET'])
def get_connections_summary():
    """Get summary of all calendar-platform connections for the user"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        supabase = config.get_client_for_user(user_id)
        
        # Get all connections
        connections_result = supabase.table('platform_connections').select('''
            calendar_id, calendar_name, platform, platform_name,
            is_connected, sync_enabled, health_status, last_sync_at
        ''').eq('user_id', user_id).execute()
        
        # Get registered platforms count
        platforms_result = supabase.table('registered_platforms').select('platform').eq('user_id', user_id).eq('is_registered', True).execute()
        
        # Get calendars count
        calendars_result = supabase.table('user_calendars').select('calendar_id').eq('user_id', user_id).execute()
        
        connections_by_calendar = {}
        connections_by_platform = {}
        
        for conn in connections_result.data:
            calendar_id = conn['calendar_id']
            platform = conn['platform']
            
            # Group by calendar
            if calendar_id not in connections_by_calendar:
                connections_by_calendar[calendar_id] = {
                    'calendar_name': conn['calendar_name'],
                    'platforms': []
                }
            connections_by_calendar[calendar_id]['platforms'].append({
                'platform': platform,
                'platform_name': conn['platform_name'],
                'is_connected': conn['is_connected'],
                'sync_enabled': conn['sync_enabled'],
                'health_status': conn['health_status'],
                'last_sync': conn['last_sync_at']
            })
            
            # Group by platform
            if platform not in connections_by_platform:
                connections_by_platform[platform] = {
                    'platform_name': conn['platform_name'],
                    'calendars': []
                }
            connections_by_platform[platform]['calendars'].append({
                'calendar_id': calendar_id,
                'calendar_name': conn['calendar_name'],
                'is_connected': conn['is_connected'],
                'sync_enabled': conn['sync_enabled'],
                'health_status': conn['health_status'],
                'last_sync': conn['last_sync_at']
            })
        
        total_connections = len(connections_result.data)
        active_connections = len([c for c in connections_result.data if c['is_connected'] and c['sync_enabled']])
        healthy_connections = len([c for c in connections_result.data if c['health_status'] == 'healthy'])
        
        return jsonify({
            'success': True,
            'summary': {
                'total_calendars': len(calendars_result.data),
                'registered_platforms': len(platforms_result.data),
                'total_connections': total_connections,
                'active_connections': active_connections,
                'healthy_connections': healthy_connections,
                'connection_health_rate': round((healthy_connections / total_connections * 100) if total_connections > 0 else 0, 1)
            },
            'connections_by_calendar': connections_by_calendar,
            'connections_by_platform': connections_by_platform
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get summary: {str(e)}'}), 500

@calendar_conn_bp.route('/<calendar_id>/sync/<platform>', methods=['POST'])
def trigger_manual_sync(calendar_id, platform):
    """Trigger manual sync for a specific calendar-platform connection"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        supabase = config.get_client_for_user(user_id)
        
        # Validate connection
        connection_result = supabase.table('platform_connections').select('*').eq('user_id', user_id).eq('calendar_id', calendar_id).eq('platform', platform).execute()
        
        if not connection_result.data:
            return jsonify({'error': 'Connection not found'}), 404
        
        connection = connection_result.data[0]
        
        if not connection['is_connected']:
            return jsonify({'error': 'Platform not connected to calendar'}), 400
        
        # Update sync timestamp
        sync_time = datetime.now().isoformat()
        supabase.table('platform_connections').update({
            'last_sync_at': sync_time,
            'next_sync_at': (datetime.now().timestamp() + (connection['sync_frequency_minutes'] * 60)),
            'updated_at': sync_time
        }).eq('user_id', user_id).eq('calendar_id', calendar_id).eq('platform', platform).execute()
        
        # Track sync event
        sync_tracker.track_sync_event(
            user_id=user_id,
            event_type=EventType.SYNC_STARTED,
            platform=platform,
            status='success',
            metadata={
                'calendar_id': calendar_id,
                'sync_type': 'manual',
                'sync_direction': connection['sync_direction']
            }
        )
        
        return jsonify({
            'success': True,
            'message': f'Manual sync triggered for {connection["platform_name"]} -> {connection["calendar_name"]}',
            'sync_started_at': sync_time
        })
        
    except Exception as e:
        return jsonify({'error': f'Sync failed: {str(e)}'}), 500

# Error handlers
@calendar_conn_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Calendar connection endpoint not found'}), 404

@calendar_conn_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

def auto_import_google_events(user_id, calendar_id):
    """Automatically import Google Calendar events when calendar is connected"""
    try:
        supabase = config.get_client_for_user(user_id)
        
        # Check if Google platform is registered and has valid credentials
        platform_result = supabase.table('registered_platforms').select('*').eq('user_id', user_id).eq('platform', 'google').execute()
        
        if not platform_result.data:
            return {'success': False, 'error': 'Google Calendar not registered'}
        
        # Initialize Google Calendar service
        google_service = GoogleCalendarService()
        
        # Get Google Calendar events using the service
        try:
            google_events = google_service.get_events(user_id, calendar_id='primary')
        except Exception as e:
            return {'success': False, 'error': f'Failed to fetch Google Calendar events: {str(e)}'}
        
        if not google_events:
            return {'success': True, 'imported_count': 0, 'failed_count': 0, 'message': 'No events to import'}
        
        # Import events to NotionFlow calendar
        imported_count = 0
        failed_count = 0
        
        for event in google_events:
            try:
                # Check if event already exists
                existing_event = supabase.table('calendar_events').select('*').eq('user_id', user_id).eq('source_calendar_id', calendar_id).eq('external_id', event.get('id')).execute()
                
                if existing_event.data:
                    continue  # Skip if event already exists
                
                # Convert Google event to NotionFlow format
                start_datetime = event.get('start', {})
                end_datetime = event.get('end', {})
                
                # Handle different date/time formats
                start_time = start_datetime.get('dateTime') or start_datetime.get('date')
                end_time = end_datetime.get('dateTime') or end_datetime.get('date')
                
                if not start_time:
                    failed_count += 1
                    continue
                
                # Prepare the event data based on schema
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
                    'last_synced_at': datetime.now().isoformat(),
                    'status': event.get('status', 'confirmed')
                }
                
                # Handle date/time fields based on whether it's all-day or not
                if 'date' in start_datetime:
                    # All-day event
                    event_data.update({
                        'start_date': start_time,
                        'end_date': end_time or start_time,
                        'is_all_day': True
                    })
                else:
                    # Timed event
                    event_data.update({
                        'start_datetime': start_time,
                        'end_datetime': end_time or start_time,
                        'is_all_day': False
                    })
                
                # Insert event into database
                result = supabase.table('calendar_events').insert(event_data).execute()
                
                if result.data:
                    imported_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                print(f"Failed to import event {event.get('id', 'unknown')}: {str(e)}")
                failed_count += 1
        
        # Track the import event
        sync_tracker.track_sync_event(
            user_id=user_id,
            event_type=EventType.SYNC_COMPLETED,
            platform='google',
            status='success' if failed_count == 0 else 'partial_success',
            metadata={
                'calendar_id': calendar_id,
                'imported_count': imported_count,
                'failed_count': failed_count,
                'auto_import': True
            }
        )
        
        return {
            'success': True,
            'imported_count': imported_count,
            'failed_count': failed_count,
            'message': f'Successfully imported {imported_count} events' + (f', {failed_count} failed' if failed_count > 0 else '')
        }
        
    except Exception as e:
        return {'success': False, 'error': f'Auto-import failed: {str(e)}'}
    