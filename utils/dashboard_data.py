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
    
    def get_user_api_keys(self, user_id: str) -> List[Dict]:
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
                
                platforms[platform] = {
                    'name': platform_info.get('name', platform.title()),
                    'enabled': config['is_enabled'],
                    'credential_type': platform_info.get('credential_type', 'api_key'),
                    'configured': True,
                    'last_sync': config['last_sync_at'],
                    'sync_frequency': config.get('sync_frequency_minutes', 15),
                    'health_status': 'healthy' if config['consecutive_failures'] == 0 else 'error',
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
    
    def get_user_calendar_events(self, user_id: str, days_ahead: int = 30, start_date: datetime = None, end_date: datetime = None, calendar_ids: List[str] = None) -> List[Dict]:
        """Get user's calendar events, optionally filtered by calendar IDs"""
        try:
            if start_date is None:
                start_date = datetime.now()
            if end_date is None:
                end_date = start_date + timedelta(days=days_ahead)
            
            # Build query - using only existing columns
            query = self.supabase.table('calendar_events').select('''
                id, title, description, start_datetime, end_datetime,
                is_all_day, status, location, attendees, created_at, updated_at, calendar_id, source_platform
            ''').eq('user_id', user_id).gte('start_datetime', start_date.isoformat()).lte('start_datetime', end_date.isoformat())
            
            # Filter by calendar IDs if provided
            if calendar_ids:
                # Include events that match calendar_id OR are from Notion (which may not have calendar_id set)
                query = query.or_(f'calendar_id.in.({",".join(calendar_ids)}),source_platform.eq.notion')
            
            result = query.order('start_datetime').execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Error getting calendar events: {e}")
            return []
    
    def get_user_calendars(self, user_id: str) -> Dict[str, Any]:
        """Get user's calendar list from new calendars table"""
        try:
            print(f"🔍 get_user_calendars called for user_id: {user_id}")
            print(f"🔍 admin_client available: {self.admin_client is not None}")
            
            # First, let's see what calendars exist in the database
            all_calendars_result = self.admin_client.table('calendars').select('''
                id, name, color, type, description, is_active, 
                public_access, allow_editing, created_at, updated_at, owner_id
            ''').execute()
            
            print(f"🔍 All calendars in database: {all_calendars_result.data}")
            print(f"🔍 Total calendars in DB: {len(all_calendars_result.data) if all_calendars_result.data else 0}")
            
            # Get calendars from new calendars table using admin client
            result = self.admin_client.table('calendars').select('''
                id, name, color, type, description, is_active, 
                public_access, allow_editing, created_at, updated_at
            ''').eq('owner_id', user_id).execute()
            
            print(f"🔍 Supabase query result for user {user_id}: {result}")
            print(f"🔍 Result data: {result.data}")
            print(f"🔍 Number of calendars found: {len(result.data) if result.data else 0}")
            
            personal_calendars = []
            shared_calendars = []
            total_events_count = 0
            
            # Process each calendar
            for calendar in result.data:
                # Skip event count query for now since calendar_id column doesn't exist
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
            # Get user's API keys
            api_keys = self.get_user_api_keys(user_id)
            
            # Count by platform
            platforms = {}
            for key in api_keys:
                platform = key.get('platform', 'unknown')
                if platform not in platforms:
                    platforms[platform] = {
                        'count': 0,
                        'status': 'disconnected',
                        'last_used': None
                    }
                platforms[platform]['count'] += 1
                if key.get('is_active'):
                    platforms[platform]['status'] = 'connected'
                    platforms[platform]['last_used'] = key.get('last_used_at')
            
            return {
                'total_keys': len(api_keys),
                'connected_platforms': len([p for p in platforms.values() if p['status'] == 'connected']),
                'platforms': platforms,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error getting API keys summary: {e}")
            return {
                'total_keys': 0,
                'connected_platforms': 0,
                'platforms': {},
                'last_updated': datetime.now().isoformat()
            }

# Global instance
dashboard_data = DashboardDataManager()