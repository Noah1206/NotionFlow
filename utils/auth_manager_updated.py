"""
🔐 Authentication & Session Manager - Updated for existing DB structure
Real user authentication with Supabase integration, adapted for existing friendships table
"""

import os
import jwt
import hashlib
import base64
import re
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from flask import session, request, g
from supabase import create_client
from functools import wraps

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# Initialize Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_API_KEY')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL environment variable is required")
if not SUPABASE_KEY:
    raise ValueError("SUPABASE_API_KEY environment variable is required")

# Use service key if available for admin operations, otherwise use anon key
supabase_key = SUPABASE_SERVICE_KEY if SUPABASE_SERVICE_KEY else SUPABASE_KEY
supabase = create_client(SUPABASE_URL, supabase_key)

class AuthManager:
    """Centralized authentication management adapted for existing DB structure"""
    
    @staticmethod
    def search_users(query: str, current_user_id: str, limit: int = 10) -> list:
        """Search for users by username, display_name, or email (adapted for existing user_profiles)"""
        try:
            # Search in user_profiles table using existing structure
            result = supabase.table('user_profiles').select('user_id, username, display_name, email, avatar_url').or_(
                f'username.ilike.%{query}%,'
                f'display_name.ilike.%{query}%,'
                f'email.ilike.%{query}%'
            ).neq('user_id', current_user_id).limit(limit).execute()
            
            users = []
            for user in result.data:
                users.append({
                    'user_id': user['user_id'],
                    'username': user.get('username', ''),
                    'display_name': user.get('display_name', ''),
                    'email': user.get('email', ''),
                    'avatar_url': user.get('avatar_url', '')
                })
            
            return users
        except Exception as e:
            print(f"❌ Error searching users: {e}")
            return []
    
    @staticmethod
    def send_friend_request(from_user_id: str, to_user_id: str) -> Tuple[bool, str]:
        """Send friend request using friendships table"""
        try:
            # Check if friendship already exists (any status)
            existing_friendship = supabase.table('friendships').select('*').or_(
                f'and(user_id.eq.{from_user_id},friend_id.eq.{to_user_id}),'
                f'and(user_id.eq.{to_user_id},friend_id.eq.{from_user_id})'
            ).execute()
            
            if existing_friendship.data:
                status = existing_friendship.data[0]['status']
                if status == 'accepted':
                    return False, "You are already friends"
                elif status == 'pending':
                    return False, "Friend request already sent"
                elif status == 'blocked':
                    return False, "Cannot send friend request"
            
            # Create friend request (pending status in friendships table)
            request_data = {
                'user_id': from_user_id,
                'friend_id': to_user_id,
                'status': 'pending',
                'created_at': datetime.now().isoformat()
            }
            
            result = supabase.table('friendships').insert(request_data).execute()
            
            if result.data:
                return True, "Friend request sent successfully"
            else:
                return False, "Failed to send friend request"
                
        except Exception as e:
            print(f"❌ Error sending friend request: {e}")
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def get_friend_requests(user_id: str) -> list:
        """Get pending friend requests for user"""
        try:
            # Get pending requests where this user is the recipient
            result = supabase.table('friendships').select(
                '''
                *,
                requester:user_profiles!friendships_user_id_fkey(
                    user_id, username, display_name, email, avatar_url
                )
                '''
            ).eq('friend_id', user_id).eq('status', 'pending').execute()
            
            requests = []
            for request in result.data:
                requester = request.get('requester')
                if requester:
                    requests.append({
                        'id': request['id'],
                        'from_user_id': request['user_id'],
                        'username': requester.get('username', ''),
                        'display_name': requester.get('display_name', ''),
                        'email': requester.get('email', ''),
                        'avatar_url': requester.get('avatar_url', ''),
                        'created_at': request['created_at']
                    })
            
            return requests
        except Exception as e:
            print(f"❌ Error getting friend requests: {e}")
            return []
    
    @staticmethod
    def respond_to_friend_request(request_id: str, action: str, user_id: str) -> Tuple[bool, str]:
        """Respond to friend request (accept/decline)"""
        try:
            # Get the friend request
            friendship_result = supabase.table('friendships').select('*').eq('id', request_id).eq('friend_id', user_id).execute()
            
            if not friendship_result.data:
                return False, "Friend request not found"
            
            friendship = friendship_result.data[0]
            
            if action == 'accept':
                # Update the existing friendship to accepted
                supabase.table('friendships').update({
                    'status': 'accepted',
                    'accepted_at': datetime.now().isoformat()
                }).eq('id', request_id).execute()
                
                # Create the reverse friendship for bidirectional relationship
                reverse_friendship = {
                    'user_id': user_id,
                    'friend_id': friendship['user_id'],
                    'status': 'accepted',
                    'created_at': datetime.now().isoformat(),
                    'accepted_at': datetime.now().isoformat()
                }
                
                supabase.table('friendships').insert(reverse_friendship).execute()
                
                return True, "Friend request accepted"
            elif action == 'decline':
                # Delete the friendship request
                supabase.table('friendships').delete().eq('id', request_id).execute()
                return True, "Friend request declined"
            else:
                return False, "Invalid action"
                
        except Exception as e:
            print(f"❌ Error responding to friend request: {e}")
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def get_friends_list(user_id: str) -> list:
        """Get user's friends list"""
        try:
            result = supabase.table('friendships').select(
                '''
                *,
                friend:user_profiles!friendships_friend_id_fkey(
                    user_id, username, display_name, email, avatar_url
                )
                '''
            ).eq('user_id', user_id).eq('status', 'accepted').execute()
            
            friends = []
            for friendship in result.data:
                friend = friendship.get('friend')
                if friend:
                    friends.append({
                        'user_id': friend['user_id'],
                        'username': friend.get('username', ''),
                        'display_name': friend.get('display_name', ''),
                        'email': friend.get('email', ''),
                        'avatar_url': friend.get('avatar_url', ''),
                        'friendship_created': friendship['created_at']
                    })
            
            return friends
        except Exception as e:
            print(f"❌ Error getting friends list: {e}")
            return []

# Keep other existing AuthManager methods...