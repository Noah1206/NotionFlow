"""
🔐 Authentication Routes
User login, registration, and session management
"""

from flask import Blueprint, request, jsonify, session, redirect, url_for
from utils.auth_manager import AuthManager, SessionManager
import re
import sys
import os

# Add parent directory to path for backend services
sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend'))
from services.sync_tracking_service import sync_tracker, EventType, ActivityType

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password: str) -> tuple[bool, str]:
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Za-z]', password):
        return False, "Password must contain at least one letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    return True, "Valid password"

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint - supports email or username"""
    try:
        data = request.get_json()
        login_identifier = data.get('email', '').strip().lower()  # Can be email or username
        password = data.get('password', '')
        
        # Validate input
        if not login_identifier or not password:
            return jsonify({'error': 'Email/Username and password are required'}), 400
        
        # Authenticate with Supabase (supports both email and username)
        success, user_data, token = AuthManager.authenticate_with_supabase(login_identifier, password)
        
        if success and user_data:
            # Create session manually for debugging
            session['user_id'] = user_data['id']
            session['user_info'] = {
                'id': user_data['id'],
                'email': user_data['email'],
                'username': user_data.get('username'),
                'display_name': user_data.get('display_name')
            }
            session['authenticated'] = True
            session.permanent = True
            
            # Also try AuthManager method
            AuthManager.create_session(user_data)
            SessionManager.extend_session()
            
            print(f"DEBUG: Session after login: {dict(session)}")
            
            # Track login activity
            sync_tracker.track_user_activity(
                user_id=user_data['id'],
                activity_type=ActivityType.LOGIN,
                details={
                    'login_identifier': login_identifier,
                    'login_method': 'password'
                },
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            
            # Get user profile
            profile = AuthManager.get_user_profile(user_data['id'])
            
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'user': {
                    'id': user_data['id'],
                    'email': user_data['email'],
                    'username': profile.get('username') if profile else None,
                    'display_name': profile.get('display_name') if profile else None
                },
                'token': token,
                'session_info': SessionManager.get_session_info()
            })
        else:
            return jsonify({
                'error': token or 'Invalid email or password'
            }), 401
            
    except Exception as e:
        return jsonify({'error': f'Login failed: {str(e)}'}), 500

@auth_bp.route('/register', methods=['POST'])
def register():
    """User registration endpoint"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        username = data.get('username', '').strip()
        display_name = data.get('display_name', '').strip()
        
        # Validate input
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validate password
        is_valid_password, password_error = validate_password(password)
        if not is_valid_password:
            return jsonify({'error': password_error}), 400
        
        # Validate username if provided
        if username and (len(username) < 3 or not re.match(r'^[a-zA-Z0-9_]+$', username)):
            return jsonify({'error': 'Username must be at least 3 characters and contain only letters, numbers, and underscores'}), 400
        
        # Register with Supabase
        success, user_data, token = AuthManager.register_with_supabase(
            email, password, username, display_name
        )
        
        if success and user_data:
            # Create session
            AuthManager.create_session(user_data)
            SessionManager.extend_session()
            
            return jsonify({
                'success': True,
                'message': 'Registration successful',
                'user': user_data,
                'token': token,
                'session_info': SessionManager.get_session_info()
            })
        else:
            return jsonify({
                'error': token or 'Registration failed'
            }), 400
            
    except Exception as e:
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """User logout endpoint"""
    try:
        # Clear session completely
        AuthManager.clear_session()
        session.clear()
        session.modified = True
        
        # Add response headers to prevent caching
        response = jsonify({
            'success': True,
            'message': 'Logout successful'
        })
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        return response
        
    except Exception as e:
        return jsonify({'error': f'Logout failed: {str(e)}'}), 500

