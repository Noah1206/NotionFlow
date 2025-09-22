"""
🔄 Sync Tracking Service
Comprehensive tracking for all synchronization events and activities
"""

import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Literal
from supabase import create_client
import json
from enum import Enum

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_API_KEY')

if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL environment variable is required")
if not SUPABASE_KEY:
    raise ValueError("SUPABASE_API_KEY environment variable is required")

class EventType(Enum):
    SYNC_STARTED = "sync_started"
    SYNC_COMPLETED = "sync_completed"
    SYNC_FAILED = "sync_failed"
    ITEM_CREATED = "item_created"
    ITEM_UPDATED = "item_updated"
    ITEM_DELETED = "item_deleted"
    PLATFORM_CONNECTED = "platform_connected"
    PLATFORM_DISCONNECTED = "platform_disconnected"

class ActivityType(Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    SYNC_TRIGGERED = "sync_triggered"
    SYNC_SCHEDULED = "sync_scheduled"
    SETTINGS_CHANGED = "settings_changed"
    PLATFORM_CONNECTED = "platform_connected"
    PLATFORM_DISCONNECTED = "platform_disconnected"
    API_KEY_ADDED = "api_key_added"
    API_KEY_REMOVED = "api_key_removed"
    SUBSCRIPTION_CHANGED = "subscription_changed"

class SyncTrackingService:
    """Service for tracking sync events and user activities"""
    
    def __init__(self):
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    def track_sync_event(
        self,
        user_id: str,
        event_type: EventType,
        platform: str,
        status: Literal["success", "failed", "skipped", "pending"] = "success",
        source_platform: Optional[str] = None,
        target_platform: Optional[str] = None,
        item_type: Optional[str] = None,
        item_id: Optional[str] = None,
        item_title: Optional[str] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict] = None,
        sync_job_id: Optional[str] = None
    ) -> Optional[str]:
        """Track a synchronization event"""
        try:
            # Check if user exists to avoid foreign key errors
            user_check = self.supabase.table('users').select('id').eq('id', user_id).execute()
            if not user_check.data:
                print(f"User {user_id} not found in users table, skipping sync event tracking")
                return None
            
            event_data = {
                "user_id": user_id,
                "event_type": event_type.value if isinstance(event_type, EventType) else event_type,
                "platform": platform,
                "status": status,
                "source_platform": source_platform,
                "target_platform": target_platform,
                "item_type": item_type,
                "item_id": item_id,
                "item_title": item_title,
                "error_message": error_message,
                "metadata": metadata or {},
                "sync_job_id": sync_job_id
            }
            
            result = self.supabase.table('sync_events').insert(event_data).execute()
            
            if result.data:
                return result.data[0]['id']
            return None
            
        except Exception as e:
            print(f"Error tracking sync event: {e}")
            return None
    
    def track_user_activity(
        self,
        user_id: str,
        activity_type: ActivityType,
        platform: Optional[str] = None,
        details: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Optional[str]:
        """Track user activity"""
        try:
            # Use the database function for consistency
            result = self.supabase.rpc('record_activity', {
                'p_user_id': user_id,
                'p_activity_type': activity_type.value if isinstance(activity_type, ActivityType) else activity_type,
                'p_platform': platform,
                'p_details': json.dumps(details) if details else '{}',
                'p_ip_address': ip_address,
                'p_user_agent': user_agent
            }).execute()
            
            return result.data if result.data else None
            
        except Exception as e:
            print(f"Error tracking user activity: {e}")
            return None
    
    def get_platform_coverage(self, user_id: str) -> Dict:
        """Get platform coverage statistics for a user"""
        try:
            result = self.supabase.table('platform_coverage').select('*').eq('user_id', user_id).execute()
            
            coverage = {}
            for platform_data in result.data:
                platform = platform_data['platform']
                coverage[platform] = {
                    'is_connected': platform_data['is_connected'],
                    'first_connected_at': platform_data['first_connected_at'],
                    'last_active_at': platform_data['last_active_at'],
                    'total_synced_items': platform_data['total_synced_items'],
                    'total_failed_items': platform_data['total_failed_items'],
                    'sync_success_rate': float(platform_data['sync_success_rate']),
                    'feature_coverage': platform_data['feature_coverage'],
                    'avg_sync_duration_ms': platform_data['avg_sync_duration_ms']
                }
            
            return coverage
            
        except Exception as e:
            print(f"Error getting platform coverage: {e}")
            return {}
    
    def get_recent_activity(
        self, 
        user_id: str, 
        limit: int = 10,
        activity_type: Optional[str] = None,
        platform: Optional[str] = None
    ) -> List[Dict]:
        """Get recent user activity"""
        try:
            query = self.supabase.table('user_activity').select('*').eq('user_id', user_id)
            
            if activity_type:
                query = query.eq('activity_type', activity_type)
            if platform:
                query = query.eq('platform', platform)
            
            result = query.order('created_at', desc=True).limit(limit).execute()
            
            return result.data
            
        except Exception as e:
            print(f"Error getting recent activity: {e}")
            return []
    
    def get_recent_sync_events(
        self,
        user_id: str,
        limit: int = 10,
        platform: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict]:
        """Get recent sync events using the database function"""
        try:
            # Use the custom function for better performance
            result = self.supabase.rpc('get_recent_sync_activity', {
                'p_user_id': user_id,
                'p_limit': limit
            }).execute()
            
            events = result.data if result.data else []
            
            # Filter by platform/status if needed
            if platform:
                events = [e for e in events if e['platform'] == platform]
            if status:
                events = [e for e in events if e['status'] == status]
            
            return events
            
        except Exception as e:
            print(f"Error getting recent sync events: {e}")
            return []
    
    def get_sync_analytics(
        self,
        user_id: str,
        period_type: Literal["hourly", "daily", "weekly", "monthly"] = "daily",
        limit: int = 7
    ) -> List[Dict]:
        """Get sync analytics for a user"""
        try:
            result = self.supabase.table('sync_analytics')\
                .select('*')\
                .eq('user_id', user_id)\
                .eq('period_type', period_type)\
                .order('period_start', desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data
            
        except Exception as e:
            print(f"Error getting sync analytics: {e}")
            return []
    
    def update_platform_features(
        self,
        user_id: str,
        platform: str,
        features: Dict[str, bool]
    ) -> bool:
        """Update platform feature coverage"""
        try:
            result = self.supabase.table('platform_coverage')\
                .update({'feature_coverage': features})\
                .eq('user_id', user_id)\
                .eq('platform', platform)\
                .execute()
            
            return bool(result.data)
            
        except Exception as e:
            print(f"Error updating platform features: {e}")
            return False
    
    def record_sync_batch(
        self,
        user_id: str,
        sync_job_id: str,
        platform: str,
        events: List[Dict]
    ) -> Dict:
        """Record a batch of sync events"""
        try:
            success_count = 0
            failed_count = 0
            
            for event in events:
                event_data = {
                    "user_id": user_id,
                    "sync_job_id": sync_job_id,
                    "platform": platform,
                    "event_type": event.get('type', EventType.ITEM_CREATED.value),
                    "item_type": event.get('item_type'),
                    "item_id": event.get('item_id'),
                    "item_title": event.get('item_title'),
                    "status": event.get('status', 'success'),
                    "error_message": event.get('error'),
                    "metadata": event.get('metadata', {})
                }
                
                result = self.supabase.table('sync_events').insert(event_data).execute()
                
                if result.data:
                    if event.get('status') == 'success':
                        success_count += 1
                    else:
                        failed_count += 1
            
            return {
                'success_count': success_count,
                'failed_count': failed_count,
                'total': len(events)
            }
            
        except Exception as e:
            print(f"Error recording sync batch: {e}")
            return {'success_count': 0, 'failed_count': 0, 'total': 0}
    
    def get_platform_sync_summary(self, user_id: str) -> List[Dict]:
        """Get platform sync summary from the view"""
        try:
            result = self.supabase.table('platform_sync_summary')\
                .select('*')\
                .eq('user_id', user_id)\
                .execute()
            
            return result.data
            
        except Exception as e:
            print(f"Error getting platform sync summary: {e}")
            return []
    
    def cleanup_old_events(self, days: int = 90) -> int:
        """Clean up old sync events (admin function)"""
        try:
            # This would typically be done via a scheduled job
            # For now, return 0
            return 0
            
        except Exception as e:
            print(f"Error cleaning up old events: {e}")
            return 0

# Create a singleton instance
sync_tracker = SyncTrackingService()