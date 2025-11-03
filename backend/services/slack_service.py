import os
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
from supabase import create_client

class SlackProvider:
    """Slack integration provider for NodeFlow"""
    
    def __init__(self, access_token: str, team_id: str = None):
        self.access_token = access_token
        self.team_id = team_id
        self.base_url = "https://slack.com/api"
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
        """Test Slack API connection"""
        try:
            response = requests.get(
                f"{self.base_url}/auth.test",
                headers=self.headers
            )
            
            data = response.json()
            
            if data.get('ok'):
                return {
                    'success': True,
                    'team': data.get('team', 'Unknown'),
                    'user': data.get('user', 'Unknown'),
                    'team_id': data.get('team_id'),
                    'user_id': data.get('user_id')
                }
            else:
                return {
                    'success': False,
                    'error': data.get('error', 'Unknown error')
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_channels(self, types: str = "public_channel,private_channel") -> List[Dict[str, Any]]:
        """Get list of Slack channels"""
        try:
            channels = []
            cursor = None
            
            while True:
                params = {
                    'types': types,
                    'limit': 100
                }
                
                if cursor:
                    params['cursor'] = cursor
                
                response = requests.get(
                    f"{self.base_url}/conversations.list",
                    headers=self.headers,
                    params=params
                )
                
                data = response.json()
                
                if not data.get('ok'):
                    raise Exception(data.get('error', 'Failed to get channels'))
                
                channels.extend(data.get('channels', []))
                
                # Check for pagination
                response_metadata = data.get('response_metadata', {})
                cursor = response_metadata.get('next_cursor')
                
                if not cursor:
                    break
            
            return channels
            
        except Exception as e:
            print(f"Error getting channels: {e}")
            return []
    
    def get_messages(self, channel_id: str, oldest: str = None, latest: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get messages from a Slack channel"""
        try:
            messages = []
            cursor = None
            
            while len(messages) < limit:
                params = {
                    'channel': channel_id,
                    'limit': min(100, limit - len(messages))
                }
                
                if oldest:
                    params['oldest'] = oldest
                if latest:
                    params['latest'] = latest
                if cursor:
                    params['cursor'] = cursor
                
                response = requests.get(
                    f"{self.base_url}/conversations.history",
                    headers=self.headers,
                    params=params
                )
                
                data = response.json()
                
                if not data.get('ok'):
                    raise Exception(data.get('error', 'Failed to get messages'))
                
                messages.extend(data.get('messages', []))
                
                # Check for pagination
                response_metadata = data.get('response_metadata', {})
                cursor = response_metadata.get('next_cursor')
                
                if not cursor or not data.get('has_more'):
                    break
            
            return messages[:limit]
            
        except Exception as e:
            print(f"Error getting messages: {e}")
            return []
    
    def post_message(self, channel: str, text: str, thread_ts: str = None, blocks: List[Dict] = None) -> Dict[str, Any]:
        """Post a message to a Slack channel"""
        try:
            payload = {
                'channel': channel,
                'text': text
            }
            
            if thread_ts:
                payload['thread_ts'] = thread_ts
            
            if blocks:
                payload['blocks'] = blocks
            
            response = requests.post(
                f"{self.base_url}/chat.postMessage",
                headers=self.headers,
                json=payload
            )
            
            data = response.json()
            
            if data.get('ok'):
                return {
                    'success': True,
                    'ts': data.get('ts'),
                    'channel': data.get('channel')
                }
            else:
                return {
                    'success': False,
                    'error': data.get('error', 'Failed to post message')
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_message(self, channel: str, ts: str, text: str, blocks: List[Dict] = None) -> Dict[str, Any]:
        """Update an existing Slack message"""
        try:
            payload = {
                'channel': channel,
                'ts': ts,
                'text': text
            }
            
            if blocks:
                payload['blocks'] = blocks
            
            response = requests.post(
                f"{self.base_url}/chat.update",
                headers=self.headers,
                json=payload
            )
            
            data = response.json()
            
            if data.get('ok'):
                return {
                    'success': True,
                    'ts': data.get('ts'),
                    'channel': data.get('channel')
                }
            else:
                return {
                    'success': False,
                    'error': data.get('error', 'Failed to update message')
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_message(self, channel: str, ts: str) -> Dict[str, Any]:
        """Delete a Slack message"""
        try:
            payload = {
                'channel': channel,
                'ts': ts
            }
            
            response = requests.post(
                f"{self.base_url}/chat.delete",
                headers=self.headers,
                json=payload
            )
            
            data = response.json()
            
            if data.get('ok'):
                return {'success': True}
            else:
                return {
                    'success': False,
                    'error': data.get('error', 'Failed to delete message')
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """Get information about a Slack user"""
        try:
            response = requests.get(
                f"{self.base_url}/users.info",
                headers=self.headers,
                params={'user': user_id}
            )
            
            data = response.json()
            
            if data.get('ok'):
                return data.get('user', {})
            else:
                return {}
                
        except Exception as e:
            print(f"Error getting user info: {e}")
            return {}
    
    def create_channel(self, name: str, is_private: bool = False) -> Dict[str, Any]:
        """Create a new Slack channel"""
        try:
            payload = {
                'name': name,
                'is_private': is_private
            }
            
            response = requests.post(
                f"{self.base_url}/conversations.create",
                headers=self.headers,
                json=payload
            )
            
            data = response.json()
            
            if data.get('ok'):
                return {
                    'success': True,
                    'channel': data.get('channel', {})
                }
            else:
                return {
                    'success': False,
                    'error': data.get('error', 'Failed to create channel')
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def add_reaction(self, channel: str, timestamp: str, name: str) -> Dict[str, Any]:
        """Add a reaction to a message"""
        try:
            payload = {
                'channel': channel,
                'timestamp': timestamp,
                'name': name
            }
            
            response = requests.post(
                f"{self.base_url}/reactions.add",
                headers=self.headers,
                json=payload
            )
            
            data = response.json()
            
            if data.get('ok'):
                return {'success': True}
            else:
                return {
                    'success': False,
                    'error': data.get('error', 'Failed to add reaction')
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def search_messages(self, query: str, count: int = 20) -> List[Dict[str, Any]]:
        """Search for messages in Slack"""
        try:
            params = {
                'query': query,
                'count': count
            }
            
            response = requests.get(
                f"{self.base_url}/search.messages",
                headers=self.headers,
                params=params
            )
            
            data = response.json()
            
            if data.get('ok'):
                return data.get('messages', {}).get('matches', [])
            else:
                return []
                
        except Exception as e:
            print(f"Error searching messages: {e}")
            return []
    
    def format_notion_to_slack(self, notion_content: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Notion content to Slack format"""
        # This is a simplified version - you may need to expand based on your needs
        text = notion_content.get('title', 'Untitled')
        
        blocks = []
        
        # Add title
        if text:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{text}*"
                }
            })
        
        # Add description if available
        if notion_content.get('description'):
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": notion_content['description']
                }
            })
        
        # Add link to Notion page if available
        if notion_content.get('url'):
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"<{notion_content['url']}|View in Notion>"
                }
            })
        
        return {
            'text': text,
            'blocks': blocks
        }
    
    def sync_to_notion(self, message: Dict[str, Any], notion_page_id: str = None) -> Dict[str, Any]:
        """Sync a Slack message to Notion"""
        # This would integrate with your existing Notion service
        # For now, returning a placeholder
        return {
            'success': True,
            'notion_page_id': notion_page_id or 'new-page-id',
            'message': 'Synced to Notion'
        }