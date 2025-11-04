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
        """Get user's friends list based on calendar sharing relationships"""
        if not self.is_available():
            return []

        try:
            print(f"🔍 [FRIENDS] Finding friends for user {user_id} via calendar shares")

            # Find friends through calendar sharing relationships
            # A "friend" is someone who has shared their calendar with you
            # OR someone you've shared your calendar with

            # Get calendars shared WITH this user (user received shares)
            received_shares = self.supabase.table('calendar_shares').select('''
                calendar_id,
                shared_by,
                shared_at,
                calendars!inner(owner_id, name)
            ''').eq('user_id', user_id).eq('is_active', True).execute()

            # Get calendars shared BY this user (user gave shares)
            given_shares = self.supabase.table('calendar_shares').select('''
                user_id,
                shared_at,
                calendar_id,
                calendars!inner(owner_id, name)
            ''').eq('shared_by', user_id).eq('is_active', True).execute()

            friend_ids = set()
            connection_dates = {}

            # Process received shares - the calendar owner is a friend
            for share in received_shares.data or []:
                if share.get('calendars') and share['shared_by']:
                    friend_id = share['shared_by']
                    friend_ids.add(friend_id)
                    connection_dates[friend_id] = share['shared_at']
                    print(f"✅ [FRIENDS] Found friend {friend_id[:8]}... (shared calendar with you)")

            # Process given shares - the person you shared with is a friend
            for share in given_shares.data or []:
                if share.get('calendars') and share['user_id']:
                    friend_id = share['user_id']
                    friend_ids.add(friend_id)
                    if friend_id not in connection_dates:
                        connection_dates[friend_id] = share['shared_at']
                    print(f"✅ [FRIENDS] Found friend {friend_id[:8]}... (you shared calendar with them)")

            # Remove self if somehow included
            friend_ids.discard(user_id)

            if not friend_ids:
                print(f"🔍 [FRIENDS] No friends found for user {user_id}")
                return []

            print(f"🤝 [FRIENDS] Found {len(friend_ids)} friends through calendar sharing")

            # Get friend details from user_profiles and users tables
            friends = []
            for friend_id in friend_ids:
                try:
                    # Try to get from user_profiles first
                    profile_result = self.supabase.table('user_profiles').select(
                        'user_id, username, email, avatar_url'
                    ).eq('user_id', friend_id).execute()

                    if profile_result.data:
                        profile = profile_result.data[0]
                        friend_info = {
                            'id': friend_id,
                            'name': profile.get('username', 'Unknown'),
                            'email': profile.get('email', ''),
                            'avatar': profile.get('avatar_url'),
                            'connected_at': connection_dates.get(friend_id)
                        }
                    else:
                        # Fallback to users table
                        user_result = self.supabase.table('users').select(
                            'id, name, email, avatar_url'
                        ).eq('id', friend_id).execute()

                        if user_result.data:
                            user = user_result.data[0]
                            friend_info = {
                                'id': friend_id,
                                'name': user.get('name', 'Unknown'),
                                'email': user.get('email', ''),
                                'avatar': user.get('avatar_url'),
                                'connected_at': connection_dates.get(friend_id)
                            }
                        else:
                            # Create minimal friend info if user not found
                            friend_info = {
                                'id': friend_id,
                                'name': f'User {friend_id[:8]}...',
                                'email': '',
                                'avatar': None,
                                'connected_at': connection_dates.get(friend_id)
                            }

                    friends.append(friend_info)
                    print(f"📝 [FRIENDS] Added friend: {friend_info['name']} ({friend_id[:8]}...)")

                except Exception as friend_error:
                    print(f"⚠️ [FRIENDS] Error getting details for friend {friend_id}: {friend_error}")
                    continue

            print(f"🎯 [FRIENDS] Successfully retrieved {len(friends)} friends")
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
                print(f"🔍 [FRIEND-CALENDARS] No friends found for user {user_id}")
                return []

            print(f"🔍 [FRIEND-CALENDARS] Found {len(friend_ids)} friends for user {user_id}")

            # Get public calendars from friends
            calendars = []
            for friend_id in friend_ids:
                try:
                    # Query calendars table for friend's public calendars
                    friend_calendars_result = self.supabase.table('calendars').select(
                        'id, name, description, color, owner_id, created_at, is_active, public_access'
                    ).eq('owner_id', friend_id).eq('public_access', True).eq('is_active', True).execute()

                    if friend_calendars_result.data:
                        # Get friend info for calendar display
                        friend_info = next((f for f in friends if f['id'] == friend_id), None)
                        friend_name = friend_info['name'] if friend_info else 'Unknown Friend'

                        for calendar in friend_calendars_result.data:
                            calendar_info = {
                                'id': calendar['id'],
                                'name': calendar['name'],
                                'description': calendar.get('description', ''),
                                'color': calendar.get('color', '#3B82F6'),
                                'owner_id': calendar['owner_id'],
                                'owner_name': friend_name,
                                'created_at': calendar['created_at'],
                                'is_public': True,
                                'can_view': True,
                                'can_edit': False  # Friends can only view public calendars by default
                            }
                            calendars.append(calendar_info)
                            print(f"✅ [FRIEND-CALENDARS] Added calendar '{calendar['name']}' from friend {friend_name}")
                    else:
                        print(f"📅 [FRIEND-CALENDARS] No public calendars found for friend {friend_id}")

                except Exception as friend_error:
                    print(f"❌ [FRIEND-CALENDARS] Error getting calendars for friend {friend_id}: {friend_error}")
                    continue

            print(f"🎯 [FRIEND-CALENDARS] Total public calendars found: {len(calendars)}")
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