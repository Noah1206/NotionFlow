"""
Calendar Sync Service
메인 캘린더 동기화 서비스 - 모든 외부 캘린더 플랫폼과 동기화
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from supabase import create_client
from dotenv import load_dotenv

# Add backend to path for service imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.notion_service import NotionService
from services.google_calendar_service import GoogleCalendarService

load_dotenv()
logger = logging.getLogger(__name__)

class CalendarSyncService:
    """Main calendar synchronization service"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.supabase_url = os.environ.get('SUPABASE_URL')
        self.supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('SUPABASE_API_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise Exception("Supabase credentials not found")
            
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        
        # Initialize service providers
        self.google_service = GoogleCalendarService()
        self.notion_service = None  # Will be initialized with API key
        
    def get_provider(self, platform: str):
        """Get provider for specific platform"""
        if platform == 'google':
            return self.google_service
        elif platform == 'notion':
            # Get Notion access token from sync config
            config = self._get_sync_config(platform)
            if config and config.get('credentials'):
                # Try both api_key and access_token for compatibility
                access_token = config['credentials'].get('access_token') or config['credentials'].get('api_key')
                if access_token:
                    try:
                        self.notion_service = NotionService(access_token)
                        # Test connection to validate token
                        test_result = self.notion_service.test_connection()
                        if test_result.get('success'):
                            return self.notion_service
                        else:
                            logger.warning(f"Notion token validation failed: {test_result.get('error')}")
                    except Exception as e:
                        logger.warning(f"Failed to create Notion service: {e}")
            return None
        else:
            logger.warning(f"Unknown platform: {platform}")
            return None
    
    def _get_sync_config(self, platform: str) -> Optional[Dict]:
        """Get sync configuration for platform"""
        try:
            result = self.supabase.table('calendar_sync_configs').select('*').eq('user_id', self.user_id).eq('platform', platform).single().execute()
            return result.data if result.data else None
        except Exception as e:
            logger.error(f"Error getting sync config: {e}")
            return None
    
    def sync_all_platforms(self, start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """Sync all enabled platforms for user"""
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now() + timedelta(days=90)
            
        results = {}
        
        # Get all enabled sync configs
        try:
            configs = self.supabase.table('calendar_sync_configs').select('platform').eq('user_id', self.user_id).eq('is_enabled', True).execute()
            
            for config in configs.data:
                platform = config['platform']
                provider = self.get_provider(platform)
                
                if provider:
                    result = self._sync_platform(provider, start_date, end_date)
                    results[platform] = result
                else:
                    results[platform] = {'error': 'Provider not available'}
                    
        except Exception as e:
            logger.error(f"Error syncing all platforms: {e}")
            
        return results
    
    def _sync_platform(self, provider: Any, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Sync specific platform"""
        try:
            platform_name = provider.__class__.__name__.replace('Service', '').replace('Provider', '').lower()
            logger.info(f"Starting sync for {platform_name}")
            
            # Get events from platform
            if isinstance(provider, GoogleCalendarService):
                events = self._sync_google_calendar(provider, start_date, end_date)
            elif isinstance(provider, NotionService):
                events = self._sync_notion(provider, start_date, end_date)
            else:
                return {'error': 'Unknown provider type'}
            
            # Save events to database
            created = 0
            updated = 0
            failed = 0
            
            for event in events:
                result = self._save_event_to_db(event, platform_name)
                if result == 'created':
                    created += 1
                elif result == 'updated':
                    updated += 1
                else:
                    failed += 1
            
            logger.info(f"Sync completed for {platform_name}: {created} created, {updated} updated, {failed} failed")
            
            return {
                'success': True,
                'total_events': len(events),
                'created': created,
                'updated': updated,
                'failed': failed
            }
            
        except Exception as e:
            logger.error(f"Error syncing platform: {e}")
            return {'error': str(e)}
    
    def _sync_google_calendar(self, provider: GoogleCalendarService, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Sync Google Calendar events"""
        events = []
        
        try:
            # Get all Google calendars
            calendars = provider.get_calendar_list(self.user_id)
            
            for calendar in calendars:
                calendar_id = calendar.get('id', 'primary')
                calendar_name = calendar.get('name', 'Google Calendar')
                
                # Get events from this calendar
                google_events = provider.get_events(
                    user_id=self.user_id,
                    calendar_id=calendar_id,
                    time_min=start_date,
                    time_max=end_date
                )
                
                # Convert Google events to our format
                for event in google_events:
                    formatted_event = self._format_google_event(event, calendar_id, calendar_name)
                    if formatted_event:
                        events.append(formatted_event)
                        
        except Exception as e:
            logger.error(f"Error syncing Google Calendar: {e}")
            
        return events
    
    def _sync_notion(self, provider: NotionService, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Sync Notion calendar events"""
        events = []
        
        try:
            # Test connection first to avoid invalid token errors
            connection_test = provider.test_connection()
            if not connection_test.get('success'):
                logger.warning(f"Notion connection test failed: {connection_test.get('error')}")
                return events
            
            # Get Notion databases (calendars)
            databases = provider.get_databases()
            
            for database in databases:
                database_id = database.get('id')
                database_name = database.get('title', [{}])[0].get('plain_text', 'Notion Calendar')
                
                # Query database for events
                # Note: This is a simplified version - actual implementation would need proper filtering
                try:
                    # First, try to get database schema to find date properties
                    try:
                        db_schema = provider.client.databases.retrieve(database_id=database_id)
                        properties = db_schema.get('properties', {})
                        
                        # Find date property dynamically
                        date_prop_name = None
                        for prop_name, prop_info in properties.items():
                            if prop_info.get('type') == 'date':
                                date_prop_name = prop_name
                                break
                        
                        # If we found a date property, use it for filtering
                        if date_prop_name:
                            response = provider.client.databases.query(
                                database_id=database_id,
                                filter={
                                    "and": [
                                        {
                                            "property": date_prop_name,
                                            "date": {
                                                "after": start_date.isoformat()
                                            }
                                        },
                                        {
                                            "property": date_prop_name,
                                            "date": {
                                                "before": end_date.isoformat()
                                            }
                                        }
                                    ]
                                }
                            )
                        else:
                            # No date property found, query without filter
                            response = provider.client.databases.query(
                                database_id=database_id
                            )
                    except Exception as schema_error:
                        # If schema check fails, query without filter
                        logger.warning(f"Could not get schema for database {database_id}: {schema_error}")
                        response = provider.client.databases.query(
                            database_id=database_id
                        )
                    
                    # Convert Notion pages to events
                    for page in response.get('results', []):
                        formatted_event = self._format_notion_event(page, database_id, database_name)
                        if formatted_event:
                            events.append(formatted_event)
                            
                except Exception as db_error:
                    logger.warning(f"Could not query database {database_id}: {db_error}")
                    
        except Exception as e:
            logger.error(f"Error syncing Notion: {e}")
            
        return events
    
    def _format_google_event(self, event: Dict, calendar_id: str, calendar_name: str) -> Optional[Dict]:
        """Format Google Calendar event for database"""
        try:
            # Extract start and end times
            start = event.get('start', {})
            end = event.get('end', {})
            
            # Handle all-day events vs timed events
            if 'dateTime' in start:
                start_datetime = start['dateTime']
                end_datetime = end['dateTime']
                is_all_day = False
            elif 'date' in start:
                start_datetime = f"{start['date']}T00:00:00Z"
                end_datetime = f"{end['date']}T23:59:59Z"
                is_all_day = True
            else:
                return None
            
            return {
                'user_id': self.user_id,
                'external_id': event.get('id'),
                'title': event.get('summary', 'Untitled Event'),
                'description': event.get('description', ''),
                'start_datetime': start_datetime,
                'end_datetime': end_datetime,
                'is_all_day': is_all_day,
                'location': event.get('location', ''),
                'source_platform': 'google',
                'source_calendar_id': calendar_id,
                'source_calendar_name': calendar_name,
                'status': event.get('status', 'confirmed'),
                'attendees': [attendee.get('email') for attendee in event.get('attendees', [])],
                'created_at': event.get('created', datetime.now().isoformat()),
                'updated_at': event.get('updated', datetime.now().isoformat())
            }
            
        except Exception as e:
            logger.error(f"Error formatting Google event: {e}")
            return None
    
    def _format_notion_event(self, page: Dict, database_id: str, database_name: str) -> Optional[Dict]:
        """Format Notion page as calendar event"""
        try:
            properties = page.get('properties', {})
            
            # Extract title (usually from Name or Title property)
            title = None
            for prop_name in ['Name', 'Title', '이름', '제목']:
                if prop_name in properties:
                    title_prop = properties[prop_name]
                    if title_prop.get('type') == 'title':
                        title = title_prop.get('title', [{}])[0].get('plain_text', 'Untitled')
                        break
            
            if not title:
                title = 'Untitled Event'
            
            # Extract date - try common names first, then find any date property
            date_prop = None
            date_prop_names = ['Date', '날짜', 'Due', 'When', '일정', 'Start', 'End', '시작', '종료', 'Deadline']
            
            # Try common date property names
            for prop_name in date_prop_names:
                if prop_name in properties and properties[prop_name].get('type') == 'date':
                    date_prop = properties[prop_name]
                    break
            
            # If not found, look for any date type property
            if not date_prop:
                for prop_name, prop_data in properties.items():
                    if prop_data.get('type') == 'date':
                        date_prop = prop_data
                        break
            
            if not date_prop:
                return None
                
            date_info = date_prop.get('date', {})
            if not date_info:
                return None
            
            start_date = date_info.get('start')
            end_date = date_info.get('end') or start_date
            
            # Check if it's all-day or has time
            is_all_day = 'T' not in start_date
            
            if is_all_day:
                start_datetime = f"{start_date}T00:00:00Z"
                end_datetime = f"{end_date}T23:59:59Z"
            else:
                start_datetime = start_date
                end_datetime = end_date
            
            # Extract description from rich text properties
            description = ''
            for prop_name in ['Description', 'Notes', '설명', '메모']:
                if prop_name in properties:
                    desc_prop = properties[prop_name]
                    if desc_prop.get('type') == 'rich_text':
                        texts = desc_prop.get('rich_text', [])
                        description = ' '.join([t.get('plain_text', '') for t in texts])
                        break
            
            return {
                'user_id': self.user_id,
                'external_id': page.get('id'),
                'title': title,
                'description': description,
                'start_datetime': start_datetime,
                'end_datetime': end_datetime,
                'is_all_day': is_all_day,
                'source_platform': 'notion',
                'source_calendar_id': database_id,
                'source_calendar_name': database_name,
                'status': 'confirmed',
                'created_at': page.get('created_time', datetime.now().isoformat()),
                'updated_at': page.get('last_edited_time', datetime.now().isoformat())
            }
            
        except Exception as e:
            logger.error(f"Error formatting Notion event: {e}")
            return None
    
    def _save_event_to_db(self, event: Dict, platform: str) -> str:
        """Save or update event in database"""
        try:
            # Check if event already exists
            existing = self.supabase.table('calendar_events').select('id').eq('user_id', self.user_id).eq('external_id', event['external_id']).eq('source_platform', platform).execute()
            
            if existing.data:
                # Update existing event
                result = self.supabase.table('calendar_events').update(event).eq('id', existing.data[0]['id']).execute()
                return 'updated' if result.data else 'failed'
            else:
                # Create new event
                result = self.supabase.table('calendar_events').insert(event).execute()
                return 'created' if result.data else 'failed'
                
        except Exception as e:
            logger.error(f"Error saving event to database: {e}")
            return 'failed'