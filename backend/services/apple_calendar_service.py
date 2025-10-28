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

    def sync_to_calendar(self, user_id: str, calendar_id: Optional[str] = None, date_range: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
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
            apple_events = self._fetch_apple_events(credentials, date_range)
            print(f"📥 [APPLE SYNC] Fetched {len(apple_events)} events from Apple Calendar")

            # Sync events to NotionFlow calendar using batch processing
            synced_count = self._sync_events_batch_apple(apple_events, user_id, calendar_id)

            print(f"✅ [APPLE SYNC] Successfully synced {synced_count} events")

            # Track sync event (if available)
            if SYNC_TRACKING_AVAILABLE and sync_tracker and EventType:
                try:
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
                except Exception as tracking_error:
                    print(f"⚠️ [APPLE SYNC] Sync tracking failed: {tracking_error}")

            return {
                'success': True,
                'synced_events': synced_count,
                'total_events': len(apple_events),
                'calendar_id': calendar_id
            }

        except Exception as e:
            print(f"❌ [APPLE SYNC] Error: {str(e)}")
            if SYNC_TRACKING_AVAILABLE and sync_tracker and EventType:
                try:
                    sync_tracker.track_sync_event(
                        user_id=user_id,
                        event_type=EventType.SYNC_ERROR,
                        platform='apple',
                        status='error',
                        error=str(e)
                    )
                except Exception as tracking_error:
                    print(f"⚠️ [APPLE SYNC] Error tracking failed: {tracking_error}")
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

            # Check if active_syncs table exists
            try:
                existing_result = supabase.table('active_syncs').select('*').eq('user_id', user_id).eq('platform', 'apple').execute()
            except Exception as table_error:
                if 'does not exist' in str(table_error):
                    print(f"⚠️ [APPLE SYNC] active_syncs table does not exist, using calendar_sync_configs instead")
                    # Fallback to using calendar_sync_configs table
                    try:
                        # Update the existing config to include calendar selection using credentials field
                        existing_config = supabase.table('calendar_sync_configs').select('*').eq('user_id', user_id).eq('platform', 'apple').execute()
                        if existing_config.data:
                            current_credentials = existing_config.data[0].get('credentials', {})
                            # Add calendar_id to credentials
                            current_credentials['selected_calendar_id'] = calendar_id

                            result = supabase.table('calendar_sync_configs').update({
                                'credentials': current_credentials,
                                'is_enabled': True,
                                'updated_at': datetime.now().isoformat()
                            }).eq('user_id', user_id).eq('platform', 'apple').execute()
                            print(f"✅ [APPLE SYNC] Updated calendar selection in sync config for calendar {calendar_id}")
                            return bool(result.data)
                        else:
                            print(f"⚠️ [APPLE SYNC] No existing sync config found")
                            return False
                    except Exception as fallback_error:
                        print(f"❌ [APPLE SYNC] Failed to update sync config: {fallback_error}")
                        return False
                else:
                    raise table_error

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

    def _fetch_apple_events(self, credentials: Dict, date_range: Optional[Dict[str, str]] = None) -> List[Dict]:
        """Fetch events from Apple Calendar using CalDAV with optional date range filtering"""
        events = []

        try:
            server_url = credentials['server_url']
            username = credentials['username']
            password = credentials['password']

            # Build CalDAV calendar URL - Apple uses a specific format
            # For iCloud, we need to discover the correct calendar URLs first
            if 'icloud.com' in server_url:
                # First, discover the user's calendar home
                principal_url = f"{server_url}/principals/"

                # Make a PROPFIND request to discover calendar home
                propfind_body = '''<?xml version="1.0" encoding="utf-8" ?>
                <D:propfind xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:caldav">
                    <D:prop>
                        <C:calendar-home-set/>
                    </D:prop>
                </D:propfind>'''

                headers = {
                    'Content-Type': 'text/xml; charset=utf-8',
                    'Depth': '0'
                }

                print(f"🔍 [APPLE SYNC] Discovering calendar home from {principal_url}")

                discovery_response = requests.request(
                    'PROPFIND',
                    principal_url,
                    auth=HTTPBasicAuth(username, password),
                    headers=headers,
                    data=propfind_body,
                    timeout=30
                )

                if discovery_response.status_code in [207, 200]:
                    # Try to extract calendar home from response
                    try:
                        import xml.etree.ElementTree as ET
                        root = ET.fromstring(discovery_response.text)
                        calendar_home_elements = root.findall('.//{urn:ietf:params:xml:ns:caldav}calendar-home-set/{DAV:}href')

                        if calendar_home_elements:
                            calendar_home = calendar_home_elements[0].text
                            if calendar_home.startswith('/'):
                                calendar_url = f"{server_url}{calendar_home}"
                            else:
                                calendar_url = calendar_home
                            print(f"✅ [APPLE SYNC] Discovered calendar home: {calendar_url}")
                        else:
                            # Fallback to common iCloud structure
                            calendar_url = f"{server_url}/{username.split('@')[0]}/calendars/"
                            print(f"⚠️ [APPLE SYNC] Using fallback calendar URL: {calendar_url}")
                    except Exception as parse_error:
                        # Fallback to common iCloud structure
                        calendar_url = f"{server_url}/{username.split('@')[0]}/calendars/"
                        print(f"⚠️ [APPLE SYNC] Calendar discovery parsing failed, using fallback: {calendar_url}")
                else:
                    # Fallback to common iCloud structure
                    calendar_url = f"{server_url}/{username.split('@')[0]}/calendars/"
                    print(f"⚠️ [APPLE SYNC] Calendar discovery failed ({discovery_response.status_code}), using fallback: {calendar_url}")
            else:
                # Generic CalDAV structure
                principal_url = f"{server_url}/principals/users/{username}/"
                calendar_url = f"{server_url}/{username.split('@')[0]}/calendars/home/"

            # CalDAV REPORT request to get events
            # Set date range for event fetching
            if date_range and date_range.get('start_date') and date_range.get('end_date'):
                # Parse user-provided date range
                start_dt = datetime.strptime(date_range['start_date'], '%Y-%m-%d')
                end_dt = datetime.strptime(date_range['end_date'], '%Y-%m-%d')
                start_date = start_dt.strftime('%Y%m%dT000000Z')
                end_date = end_dt.strftime('%Y%m%dT235959Z')
                print(f"📅 [APPLE SYNC] Using user-specified date range: {date_range['start_date']} to {date_range['end_date']}")
            else:
                # Default: Get events from last 30 days to next 90 days
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%dT000000Z')
                end_date = (datetime.now() + timedelta(days=90)).strftime('%Y%m%dT235959Z')
                print(f"📅 [APPLE SYNC] Using default date range: last 30 days to next 90 days")

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

            # For iCloud, we need to discover individual calendars first
            if 'icloud.com' in server_url:
                print(f"🔍 [APPLE SYNC] Discovering individual calendars from {calendar_url}")

                # PROPFIND to discover calendars
                calendar_propfind_body = '''<?xml version="1.0" encoding="utf-8" ?>
                <D:propfind xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:caldav">
                    <D:prop>
                        <D:resourcetype/>
                        <D:displayname/>
                        <C:supported-calendar-component-set/>
                    </D:prop>
                </D:propfind>'''

                calendar_discovery_response = requests.request(
                    'PROPFIND',
                    calendar_url,
                    auth=HTTPBasicAuth(username, password),
                    headers={'Content-Type': 'text/xml; charset=utf-8', 'Depth': '1'},
                    data=calendar_propfind_body,
                    timeout=30
                )

                if calendar_discovery_response.status_code in [207, 200]:
                    # Parse to find individual calendar URLs
                    try:
                        import xml.etree.ElementTree as ET
                        root = ET.fromstring(calendar_discovery_response.text)

                        calendar_urls = []
                        print(f"🔍 [APPLE SYNC] Parsing calendar discovery response...")

                        all_responses = root.findall('.//{DAV:}response')
                        print(f"🔍 [APPLE SYNC] Found {len(all_responses)} response elements")

                        for i, response_elem in enumerate(all_responses):
                            href_elem = response_elem.find('.//{DAV:}href')
                            resourcetype_elem = response_elem.find('.//{DAV:}resourcetype')
                            displayname_elem = response_elem.find('.//{DAV:}displayname')

                            href_text = href_elem.text if href_elem is not None else "None"
                            display_name = displayname_elem.text if displayname_elem is not None else "No name"

                            print(f"📋 [APPLE SYNC] Response {i+1}: href='{href_text}', name='{display_name}'")

                            if href_elem is not None and resourcetype_elem is not None:
                                # Check if it's a calendar resource
                                calendar_elem = resourcetype_elem.find('.//{urn:ietf:params:xml:ns:caldav}calendar')
                                if calendar_elem is not None:
                                    href = href_elem.text
                                    if href and not href.endswith('/'):
                                        href += '/'

                                    if href.startswith('/'):
                                        full_url = f"https://p25-caldav.icloud.com:443{href}"
                                    else:
                                        full_url = href

                                    calendar_urls.append(full_url)
                                    print(f"📅 [APPLE SYNC] Found calendar: {full_url} (Name: {display_name})")
                                else:
                                    print(f"⚠️ [APPLE SYNC] Not a calendar: {href_text}")
                            else:
                                print(f"⚠️ [APPLE SYNC] Missing href or resourcetype in response {i+1}")

                        print(f"📊 [APPLE SYNC] Total calendars discovered: {len(calendar_urls)}")

                        # Try to fetch events from each calendar
                        all_events = []
                        for cal_url in calendar_urls[:3]:  # Limit to first 3 calendars
                            print(f"🔍 [APPLE SYNC] Fetching events from calendar: {cal_url}")

                            response = requests.request(
                                'REPORT',
                                cal_url,
                                auth=HTTPBasicAuth(username, password),
                                headers=headers,
                                data=report_body,
                                timeout=30
                            )

                            if response.status_code in [207, 200]:
                                cal_events = self._parse_caldav_events(response.text)
                                all_events.extend(cal_events)
                                print(f"✅ [APPLE SYNC] Found {len(cal_events)} events in calendar")
                            else:
                                print(f"⚠️ [APPLE SYNC] Calendar {cal_url} returned {response.status_code}")

                        events = all_events
                        print(f"✅ [APPLE SYNC] Total events found: {len(events)}")

                    except Exception as parse_error:
                        print(f"❌ [APPLE SYNC] Failed to parse calendar discovery: {parse_error}")
                        events = []
                else:
                    print(f"❌ [APPLE SYNC] Calendar discovery failed: {calendar_discovery_response.status_code}")
                    events = []
            else:
                # For non-iCloud servers, try direct access
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
                    events = []

        except Exception as e:
            print(f"❌ [APPLE SYNC] Error fetching events: {e}")

        return events

    def _parse_caldav_events(self, xml_response: str) -> List[Dict]:
        """Parse CalDAV XML response to extract events"""
        events = []
        print(f"📥 [APPLE SYNC] Starting to parse CalDAV XML response ({len(xml_response)} chars)")

        try:
            # Parse XML response
            root = ET.fromstring(xml_response)
            print(f"✅ [APPLE SYNC] Successfully parsed XML root element")

            # Find all response elements (each contains an event)
            response_elements = root.findall('.//{DAV:}response')
            print(f"🔍 [APPLE SYNC] Found {len(response_elements)} response elements in CalDAV XML")

            for i, response in enumerate(response_elements):
                print(f"📋 [APPLE SYNC] Processing response element {i+1}/{len(response_elements)}")

                calendar_data = response.find('.//{urn:ietf:params:xml:ns:caldav}calendar-data')

                if calendar_data is not None:
                    if calendar_data.text:
                        print(f"📅 [APPLE SYNC] Found calendar-data in response {i+1} ({len(calendar_data.text)} chars)")
                        # Parse iCalendar data
                        event = self._parse_icalendar_event(calendar_data.text)
                        if event:
                            events.append(event)
                            print(f"✅ [APPLE SYNC] Successfully parsed event: '{event.get('title', 'No title')}'")
                        else:
                            print(f"⚠️ [APPLE SYNC] Failed to parse iCalendar event in response {i+1}")
                    else:
                        print(f"⚠️ [APPLE SYNC] Empty calendar-data text in response {i+1}")
                else:
                    print(f"⚠️ [APPLE SYNC] No calendar-data element found in response {i+1}")
                    # Let's check what's actually in this response
                    href_elem = response.find('.//{DAV:}href')
                    href_text = href_elem.text if href_elem is not None else "No href"
                    print(f"🔍 [APPLE SYNC] Response {i+1} href: {href_text}")

            print(f"📊 [APPLE SYNC] Finished parsing: {len(events)} valid events extracted")

        except Exception as e:
            print(f"❌ [APPLE SYNC] Error parsing CalDAV response: {e}")
            print(f"📋 [APPLE SYNC] XML response preview: {xml_response[:500]}...")

        return events

    def _parse_icalendar_event(self, ical_text: str) -> Optional[Dict]:
        """Parse iCalendar format event to dictionary"""
        print(f"📅 [APPLE SYNC] Parsing iCalendar event ({len(ical_text)} chars)")
        print(f"📋 [APPLE SYNC] iCal preview: {ical_text[:200]}...")

        try:
            event = {}
            lines = ical_text.strip().split('\n')
            print(f"🔍 [APPLE SYNC] Processing {len(lines)} lines in iCalendar data")

            vevent_started = False
            for i, line in enumerate(lines):
                line = line.strip()

                # Check if we're in a VEVENT block
                if line == 'BEGIN:VEVENT':
                    vevent_started = True
                    print(f"📍 [APPLE SYNC] Found VEVENT start at line {i+1}")
                    continue
                elif line == 'END:VEVENT':
                    print(f"📍 [APPLE SYNC] Found VEVENT end at line {i+1}")
                    break

                if not vevent_started:
                    continue

                if line.startswith('SUMMARY:'):
                    event['title'] = line.replace('SUMMARY:', '').strip()
                    print(f"📝 [APPLE SYNC] Found title: '{event['title']}'")
                elif line.startswith('DTSTART'):
                    # Parse start time
                    dt_value = line.split(':')[-1].strip()
                    event['start_datetime'] = self._parse_ical_datetime(dt_value)
                    print(f"⏰ [APPLE SYNC] Found start time: {event['start_datetime']}")
                elif line.startswith('DTEND'):
                    # Parse end time
                    dt_value = line.split(':')[-1].strip()
                    event['end_datetime'] = self._parse_ical_datetime(dt_value)
                    print(f"⏰ [APPLE SYNC] Found end time: {event['end_datetime']}")
                elif line.startswith('DESCRIPTION:'):
                    event['description'] = line.replace('DESCRIPTION:', '').strip()
                    print(f"📖 [APPLE SYNC] Found description: '{event['description'][:50]}...'")
                elif line.startswith('LOCATION:'):
                    event['location'] = line.replace('LOCATION:', '').strip()
                    print(f"📍 [APPLE SYNC] Found location: '{event['location']}'")
                elif line.startswith('UID:'):
                    event['external_id'] = 'apple_' + line.replace('UID:', '').strip()
                    print(f"🆔 [APPLE SYNC] Found UID: {event['external_id']}")

            print(f"📊 [APPLE SYNC] Extracted fields: {list(event.keys())}")

            # Only return if we have at least title and start time
            if event.get('title') and event.get('start_datetime'):
                print(f"✅ [APPLE SYNC] Event validation passed: has title and start time")

                # Set default values
                if not event.get('end_datetime'):
                    # Default to 1 hour duration
                    start_dt = parser.parse(event['start_datetime'])
                    end_dt = start_dt + timedelta(hours=1)
                    event['end_datetime'] = end_dt.isoformat()
                    print(f"⏰ [APPLE SYNC] Set default end time: {event['end_datetime']}")

                event['platform'] = 'apple'
                event['all_day'] = 'T' not in event['start_datetime']
                print(f"📋 [APPLE SYNC] Final event: title='{event['title']}', all_day={event['all_day']}")

                return event
            else:
                print(f"❌ [APPLE SYNC] Event validation failed: title={bool(event.get('title'))}, start_datetime={bool(event.get('start_datetime'))}")
                if not event.get('title'):
                    print(f"⚠️ [APPLE SYNC] Missing SUMMARY field")
                if not event.get('start_datetime'):
                    print(f"⚠️ [APPLE SYNC] Missing DTSTART field")

        except Exception as e:
            print(f"❌ [APPLE SYNC] Error parsing iCalendar event: {e}")
            print(f"📋 [APPLE SYNC] Failed iCal data: {ical_text}")

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

            # Create new event (following the same schema as Google Calendar)
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
                'source_platform': 'apple',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }

            result = supabase.table('calendar_events').insert(event_data).execute()
            print(f"✅ [APPLE SYNC] Created new event: {event.get('title')}")
            return bool(result.data)

        except Exception as e:
            print(f"⚠️ [APPLE SYNC] Failed to sync event: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _sync_events_batch_apple(self, events: List[Dict], user_id: str, calendar_id: str) -> int:
        """Apple Calendar 이벤트들을 배치로 처리하여 중복 에러 방지"""
        if not events:
            return 0

        try:
            print(f"💾 [APPLE BATCH] Processing {len(events)} Apple Calendar events")

            # 1. 기존 이벤트들의 external_id 조회 (한 번의 쿼리로)
            event_ids = [event.get('external_id') for event in events if event.get('external_id')]
            if not event_ids:
                return 0

            supabase = config.get_client_for_user(user_id)
            existing_result = supabase.table('calendar_events').select('external_id').eq(
                'user_id', user_id
            ).eq('source_platform', 'apple').in_('external_id', event_ids).execute()

            existing_external_ids = set()
            if existing_result and existing_result.data:
                existing_external_ids = {item['external_id'] for item in existing_result.data}

            print(f"🔍 [APPLE BATCH] Found {len(existing_external_ids)} existing events")

            # 2. 새 이벤트와 업데이트 대상 분리
            new_events = []
            update_events = []

            for event in events:
                external_id = event.get('external_id')
                if not external_id:
                    continue

                if external_id in existing_external_ids:
                    # 기존 이벤트 업데이트 대상
                    update_events.append({
                        'external_id': external_id,
                        'data': {
                            'title': event.get('title'),
                            'description': event.get('description', ''),
                            'start_datetime': event.get('start_datetime'),
                            'end_datetime': event.get('end_datetime'),
                            'location': event.get('location', ''),
                            'is_all_day': event.get('all_day', False),
                            'updated_at': datetime.now().isoformat()
                        }
                    })
                else:
                    # 새 이벤트 삽입 대상
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
                        'source_platform': 'apple',
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }
                    new_events.append(event_data)

            synced_count = 0

            # 3. 배치 삽입 (새 이벤트들)
            if new_events:
                try:
                    insert_result = supabase.table('calendar_events').insert(new_events).execute()
                    if insert_result and insert_result.data:
                        synced_count += len(insert_result.data)
                        print(f"✅ [APPLE BATCH] Created {len(insert_result.data)} new events")
                except Exception as insert_error:
                    print(f"❌ [APPLE BATCH] Insert failed: {insert_error}")

            # 4. 개별 업데이트 (기존 이벤트들)
            updated_count = 0
            for update_item in update_events:
                try:
                    update_result = supabase.table('calendar_events').update(
                        update_item['data']
                    ).eq('user_id', user_id).eq(
                        'external_id', update_item['external_id']
                    ).eq('source_platform', 'apple').execute()

                    if update_result and update_result.data:
                        updated_count += 1
                        synced_count += 1
                except Exception as update_error:
                    print(f"❌ [APPLE BATCH] Update failed for {update_item['external_id']}: {update_error}")

            if updated_count > 0:
                print(f"✅ [APPLE BATCH] Updated {updated_count} existing events")

            print(f"💾 [APPLE BATCH] Completed processing Apple Calendar events")
            return synced_count

        except Exception as e:
            print(f"❌ [APPLE BATCH] Error processing batch: {e}")
            return 0

# Create singleton instance
apple_calendar_sync = AppleCalendarSync()