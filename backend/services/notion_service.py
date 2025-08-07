"""
Notion service for calendar synchronization
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from notion_client import Client as NotionClient

logger = logging.getLogger(__name__)

class NotionService:
    """Service for Notion integration and synchronization"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Notion service with API key"""
        self.api_key = api_key
        self.client = NotionClient(auth=api_key) if api_key else None
        
    def test_connection(self) -> Dict[str, Any]:
        """Test Notion API connection"""
        try:
            if not self.client:
                return {
                    'success': False,
                    'error': 'No API key provided'
                }
                
            # Try to list users to test connection
            users = self.client.users.list()
            return {
                'success': True,
                'message': 'Successfully connected to Notion'
            }
        except Exception as e:
            logger.error(f"Notion connection test failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_databases(self) -> List[Dict[str, Any]]:
        """Get list of accessible databases"""
        try:
            if not self.client:
                return []
                
            # Search for databases
            response = self.client.search(filter={"property": "object", "value": "database"})
            return response.get('results', [])
        except Exception as e:
            logger.error(f"Failed to get databases: {str(e)}")
            return []
    
    def create_event(self, database_id: str, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new event in Notion database"""
        try:
            if not self.client:
                return None
                
            page = self.client.pages.create(
                parent={"database_id": database_id},
                properties=event_data
            )
            return page
        except Exception as e:
            logger.error(f"Failed to create event: {str(e)}")
            return None
    
    def update_event(self, page_id: str, properties: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing event in Notion"""
        try:
            if not self.client:
                return None
                
            page = self.client.pages.update(
                page_id=page_id,
                properties=properties
            )
            return page
        except Exception as e:
            logger.error(f"Failed to update event: {str(e)}")
            return None
    
    def delete_event(self, page_id: str) -> bool:
        """Delete (archive) an event in Notion"""
        try:
            if not self.client:
                return False
                
            self.client.pages.update(
                page_id=page_id,
                archived=True
            )
            return True
        except Exception as e:
            logger.error(f"Failed to delete event: {str(e)}")
            return False