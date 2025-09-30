"""
Apple Calendar (CalDAV) Synchronization Service
Handles bidirectional sync between Apple Calendar and NotionFlow
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import requests
from requests.auth import HTTPBasicAuth
import xml.etree.ElementTree as ET
from dateutil import parser
import pytz

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../../utils'))
from utils.config import config

# Optional import for sync tracking
try:
    from services.sync_tracking_service import sync_tracker, EventType
    SYNC_TRACKING_AVAILABLE = True
except Exception as e:
    print(f"⚠️ [APPLE SYNC] Sync tracking not available: {e}")
    sync_tracker = None
    EventType = None
    SYNC_TRACKING_AVAILABLE = False

class AppleCalendarSync:
    """Apple Calendar synchronization service using CalDAV protocol"""

    def __init__(self):
        """Initialize Apple Calendar sync service"""
        self.default_server = 'https://caldav.icloud.com'

    def sync_to_calendar(self, user_id: str, calendar_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Sync Apple Calendar events to NotionFlow calendar

        Args:
            user_id: User ID to sync for
            calendar_id: Optional specific calendar ID to sync to

        Returns:
            Dictionary with sync results
        """
        try:
            print(f"🍎 [APPLE SYNC] Starting sync for user {user_id}")

            # Get Apple Calendar credentials
            credentials = self._get_apple_credentials(user_id)
            if not credentials:
                print(f"❌ [APPLE SYNC] No Apple Calendar credentials found")
                return {
                    'success': False,
                    'error': 'Apple Calendar not connected',
                    'synced_events': 0
                }

            # Get or determine calendar ID
            if not calendar_id:
                calendar_id = self._get_sync_calendar_id(user_id)
                if not calendar_id:
                    print(f"❌ [APPLE SYNC] No calendar selected for sync")
                    return {
                        'success': False,
                        'error': 'No calendar selected for Apple sync',
                        'synced_events': 0
                    }
            else:
                # If calendar_id is provided, create/update the active sync record
                self._create_active_sync(user_id, calendar_id)

            print(f"📅 [APPLE SYNC] Using calendar {calendar_id}")

            # Fetch events from Apple Calendar
            apple_events = self._fetch_apple_events(credentials)
            print(f"📥 [APPLE SYNC] Fetched {len(apple_events)} events from Apple Calendar")

            # Sync events to NotionFlow calendar
            synced_count = 0
            for event in apple_events:
                if self._sync_event_to_notionflow(user_id, calendar_id, event):
                    synced_count += 1

            print(f"✅ [APPLE SYNC] Successfully synced {synced_count} events")

            # Track sync event (if available)
            if SYNC_TRACKING_AVAILABLE and sync_tracker and EventType:
                sync_tracker.track_sync_event(
                    user_id=user_id,
                    event_type=EventType.SYNC_SUCCESS,
                    platform='apple',
                    status='success',
                    metadata={
                        'calendar_id': calendar_id,
                        'events_synced': synced_count,
                        'total_events': len(apple_events)
                    }
                )

            return {
                'success': True,
                'synced_events': synced_count,
                'total_events': len(apple_events),
                'calendar_id': calendar_id
            }

        except Exception as e:
            print(f"❌ [APPLE SYNC] Error: {str(e)}")
            if SYNC_TRACKING_AVAILABLE and sync_tracker and EventType:
                sync_tracker.track_sync_event(
                    user_id=user_id,
                    event_type=EventType.SYNC_ERROR,
                    platform='apple',
                    status='error',
                    error=str(e)
                )
            return {
                'success': False,
                'error': str(e),
                'synced_events': 0
            }

    def _get_apple_credentials(self, user_id: str) -> Optional[Dict]:
        """Get Apple Calendar credentials from database"""
        try:
            supabase = config.get_client_for_user(user_id)
            result = supabase.table('calendar_sync_configs').select('*').eq('user_id', user_id).eq('platform', 'apple').eq('is_enabled', True).execute()

            if result.data:
                config_data = result.data[0]
                credentials = config_data.get('credentials', {})

                # Check if we have required credentials
                if credentials.get('username') and credentials.get('password'):
                    return {
                        'server_url': credentials.get('server_url', self.default_server),
                        'username': credentials.get('username'),
                        'password': credentials.get('password'),
                        'calendar_id': credentials.get('calendar_id')
                    }

            return None

        except Exception as e:
            print(f"❌ [APPLE SYNC] Failed to get credentials: {e}")
            return None

    def _get_sync_calendar_id(self, user_id: str) -> Optional[str]:
        """Get the calendar ID configured for Apple sync"""
        try:
            supabase = config.get_client_for_user(user_id)

            # Check active sync configuration
            result = supabase.table('active_syncs').select('*').eq('user_id', user_id).eq('platform', 'apple').eq('sync_status', 'active').execute()

            if result.data:
                return result.data[0].get('calendar_id')

            return None

        except Exception as e:
            print(f"❌ [APPLE SYNC] Failed to get sync calendar: {e}")
            return None

    def _create_active_sync(self, user_id: str, calendar_id: str) -> bool:
        """Create or update active sync record for Apple Calendar"""
        try:
            supabase = config.get_client_for_user(user_id)

            # Check if active sync already exists
            existing_result = supabase.table('active_syncs').select('*').eq('user_id', user_id).eq('platform', 'apple').execute()

            sync_data = {
                'user_id': user_id,
                'platform': 'apple',
                'calendar_id': calendar_id,
                'sync_status': 'active',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }

            if existing_result.data:
                # Update existing sync
                result = supabase.table('active_syncs').update({
                    'calendar_id': calendar_id,
                    'sync_status': 'active',
                    'updated_at': datetime.now().isoformat()
                }).eq('user_id', user_id).eq('platform', 'apple').execute()
                print(f"✅ [APPLE SYNC] Updated active sync for calendar {calendar_id}")
            else:
                # Create new sync
                result = supabase.table('active_syncs').insert(sync_data).execute()
                print(f"✅ [APPLE SYNC] Created active sync for calendar {calendar_id}")

            return bool(result.data)

        except Exception as e:
            print(f"❌ [APPLE SYNC] Failed to create active sync: {e}")
            return False

    def _fetch_apple_events(self, credentials: Dict) -> List[Dict]:
        """Fetch events from Apple Calendar using CalDAV"""
        events = []

        try:
            server_url = credentials['server_url']
            username = credentials['username']
            password = credentials['password']

            # Build CalDAV calendar URL - Apple uses a specific format
            # First, we need to get the principal URL
            principal_url = f"{server_url}/principals/users/{username}/"

            # Then get the calendar home URL (typically the user's default calendar)
            calendar_url = f"{server_url}/{username.split('@')[0]}/calendars/home/"

            # CalDAV REPORT request to get events
            # Get events from last 30 days to next 90 days
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%dT000000Z')
            end_date = (datetime.now() + timedelta(days=90)).strftime('%Y%m%dT235959Z')

            report_body = f'''<?xml version="1.0" encoding="utf-8" ?>
            <C:calendar-query xmlns:C="urn:ietf:params:xml:ns:caldav" xmlns:D="DAV:">
                <D:prop>
                    <D:getetag/>
                    <C:calendar-data/>
                </D:prop>
                <C:filter>
                    <C:comp-filter name="VCALENDAR">
                        <C:comp-filter name="VEVENT">
                            <C:time-range start="{start_date}" end="{end_date}"/>
                        </C:comp-filter>
                    </C:comp-filter>
                </C:filter>
            </C:calendar-query>'''

            headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'Depth': '1'
            }

            print(f"🔍 [APPLE SYNC] Fetching events from {calendar_url}")

            response = requests.request(
                'REPORT',
                calendar_url,
                auth=HTTPBasicAuth(username, password),
                headers=headers,
                data=report_body,
                timeout=30
            )

            if response.status_code in [207, 200]:  # Multi-Status or OK
                # Parse CalDAV XML response
                events = self._parse_caldav_events(response.text)
                print(f"✅ [APPLE SYNC] Parsed {len(events)} events from CalDAV response")
            else:
                print(f"❌ [APPLE SYNC] Failed to fetch events: {response.status_code}")
                print(f"Response: {response.text[:500]}")

        except Exception as e:
            print(f"❌ [APPLE SYNC] Error fetching events: {e}")

        return events

    def _parse_caldav_events(self, xml_response: str) -> List[Dict]:
        """Parse CalDAV XML response to extract events"""
        events = []

        try:
            # Parse XML response
            root = ET.fromstring(xml_response)

            # Find all response elements (each contains an event)
            for response in root.findall('.//{DAV:}response'):
                calendar_data = response.find('.//{urn:ietf:params:xml:ns:caldav}calendar-data')

                if calendar_data is not None and calendar_data.text:
                    # Parse iCalendar data
                    event = self._parse_icalendar_event(calendar_data.text)
                    if event:
                        events.append(event)

        except Exception as e:
            print(f"❌ [APPLE SYNC] Error parsing CalDAV response: {e}")

        return events

    def _parse_icalendar_event(self, ical_text: str) -> Optional[Dict]:
        """Parse iCalendar format event to dictionary"""
        try:
            event = {}
            lines = ical_text.strip().split('\n')

            for line in lines:
                if line.startswith('SUMMARY:'):
                    event['title'] = line.replace('SUMMARY:', '').strip()
                elif line.startswith('DTSTART'):
                    # Parse start time
                    dt_value = line.split(':')[-1].strip()
                    event['start_datetime'] = self._parse_ical_datetime(dt_value)
                elif line.startswith('DTEND'):
                    # Parse end time
                    dt_value = line.split(':')[-1].strip()
                    event['end_datetime'] = self._parse_ical_datetime(dt_value)
                elif line.startswith('DESCRIPTION:'):
                    event['description'] = line.replace('DESCRIPTION:', '').strip()
                elif line.startswith('LOCATION:'):
                    event['location'] = line.replace('LOCATION:', '').strip()
                elif line.startswith('UID:'):
                    event['external_id'] = 'apple_' + line.replace('UID:', '').strip()

            # Only return if we have at least title and start time
            if event.get('title') and event.get('start_datetime'):
                # Set default values
                if not event.get('end_datetime'):
                    # Default to 1 hour duration
                    start_dt = parser.parse(event['start_datetime'])
                    end_dt = start_dt + timedelta(hours=1)
                    event['end_datetime'] = end_dt.isoformat()

                event['platform'] = 'apple'
                event['all_day'] = 'T' not in event['start_datetime']

                return event

        except Exception as e:
            print(f"⚠️ [APPLE SYNC] Error parsing iCalendar event: {e}")

        return None

    def _parse_ical_datetime(self, dt_string: str) -> str:
        """Parse iCalendar datetime format to ISO format"""
        try:
            # Handle different iCal datetime formats
            if 'T' in dt_string:
                # DateTime format (YYYYMMDDTHHmmss or with Z)
                if dt_string.endswith('Z'):
                    dt = datetime.strptime(dt_string, '%Y%m%dT%H%M%SZ')
                    dt = dt.replace(tzinfo=pytz.UTC)
                else:
                    dt = datetime.strptime(dt_string[:15], '%Y%m%dT%H%M%S')
            else:
                # Date only format (YYYYMMDD)
                dt = datetime.strptime(dt_string[:8], '%Y%m%d')

            return dt.isoformat()

        except Exception as e:
            print(f"⚠️ [APPLE SYNC] Error parsing datetime {dt_string}: {e}")
            return datetime.now().isoformat()

    def _sync_event_to_notionflow(self, user_id: str, calendar_id: str, event: Dict) -> bool:
        """Sync a single event to NotionFlow calendar using calendar_events table"""
        try:
            supabase = config.get_client_for_user(user_id)

            # Check if event already exists (using the same schema as Notion)
            external_id = event.get('external_id')
            if external_id:
                existing = supabase.table('calendar_events').select('id').eq(
                    'user_id', user_id
                ).eq('external_id', external_id).eq(
                    'source_platform', 'apple'
                ).execute()

                if existing.data:
                    # Update existing event
                    result = supabase.table('calendar_events').update({
                        'title': event.get('title'),
                        'description': event.get('description', ''),
                        'start_datetime': event.get('start_datetime'),
                        'end_datetime': event.get('end_datetime'),
                        'location': event.get('location', ''),
                        'is_all_day': event.get('all_day', False),
                        'updated_at': datetime.now().isoformat()
                    }).eq('id', existing.data[0]['id']).execute()

                    print(f"✅ [APPLE SYNC] Updated existing event: {event.get('title')}")
                    return bool(result.data)

            # Create new event (following the same schema as Notion)
            event_data = {
                'user_id': user_id,
                'calendar_id': calendar_id,
                'title': event.get('title', 'Untitled Event'),
                'description': event.get('description', ''),
                'start_datetime': event.get('start_datetime'),
                'end_datetime': event.get('end_datetime'),
                'location': event.get('location', ''),
                'is_all_day': event.get('all_day', False),
                'external_id': external_id,
                'source_platform': 'apple',  # Using source_platform instead of platform
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'is_recurring': False,
                'platform_metadata': {
                    'source': 'apple_caldav',
                    'synced_at': datetime.now().isoformat()
                }
            }

            result = supabase.table('calendar_events').insert(event_data).execute()
            print(f"✅ [APPLE SYNC] Created new event: {event.get('title')}")
            return bool(result.data)

        except Exception as e:
            print(f"⚠️ [APPLE SYNC] Failed to sync event: {e}")
            import traceback
            traceback.print_exc()
            return False

# Create singleton instance
apple_calendar_sync = AppleCalendarSync()