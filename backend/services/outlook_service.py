import os
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
from supabase import create_client

class OutlookProvider:
    """Outlook/Microsoft Graph integration provider for NotionFlow"""
    
    def __init__(self, access_token: str, refresh_token: str = None):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.base_url = "https://graph.microsoft.com/v1.0"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Initialize Supabase for storing sync data
        self.supabase_url = os.environ.get('SUPABASE_URL')
        self.supabase_key = os.environ.get('SUPABASE_KEY')
        if self.supabase_url and self.supabase_key:
            self.supabase = create_client(self.supabase_url, self.supabase_key)
        else:
            self.supabase = None
    
    def test_connection(self) -> Dict[str, Any]:
        """Test Microsoft Graph API connection"""
        try:
            response = requests.get(
                f"{self.base_url}/me",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'user': data.get('displayName', 'Unknown'),
                    'email': data.get('mail') or data.get('userPrincipalName'),
                    'id': data.get('id')
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_calendars(self) -> List[Dict[str, Any]]:
        """Get list of Outlook calendars"""
        try:
            response = requests.get(
                f"{self.base_url}/me/calendars",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('value', [])
            else:
                print(f"Error getting calendars: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Error getting calendars: {e}")
            return []
    
    def get_events(self, calendar_id: str = None, start_datetime: str = None, end_datetime: str = None) -> List[Dict[str, Any]]:
        """Get calendar events from Outlook"""
        try:
            # Use primary calendar if no calendar_id specified
            if calendar_id:
                url = f"{self.base_url}/me/calendars/{calendar_id}/events"
            else:
                url = f"{self.base_url}/me/events"
            
            params = {
                '$orderby': 'start/dateTime',
                '$top': 250  # Maximum allowed by API
            }
            
            # Add date filters if provided
            filters = []
            if start_datetime:
                filters.append(f"start/dateTime ge '{start_datetime}'")
            if end_datetime:
                filters.append(f"end/dateTime le '{end_datetime}'")
            
            if filters:
                params['$filter'] = ' and '.join(filters)
            
            all_events = []
            
            while url:
                response = requests.get(url, headers=self.headers, params=params if url.startswith(self.base_url) else None)
                
                if response.status_code == 200:
                    data = response.json()
                    all_events.extend(data.get('value', []))
                    
                    # Check for next page
                    url = data.get('@odata.nextLink')
                else:
                    print(f"Error getting events: HTTP {response.status_code}")
                    break
            
            return all_events
            
        except Exception as e:
            print(f"Error getting events: {e}")
            return []
    
    def create_event(self, event_data: Dict[str, Any], calendar_id: str = None) -> Dict[str, Any]:
        """Create a new calendar event in Outlook"""
        try:
            # Use primary calendar if no calendar_id specified
            if calendar_id:
                url = f"{self.base_url}/me/calendars/{calendar_id}/events"
            else:
                url = f"{self.base_url}/me/events"
            
            # Ensure required fields
            if 'subject' not in event_data:
                event_data['subject'] = 'Untitled Event'
            
            # Convert datetime strings to proper format if needed
            if 'start' in event_data and isinstance(event_data['start'], str):
                event_data['start'] = {
                    'dateTime': event_data['start'],
                    'timeZone': 'UTC'
                }
            
            if 'end' in event_data and isinstance(event_data['end'], str):
                event_data['end'] = {
                    'dateTime': event_data['end'],
                    'timeZone': 'UTC'
                }
            
            response = requests.post(
                url,
                headers=self.headers,
                json=event_data
            )
            
            if response.status_code == 201:
                return {
                    'success': True,
                    'event': response.json()
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_event(self, event_id: str, event_data: Dict[str, Any], calendar_id: str = None) -> Dict[str, Any]:
        """Update an existing calendar event in Outlook"""
        try:
            # Use primary calendar if no calendar_id specified
            if calendar_id:
                url = f"{self.base_url}/me/calendars/{calendar_id}/events/{event_id}"
            else:
                url = f"{self.base_url}/me/events/{event_id}"
            
            # Convert datetime strings to proper format if needed
            if 'start' in event_data and isinstance(event_data['start'], str):
                event_data['start'] = {
                    'dateTime': event_data['start'],
                    'timeZone': 'UTC'
                }
            
            if 'end' in event_data and isinstance(event_data['end'], str):
                event_data['end'] = {
                    'dateTime': event_data['end'],
                    'timeZone': 'UTC'
                }
            
            response = requests.patch(
                url,
                headers=self.headers,
                json=event_data
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'event': response.json()
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_event(self, event_id: str, calendar_id: str = None) -> Dict[str, Any]:
        """Delete a calendar event from Outlook"""
        try:
            # Use primary calendar if no calendar_id specified
            if calendar_id:
                url = f"{self.base_url}/me/calendars/{calendar_id}/events/{event_id}"
            else:
                url = f"{self.base_url}/me/events/{event_id}"
            
            response = requests.delete(
                url,
                headers=self.headers
            )
            
            if response.status_code == 204:
                return {'success': True}
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_event_instances(self, event_id: str, start_datetime: str, end_datetime: str) -> List[Dict[str, Any]]:
        """Get instances of a recurring event"""
        try:
            url = f"{self.base_url}/me/events/{event_id}/instances"
            
            params = {
                'startDateTime': start_datetime,
                'endDateTime': end_datetime,
                '$top': 250
            }
            
            all_instances = []
            
            while url:
                response = requests.get(url, headers=self.headers, params=params if url.startswith(self.base_url) else None)
                
                if response.status_code == 200:
                    data = response.json()
                    all_instances.extend(data.get('value', []))
                    
                    # Check for next page
                    url = data.get('@odata.nextLink')
                else:
                    print(f"Error getting event instances: HTTP {response.status_code}")
                    break
            
            return all_instances
            
        except Exception as e:
            print(f"Error getting event instances: {e}")
            return []
    
    def accept_event(self, event_id: str, comment: str = None, send_response: bool = True) -> Dict[str, Any]:
        """Accept a meeting invitation"""
        try:
            url = f"{self.base_url}/me/events/{event_id}/accept"
            
            payload = {
                'sendResponse': send_response
            }
            
            if comment:
                payload['comment'] = comment
            
            response = requests.post(
                url,
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 202:
                return {'success': True}
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def decline_event(self, event_id: str, comment: str = None, send_response: bool = True) -> Dict[str, Any]:
        """Decline a meeting invitation"""
        try:
            url = f"{self.base_url}/me/events/{event_id}/decline"
            
            payload = {
                'sendResponse': send_response
            }
            
            if comment:
                payload['comment'] = comment
            
            response = requests.post(
                url,
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 202:
                return {'success': True}
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_calendar_view(self, start_datetime: str, end_datetime: str, calendar_id: str = None) -> List[Dict[str, Any]]:
        """Get calendar view (expanded recurring events)"""
        try:
            # Use primary calendar if no calendar_id specified
            if calendar_id:
                url = f"{self.base_url}/me/calendars/{calendar_id}/calendarView"
            else:
                url = f"{self.base_url}/me/calendarView"
            
            params = {
                'startDateTime': start_datetime,
                'endDateTime': end_datetime,
                '$orderby': 'start/dateTime',
                '$top': 250
            }
            
            all_events = []
            
            while url:
                response = requests.get(url, headers=self.headers, params=params if url.startswith(self.base_url) else None)
                
                if response.status_code == 200:
                    data = response.json()
                    all_events.extend(data.get('value', []))
                    
                    # Check for next page
                    url = data.get('@odata.nextLink')
                else:
                    print(f"Error getting calendar view: HTTP {response.status_code}")
                    break
            
            return all_events
            
        except Exception as e:
            print(f"Error getting calendar view: {e}")
            return []
    
    def format_notion_to_outlook(self, notion_event: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Notion calendar data to Outlook format"""
        outlook_event = {
            'subject': notion_event.get('title', 'Untitled Event'),
            'body': {
                'contentType': 'HTML',
                'content': notion_event.get('description', '')
            }
        }
        
        # Handle dates
        if notion_event.get('start'):
            outlook_event['start'] = {
                'dateTime': notion_event['start'],
                'timeZone': notion_event.get('timezone', 'UTC')
            }
        
        if notion_event.get('end'):
            outlook_event['end'] = {
                'dateTime': notion_event['end'],
                'timeZone': notion_event.get('timezone', 'UTC')
            }
        
        # Handle location
        if notion_event.get('location'):
            outlook_event['location'] = {
                'displayName': notion_event['location']
            }
        
        # Handle attendees
        if notion_event.get('attendees'):
            outlook_event['attendees'] = [
                {
                    'emailAddress': {
                        'address': attendee.get('email', attendee),
                        'name': attendee.get('name', '')
                    },
                    'type': 'required'
                }
                for attendee in notion_event['attendees']
            ]
        
        # Handle reminders
        if notion_event.get('reminder_minutes'):
            outlook_event['reminderMinutesBeforeStart'] = notion_event['reminder_minutes']
            outlook_event['isReminderOn'] = True
        
        # Handle recurrence
        if notion_event.get('recurrence'):
            # This is a simplified version - you may need to expand based on your needs
            recurrence = notion_event['recurrence']
            outlook_event['recurrence'] = {
                'pattern': {
                    'type': recurrence.get('type', 'daily'),
                    'interval': recurrence.get('interval', 1)
                },
                'range': {
                    'type': recurrence.get('range_type', 'noEnd'),
                    'startDate': recurrence.get('start_date', notion_event.get('start', '').split('T')[0])
                }
            }
        
        return outlook_event
    
    def format_outlook_to_notion(self, outlook_event: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Outlook event to Notion format"""
        notion_event = {
            'title': outlook_event.get('subject', 'Untitled Event'),
            'description': outlook_event.get('body', {}).get('content', ''),
            'outlook_id': outlook_event.get('id'),
            'outlook_url': outlook_event.get('webLink')
        }
        
        # Handle dates
        if outlook_event.get('start'):
            notion_event['start'] = outlook_event['start'].get('dateTime')
            notion_event['timezone'] = outlook_event['start'].get('timeZone', 'UTC')
        
        if outlook_event.get('end'):
            notion_event['end'] = outlook_event['end'].get('dateTime')
        
        # Handle location
        if outlook_event.get('location'):
            notion_event['location'] = outlook_event['location'].get('displayName', '')
        
        # Handle attendees
        if outlook_event.get('attendees'):
            notion_event['attendees'] = [
                {
                    'email': attendee.get('emailAddress', {}).get('address'),
                    'name': attendee.get('emailAddress', {}).get('name'),
                    'status': attendee.get('status', {}).get('response')
                }
                for attendee in outlook_event['attendees']
            ]
        
        # Handle reminders
        if outlook_event.get('isReminderOn'):
            notion_event['reminder_minutes'] = outlook_event.get('reminderMinutesBeforeStart', 15)
        
        # Handle recurrence
        if outlook_event.get('recurrence'):
            pattern = outlook_event['recurrence'].get('pattern', {})
            range_data = outlook_event['recurrence'].get('range', {})
            
            notion_event['recurrence'] = {
                'type': pattern.get('type'),
                'interval': pattern.get('interval'),
                'range_type': range_data.get('type'),
                'start_date': range_data.get('startDate'),
                'end_date': range_data.get('endDate')
            }
        
        # Handle meeting status
        notion_event['is_online_meeting'] = outlook_event.get('isOnlineMeeting', False)
        if outlook_event.get('onlineMeeting'):
            notion_event['meeting_url'] = outlook_event['onlineMeeting'].get('joinUrl')
        
        return notion_event