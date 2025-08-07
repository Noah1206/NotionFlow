"""
📅 NotionFlow Calendar Service
Database operations for calendar management system
"""

import sys
import os
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from uuid import uuid4

# Add utils to path for config access
sys.path.append(os.path.join(os.path.dirname(__file__), '../../utils'))
from utils.config import config

class CalendarService:
    """Service class for calendar database operations"""
    
    def __init__(self):
        self.supabase = config.supabase_client
        self.service_supabase = config.supabase_admin
    
    def insert_calendar(self, user_id: str, cal_id: str, calendar_type: str, share_link: Optional[str] = None) -> bool:
        """
        Insert a new calendar into the database
        
        Args:
            user_id: Owner's user ID
            cal_id: Unique calendar ID
            calendar_type: 'personal' or 'shared'
            share_link: Optional share link for shared calendars
            
        Returns:
            bool: Success status
        """
        try:
            # Insert into calendars table
            calendar_data = {
                'id': cal_id,
                'owner_id': user_id,
                'type': calendar_type,
                'share_link': share_link,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            result = self.service_supabase.table('calendars').insert(calendar_data).execute()
            
            if not result.data:
                # Failed to insert calendar
                return False
            
            # Add owner as member
            member_data = {
                'calendar_id': cal_id,
                'user_id': user_id,
                'role': 'owner',
                'joined_at': datetime.now(timezone.utc).isoformat()
            }
            
            member_result = self.service_supabase.table('calendar_members').insert(member_data).execute()
            
            if not member_result.data:
                # Failed to add owner as member
                # Rollback calendar creation
                self.service_supabase.table('calendars').delete().eq('id', cal_id).execute()
                return False
            
            # Calendar created successfully
            return True
            
        except Exception as e:
            # Error inserting calendar
            return False
    
    def add_member_to_calendar(self, user_id: str, calendar_id: str) -> bool:
        """
        Add a user as member to an existing calendar
        
        Args:
            user_id: User to add
            calendar_id: Target calendar ID
            
        Returns:
            bool: Success status
        """
        try:
            # Check if calendar exists and is shared
            calendar_result = self.service_supabase.table('calendars').select('*').eq('id', calendar_id).execute()
            
            if not calendar_result.data:
                # Calendar not found
                return False
            
            calendar = calendar_result.data[0]
            if calendar['type'] != 'shared':
                # Cannot join personal calendar
                return False
            
            # Check if user is already a member
            existing_member = self.service_supabase.table('calendar_members').select('*').eq('calendar_id', calendar_id).eq('user_id', user_id).execute()
            
            if existing_member.data:
                # User is already a member of calendar
                return True
            
            # Add user as member
            member_data = {
                'calendar_id': calendar_id,
                'user_id': user_id,
                'role': 'member',
                'joined_at': datetime.now(timezone.utc).isoformat()
            }
            
            result = self.service_supabase.table('calendar_members').insert(member_data).execute()
            
            if not result.data:
                # Failed to add member
                return False
            
            # User added to calendar
            return True
            
        except Exception as e:
            # Error adding member to calendar
            return False
    
    def get_calendars_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all calendars accessible to a user
        
        Args:
            user_id: User ID
            
        Returns:
            List[Dict]: List of calendar objects
        """
        try:
            # Get calendars where user is a member
            result = self.service_supabase.table('calendar_members').select('''
                calendar_id,
                role,
                joined_at,
                calendars:calendar_id (
                    id,
                    type,
                    share_link,
                    created_at,
                    owner_id
                )
            ''').eq('user_id', user_id).execute()
            
            if not result.data:
                # No calendars found for user
                return []
            
            calendars = []
            for membership in result.data:
                calendar_data = membership['calendars']
                if calendar_data:
                    calendars.append({
                        'id': calendar_data['id'],
                        'type': calendar_data['type'],
                        'share_link': calendar_data['share_link'],
                        'role': membership['role'],
                        'joined_at': membership['joined_at'],
                        'created_at': calendar_data['created_at'],
                        'is_owner': calendar_data['owner_id'] == user_id
                    })
            
            # Found calendars for user
            return calendars
            
        except Exception as e:
            # Error getting calendars for user
            return []
    
    def add_event_to_calendar(self, user_id: str, event: Dict[str, Any], calendar_id: Optional[str] = None) -> bool:
        """
        Add an event to user's calendar
        
        Args:
            user_id: User ID
            event: Event data dict with title, date, time, description, location
            calendar_id: Optional specific calendar ID (defaults to user's first calendar)
            
        Returns:
            bool: Success status
        """
        try:
            # If no calendar_id specified, use user's first calendar
            if not calendar_id:
                user_calendars = self.get_calendars_for_user(user_id)
                if not user_calendars:
                    # No calendars found for user
                    return False
                calendar_id = user_calendars[0]['id']
            
            # Validate user has access to calendar
            user_calendars = self.get_calendars_for_user(user_id)
            calendar_ids = [cal['id'] for cal in user_calendars]
            
            if calendar_id not in calendar_ids:
                # User doesn't have access to calendar
                return False
            
            # Prepare event data
            event_id = str(uuid4())
            event_data = {
                'id': event_id,
                'calendar_id': calendar_id,
                'creator_id': user_id,
                'title': event.get('title', 'Untitled Event'),
                'description': event.get('description', ''),
                'start_date': event.get('date'),
                'start_time': event.get('time'),
                'location': event.get('location', ''),
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Insert event
            result = self.service_supabase.table('calendar_events').insert(event_data).execute()
            
            if not result.data:
                # Failed to insert event
                return False
            
            # Event added successfully
            return True
            
        except Exception as e:
            # Error adding event to calendar
            return False
    
    def create_tables_if_not_exist(self):
        """
        Create necessary tables if they don't exist
        Note: In production, this should be done via Supabase dashboard/migrations
        """
        try:
            # This is a placeholder - actual table creation should be done in Supabase dashboard
            # Table creation should be done via Supabase dashboard
            pass
            
        except Exception as e:
            # Error in table creation guidance

# Global service instance
calendar_service = CalendarService()

# Export functions for backwards compatibility
def insert_calendar(user_id: str, cal_id: str, calendar_type: str, share_link: Optional[str] = None) -> bool:
    return calendar_service.insert_calendar(user_id, cal_id, calendar_type, share_link)

def add_member_to_calendar(user_id: str, calendar_id: str) -> bool:
    return calendar_service.add_member_to_calendar(user_id, calendar_id)

def get_calendars_for_user(user_id: str) -> List[Dict[str, Any]]:
    return calendar_service.get_calendars_for_user(user_id)

def add_event_to_calendar(user_id: str, event: Dict[str, Any], calendar_id: Optional[str] = None) -> bool:
    return calendar_service.add_event_to_calendar(user_id, event, calendar_id)