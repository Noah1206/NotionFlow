"""
📊 Dashboard Data Manager
Centralized data loading for all dashboard pages with real Supabase integration
"""

import sys
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

# Add config to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../utils'))
from utils.config import config

class DashboardDataManager:
    """Manages data loading for all dashboard pages"""
    
    def __init__(self):
        self.supabase = config.supabase_client
        self.admin_client = config.supabase_admin
    
    def get_user_dashboard_data(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive dashboard data for a user"""
        try:
            # Get user profile
            profile = self.get_user_profile(user_id)
            if not profile:
                return None
            
            # Get all dashboard data in parallel
            data = {
                'user_profile': profile,
                'api_keys': self.get_user_api_keys(user_id),
                'calendar_events': self.get_user_calendar_events(user_id),
                'sync_status': self.get_user_sync_status(user_id),
                'platform_stats': self.get_platform_coverage(user_id),
                'recent_activity': self.get_recent_activity(user_id),
                'friends': self.get_user_friends(user_id)
            }
            
            return data
            
        except Exception as e:
            print(f"Error loading dashboard data: {e}")
            return None
    
    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Get user profile data"""
        try:
            result = self.supabase.table('user_profiles').select('*').eq('user_id', user_id).single().execute()
            return result.data if result.data else None
        except Exception as e:
            print(f"Error getting user profile: {e}")
            return None
    
    def get_user_api_keys(self, user_id: str) -> Dict[str, Dict]:
        """Get user's platform configurations"""
        try:
            result = self.supabase.table('calendar_sync_configs').select('''
                platform, is_enabled, last_sync_at, 
                consecutive_failures, sync_frequency_minutes, created_at
            ''').eq('user_id', user_id).execute()
            
            # Format platform data
            platforms = {}
            platform_configs = {
                'notion': {'name': 'Notion', 'credential_type': 'api_key'},
                'google': {'name': 'Google Calendar', 'credential_type': 'oauth'},
                'apple': {'name': 'Apple Calendar', 'credential_type': 'caldav'},
                'outlook': {'name': 'Microsoft Outlook', 'credential_type': 'oauth'},
                'slack': {'name': 'Slack', 'credential_type': 'webhook_url'}
            }
            
            for config in result.data:
                platform = config['platform']
                platform_info = platform_configs.get(platform, {})
                
                # Check if actually configured with valid credentials
                has_valid_credentials = self._has_valid_credentials(user_id, platform, config)
                
                # Check if calendar is connected for platforms that support it
                calendar_connected = bool(config.get('calendar_id'))
                
                # Determine status based on credentials and calendar connection
                if has_valid_credentials and calendar_connected:
                    status = 'connected'  # OAuth + 캘린더 연결 완료
                elif has_valid_credentials and not calendar_connected:
                    status = 'oauth_only'  # OAuth만 완료, 캘린더 미연결
                else:
                    status = 'not_configured'  # OAuth 미완료
                
                platforms[platform] = {
                    'name': platform_info.get('name', platform.title()),
                    'enabled': config['is_enabled'] and has_valid_credentials and calendar_connected,
                    'credential_type': platform_info.get('credential_type', 'api_key'),
                    'configured': has_valid_credentials,
                    'calendar_connected': calendar_connected,
                    'last_sync': config['last_sync_at'],
                    'sync_frequency': config.get('sync_frequency_minutes', 15),
                    'health_status': status,
                    'failures': config['consecutive_failures'],
                    'created_at': config['created_at']
                }
            
            # Add unconfigured platforms
            for platform_id, platform_info in platform_configs.items():
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
            
            return platforms
            
        except Exception as e:
            print(f"Error getting user API keys: {e}")
            return {}
    
    def _has_valid_credentials(self, user_id: str, platform: str, config: dict) -> bool:
        """Check if platform has valid credentials stored"""
        try:
            # Check if credentials field exists and has content
            credentials = config.get('credentials')
            if not credentials:
                return False
                
            # For Notion, check if access_token exists and is not empty
            if platform == 'notion':
                if isinstance(credentials, dict):
                    access_token = credentials.get('access_token')
                    return bool(access_token and access_token.strip() and access_token != '')
                return False
                
            # For Google, check if we have refresh_token or access_token
            elif platform == 'google':
                if isinstance(credentials, dict):
                    return bool(credentials.get('refresh_token') or credentials.get('access_token'))
                return False
                
            # For other platforms, check if credentials exist
            else:
                return bool(credentials)
                
        except Exception as e:
            print(f"Error validating credentials for {platform}: {e}")
            return False
    
    def get_user_calendar_events(self, user_id: str, days_ahead: int = 30, start_datetime: datetime = None, end_datetime: datetime = None, calendar_ids: List[str] = None) -> List[Dict]:
        """Get user's calendar events, optionally filtered by calendar IDs"""
        try:
            # UUID 정규화 (통일된 형식 - 하이픈 없음)
            from utils.uuid_helper import normalize_uuid
            normalized_user_id = normalize_uuid(user_id)
            # print(f"🔍 [EVENTS] Searching calendar events for user {user_id} (normalized: {normalized_user_id})")
            
            if start_datetime is None:
                start_datetime = datetime.now()
            if end_datetime is None:
                end_datetime = start_datetime + timedelta(days=days_ahead)
            
            # print(f"📅 [EVENTS] Date range: {start_datetime.isoformat()} to {end_datetime.isoformat()}")
            
            # Build query - using actual column names from the database
            query = self.supabase.table('calendar_events').select('''
                id, title, description, start_datetime, end_datetime,
                is_all_day, status, location, attendees, created_at, updated_at, calendar_id, source_platform
            ''').eq('user_id', normalized_user_id).gte('start_datetime', start_datetime.isoformat()).lte('start_datetime', end_datetime.isoformat())
            
            # Filter by calendar IDs if provided
            if calendar_ids:
                # Include events that exactly match the specified calendar_id(s)
                # This applies to ALL events including Notion events - they must have matching calendar_id
                query = query.in_('calendar_id', calendar_ids)
                # print(f"📅 [EVENTS] Filtering by calendar IDs: {calendar_ids}")
            else:
                # print(f"📅 [EVENTS] No calendar ID filter - showing all events")
                pass
            
            result = query.order('start_datetime').execute()
            
            events_found = len(result.data) if result.data else 0
            print(f"📊 [EVENTS] Found {events_found} events for user {normalized_user_id}")
            
            if result.data:
                notion_events = [e for e in result.data if e.get('source_platform') == 'notion']
                print(f"🎯 [EVENTS] Notion events found: {len(notion_events)}")
                for event in notion_events[:3]:  # 처음 3개만 로깅
                    print(f"  📝 {event.get('title')} - {event.get('start_datetime')}")
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Error getting calendar events: {e}")
            return []
    
    def get_user_calendars(self, user_id: str) -> Dict[str, Any]:
        """Get user's calendar list from new calendars table"""
        try:
            # CRITICAL: Normalize user_id first to ensure consistency
            from utils.uuid_helper import normalize_uuid
            normalized_user_id = normalize_uuid(user_id)  # Unified format (no hyphens)
            original_user_id = user_id
            
            print(f"🔍 get_user_calendars called for user_id: {original_user_id} (normalized: {normalized_user_id})")
            print(f"🔍 admin_client available: {self.admin_client is not None}")
            
            # First, let's see what calendars exist in the database
            all_calendars_result = self.admin_client.table('calendars').select('''
                id, name, color, type, description, is_active, 
                public_access, allow_editing, created_at, updated_at, owner_id
            ''').execute()
            
            print(f"🔍 All calendars in database: {all_calendars_result.data}")
            print(f"🔍 Total calendars in DB: {len(all_calendars_result.data) if all_calendars_result.data else 0}")
            
            # Get calendars from new calendars table using admin client
            # Query with BOTH formats for maximum compatibility
            result = self.admin_client.table('calendars').select('''
                id, name, color, type, description, is_active, 
                public_access, allow_editing, created_at, updated_at
            ''').or_(f'owner_id.eq.{original_user_id},owner_id.eq.{normalized_user_id}').execute()
            
            print(f"🔍 Supabase query result for user {user_id}: {result}")
            print(f"🔍 Result data: {result.data}")
            print(f"🔍 Number of calendars found: {len(result.data) if result.data else 0}")
            
            personal_calendars = []
            shared_calendars = []
            total_events_count = 0
            
            # Process each calendar
            for calendar in result.data:
                # Calculate actual event count for this calendar
                try:
                    # Query calendar_events table to get actual event count
                    events_result = self.admin_client.table('calendar_events').select(
                        'id', count='exact'
                    ).eq('user_id', normalized_user_id).eq('calendar_id', calendar['id']).execute()
                    
                    event_count = events_result.count if events_result.count is not None else 0
                    print(f"📊 [EVENT-COUNT] Calendar '{calendar['name']}' ({calendar['id'][:8]}...): {event_count} events")
                    
                except Exception as count_error:
                    print(f"⚠️ [EVENT-COUNT] Error counting events for calendar {calendar['id']}: {count_error}")
                    event_count = 0
                
                total_events_count += event_count
                
                # Format created time for last sync display
                last_sync_display = "Just created"
                if calendar.get('updated_at'):
                    try:
                        from datetime import datetime
                        updated_at = datetime.fromisoformat(calendar['updated_at'].replace('Z', '+00:00'))
                        time_diff = datetime.now() - updated_at.replace(tzinfo=None)
                        if time_diff.total_seconds() < 120:  # Less than 2 minutes
                            last_sync_display = f"Updated {int(time_diff.total_seconds()//60)} min ago"
                        elif time_diff.total_seconds() < 3600:  # Less than 1 hour
                            last_sync_display = f"Updated {int(time_diff.total_seconds()//60)} min ago"
                        else:
                            last_sync_display = f"Updated {int(time_diff.total_seconds()//3600)} hours ago"
                    except:
                        last_sync_display = "Recently updated"
                
                calendar_data = {
                    'id': calendar['id'],
                    'name': calendar['name'],
                    'platform': calendar['type'],  # type maps to platform
                    'color': calendar['color'] or '#2563eb',
                    'event_count': event_count,
                    'sync_status': 'active' if calendar['is_active'] else 'inactive',
                    'last_sync_display': last_sync_display,
                    'is_enabled': calendar['is_active'],
                    'is_shared': calendar.get('public_access', False),
                    'shared_with_count': 0  # TODO: implement sharing count
                }
                
                # Categorize calendar
                if calendar.get('public_access', False):
                    shared_calendars.append(calendar_data)
                else:
                    personal_calendars.append(calendar_data)
            
            return {
                'personal_calendars': personal_calendars,
                'shared_calendars': shared_calendars,
                'summary': {
                    'total_calendars': len(personal_calendars) + len(shared_calendars),
                    'personal_calendars': len(personal_calendars),
                    'shared_calendars': len(shared_calendars),
                    'total_events': total_events_count,
                    'active_calendars': len([c for c in personal_calendars + shared_calendars if c['is_enabled']])
                }
            }
            
        except Exception as e:
            print(f"Error getting user calendars: {e}")
            return {
                'personal_calendars': [],
                'shared_calendars': [],
                'summary': {
                    'total_calendars': 0,
                    'personal_calendars': 0,
                    'shared_calendars': 0,
                    'total_events': 0,
                    'active_calendars': 0
                }
            }
    
    def get_user_sync_status(self, user_id: str) -> Dict[str, Any]:
        """Get user's sync status and statistics"""
        try:
            # Get platform coverage
            coverage_result = self.supabase.table('platform_coverage').select('*').eq('user_id', user_id).execute()
            
            # Get recent sync events
            sync_events_result = self.supabase.table('sync_events').select('''
                id, event_type, platform, status, created_at, error_message
            ''').eq('user_id', user_id).order('created_at', desc=True).limit(20).execute()
            
            # Calculate summary statistics
            total_platforms = len(coverage_result.data) if coverage_result.data else 0
            connected_platforms = len([p for p in coverage_result.data if p.get('is_connected')]) if coverage_result.data else 0
            
            recent_failures = len([e for e in sync_events_result.data if e.get('status') == 'failed']) if sync_events_result.data else 0
            
            return {
                'total_platforms': total_platforms,
                'connected_platforms': connected_platforms,
                'connection_rate': (connected_platforms / max(total_platforms, 1)) * 100,
                'recent_failures': recent_failures,
                'platform_coverage': coverage_result.data if coverage_result.data else [],
                'recent_events': sync_events_result.data if sync_events_result.data else []
            }
            
        except Exception as e:
            print(f"Error getting sync status: {e}")
            return {
                'total_platforms': 0,
                'connected_platforms': 0,
                'connection_rate': 0,
                'recent_failures': 0,
                'platform_coverage': [],
                'recent_events': []
            }
    
    def get_platform_coverage(self, user_id: str) -> Dict[str, Any]:
        """Get detailed platform coverage stats"""
        try:
            # First check if user exists to avoid foreign key errors
            user_check = self.supabase.table('users').select('id').eq('id', user_id).execute()
            if not user_check.data:
                print(f"User {user_id} not found in users table, skipping platform coverage")
                return {}
            
            result = self.supabase.table('platform_coverage').select('*').eq('user_id', user_id).execute()
            
            if not result.data:
                return {}
            
            stats = {}
            for platform in result.data:
                stats[platform['platform']] = {
                    'is_connected': platform['is_connected'],
                    'total_synced_items': platform['total_synced_items'],
                    'total_failed_items': platform['total_failed_items'],
                    'sync_success_rate': platform['sync_success_rate'],
                    'avg_sync_duration_ms': platform['avg_sync_duration_ms'],
                    'last_active_at': platform['last_active_at'],
                    'feature_coverage': platform['feature_coverage']
                }
            
            return stats
            
        except Exception as e:
            print(f"Error getting platform coverage: {e}")
            return {}
    
    def get_recent_activity(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get user's recent activity"""
        try:
            result = self.supabase.table('user_activity').select('''
                id, activity_type, platform, activity_details, 
                ip_address, created_at
            ''').eq('user_id', user_id).order('created_at', desc=True).limit(limit).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Error getting recent activity: {e}")
            return []
    
    def get_user_friends(self, user_id: str) -> List[Dict]:
        """Get user's friends/connections (placeholder for future feature)"""
        # This would connect to a friends/connections table when implemented
        return []
    
    def get_dashboard_summary(self, user_id: str) -> Dict[str, Any]:
        """Get dashboard summary statistics"""
        try:
            # Get counts from various tables
            events_today = self.supabase.table('calendar_events').select('id', count='exact').eq('user_id', user_id).gte('start_datetime', datetime.now().date().isoformat()).lt('start_datetime', (datetime.now().date() + timedelta(days=1)).isoformat()).execute()
            
            total_events = self.supabase.table('calendar_events').select('id', count='exact').eq('user_id', user_id).execute()
            
            active_configs = self.supabase.table('calendar_sync_configs').select('id', count='exact').eq('user_id', user_id).eq('is_enabled', True).execute()
            
            return {
                'events_today': events_today.count if events_today.count else 0,
                'total_events': total_events.count if total_events.count else 0,
                'active_platforms': active_configs.count if active_configs.count else 0,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error getting dashboard summary: {e}")
            return {
                'events_today': 0,
                'total_events': 0,
                'active_platforms': 0,
                'last_updated': datetime.now().isoformat()
            }
    
    def get_api_keys_summary(self, user_id: str) -> Dict[str, Any]:
        """Get API keys summary for API Keys page"""
        try:
            # Get user's API keys (returns dict with platform_id as key)
            api_keys = self.get_user_api_keys(user_id)
            
            # Ensure api_keys is a dictionary
            if not isinstance(api_keys, dict):
                api_keys = {}
            
            # Count by platform
            platforms = {}
            for platform_id, platform_data in api_keys.items():
                if not isinstance(platform_data, dict):
                    continue
                    
                platforms[platform_id] = {
                    'count': 1,
                    'status': 'connected' if platform_data.get('configured') and platform_data.get('enabled') else 'disconnected',
                    'last_used': platform_data.get('last_sync')
                }
            
            return {
                'total_keys': len(api_keys),
                'connected_platforms': len([p for p in platforms.values() if p['status'] == 'connected']),
                'platforms': platforms,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error getting API keys summary: {e}")
            import traceback
            traceback.print_exc()
            return {
                'total_keys': 0,
                'connected_platforms': 0,
                'platforms': {},
                'last_updated': datetime.now().isoformat()
            }

# Global instance
dashboard_data = DashboardDataManager()