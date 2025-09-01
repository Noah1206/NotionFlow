"""
Friends Routes - 친구 시스템 API 라우트
"""

import os
import sys
from flask import Blueprint, request, jsonify
from datetime import datetime

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../utils'))

try:
    from friends_db import friends_db
    print("✅ Friends DB imported successfully")
except ImportError as e:
    print(f"❌ Friends Routes: Failed to import friends_db: {e}")
    friends_db = None

try:
    from auth_manager import verify_token
    print("✅ Auth manager imported successfully")
except ImportError:
    print("⚠️ Auth manager not found, using simple auth fallback")
    def verify_token(token):
        # Simple fallback - just return success for testing
        if token and len(token) > 10:
            return True, {'user_id': 'test_user_123'}
        return False, "Invalid token"

friends_bp = Blueprint('friends', __name__, url_prefix='/api')

def get_current_user():
    """Get current user from token"""
    auth_header = request.headers.get('Authorization')
    
    # For testing: allow access without authentication
    if not auth_header or not auth_header.startswith('Bearer '):
        print("⚠️ No auth header found, using test user for development")
        return 'test_user_123'  # Test user ID
    
    token = auth_header.replace('Bearer ', '')
    
    # For testing: accept any token longer than 10 characters
    if len(token) > 10:
        print("✅ Using test authentication")
        return 'test_user_123'
    
    is_valid, user_info = verify_token(token)
    
    if is_valid and isinstance(user_info, dict):
        return user_info.get('user_id') or user_info.get('id')
    return None

@friends_bp.route('/users/search', methods=['GET'])
def search_users():
    """사용자 검색 API"""
    try:
        # Get current user
        current_user_id = get_current_user()
        if not current_user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Get search query
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'users': []}), 200
        
        if len(query) < 2:
            return jsonify({'users': []}), 200
        
        # Check if friends_db is available
        if not friends_db or not friends_db.is_available():
            return jsonify({'error': 'Database not available'}), 503
        
        # Search users by email
        users = friends_db.search_users_by_email(query)
        
        # Also search by name if implemented
        if hasattr(friends_db, 'search_users_by_name'):
            name_results = friends_db.search_users_by_name(query)
            # Merge results and remove duplicates
            user_ids = {user['user_id'] for user in users}
            for user in name_results:
                if user['user_id'] not in user_ids:
                    users.append(user)
        
        # Filter out current user
        users = [user for user in users if user['user_id'] != current_user_id]
        
        # Get friendship status for each user
        result_users = []
        for user in users:
            user_data = {
                'id': user['user_id'],  # Use user_id as the ID
                'name': user['username'],  # Use username as display name
                'email': user['email'],
                'avatar': user.get('avatar_url'),
                'is_friend': False,
                'request_sent': False
            }
            
            # Check if already friends
            friendship = friends_db.get_friendship_status(current_user_id, user['user_id'])
            if friendship and friendship.get('status') == 'accepted':
                user_data['is_friend'] = True
            
            # Check if friend request already sent
            if hasattr(friends_db, 'has_pending_request'):
                user_data['request_sent'] = friends_db.has_pending_request(current_user_id, user['user_id'])
            
            result_users.append(user_data)
        
        return jsonify({'users': result_users, 'success': True}), 200
        
    except Exception as e:
        print(f"❌ User search error: {e}")
        return jsonify({'error': 'Search failed', 'details': str(e)}), 500

@friends_bp.route('/friends/request', methods=['POST'])
def send_friend_request():
    """친구 요청 전송"""
    try:
        # Get current user
        current_user_id = get_current_user()
        if not current_user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Get request data
        data = request.get_json()
        if not data or 'user_id' not in data:
            return jsonify({'error': 'Missing user_id'}), 400
        
        target_user_id = data['user_id']
        message = data.get('message', '')
        
        # Validate target user
        if target_user_id == current_user_id:
            return jsonify({'error': 'Cannot send friend request to yourself'}), 400
        
        # Check if friends_db is available
        if not friends_db or not friends_db.is_available():
            return jsonify({'error': 'Database not available'}), 503
        
        # Send friend request
        success = friends_db.send_friend_request(current_user_id, target_user_id, message)
        
        if success:
            return jsonify({'success': True, 'message': 'Friend request sent'}), 200
        else:
            return jsonify({'error': 'Failed to send friend request. You might already be friends or have a pending request.'}), 400
    
    except Exception as e:
        print(f"❌ Send friend request error: {e}")
        return jsonify({'error': 'Failed to send friend request', 'details': str(e)}), 500