@auth_bp.route('/status', methods=['GET'])
def auth_status():
    """Get current authentication status"""
    try:
        user_id = AuthManager.get_current_user_id()
        
        if user_id:
            profile = AuthManager.get_user_profile(user_id)
            session_info = SessionManager.get_session_info()
            
            return jsonify({
                'authenticated': True,
                'user': {
                    'id': user_id,
                    'email': profile.get('email') if profile else None,
                    'username': profile.get('username') if profile else None,
                    'display_name': profile.get('display_name') if profile else None
                },
                'session': session_info
            })
        else:
            return jsonify({
                'authenticated': False,
                'user': None,
                'session': None
            })
            
    except Exception as e:
        return jsonify({
            'authenticated': False,
            'error': str(e)
        }), 500

@auth_bp.route('/refresh', methods=['POST'])
def refresh_session():
    """Refresh user session"""
    try:
        if not AuthManager.is_authenticated():
            return jsonify({'error': 'Not authenticated'}), 401
        
        if SessionManager.is_session_expired():
            AuthManager.clear_session()
            return jsonify({'error': 'Session expired'}), 401
        
        # Extend session
        SessionManager.extend_session()
        
        return jsonify({
            'success': True,
            'message': 'Session refreshed',
            'session_info': SessionManager.get_session_info()
        })
        
    except Exception as e:
        return jsonify({'error': f'Session refresh failed: {str(e)}'}), 500

@auth_bp.route('/profile', methods=['GET'])
def get_profile():
    """Get user profile"""
    try:
        user_id = AuthManager.get_current_user_id()
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        profile = AuthManager.get_user_profile(user_id)
        if not profile:
            return jsonify({'error': 'Profile not found'}), 404
        
        return jsonify({
            'success': True,
            'profile': {
                'id': profile['user_id'],
                'email': profile['email'],
                'username': profile['username'],
                'display_name': profile['display_name'],
                'avatar_url': profile.get('avatar_url'),
                'bio': profile.get('bio'),
                'created_at': profile['created_at']
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get profile: {str(e)}'}), 500

@auth_bp.route('/profile', methods=['PUT'])
def update_profile():
    """Update user profile"""
    try:
        user_id = AuthManager.get_current_user_id()
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json()
        
        # Validate updateable fields
        allowed_fields = ['username', 'display_name', 'bio', 'avatar_url']
        update_data = {}
        
        for field in allowed_fields:
            if field in data:
                value = data[field].strip() if isinstance(data[field], str) else data[field]
                
                # Validate username if being updated
                if field == 'username' and value:
                    if len(value) < 3 or not re.match(r'^[a-zA-Z0-9_]+$', value):
                        return jsonify({'error': 'Username must be at least 3 characters and contain only letters, numbers, and underscores'}), 400
                
                update_data[field] = value
        
        if not update_data:
            return jsonify({'error': 'No valid fields to update'}), 400
        
        # Update profile in database
        from supabase import create_client
        SUPABASE_URL = os.getenv('SUPABASE_URL')
        SUPABASE_KEY = os.getenv('SUPABASE_API_KEY')
        
        if not SUPABASE_URL or not SUPABASE_KEY:
            return jsonify({'error': 'Database configuration error'}), 500
            
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        result = supabase.table('user_profiles').update(update_data).eq('user_id', user_id).execute()
        
        if result.data:
            return jsonify({
                'success': True,
                'message': 'Profile updated successfully',
                'profile': result.data[0]
            })
        else:
            return jsonify({'error': 'Failed to update profile'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Profile update failed: {str(e)}'}), 500

@auth_bp.route('/dashboard-url', methods=['POST'])
def get_dashboard_url():
    """Generate dashboard URL based on encrypted email"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Generate dashboard URL using encrypted email
        dashboard_url = AuthManager.get_dashboard_url(email)
        
        return jsonify({
            'success': True,
            'dashboard_url': dashboard_url
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to generate dashboard URL: {str(e)}'}), 500

@auth_bp.route('/set-session', methods=['POST'])
def set_session():
    """Set user session (for calendar popup functionality)"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({
                'success': False,
                'message': 'User ID is required'
            }), 400
        
        # Set user_id in session
        session['user_id'] = user_id
        session.permanent = True
        
        return jsonify({
            'success': True,
            'message': 'Session set successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to set session: {str(e)}'
        }), 500

# Error handlers
@auth_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Auth endpoint not found'}), 404

@auth_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal authentication error'}), 500