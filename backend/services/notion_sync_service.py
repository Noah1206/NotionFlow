"""
Enhanced Notion Sync Service for NotionFlow
Syncs Notion calendar databases with NotionFlow calendars
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from notion_client import Client as NotionClient
from supabase import create_client
import json

logger = logging.getLogger(__name__)

class NotionSyncService:
    """Service for syncing Notion calendar events with NotionFlow"""
    
    def __init__(self):
        """Initialize Notion sync service"""
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_API_KEY')
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        
    def get_user_notion_token(self, user_id: str) -> Optional[str]:
        """Get Notion OAuth token for user"""
        try:
            # Check oauth_tokens table for Notion token
            result = self.supabase.table('oauth_tokens').select('*').eq(
                'user_id', user_id
            ).eq('platform', 'notion').execute()
            
            if result.data:
                return result.data[0].get('access_token')
            
            # Fallback to calendar_sync_configs
            config_result = self.supabase.table('calendar_sync_configs').select('*').eq(
                'user_id', user_id
            ).eq('platform', 'notion').execute()
            
            if config_result.data and config_result.data[0].get('credentials'):
                creds = config_result.data[0]['credentials']
                if isinstance(creds, dict):
                    return creds.get('access_token') or creds.get('api_key')
                    
            return None
            
        except Exception as e:
            logger.error(f"Error getting Notion token: {e}")
            return None
    
    def sync_notion_to_calendar(self, user_id: str, calendar_id: str) -> Dict[str, Any]:
        """Sync Notion database events to NotionFlow calendar"""
        try:
            # Get Notion token
            token = self.get_user_notion_token(user_id)
            if not token:
                return {
                    'success': False,
                    'error': 'No Notion token found for user'
                }
            
            # Initialize Notion client
            notion = NotionClient(auth=token)
            
            # Find calendar databases in Notion
            databases = self._find_calendar_databases(notion)
            
            if not databases:
                return {
                    'success': False,
                    'error': 'No calendar databases found in Notion'
                }
            
            sync_results = {
                'synced_events': 0,
                'failed_events': 0,
                'databases_processed': len(databases)
            }
            
            # Process each database
            for db in databases:
                db_id = db['id']
                db_name = self._get_database_title(db)
                logger.info(f"Processing Notion database: {db_name}")
                
                # Query database for events
                events = self._get_database_events(notion, db_id)
                
                for event in events:
                    try:
                        # Convert Notion page to calendar event
                        calendar_event = self._notion_to_calendar_event(event, calendar_id, user_id)
                        
                        if calendar_event:
                            # Check if event already exists (by external_id)
                            existing = self._get_existing_event(calendar_event['external_id'], calendar_id)
                            
                            if existing:
                                # Update existing event
                                self._update_calendar_event(existing['id'], calendar_event)
                            else:
                                # Create new event
                                self._create_calendar_event(calendar_event)
                            
                            sync_results['synced_events'] += 1
                            
                            # Update event_sync_mapping
                            self._update_sync_mapping(
                                event_id=existing['id'] if existing else calendar_event.get('id'),
                                platform='notion',
                                external_id=calendar_event['external_id'],
                                user_id=user_id
                            )
                    
                    except Exception as e:
                        logger.error(f"Error syncing event: {e}")
                        sync_results['failed_events'] += 1
            
            # Update sync status
            self._update_sync_status(user_id, 'notion', 'success', sync_results)
            
            return {
                'success': True,
                'results': sync_results
            }
            
        except Exception as e:
            logger.error(f"Notion sync failed: {e}")
            self._update_sync_status(user_id, 'notion', 'failed', {'error': str(e)})
            return {
                'success': False,
                'error': str(e)
            }
    
    def _find_calendar_databases(self, notion: NotionClient) -> List[Dict]:
        """Find calendar-related databases in Notion"""
        try:
            # Search for databases
            response = notion.search(
                filter={"property": "object", "value": "database"}
            )
            
            databases = []
            for db in response.get('results', []):
                title = self._get_database_title(db)
                # Check if database name contains calendar-related keywords
                calendar_keywords = ['calendar', 'schedule', 'event', 'task', '일정', '캘린더', '스케줄']
                if any(keyword in title.lower() for keyword in calendar_keywords):
                    databases.append(db)
                    
                # Also check database properties for date fields
                elif self._has_date_properties(db):
                    databases.append(db)
            
            return databases
            
        except Exception as e:
            logger.error(f"Error finding databases: {e}")
            return []
    
    def _get_database_title(self, database: Dict) -> str:
        """Extract database title"""
        try:
            if 'title' in database:
                if isinstance(database['title'], list) and database['title']:
                    return database['title'][0].get('plain_text', 'Untitled')
            return 'Untitled Database'
        except:
            return 'Untitled Database'
    
    def _has_date_properties(self, database: Dict) -> bool:
        """Check if database has date properties"""
        try:
            properties = database.get('properties', {})
            for prop_name, prop_data in properties.items():
                if prop_data.get('type') == 'date':
                    return True
            return False
        except:
            return False
    
    def _get_database_events(self, notion: NotionClient, database_id: str) -> List[Dict]:
        """Query database for events/tasks"""
        try:
            # Query all pages from database
            response = notion.databases.query(
                database_id=database_id,
                filter={
                    "or": [
                        {"property": "Status", "select": {"does_not_equal": "Cancelled"}},
                        {"property": "상태", "select": {"does_not_equal": "취소"}},
                        {"property": "Done", "checkbox": {"equals": False}}
                    ]
                }
            )
            
            return response.get('results', [])
            
        except Exception as e:
            logger.error(f"Error querying database: {e}")
            # Try without filter if it fails
            try:
                response = notion.databases.query(database_id=database_id)
                return response.get('results', [])
            except:
                return []
    
    def _notion_to_calendar_event(self, notion_page: Dict, calendar_id: str, user_id: str) -> Optional[Dict]:
        """Convert Notion page to calendar event format"""
        try:
            properties = notion_page.get('properties', {})
            
            # Extract title
            title = self._extract_title(properties)
            if not title:
                title = "Untitled Event"
            
            # Extract dates
            date_info = self._extract_dates(properties)
            if not date_info:
                return None  # Skip if no date found
            
            # Extract description
            description = self._extract_description(properties)
            
            # Create calendar event
            event = {
                'calendar_id': calendar_id,
                'user_id': user_id,
                'title': title,
                'description': description,
                'start_date': date_info['start'],
                'end_date': date_info['end'],
                'all_day': date_info.get('all_day', False),
                'external_id': f"notion_{notion_page['id']}",
                'external_platform': 'notion',
                'metadata': {
                    'notion_page_id': notion_page['id'],
                    'notion_url': notion_page.get('url', ''),
                    'last_edited': notion_page.get('last_edited_time', '')
                }
            }
            
            return event
            
        except Exception as e:
            logger.error(f"Error converting Notion page: {e}")
            return None
    
    def _extract_title(self, properties: Dict) -> str:
        """Extract title from Notion properties"""
        # Common title property names
        title_keys = ['Name', 'Title', '제목', 'Task', '작업', 'Event', '이벤트']
        
        for key in title_keys:
            if key in properties:
                prop = properties[key]
                if prop['type'] == 'title' and prop.get('title'):
                    return prop['title'][0].get('plain_text', '')
                elif prop['type'] == 'rich_text' and prop.get('rich_text'):
                    return prop['rich_text'][0].get('plain_text', '')
        
        # Fallback: use first title property
        for prop_name, prop_data in properties.items():
            if prop_data['type'] == 'title' and prop_data.get('title'):
                return prop_data['title'][0].get('plain_text', '')
                
        return ""
    
    def _extract_dates(self, properties: Dict) -> Optional[Dict]:
        """Extract date information from Notion properties"""
        # Common date property names
        date_keys = ['Date', 'Due', 'When', '날짜', '일정', 'Start', 'End', '시작', '종료']
        
        for key in date_keys:
            if key in properties and properties[key]['type'] == 'date':
                date_prop = properties[key].get('date')
                if date_prop:
                    start = date_prop.get('start')
                    end = date_prop.get('end') or start
                    
                    if start:
                        # Check if it's all-day event (no time component)
                        all_day = 'T' not in start
                        
                        return {
                            'start': start,
                            'end': end,
                            'all_day': all_day
                        }
        
        return None
    
    def _extract_description(self, properties: Dict) -> str:
        """Extract description from Notion properties"""
        # Common description property names
        desc_keys = ['Description', 'Notes', '설명', '메모', 'Details', '상세']
        
        for key in desc_keys:
            if key in properties:
                prop = properties[key]
                if prop['type'] == 'rich_text' and prop.get('rich_text'):
                    texts = [t.get('plain_text', '') for t in prop['rich_text']]
                    return ' '.join(texts)
        
        return ""
    
    def _get_existing_event(self, external_id: str, calendar_id: str) -> Optional[Dict]:
        """Check if event already exists in calendar"""
        try:
            result = self.supabase.table('calendar_events').select('*').eq(
                'external_id', external_id
            ).eq('calendar_id', calendar_id).execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"Error checking existing event: {e}")
            return None
    
    def _create_calendar_event(self, event: Dict) -> Optional[str]:
        """Create new calendar event"""
        try:
            result = self.supabase.table('calendar_events').insert(event).execute()
            if result.data:
                return result.data[0]['id']
            return None
            
        except Exception as e:
            logger.error(f"Error creating event: {e}")
            return None
    
    def _update_calendar_event(self, event_id: str, event_data: Dict) -> bool:
        """Update existing calendar event"""
        try:
            # Remove fields that shouldn't be updated
            update_data = {k: v for k, v in event_data.items() 
                          if k not in ['id', 'created_at', 'user_id', 'calendar_id']}
            
            result = self.supabase.table('calendar_events').update(
                update_data
            ).eq('id', event_id).execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error updating event: {e}")
            return False
    
    def _update_sync_mapping(self, event_id: str, platform: str, external_id: str, user_id: str):
        """Update event sync mapping table"""
        try:
            # Upsert sync mapping
            self.supabase.table('event_sync_mapping').upsert({
                'event_id': event_id,
                'platform': platform,
                'external_id': external_id,
                'user_id': user_id,
                'last_synced_at': datetime.now(timezone.utc).isoformat()
            }).execute()
            
        except Exception as e:
            logger.error(f"Error updating sync mapping: {e}")
    
    def _update_sync_status(self, user_id: str, platform: str, status: str, details: Dict):
        """Update sync status in database"""
        try:
            # Update sync_status table
            self.supabase.table('sync_status').upsert({
                'user_id': user_id,
                'platform': platform,
                'status': status,
                'last_sync_at': datetime.now(timezone.utc).isoformat(),
                'details': details
            }).execute()
            
            # Update calendar_sync_configs
            self.supabase.table('calendar_sync_configs').update({
                'last_sync_at': datetime.now(timezone.utc).isoformat(),
                'health_status': 'healthy' if status == 'success' else 'error'
            }).eq('user_id', user_id).eq('platform', platform).execute()
            
        except Exception as e:
            logger.error(f"Error updating sync status: {e}")


# Singleton instance
notion_sync_service = NotionSyncService()