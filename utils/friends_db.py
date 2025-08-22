"""
Friends Database Management
친구 시스템을 위한 데이터베이스 관리 모듈
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class FriendsDB:
    def __init__(self):
        self.supabase = None
        self._initialize_supabase()
    
    def _initialize_supabase(self):
        """Initialize Supabase connection"""
        try:
            from supabase import create_client
            
            url = os.getenv('SUPABASE_URL')
            # Try different key names
            key = os.getenv('SUPABASE_API_KEY') or os.getenv('SUPABASE_ANON_KEY')
            
            if url and key:
                self.supabase = create_client(url, key)
                print("✅ Friends DB: Supabase connection successful")
            else:
                print("❌ Friends DB: Missing Supabase credentials")
                
        except ImportError as e:
            print(f"❌ Friends DB: Supabase library not available: {e}")
        except Exception as e:
            print(f"❌ Friends DB: Connection failed: {e}")
    
    def is_available(self):
        """Check if database is available"""
        return self.supabase is not None
    
    def create_tables(self):
        """Create necessary tables for friends system"""
        if not self.is_available():
            return False
        
        try:
            # Create tables using SQL
            sql_commands = [
                # User profiles table
                """
                CREATE TABLE IF NOT EXISTS user_profiles (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    avatar_url TEXT,
                    is_public BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                """,
                
                # Friendships table
                """
                CREATE TABLE IF NOT EXISTS friendships (
                    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                    requester_id TEXT NOT NULL,
                    addressee_id TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'blocked')),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    UNIQUE(requester_id, addressee_id)
                );
                """,
                
                # Friend requests table
                """
                CREATE TABLE IF NOT EXISTS friend_requests (
                    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                    sender_id TEXT NOT NULL,
                    receiver_id TEXT NOT NULL,
                    message TEXT,
                    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'declined')),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    UNIQUE(sender_id, receiver_id)
                );
                """,
                
                # Calendar sharing table
                """
                CREATE TABLE IF NOT EXISTS calendar_sharing (
                    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                    calendar_id TEXT NOT NULL,
                    owner_id TEXT NOT NULL,
                    shared_with_id TEXT,
                    is_public BOOLEAN DEFAULT FALSE,
                    can_view BOOLEAN DEFAULT TRUE,
                    can_edit BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                """
            ]
            
            for sql in sql_commands:
                self.supabase.rpc('exec_sql', {'sql': sql}).execute()
            
            print("✅ Friends DB: Tables created successfully")
            return True
            
        except Exception as e:
            print(f"❌ Friends DB: Failed to create tables: {e}")
            return False
    
    # User Profile Methods
    def create_user_profile(self, user_id, name, email, avatar_url=None):
        """Create or update user profile"""
        if not self.is_available():
            return False
        
        try:
            data = {
                'id': user_id,
                'name': name,
                'email': email,
                'avatar_url': avatar_url,
                'updated_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table('user_profiles').upsert(data).execute()
            return bool(result.data)
            
        except Exception as e:
            print(f"❌ Failed to create user profile: {e}")
            return False
    
    def get_user_profile(self, user_id):
        """Get user profile by ID"""
        if not self.is_available():
            return None
        
        try:
            result = self.supabase.table('user_profiles').select('*').eq('id', user_id).execute()
            return result.data[0] if result.data else None
            
        except Exception as e:
            print(f"❌ Failed to get user profile: {e}")
            return None
    
    def search_users_by_email(self, email):
        """Search users by email"""
        if not self.is_available():
            return []
        
        try:
            result = self.supabase.table('user_profiles').select('*').ilike('email', f'%{email}%').execute()
            return result.data or []
            
        except Exception as e:
            print(f"❌ Failed to search users: {e}")
            return []
    
    # Friend Request Methods
    def send_friend_request(self, sender_id, receiver_id, message=None):
        """Send friend request"""
        if not self.is_available():
            return False
        
        try:
            # Check if request already exists
            existing = self.supabase.table('friend_requests').select('*').eq('sender_id', sender_id).eq('receiver_id', receiver_id).execute()
            if existing.data:
                return False  # Request already exists
            
            # Check if they're already friends
            friends = self.get_friendship_status(sender_id, receiver_id)
            if friends and friends.get('status') == 'accepted':
                return False  # Already friends
            
            data = {
                'sender_id': sender_id,
                'receiver_id': receiver_id,
                'message': message,
                'status': 'pending'
            }
            
            result = self.supabase.table('friend_requests').insert(data).execute()
            return bool(result.data)
            
        except Exception as e:
            print(f"❌ Failed to send friend request: {e}")
            return False
    
    def get_friend_requests(self, user_id):
        """Get pending friend requests for user"""
        if not self.is_available():
            return []
        
        try:
            result = self.supabase.table('friend_requests').select('''
                *,
                sender:user_profiles!sender_id(name, email, avatar_url)
            ''').eq('receiver_id', user_id).eq('status', 'pending').execute()
            
            return result.data or []
            
        except Exception as e:
            print(f"❌ Failed to get friend requests: {e}")
            return []
    
    def accept_friend_request(self, request_id, user_id):
        """Accept friend request"""
        if not self.is_available():
            return False
        
        try:
            # Get the request
            request_result = self.supabase.table('friend_requests').select('*').eq('id', request_id).eq('receiver_id', user_id).execute()
            if not request_result.data:
                return False
            
            request_data = request_result.data[0]
            sender_id = request_data['sender_id']
            receiver_id = request_data['receiver_id']
            
            # Update request status
            self.supabase.table('friend_requests').update({'status': 'accepted', 'updated_at': datetime.now().isoformat()}).eq('id', request_id).execute()
            
            # Create friendship
            friendship_data = {
                'requester_id': sender_id,
                'addressee_id': receiver_id,
                'status': 'accepted'
            }
            
            self.supabase.table('friendships').insert(friendship_data).execute()
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to accept friend request: {e}")
            return False
    
    def decline_friend_request(self, request_id, user_id):
        """Decline friend request"""
        if not self.is_available():
            return False
        
        try:
            result = self.supabase.table('friend_requests').update({
                'status': 'declined', 
                'updated_at': datetime.now().isoformat()
            }).eq('id', request_id).eq('receiver_id', user_id).execute()
            
            return bool(result.data)
            
        except Exception as e:
            print(f"❌ Failed to decline friend request: {e}")
            return False
    
    # Friendship Methods
    def get_friends(self, user_id):
        """Get user's friends list"""
        if not self.is_available():
            return []
        
        try:
            # Get friendships where user is requester or addressee
            result = self.supabase.rpc('get_user_friends', {'user_id': user_id}).execute()
            
            if result.data:
                return result.data
            
            # Fallback: manual query
            friends_as_requester = self.supabase.table('friendships').select('''
                addressee_id as friend_id,
                created_at,
                addressee:user_profiles!addressee_id(name, email, avatar_url)
            ''').eq('requester_id', user_id).eq('status', 'accepted').execute()
            
            friends_as_addressee = self.supabase.table('friendships').select('''
                requester_id as friend_id,
                created_at,
                requester:user_profiles!requester_id(name, email, avatar_url)
            ''').eq('addressee_id', user_id).eq('status', 'accepted').execute()
            
            friends = []
            
            # Process friends where user is requester
            for friend in friends_as_requester.data or []:
                if friend.get('addressee'):
                    friends.append({
                        'id': friend['friend_id'],
                        'name': friend['addressee']['name'],
                        'email': friend['addressee']['email'],
                        'avatar': friend['addressee']['avatar_url'],
                        'connected_at': friend['created_at']
                    })
            
            # Process friends where user is addressee
            for friend in friends_as_addressee.data or []:
                if friend.get('requester'):
                    friends.append({
                        'id': friend['friend_id'],
                        'name': friend['requester']['name'],
                        'email': friend['requester']['email'],
                        'avatar': friend['requester']['avatar_url'],
                        'connected_at': friend['created_at']
                    })
            
            return friends
            
        except Exception as e:
            print(f"❌ Failed to get friends: {e}")
            return []
    
    def get_friendship_status(self, user1_id, user2_id):
        """Get friendship status between two users"""
        if not self.is_available():
            return None
        
        try:
            result = self.supabase.table('friendships').select('*').or_(
                f'and(requester_id.eq.{user1_id},addressee_id.eq.{user2_id}),'
                f'and(requester_id.eq.{user2_id},addressee_id.eq.{user1_id})'
            ).execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            print(f"❌ Failed to get friendship status: {e}")
            return None
    
    # Calendar Sharing Methods
    def get_friend_calendars(self, user_id):
        """Get public calendars from friends"""
        if not self.is_available():
            return []
        
        try:
            # Get friends
            friends = self.get_friends(user_id)
            friend_ids = [friend['id'] for friend in friends]
            
            if not friend_ids:
                return []
            
            # Get public calendars from friends
            calendars = []
            for friend_id in friend_ids:
                # This would integrate with your existing calendar system
                # For now, return mock data
                pass
            
            return calendars
            
        except Exception as e:
            print(f"❌ Failed to get friend calendars: {e}")
            return []
    
    def share_calendar(self, calendar_id, owner_id, shared_with_id=None, is_public=False, can_edit=False):
        """Share calendar with friend or make public"""
        if not self.is_available():
            return False
        
        try:
            data = {
                'calendar_id': calendar_id,
                'owner_id': owner_id,
                'shared_with_id': shared_with_id,
                'is_public': is_public,
                'can_view': True,
                'can_edit': can_edit
            }
            
            result = self.supabase.table('calendar_sharing').insert(data).execute()
            return bool(result.data)
            
        except Exception as e:
            print(f"❌ Failed to share calendar: {e}")
            return False


# Global instance
friends_db = FriendsDB()