@friends_bp.route('/friends', methods=['GET'])
def get_friends():
    """친구 목록 조회"""
    try:
        # Get current user
        current_user_id = get_current_user()
        if not current_user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Check if friends_db is available
        if not friends_db or not friends_db.is_available():
            return jsonify({'friends': []}), 200
        
        # Get friends list
        friends_list = friends_db.get_friends(current_user_id)
        
        return jsonify({'friends': friends_list, 'success': True}), 200
        
    except Exception as e:
        print(f"❌ Get friends error: {e}")
        return jsonify({'error': 'Failed to get friends', 'friends': []}), 500

@friends_bp.route('/friends/requests', methods=['GET'])
def get_friend_requests():
    """친구 요청 목록 조회"""
    try:
        # Get current user
        current_user_id = get_current_user()
        if not current_user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Check if friends_db is available
        if not friends_db or not friends_db.is_available():
            return jsonify({'requests': []}), 200
        
        # Get friend requests
        requests = friends_db.get_friend_requests(current_user_id)
        
        return jsonify({'requests': requests, 'success': True}), 200
        
    except Exception as e:
        print(f"❌ Get friend requests error: {e}")
        return jsonify({'error': 'Failed to get friend requests', 'requests': []}), 500

@friends_bp.route('/friends/request/<request_id>/accept', methods=['POST'])
def accept_friend_request(request_id):
    """친구 요청 승인"""
    try:
        # Get current user
        current_user_id = get_current_user()
        if not current_user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Check if friends_db is available
        if not friends_db or not friends_db.is_available():
            return jsonify({'error': 'Database not available'}), 503
        
        # Accept friend request
        success = friends_db.accept_friend_request(request_id, current_user_id)
        
        if success:
            return jsonify({'success': True, 'message': 'Friend request accepted'}), 200
        else:
            return jsonify({'error': 'Failed to accept friend request'}), 400
    
    except Exception as e:
        print(f"❌ Accept friend request error: {e}")
        return jsonify({'error': 'Failed to accept friend request', 'details': str(e)}), 500

@friends_bp.route('/friends/request/<request_id>/decline', methods=['POST'])
def decline_friend_request(request_id):
    """친구 요청 거절"""
    try:
        # Get current user
        current_user_id = get_current_user()
        if not current_user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Check if friends_db is available
        if not friends_db or not friends_db.is_available():
            return jsonify({'error': 'Database not available'}), 503
        
        # Decline friend request
        success = friends_db.decline_friend_request(request_id, current_user_id)
        
        if success:
            return jsonify({'success': True, 'message': 'Friend request declined'}), 200
        else:
            return jsonify({'error': 'Failed to decline friend request'}), 400
    
    except Exception as e:
        print(f"❌ Decline friend request error: {e}")
        return jsonify({'error': 'Failed to decline friend request', 'details': str(e)}), 500

@friends_bp.route('/friends/calendars', methods=['GET'])
def get_friend_calendars():
    """친구들의 공개 캘린더 조회"""
    try:
        # Get current user
        current_user_id = get_current_user()
        if not current_user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Check if friends_db is available
        if not friends_db or not friends_db.is_available():
            return jsonify({'calendars': []}), 200
        
        # Get friend calendars
        calendars = friends_db.get_friend_calendars(current_user_id)
        
        return jsonify({'calendars': calendars, 'success': True}), 200
        
    except Exception as e:
        print(f"❌ Get friend calendars error: {e}")
        return jsonify({'error': 'Failed to get friend calendars', 'calendars': []}), 500