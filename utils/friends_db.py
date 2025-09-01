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
            # Use service role key for admin operations, fallback to anon key
            key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_API_KEY') or os.getenv('SUPABASE_ANON_KEY')
            
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
            # Check if user_profiles table exists and create minimal test data
            print("🔧 Checking database tables...")
            
            # Try to access user_profiles table
            try:
                result = self.supabase.table('user_profiles').select('*').limit(1).execute()
                print("✅ user_profiles table exists")
            except Exception as e:
                print(f"❌ user_profiles table issue: {e}")
                print("📝 Note: Tables need to be created in Supabase dashboard")
                return False
            
            # Check other tables
            for table_name in ['friendships', 'friend_requests']:
                try:
                    result = self.supabase.table(table_name).select('*').limit(1).execute()
                    print(f"✅ {table_name} table exists")
                except Exception as e:
                    print(f"❌ {table_name} table issue: {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ Friends DB: Failed to check tables: {e}")
            return False
    
    # User Profile Methods
    def create_user_profile(self, user_id, name, email, avatar_url=None):
        """Create or update user profile"""
        if not self.is_available():
            return False
        
        try:
            import uuid
            
            # Generate username from name/email
            username = name if name else email.split('@')[0] if email else user_id
            
            # First, create or get user in main users table
            user_uuid = str(uuid.uuid4())
            
            # Check if user already exists by email
            existing_user = self.supabase.table('users').select('*').eq('email', email).execute()
            
            if existing_user.data:
                # Use existing user
                user_uuid = existing_user.data[0]['id']
                print(f"Using existing user: {user_uuid}")
            else:
                # Create new user in main users table
                user_data = {
                    'id': user_uuid,
                    'email': email,
                    'name': username,  # Required field in users table
                    'created_at': datetime.now().isoformat()
                }
                
                user_result = self.supabase.table('users').insert(user_data).execute()
                if not user_result.data:
                    print("❌ Failed to create user in main users table")
                    return False
                print(f"✅ Created new user: {user_uuid}")
            
            # Now create/update profile
            profile_data = {
                'user_id': user_uuid,  # Reference to main users table
                'username': username,   # Display name
                'email': email,
                'avatar_url': avatar_url
            }
            
            # Check if profile exists
            existing_profile = self.supabase.table('user_profiles').select('*').eq('user_id', user_uuid).execute()
            
            if existing_profile.data:
                # Update existing profile
                result = self.supabase.table('user_profiles').update({
                    'username': username,
                    'email': email,
                    'avatar_url': avatar_url
                }).eq('user_id', user_uuid).execute()
            else:
                # Insert new profile
                result = self.supabase.table('user_profiles').insert(profile_data).execute()
            
            return bool(result.data)
            
        except Exception as e:
            print(f"❌ Failed to create user profile: {e}")
            return False
    
    def get_user_profile(self, user_id):
        """Get user profile by ID"""
        if not self.is_available():
            return None
        
        try:
            result = self.supabase.table('user_profiles').select('*').eq('user_id', user_id).execute()
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
    
    def search_users_by_name(self, name):
        """Search users by username"""
        if not self.is_available():
            return []
        
        try:
            result = self.supabase.table('user_profiles').select('*').ilike('username', f'%{name}%').execute()
            return result.data or []
            
        except Exception as e:
            print(f"❌ Failed to search users by name: {e}")
            return []
    
    def search_users(self, query):
        """Search users by username or email"""
        if not self.is_available():
            return []
        
        try:
            # Search by email or username
            result = self.supabase.table('user_profiles').select('*').or_(
                f'email.ilike.%{query}%,username.ilike.%{query}%'
            ).execute()
            
            return result.data or []
            
        except Exception as e:
            print(f"❌ Failed to search users: {e}")
            return []
    
    def has_pending_request(self, sender_id, receiver_id):
        """Check if there's a pending friend request"""
        if not self.is_available():
            return False
        
        try:
            result = self.supabase.table('friend_requests').select('id').eq('sender_id', sender_id).eq('receiver_id', receiver_id).eq('status', 'pending').execute()
            return len(result.data) > 0
            
        except Exception as e:
            print(f"❌ Failed to check pending request: {e}")
            return False
    
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
                        'name': friend['addressee']['username'],  # Use username
                        'email': friend['addressee']['email'],
                        'avatar': friend['addressee']['avatar_url'],
                        'connected_at': friend['created_at']
                    })
            
            # Process friends where user is addressee
            for friend in friends_as_addressee.data or []:
                if friend.get('requester'):
                    friends.append({
                        'id': friend['friend_id'],
                        'name': friend['requester']['username'],  # Use username
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