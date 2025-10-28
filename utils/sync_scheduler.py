"""
⏰ Calendar Sync Scheduler
Automatic 15-minute interval synchronization system
"""

import threading
import time
import fcntl
import tempfile
import atexit
from datetime import datetime, timedelta
from typing import Dict, List
from supabase import create_client
from utils.auth_manager import AuthManager
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend'))
from services.sync_status_service import get_sync_status_service
from services.sync_tracking_service import sync_tracker, EventType, ActivityType

# Initialize Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_API_KEY')

if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL environment variable is required")
if not SUPABASE_KEY:
    raise ValueError("SUPABASE_API_KEY environment variable is required")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

class SyncScheduler:
    """Automatic calendar synchronization scheduler with singleton pattern"""
    
    _instance = None
    _lock = threading.Lock()
    _file_lock = None
    _lock_file_path = None
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(SyncScheduler, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.is_running = False
        self.sync_thread = None
        self.sync_interval = 900  # 15 minutes in seconds
        self.last_sync_times = {}  # Track last sync per user/platform
        self._initialized = True
        
        # Create lock file to prevent multiple scheduler instances
        self._lock_file_path = os.path.join(tempfile.gettempdir(), 'notionflow_sync_scheduler.lock')
        self._file_lock = None
        
        # Register cleanup on exit
        atexit.register(self._cleanup_lock)
        
    def start_scheduler(self):
        """Start the sync scheduler with file locking to prevent duplicates"""
        if self.is_running:
            print("🔄 Sync scheduler is already running in this instance")
            return
            
        # Try to acquire file lock to prevent multiple scheduler instances
        try:
            self._file_lock = open(self._lock_file_path, 'w')
            fcntl.flock(self._file_lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self._file_lock.write(f"PID: {os.getpid()}\nStarted: {datetime.now().isoformat()}\n")
            self._file_lock.flush()
            print(f"🔒 Acquired sync scheduler lock (PID: {os.getpid()})")
        except (IOError, OSError) as e:
            print(f"⚠️  Cannot start sync scheduler - another instance is already running: {e}")
            if self._file_lock:
                self._file_lock.close()
                self._file_lock = None
            return
        
        self.is_running = True
        self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.sync_thread.start()
        print(f"✅ Sync scheduler started successfully (PID: {os.getpid()})")
    
    def stop_scheduler(self):
        """Stop the sync scheduler and release file lock"""
        self.is_running = False
        if self.sync_thread:
            self.sync_thread.join()
        self._cleanup_lock()
        print("🛑 Sync scheduler stopped")
    
    def _cleanup_lock(self):
        """Clean up file lock resources"""
        if self._file_lock:
            try:
                fcntl.flock(self._file_lock.fileno(), fcntl.LOCK_UN)
                self._file_lock.close()
                print(f"🔓 Released sync scheduler lock (PID: {os.getpid()})")
            except:
                pass
            finally:
                self._file_lock = None
        
        # Remove lock file if it exists
        try:
            if self._lock_file_path and os.path.exists(self._lock_file_path):
                os.remove(self._lock_file_path)
        except:
            pass
    
    def _sync_loop(self):
        """Main sync loop running in background thread"""
        while self.is_running:
            try:
                self._run_scheduled_syncs()
            except Exception as e:
                print(f"Error in sync loop: {e}")
            
            # Sleep for sync interval
            time.sleep(self.sync_interval)
    
    def _run_scheduled_syncs(self):
        """Run synchronization for all enabled configurations"""
        try:
            # Get all enabled sync configurations
            result = supabase.table('calendar_sync_configs').select('''
                user_id, platform, sync_frequency_minutes, last_sync_at, 
                consecutive_failures, credentials, is_enabled
            ''').eq('is_enabled', True).execute()
            
            current_time = datetime.now()
            sync_tasks = []
            
            for config in result.data:
                user_id = config['user_id']
                platform = config['platform']
                sync_frequency = config.get('sync_frequency_minutes', 15)
                last_sync = config.get('last_sync_at')
                consecutive_failures = config.get('consecutive_failures', 0)
                
                # Skip if too many consecutive failures
                if consecutive_failures >= 5:
                    continue
                
                # Check if sync is due
                if self._is_sync_due(last_sync, sync_frequency, current_time):
                    sync_tasks.append({
                        'user_id': user_id,
                        'platform': platform,
                        'config': config
                    })
            
            # Execute sync tasks
            if sync_tasks:
                # Running scheduled syncs
                self._execute_sync_tasks(sync_tasks)
            
        except Exception as e:
            print(f"Error getting sync configurations: {e}")
    
    def _is_sync_due(self, last_sync: str, frequency_minutes: int, current_time: datetime) -> bool:
        """Check if sync is due based on frequency"""
        if not last_sync:
            return True  # Never synced before
        
        try:
            last_sync_time = datetime.fromisoformat(last_sync.replace('Z', '+00:00'))
            time_since_last = current_time - last_sync_time
            frequency_delta = timedelta(minutes=frequency_minutes)
            
            return time_since_last >= frequency_delta
            
        except Exception:
            return True  # If we can't parse, assume sync is due
    
    def _execute_sync_tasks(self, sync_tasks: List[Dict]):
        """Execute synchronization tasks"""
        for task in sync_tasks:
            try:
                self._sync_user_platform(
                    task['user_id'], 
                    task['platform'], 
                    task['config']
                )
            except Exception as e:
                # Sync failed
                self._record_sync_failure(task['user_id'], task['platform'], str(e))
    
    def _sync_user_platform(self, user_id: str, platform: str, config: Dict):
        """Sync a specific user's platform"""
        sync_status_service = get_sync_status_service()
        start_result = None
        
        try:
            # Import here to avoid circular imports
            from services.calendar_service import CalendarSyncService
            
            # Track sync started event
            sync_tracker.track_sync_event(
                user_id=user_id,
                event_type=EventType.SYNC_STARTED,
                platform=platform,
                status='pending',
                metadata={'sync_type': 'scheduled'}
            )
            
            # Record sync start
            start_result = sync_status_service.start_sync(user_id, platform)
            start_time = start_result.get('start_time', time.time())
            
            # Create sync service
            sync_service = CalendarSyncService(user_id)
            
            # Get provider for platform
            provider = sync_service.get_provider(platform)
            if not provider:
                print(f"⚠️ [SYNC] Provider not available for {platform} (user: {user_id})")
                # Disable invalid configuration to prevent repeated failures
                supabase.table('calendar_sync_configs').update({
                    'is_enabled': False,
                    'consecutive_failures': 999,
                    'updated_at': datetime.now().isoformat()
                }).eq('user_id', user_id).eq('platform', platform).execute()
                return
            
            # Perform sync
            start_date = datetime.now() - timedelta(days=30)
            end_date = datetime.now() + timedelta(days=90)
            
            sync_result = sync_service._sync_platform(provider, start_date, end_date)
            
            # Log success
            # Sync completed
            
            # Track sync completed event
            sync_tracker.track_sync_event(
                user_id=user_id,
                event_type=EventType.SYNC_COMPLETED,
                platform=platform,
                status='success',
                metadata={
                    'sync_type': 'scheduled',
                    'items_processed': sync_result.get('total_events', 0),
                    'items_created': sync_result.get('created', 0),
                    'items_updated': sync_result.get('updated', 0)
                }
            )
            
            # Record sync completion
            items_processed = sync_result.get('total_events', 0)
            items_created = sync_result.get('created', 0)
            items_updated = sync_result.get('updated', 0)
            
            sync_status_service.complete_sync(
                user_id=user_id,
                platform=platform,
                start_time=start_time,
                items_processed=items_processed,
                items_created=items_created,
                items_updated=items_updated
            )
            
            # Update sync timestamp
            self._update_sync_success(user_id, platform, sync_result)
            
        except Exception as e:
            # Sync error
            
            # Track sync failed event
            sync_tracker.track_sync_event(
                user_id=user_id,
                event_type=EventType.SYNC_FAILED,
                platform=platform,
                status='failed',
                error_message=str(e),
                metadata={'sync_type': 'scheduled'}
            )
            
            # Record sync failure in new system
            if start_result and start_result.get('start_time'):
                sync_status_service.complete_sync(
                    user_id=user_id,
                    platform=platform,
                    start_time=start_result['start_time'],
                    error_message=str(e)
                )
            
            self._record_sync_failure(user_id, platform, str(e))
            raise e
    
    def _update_sync_success(self, user_id: str, platform: str, sync_result: Dict):
        """Update sync configuration after successful sync"""
        try:
            update_data = {
                'last_sync_at': datetime.now().isoformat(),
                'consecutive_failures': 0,
                'sync_errors': []  # Clear errors on success
            }
            
            supabase.table('calendar_sync_configs').update(update_data).eq('user_id', user_id).eq('platform', platform).execute()
            
        except Exception as e:
            print(f"Error updating sync success: {e}")
    
    def _record_sync_failure(self, user_id: str, platform: str, error_message: str):
        """Record sync failure in database"""
        try:
            # Get current config
            result = supabase.table('calendar_sync_configs').select('consecutive_failures, sync_errors').eq('user_id', user_id).eq('platform', platform).single().execute()
            
            if result.data:
                current_failures = result.data.get('consecutive_failures', 0)
                current_errors = result.data.get('sync_errors', [])
                
                # Add new error (keep only last 10 errors)
                current_errors.append({
                    'timestamp': datetime.now().isoformat(),
                    'error': error_message
                })
                
                if len(current_errors) > 10:
                    current_errors = current_errors[-10:]
                
                # Update failures and errors
                update_data = {
                    'consecutive_failures': current_failures + 1,
                    'sync_errors': current_errors
                }
                
                # Disable sync if too many failures
                if current_failures + 1 >= 5:
                    update_data['is_enabled'] = False
                    # Disabled sync due to repeated failures
                
                supabase.table('calendar_sync_configs').update(update_data).eq('user_id', user_id).eq('platform', platform).execute()
                
        except Exception as e:
            print(f"Error recording sync failure: {e}")
    
    def trigger_manual_sync(self, user_id: str, platform: str = None) -> Dict:
        """Trigger manual sync for specific user/platform"""
        try:
            if platform:
                # Sync specific platform
                config_result = supabase.table('calendar_sync_configs').select('*').eq('user_id', user_id).eq('platform', platform).eq('is_enabled', True).execute()
                
                if not config_result.data:
                    return {'error': f'No enabled configuration found for {platform}'}
                
                config = config_result.data[0]
                self._sync_user_platform(user_id, platform, config)
                
                return {
                    'success': True,
                    'message': f'Manual sync completed for {platform}',
                    'platform': platform
                }
            else:
                # Sync all enabled platforms for user
                configs_result = supabase.table('calendar_sync_configs').select('*').eq('user_id', user_id).eq('is_enabled', True).execute()
                
                results = {}
                for config in configs_result.data:
                    platform_name = config['platform']
                    try:
                        self._sync_user_platform(user_id, platform_name, config)
                        results[platform_name] = {'success': True}
                    except Exception as e:
                        results[platform_name] = {'success': False, 'error': str(e)}
                
                return {
                    'success': True,
                    'message': 'Manual sync completed for all platforms',
                    'results': results
                }
                
        except Exception as e:
            return {'error': f'Manual sync failed: {str(e)}'}
    
    def get_sync_status(self) -> Dict:
        """Get current sync scheduler status"""
        try:
            # Get total configurations
            total_result = supabase.table('calendar_sync_configs').select('user_id', count='exact').execute()
            
            # Get enabled configurations
            enabled_result = supabase.table('calendar_sync_configs').select('user_id', count='exact').eq('is_enabled', True).execute()
            
            # Get configurations with failures
            failed_result = supabase.table('calendar_sync_configs').select('user_id', count='exact').gte('consecutive_failures', 1).execute()
            
            return {
                'scheduler_running': self.is_running,
                'sync_interval_minutes': self.sync_interval / 60,
                'total_configurations': total_result.count or 0,
                'enabled_configurations': enabled_result.count or 0,
                'failed_configurations': failed_result.count or 0,
                'next_sync_in_seconds': self.sync_interval if self.is_running else None
            }
            
        except Exception as e:
            return {
                'scheduler_running': self.is_running,
                'error': str(e)
            }

# Global scheduler instance
_scheduler_instance = None

def get_scheduler() -> SyncScheduler:
    """Get global scheduler instance"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = SyncScheduler()
    return _scheduler_instance

def start_sync_scheduler():
    """Start the global sync scheduler"""
    scheduler = get_scheduler()
    scheduler.start_scheduler()

def stop_sync_scheduler():
    """Stop the global sync scheduler"""
    scheduler = get_scheduler()
    scheduler.stop_scheduler()

def trigger_manual_sync(user_id: str, platform: str = None) -> Dict:
    """Trigger manual sync via global scheduler"""
    scheduler = get_scheduler()
    return scheduler.trigger_manual_sync(user_id, platform)

def get_sync_status() -> Dict:
    """Get sync status via global scheduler"""
    scheduler = get_scheduler()
    return scheduler.get_sync_status()