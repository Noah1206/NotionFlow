"""
🚀 NodeFlow User Visit Tracking Service
Manages user visits and first-time popup display logic with Supabase integration
"""

import os
import json
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple
from supabase import create_client
from flask import request

class UserVisitService:
    """Service for tracking user visits and managing popup display logic"""
    
    def __init__(self):
        """Initialize Supabase client for visit tracking"""
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_API_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase credentials are required for visit tracking")
        
        self.supabase = create_client(self.supabase_url, self.supabase_key)
    
    def record_visit(self, user_id: str, visit_type: str = 'calendar_page') -> Dict:
        """
        Record a user visit and determine if popup should be shown
        
        Args:
            user_id: Authenticated user ID
            visit_type: Type of page visit (default: calendar_page)
            
        Returns:
            Dict with visit info and popup display decision
        """
        try:
            # Get request metadata
            user_agent = request.headers.get('User-Agent', '')[:500]  # Limit length
            ip_address = self._get_client_ip()
            
            # Check if user visit record exists
            existing_visit = self._get_user_visit(user_id, visit_type)
            
            if existing_visit:
                # Update existing visit record
                updated_visit = self._update_visit_record(existing_visit, user_agent, ip_address)
                
                # Determine popup display logic
                should_show_popup = self._should_show_popup(updated_visit)
                
                return {
                    'success': True,
                    'is_first_visit': False,
                    'visit_count': updated_visit['visit_count'],
                    'should_show_popup': should_show_popup,
                    'popup_already_shown': updated_visit['popup_shown'],
                    'popup_dismissed': updated_visit['popup_dismissed'],
                    'calendar_created': updated_visit['calendar_created'],
                    'visit_data': updated_visit
                }
            else:
                # Create new visit record for first-time user
                new_visit = self._create_visit_record(user_id, visit_type, user_agent, ip_address)
                
                return {
                    'success': True,
                    'is_first_visit': True,
                    'visit_count': 1,
                    'should_show_popup': True,  # Always show on first visit
                    'popup_already_shown': False,
                    'popup_dismissed': False,
                    'calendar_created': False,
                    'visit_data': new_visit
                }
                
        except Exception as e:
            print(f"Error recording user visit: {e}")
            # Return safe fallback - don't show popup on error
            return {
                'success': False,
                'error': str(e),
                'is_first_visit': False,
                'should_show_popup': False,
                'popup_already_shown': True  # Safe fallback
            }
    
    def mark_popup_shown(self, user_id: str, visit_type: str = 'calendar_page') -> Dict:
        """Mark that popup has been shown to user"""
        try:
            result = self.supabase.table('user_visits').update({
                'popup_shown': True,
                'popup_shown_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }).eq('user_id', user_id).eq('visit_type', visit_type).execute()
            
            return {
                'success': True,
                'message': 'Popup shown status updated'
            }
            
        except Exception as e:
            print(f"Error marking popup shown: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def mark_popup_dismissed(self, user_id: str, visit_type: str = 'calendar_page') -> Dict:
        """Mark that user dismissed the popup (나중에 하기)"""
        try:
            result = self.supabase.table('user_visits').update({
                'popup_dismissed': True,
                'popup_dismissed_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }).eq('user_id', user_id).eq('visit_type', visit_type).execute()
            
            return {
                'success': True,
                'message': 'Popup dismissed status updated'
            }
            
        except Exception as e:
            print(f"Error marking popup dismissed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def mark_calendar_created(self, user_id: str, visit_type: str = 'calendar_page') -> Dict:
        """Mark that user has created a calendar"""
        try:
            result = self.supabase.table('user_visits').update({
                'calendar_created': True,
                'calendar_created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }).eq('user_id', user_id).eq('visit_type', visit_type).execute()
            
            return {
                'success': True,
                'message': 'Calendar created status updated'
            }
            
        except Exception as e:
            print(f"Error marking calendar created: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_user_visit_status(self, user_id: str, visit_type: str = 'calendar_page') -> Dict:
        """Get current visit status for user"""
        try:
            visit_data = self._get_user_visit(user_id, visit_type)
            
            if not visit_data:
                return {
                    'success': True,
                    'is_first_visit': True,
                    'should_show_popup': True,
                    'visit_count': 0
                }
            
            should_show_popup = self._should_show_popup(visit_data)
            
            return {
                'success': True,
                'is_first_visit': visit_data['visit_count'] == 1,
                'should_show_popup': should_show_popup,
                'visit_count': visit_data['visit_count'],
                'popup_shown': visit_data['popup_shown'],
                'popup_dismissed': visit_data['popup_dismissed'],
                'calendar_created': visit_data['calendar_created'],
                'first_visit_at': visit_data['first_visit_at'],
                'last_visit_at': visit_data['last_visit_at']
            }
            
        except Exception as e:
            print(f"Error getting user visit status: {e}")
            return {
                'success': False,
                'error': str(e),
                'should_show_popup': False
            }
    
    def _get_user_visit(self, user_id: str, visit_type: str) -> Optional[Dict]:
        """Get existing visit record for user"""
        try:
            result = self.supabase.table('user_visits').select('*').eq(
                'user_id', user_id
            ).eq('visit_type', visit_type).single().execute()
            
            return result.data if result.data else None
            
        except Exception:
            # No existing record found
            return None
    
    def _create_visit_record(self, user_id: str, visit_type: str, user_agent: str, ip_address: str) -> Dict:
        """Create new visit record for first-time user"""
        now = datetime.now(timezone.utc).isoformat()
        
        visit_data = {
            'user_id': user_id,
            'visit_type': visit_type,
            'visit_count': 1,
            'first_visit_at': now,
            'last_visit_at': now,
            'popup_shown': False,
            'popup_dismissed': False,
            'calendar_created': False,
            'user_agent': user_agent,
            'ip_address': ip_address,
            'session_data': {},
            'created_at': now,
            'updated_at': now
        }
        
        result = self.supabase.table('user_visits').insert(visit_data).execute()
        return result.data[0] if result.data else visit_data
    
    def _update_visit_record(self, existing_visit: Dict, user_agent: str, ip_address: str) -> Dict:
        """Update existing visit record with new visit"""
        now = datetime.now(timezone.utc).isoformat()
        
        updated_data = {
            'visit_count': existing_visit['visit_count'] + 1,
            'last_visit_at': now,
            'user_agent': user_agent,
            'ip_address': ip_address,
            'updated_at': now
        }
        
        result = self.supabase.table('user_visits').update(updated_data).eq(
            'user_id', existing_visit['user_id']
        ).eq('visit_type', existing_visit['visit_type']).execute()
        
        # Return merged data
        return {**existing_visit, **updated_data}
    
    def _should_show_popup(self, visit_data: Dict) -> bool:
        """
        Determine if popup should be shown based on visit data
        
        Logic:
        - Show on first visit (visit_count == 1)
        - Don't show if already shown and not dismissed
        - Don't show if user has created calendar
        - Don't show if user dismissed it
        """
        # Never show if user already created a calendar
        if visit_data.get('calendar_created', False):
            return False
        
        # Never show if user dismissed it
        if visit_data.get('popup_dismissed', False):
            return False
        
        # Show on first visit if not already shown
        if visit_data['visit_count'] == 1 and not visit_data.get('popup_shown', False):
            return True
        
        # Don't show for subsequent visits
        return False
    
    def _get_client_ip(self) -> str:
        """Get client IP address from request"""
        # Check for forwarded IP first (for proxy/load balancer)
        if request.headers.get('X-Forwarded-For'):
            return request.headers['X-Forwarded-For'].split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers['X-Real-IP']
        else:
            return request.remote_addr or 'unknown'

# Global service instance
visit_service = UserVisitService()