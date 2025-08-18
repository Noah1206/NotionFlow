"""
🗓️ Calendar Database Operations
SupaBase database operations for calendar management
"""

import uuid
import datetime
from typing import List, Dict, Optional, Any
import json

try:
    from config import Config
    config = Config()
except ImportError:
    try:
        # 상대 경로로 다시 시도
        from .config import Config
        config = Config()
    except ImportError:
        print("⚠️ Config not available, using mock functions")
        config = None

class CalendarDatabase:
    """Database operations for calendar management"""
    
    def __init__(self):
        self.supabase = config.supabase_admin if config else None
        
    def is_available(self) -> bool:
        """Check if database is available"""
        return self.supabase is not None
    
    def get_user_calendars(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all calendars for a user"""
        if not self.supabase:
            print("⚠️ Database not available, returning empty list")
            return []
        
        try:
            result = self.supabase.table('calendars').select('*').eq('owner_id', user_id).execute()
            
            calendars = result.data if result.data else []
            print(f"✅ Loaded {len(calendars)} calendars from database for user {user_id}")
            
            # Debug: Print actual calendar names from database
            for i, cal in enumerate(calendars):
                print(f"📋 Calendar {i+1}: name='{cal.get('name', 'NO_NAME')}', id={cal.get('id', 'NO_ID')}")
            
            # Convert database format to JSON format for compatibility
            formatted_calendars = []
            for cal in calendars:
                formatted_cal = {
                    'id': str(cal['id']),
                    'name': cal['name'],
                    'color': cal['color'],
                    'platform': cal.get('type', 'personal'),  # type -> platform mapping
                    'is_shared': cal.get('public_access', False),  # public_access -> is_shared
                    'event_count': cal.get('event_count', 0),
                    'sync_status': 'synced' if cal.get('is_active', True) else 'inactive',
                    'last_sync_display': 'Synced recently',
                    'is_enabled': cal.get('is_active', True),  # is_active -> is_enabled
                    'user_id': cal['owner_id'],
                    'created_at': cal['created_at'],
                    'description': cal.get('description', ''),
                    # Add media file fields
                    'media_filename': cal.get('media_filename'),
                    'media_file_path': cal.get('media_file_path'),
                    'media_file_type': cal.get('media_file_type')
                }
                
                # Add shared_with_count for shared calendars
                if formatted_cal['is_shared']:
                    formatted_cal['shared_with_count'] = cal.get('shared_with_count', 0)
                    
                formatted_calendars.append(formatted_cal)
            
            return formatted_calendars
            
        except Exception as e:
            print(f"❌ Failed to get user calendars: {e}")
            return []
    
    def create_calendar(self, user_id: str, calendar_data: Dict[str, Any]) -> Optional[str]:
        """Create a new calendar"""
        if not self.supabase:
            print("⚠️ Database not available")
            return None
        
        try:
            # Generate UUID if not provided
            calendar_id = calendar_data.get('id', str(uuid.uuid4()))
            
            # Prepare database data - map to actual schema
            db_data = {
                'id': calendar_id,
                'owner_id': user_id,
                'name': calendar_data['name'],
                'color': calendar_data.get('color', '#2563eb'),
                'type': calendar_data.get('platform', 'personal'),  # platform -> type
                'description': calendar_data.get('description', f"{calendar_data['name']} - Created by user"),
                'is_active': calendar_data.get('is_enabled', True),  # is_enabled -> is_active
                'public_access': calendar_data.get('is_shared', False),  # is_shared -> public_access
                'allow_editing': True
            }
            
            # Insert into database
            result = self.supabase.table('calendars').insert(db_data).execute()
            
            if result.data:
                print(f"✅ Calendar created in database: {calendar_data['name']}")
                return calendar_id
            else:
                print(f"❌ Failed to create calendar: no data returned")
                return None
                
        except Exception as e:
            print(f"❌ Failed to create calendar: {e}")
            return None
    
    def update_calendar(self, calendar_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing calendar"""
        if not self.supabase:
            print("⚠️ Database not available")
            return False
        
        try:
            # Add updated_at timestamp
            updates['updated_at'] = datetime.datetime.now().isoformat()
            
            result = self.supabase.table('calendars').update(updates).eq('id', calendar_id).execute()
            
            if result.data:
                print(f"✅ Calendar updated: {calendar_id}")
                return True
            else:
                print(f"❌ Failed to update calendar: {calendar_id}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to update calendar: {e}")
            return False
    
    def delete_calendar(self, calendar_id: str, user_id: str) -> bool:
        """Delete a calendar"""
        if not self.supabase:
            print("⚠️ Database not available")
            return False
        
        try:
            # Delete with user verification for security
            result = self.supabase.table('calendars').delete().eq('id', calendar_id).eq('owner_id', user_id).execute()
            
            if result.data:
                print(f"✅ Calendar deleted: {calendar_id}")
                return True
            else:
                print(f"❌ Failed to delete calendar: {calendar_id}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to delete calendar: {e}")
            return False
    
    def get_calendar_by_id(self, calendar_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific calendar by ID"""
        if not self.supabase:
            print("⚠️ Database not available")
            return None
        
        try:
            result = self.supabase.table('calendars').select('*').eq('id', calendar_id).eq('owner_id', user_id).single().execute()
            
            if result.data:
                cal = result.data
                return {
                    'id': str(cal['id']),
                    'name': cal['name'],
                    'color': cal['color'],
                    'platform': cal.get('type', 'personal'),  # type -> platform mapping
                    'is_shared': cal.get('public_access', False),  # public_access -> is_shared
                    'event_count': cal.get('event_count', 0),
                    'sync_status': 'synced' if cal.get('is_active', True) else 'inactive',
                    'last_sync_display': 'Synced recently',
                    'is_enabled': cal.get('is_active', True),  # is_active -> is_enabled
                    'user_id': cal['owner_id'],
                    'created_at': cal['created_at'],
                    'description': cal.get('description', ''),
                    # Add media file fields
                    'media_filename': cal.get('media_filename'),
                    'media_file_path': cal.get('media_file_path'),
                    'media_file_type': cal.get('media_file_type'),
                    'shared_with_count': cal.get('shared_with_count', 0) if cal.get('public_access', False) else None
                }
            else:
                return None
                
        except Exception as e:
            print(f"❌ Failed to get calendar: {e}")
            return None
    
    def create_default_calendar(self, user_id: str) -> Optional[str]:
        """Create default calendar for new users with unique name"""
        import datetime
        
        # Create unique name based on timestamp
        timestamp = datetime.datetime.now().strftime("%m월 %d일")
        default_calendar = {
            'name': f'내 캘린더 ({timestamp})',
            'platform': 'personal',
            'color': '#2563eb',
            'description': f'기본 캘린더 - {timestamp} 생성',
            'is_enabled': True
        }
        
        return self.create_calendar(user_id, default_calendar)
    
    def get_calendar_summary(self, user_id: str) -> Dict[str, int]:
        """Get calendar summary statistics for a user"""
        calendars = self.get_user_calendars(user_id)
        
        personal_calendars = [cal for cal in calendars if not cal.get('is_shared', False)]
        shared_calendars = [cal for cal in calendars if cal.get('is_shared', False)]
        total_events = sum(cal.get('event_count', 0) for cal in calendars)
        
        return {
            'total_calendars': len(calendars),
            'personal_calendars': len(personal_calendars),
            'shared_calendars': len(shared_calendars),
            'total_events': total_events
        }

# Create global instance
calendar_db = CalendarDatabase()

# Backward compatibility functions (drop-in replacements for JSON functions)
def save_user_calendars(user_id: str, calendars: List[Dict[str, Any]]) -> bool:
    """Backward compatibility: Save calendars (now saves to database)"""
    if not calendar_db.is_available():
        print("⚠️ Database not available, operation failed")
        return False
    
    try:
        # Get existing calendars
        existing = calendar_db.get_user_calendars(user_id)
        existing_names = {cal['name'] for cal in existing}
        
        # Create new calendars
        success_count = 0
        for calendar in calendars:
            if calendar['name'] not in existing_names:
                if calendar_db.create_calendar(user_id, calendar):
                    success_count += 1
            else:
                # Update existing calendar
                existing_cal = next((cal for cal in existing if cal['name'] == calendar['name']), None)
                if existing_cal:
                    if calendar_db.update_calendar(existing_cal['id'], calendar):
                        success_count += 1
        
        print(f"✅ Processed {success_count} calendars for user {user_id}")
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Failed to save calendars: {e}")
        return False

def load_user_calendars(user_id: str) -> List[Dict[str, Any]]:
    """Backward compatibility: Load calendars (now loads from database)"""
    calendars = calendar_db.get_user_calendars(user_id)
    
    # If no calendars found, create default
    if not calendars:
        print(f"📁 No calendars found for user {user_id}, creating default")
        if calendar_db.create_default_calendar(user_id):
            calendars = calendar_db.get_user_calendars(user_id)
    
    return calendars