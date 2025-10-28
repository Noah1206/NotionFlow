"""
🔄 Sync Status Service
Manages synchronization status tracking and reporting
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from supabase import create_client
import time

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_API_KEY')

if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL environment variable is required")
if not SUPABASE_KEY:
    raise ValueError("SUPABASE_API_KEY environment variable is required")


class SyncStatusService:
    """Service for managing sync status across platforms"""
    
    def __init__(self):
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    def get_user_sync_status(self, user_id: str) -> Dict:
        """Get sync status for all platforms for a user"""
        try:
            # Get sync status
            result = self.supabase.table('sync_status').select('*').eq('user_id', user_id).execute()
            
            platforms = {}
            for status in result.data:
                platform = status['platform']
                platforms[platform] = {
                    'is_connected': status['is_connected'],
                    'is_synced': status['is_synced'],
                    'last_sync_at': status['last_sync_at'],
                    'next_sync_at': status['next_sync_at'],
                    'sync_frequency': status['sync_frequency'],
                    'is_active': status['is_active'],
                    'items_synced': status['items_synced'],
                    'items_failed': status['items_failed'],
                    'error_message': status['error_message'],
                    'sync_duration_ms': status['sync_duration_ms']
                }
            
            # Get summary
            summary_result = self.supabase.table('platform_sync_summary').select('*').eq('user_id', user_id).execute()
            summary = summary_result.data[0] if summary_result.data else {}
            
            return {
                'success': True,
                'platforms': platforms,
                'summary': {
                    'total_platforms': summary.get('total_platforms', 0),
                    'connected_platforms': summary.get('connected_platforms', 0),
                    'synced_platforms': summary.get('synced_platforms', 0),
                    'active_platforms': summary.get('active_platforms', 0),
                    'latest_sync': summary.get('latest_sync'),
                    'total_items_synced': summary.get('total_items_synced', 0),
                    'total_items_failed': summary.get('total_items_failed', 0)
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def update_platform_connection(self, user_id: str, platform: str, is_connected: bool, 
                                  credentials: Optional[Dict] = None) -> Dict:
        """Update platform connection status"""
        try:
            # Start sync log
            log_data = {
                'user_id': user_id,
                'platform': platform,
                'action': 'connection_added' if is_connected else 'connection_removed',
                'details': {'has_credentials': bool(credentials)},
                'created_at': datetime.now().isoformat()
            }
            self.supabase.table('sync_logs').insert(log_data).execute()
            
            # Update or insert sync status
            status_data = {
                'user_id': user_id,
                'platform': platform,
                'is_connected': is_connected,
                'is_active': is_connected,
                'updated_at': datetime.now().isoformat()
            }
            
            if not is_connected:
                status_data['is_synced'] = False
                status_data['error_message'] = None
            
            # Try update first
            update_result = self.supabase.table('sync_status').update(status_data).eq(
                'user_id', user_id
            ).eq('platform', platform).execute()
            
            # If no rows updated, insert new
            if not update_result.data:
                self.supabase.table('sync_status').insert(status_data).execute()
            
            return {'success': True, 'message': f'Platform {platform} connection updated'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def start_sync(self, user_id: str, platform: str) -> Dict:
        """Record sync start"""
        try:
            start_time = datetime.now()
            
            # Log sync start
            log_data = {
                'user_id': user_id,
                'platform': platform,
                'action': 'sync_started',
                'created_at': start_time.isoformat()
            }
            self.supabase.table('sync_logs').insert(log_data).execute()
            
            # Update sync status
            status_data = {
                'updated_at': start_time.isoformat()
            }
            self.supabase.table('sync_status').update(status_data).eq(
                'user_id', user_id
            ).eq('platform', platform).execute()
            
            return {
                'success': True, 
                'sync_id': log_data.get('id'),
                'start_time': start_time.timestamp()
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def complete_sync(self, user_id: str, platform: str, start_time: float,
                     items_processed: int = 0, items_created: int = 0,
                     items_updated: int = 0, items_deleted: int = 0,
                     error_message: Optional[str] = None) -> Dict:
        """Record sync completion"""
        try:
            end_time = datetime.now()
            duration_ms = int((end_time.timestamp() - start_time) * 1000)
            is_success = error_message is None
            
            # Log sync completion
            log_data = {
                'user_id': user_id,
                'platform': platform,
                'action': 'sync_completed' if is_success else 'sync_failed',
                'items_processed': items_processed,
                'items_created': items_created,
                'items_updated': items_updated,
                'items_deleted': items_deleted,
                'error_message': error_message,
                'duration_ms': duration_ms,
                'created_at': end_time.isoformat()
            }
            self.supabase.table('sync_logs').insert(log_data).execute()
            
            # Update sync status
            status_data = {
                'is_synced': is_success,
                'last_sync_at': end_time.isoformat() if is_success else None,
                'error_message': error_message,
                'sync_duration_ms': duration_ms,
                'updated_at': end_time.isoformat()
            }
            
            if is_success:
                # Get sync frequency to calculate next sync
                result = self.supabase.table('sync_status').select('sync_frequency').eq(
                    'user_id', user_id
                ).eq('platform', platform).execute()
                
                sync_frequency = 15  # default
                if result.data:
                    sync_frequency = result.data[0].get('sync_frequency', 15)
                
                status_data['next_sync_at'] = (end_time + timedelta(minutes=sync_frequency)).isoformat()
                status_data['items_synced'] = items_processed
                status_data['items_failed'] = 0
            else:
                status_data['items_failed'] = items_processed
            
            self.supabase.table('sync_status').update(status_data).eq(
                'user_id', user_id
            ).eq('platform', platform).execute()
            
            return {'success': True, 'duration_ms': duration_ms}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_sync_history(self, user_id: str, platform: Optional[str] = None, 
                        limit: int = 20) -> Dict:
        """Get sync history for user"""
        try:
            query = self.supabase.table('sync_logs').select('*').eq('user_id', user_id)
            
            if platform:
                query = query.eq('platform', platform)
            
            result = query.order('created_at', desc=True).limit(limit).execute()
            
            history = []
            for log in result.data:
                history.append({
                    'platform': log['platform'],
                    'action': log['action'],
                    'timestamp': log['created_at'],
                    'items_processed': log.get('items_processed', 0),
                    'items_created': log.get('items_created', 0),
                    'items_updated': log.get('items_updated', 0),
                    'items_deleted': log.get('items_deleted', 0),
                    'duration_ms': log.get('duration_ms'),
                    'error_message': log.get('error_message'),
                    'details': log.get('details', {})
                })
            
            return {'success': True, 'history': history}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def update_sync_frequency(self, user_id: str, platform: str, 
                            frequency_minutes: int) -> Dict:
        """Update sync frequency for a platform"""
        try:
            if frequency_minutes < 5 or frequency_minutes > 1440:  # 5 min to 24 hours
                return {'success': False, 'error': 'Frequency must be between 5 and 1440 minutes'}
            
            status_data = {
                'sync_frequency': frequency_minutes,
                'updated_at': datetime.now().isoformat()
            }
            
            # Calculate next sync time
            result = self.supabase.table('sync_status').select('last_sync_at').eq(
                'user_id', user_id
            ).eq('platform', platform).execute()
            
            if result.data and result.data[0].get('last_sync_at'):
                last_sync = datetime.fromisoformat(result.data[0]['last_sync_at'].replace('Z', '+00:00'))
                status_data['next_sync_at'] = (last_sync + timedelta(minutes=frequency_minutes)).isoformat()
            
            self.supabase.table('sync_status').update(status_data).eq(
                'user_id', user_id
            ).eq('platform', platform).execute()
            
            return {'success': True, 'message': f'Sync frequency updated to {frequency_minutes} minutes'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def toggle_platform_sync(self, user_id: str, platform: str, is_active: bool) -> Dict:
        """Enable or disable sync for a platform"""
        try:
            status_data = {
                'is_active': is_active,
                'updated_at': datetime.now().isoformat()
            }
            
            self.supabase.table('sync_status').update(status_data).eq(
                'user_id', user_id
            ).eq('platform', platform).execute()
            
            action = 'enabled' if is_active else 'disabled'
            return {'success': True, 'message': f'Sync {action} for {platform}'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}


# Global service instance
_sync_status_service = None

def get_sync_status_service() -> SyncStatusService:
    """Get global sync status service instance"""
    global _sync_status_service
    if _sync_status_service is None:
        _sync_status_service = SyncStatusService()
    return _sync_status_service