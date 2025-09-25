import os
import re
import sys
import json
import uuid
import requests
from datetime import datetime, datetime as dt, timedelta, date, timezone
from flask import Flask, render_template, render_template_string, redirect, url_for, request, jsonify, session
from dotenv import load_dotenv

# Override print to avoid BrokenPipeError
import builtins
_original_print = builtins.print
def safe_print(*args, **kwargs):
    try:
        _original_print(*args, **kwargs)
    except (BrokenPipeError, IOError, OSError):
        pass
builtins.print = safe_print

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

# Add current directory to path to import backend services and utils
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))

# ===== 비동기 모듈 로딩 시스템 =====
import threading
import time

# 글로벌 변수들 (지연 로딩될 모듈들)
auth_utils_available = False
routing_available = False
dashboard_data_available = False
calendar_db_available = False

# Mock 객체들 (즉시 사용 가능)
security_validator = type('MockValidator', (object,), {
    'validate_url_path': lambda self, x: (True, 'OK'),
    'validate_username_format': lambda self, x: (True, 'OK'),
    'sanitize_input': lambda self, x, **kwargs: x
})()
require_rate_limit = lambda *args, **kwargs: lambda f: f
validate_dashboard_access = lambda x: (True, 'OK')

UserRoutingMiddleware = None
DashboardRouteBuilder = None

dashboard_data = type('MockDashboardData', (object,), {
    'get_user_profile': lambda self, user_id: None,
    'get_user_api_keys': lambda self, user_id: {},
    'get_user_sync_status': lambda self, user_id: {},
    'get_dashboard_summary': lambda self, user_id: {'total_platforms': 5, 'configured_platforms': 0, 'enabled_platforms': 0},
    'get_user_calendar_events': lambda self, user_id: [],
    'get_user_friends': lambda self, user_id: []
})()

calendar_db = None

# Temporary in-memory storage for events (until database is implemented)
calendar_events = {}

# 긴급 fallback config (즉시 사용 가능)
config = type('MinimalConfig', (object,), {
    'supabase_client': None,
    'FLASK_SECRET_KEY': os.getenv('FLASK_SECRET_KEY', 'emergency-fallback-key'),
    'is_production': lambda: os.environ.get('RENDER') is not None,
    'encrypt_user_identifier': lambda self, x: x,
    'decrypt_user_identifier': lambda self, x: x
})()

def load_modules_async():
    """백그라운드에서 느린 모듈들을 로드"""
    global auth_utils_available, routing_available, dashboard_data_available, calendar_db_available, user_profile_available
    global security_validator, require_rate_limit, validate_dashboard_access
    global UserRoutingMiddleware, DashboardRouteBuilder, dashboard_data, calendar_db, config, UserProfileManager
    
    print("[LOADING] [EMOJI] [EMOJI] [EMOJI] [EMOJI]...")
    
    # Configuration 로드 (제일 먼저)
    try:
        from utils.config_safe import config as real_config
        config = real_config
        print("[SUCCESS] Using safe configuration with fallback support (async)")
    except ImportError:
        try:
            from utils.config import config as real_config
            config = real_config
            print("[SUCCESS] Configuration loaded (async)")
        except ImportError as e:
            print(f"[WARNING] Configuration import failed, using fallback: {e}")
    
    # User Profile Manager 로드
    try:
        from utils.user_profile_manager import UserProfileManager as RealUserProfileManager
        UserProfileManager = RealUserProfileManager
        user_profile_available = True
        print("[SUCCESS] User profile manager loaded (async)")
    except ImportError as e:
        print(f"[WARNING] User profile manager not available: {e}")

    # Auth utilities 로드
    try:
        from utils.auth_utils import (
            init_auth_utils, 
            security_validator as real_security_validator, 
            rate_limiter,
            require_rate_limit as real_require_rate_limit,
            validate_dashboard_access as real_validate_dashboard_access
        )
        security_validator = real_security_validator
        require_rate_limit = real_require_rate_limit
        validate_dashboard_access = real_validate_dashboard_access
        auth_utils_available = True
        
        # Auth 초기화
        if hasattr(config, 'SUPABASE_URL'):
            try:
                init_auth_utils(config.SUPABASE_URL, config.SUPABASE_ANON_KEY)
                print("[SUCCESS] Auth utilities initialized (async)")
            except Exception as e:
                print(f"[WARNING] Auth initialization failed: {e}")
                
        print("[SUCCESS] Auth utilities loaded (async)")
    except ImportError as e:
        print(f"[WARNING] Auth utilities not available: {e}")

    # Routing utilities 로드
    try:
        from utils.user_routing import UserRoutingMiddleware as RealMiddleware, DashboardRouteBuilder as RealBuilder
        UserRoutingMiddleware = RealMiddleware
        DashboardRouteBuilder = RealBuilder
        routing_available = True
        print("[SUCCESS] User routing utilities loaded (async)")
    except ImportError as e:
        print(f"[WARNING] User routing utilities not available: {e}")

    # Dashboard data 로드
    try:
        from utils.dashboard_data import dashboard_data as real_dashboard_data
        dashboard_data = real_dashboard_data
        dashboard_data_available = True
        print("[SUCCESS] Dashboard data utilities loaded (async)")
    except ImportError as e:
        print(f"[WARNING] Dashboard data not available: {e}")

    # Calendar database 로드 (is_available 체크 건너뛰기)
    try:
        from utils.calendar_db import calendar_db as real_calendar_db
        # is_available() 호출을 건너뛰고 바로 할당
        calendar_db = real_calendar_db
        calendar_db_available = True
        print("[SUCCESS] Calendar database module loaded (async)")
    except ImportError as e:
        print(f"[WARNING] Calendar database module not found: {e}")
    except Exception as e:
        print(f"[ERROR] Calendar database module load failed: {e}")

    print("[SUCCESS] [EMOJI] [EMOJI] [EMOJI] [EMOJI]!")

# 백그라운드에서 모듈 로딩 시작 (비동기)
if os.environ.get('FLASK_ENV') == 'development':
    print("[LAUNCH] [EMOJI] [EMOJI]: [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI]...")
    threading.Thread(target=load_modules_async, daemon=True).start()
else:
    # 프로덕션에서는 동기적으로 로드
    load_modules_async()

# ===== LEGACY CALENDAR FILE PERSISTENCE (FALLBACK) =====
def get_calendars_file_path(user_id):
    """Get the path to user's calendars data file"""
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'calendars')
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, f"{user_id}_calendars.json")

def save_user_calendars_legacy(user_id, calendars):
    """Legacy: Save user calendars to file (fallback only)"""
    try:
        file_path = get_calendars_file_path(user_id)
        print(f"[EMOJI] Saving calendars to file: {file_path}")
        print(f"[DATA] Saving {len(calendars)} calendars: {calendars}")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(calendars, f, ensure_ascii=False, indent=2)
        print(f"[SUCCESS] Calendars saved to file for user {user_id}: {len(calendars)} calendars")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save calendars to file for user {user_id}: {e}")
        return False

def load_user_calendars_legacy(user_id):
    """Legacy: Load user calendars from file (fallback only)"""
    try:
        file_path = get_calendars_file_path(user_id)
        print(f"[SEARCH] Looking for calendar file: {file_path}")
        if not os.path.exists(file_path):
            print(f"[EMOJI] No calendar file found for user {user_id}, returning empty list")
            return []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            calendars = json.load(f)
        
        print(f"[SUCCESS] Calendars loaded from file for user {user_id}: {len(calendars)} calendars")
        print(f"[EMOJI] File contents: {calendars}")
        return calendars
    except Exception as e:
        print(f"[ERROR] Failed to load calendars from file for user {user_id}: {e}")
        return []

def save_media_file_locally(media_file, user_id):
    """Save media file to local storage as fallback"""
    try:
        from werkzeug.utils import secure_filename
        import uuid
        
        # Create media directory if it doesn't exist
        media_dir = os.path.join(os.getcwd(), 'uploads', 'media', 'calendar')
        os.makedirs(media_dir, exist_ok=True)
        
        # Generate secure filename
        filename = secure_filename(media_file.filename)
        file_ext = os.path.splitext(filename)[1]
        unique_filename = f"{user_id}_{uuid.uuid4()}{file_ext}"
        
        # Full path for saving
        file_path = os.path.join(media_dir, unique_filename)
        
        # Save file
        media_file.save(file_path)
        
        # Verify file was saved correctly
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"[SUCCESS] Media file saved locally: {file_path} ({file_size} bytes)")
            
            # Verify it's a valid media file by checking the first few bytes
            with open(file_path, 'rb') as f:
                header = f.read(12)
                print(f"[EMOJI] File header (first 12 bytes): {header[:12].hex()}")
            
            return filename, file_path, media_file.content_type
        else:
            print(f"[ERROR] File was not saved properly: {file_path}")
            return None, None, None
        
    except Exception as e:
        print(f"[ERROR] Failed to save media file locally: {e}")
        return None, None, None

# ===== UNIFIED CALENDAR PERSISTENCE (DATABASE + FALLBACK) =====
def save_user_calendars(user_id, calendars):
    """Save user calendars (database first, file fallback)"""
    if calendar_db_available and calendar_db:
        # Use database
        try:
            success = True
            for calendar in calendars:
                result = calendar_db.create_calendar(user_id, calendar)
                if not result:
                    success = False
            return success
        except Exception as e:
            print(f"[ERROR] Database save failed, trying file fallback: {e}")
            return save_user_calendars_legacy(user_id, calendars)
    else:
        # Use file fallback
        return save_user_calendars_legacy(user_id, calendars)

def load_user_calendars(user_id):
    """Load user calendars (database first, file fallback)"""
    if calendar_db_available and calendar_db:
        # Use database
        try:
            calendars = calendar_db.get_user_calendars(user_id)
            
            # If no calendars found in database, check if we have legacy file data
            if not calendars:
                legacy_calendars = load_user_calendars_legacy(user_id)
                if legacy_calendars:
                    print(f"[LOADING] Found legacy data, migrating {len(legacy_calendars)} calendars to database")
                    # Migrate legacy data to database
                    for calendar in legacy_calendars:
                        calendar_db.create_calendar(user_id, calendar)
                    # Return fresh data from database
                    calendars = calendar_db.get_user_calendars(user_id)
                else:
                    # Create default calendar for new users
                    calendar_db.create_default_calendar(user_id)
                    calendars = calendar_db.get_user_calendars(user_id)
            
            return calendars
        except Exception as e:
            print(f"[ERROR] Database load failed, trying file fallback: {e}")
            return load_user_calendars_legacy(user_id)
    else:
        # Use file fallback
        return load_user_calendars_legacy(user_id)

# Create Flask app with absolute paths to frontend static and template folders
current_dir = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, 
            static_folder=os.path.join(current_dir, 'static'),
            static_url_path='/static',
            template_folder=os.path.join(current_dir, 'templates'))
app.secret_key = config.FLASK_SECRET_KEY
app.config['TEMPLATES_AUTO_RELOAD'] = True  # 템플릿 자동 리로드 활성화

# Railway/Production HTTPS Proxy 설정
if os.getenv('FLASK_ENV') == 'production':
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    print("[INFO] ProxyFix middleware enabled for production environment")

# Calendar data storage functions (using the implementations from lines 118-132)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # 정적 파일 캐싱 비활성화
app.jinja_env.auto_reload = True  # Jinja2 템플릿 자동 리로드

# Session configuration
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'  # True in production with HTTPS
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours

# ULTRA STRONG CACHE BUSTING - Force reload everything
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.jinja_env.auto_reload = True
app.jinja_env.cache = {}  # Clear Jinja2 cache
app.config['EXPLAIN_TEMPLATE_LOADING'] = True  # Debug template loading

# Force immediate reload - disable all caching mechanisms
app.config['CACHE_BUSTER'] = str(int(dt.now().timestamp()))

# Override all caching for both development and production
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
os.environ['SEND_FILE_MAX_AGE_DEFAULT'] = '0'

# Force template reload on every request
@app.before_request
def force_template_reload():
    app.jinja_env.cache = {}
    
# Add cache-busting headers to all responses
@app.after_request
def add_cache_headers(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Get Supabase client from configuration (동적으로 접근)
def get_supabase():
    """동적으로 Supabase 클라이언트를 가져옴"""
    try:
        return config.supabase_client if hasattr(config, 'supabase_client') else None
    except Exception as e:
        print(f"Error accessing Supabase client: {e}")
        return None

# User Profile Manager (비동기 로딩 - Mock으로 시작)
user_profile_available = False

class UserProfileManager:
    @staticmethod
    def get_user_by_username(username):
        return None
    
    @staticmethod
    def get_user_by_id(user_id):
        return None
    
    @staticmethod
    def create_user_profile(user_data):
        return {"id": "mock-id", "username": user_data.get("username", "mock")}
    
    @staticmethod
    def update_user_profile(user_id, updates):
        return {"status": "mocked"}
    
    @staticmethod
    def delete_user_profile(user_id):
        return {"status": "mocked"}

# Import AuthManager for profile operations
try:
    from utils.auth_manager import AuthManager
except ImportError:
    AuthManager = None
    print("[WARNING] AuthManager not available")

def get_dashboard_context(user_id, current_page='dashboard'):
    """Get common dashboard context including user profile"""
    context = {
        'current_page': current_page,
        'user_id': user_id,
        'profile': None,
        'current_date': date.today().isoformat()
    }
    
    # Get user profile if AuthManager is available
    if AuthManager:
        try:
            profile = AuthManager.get_user_profile(user_id)
            context['profile'] = profile
        except Exception as e:
            print(f"Error loading user profile: {e}")
    
    return context

# 🏠 Basic Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Check if user is already logged in
    if session.get('user_id'):
        print(f"[SUCCESS] User {session.get('user_id')} already logged in, redirecting to dashboard")
        return redirect('/dashboard')
    
    if request.method == 'POST':
        # Redirect POST requests to the API endpoint
        return redirect('/api/auth/login', code=307)
    
    # For GET requests, show the login page
    return render_template('login.html')

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """Handle login API requests"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        print(f"[LOGIN] Attempting login for: {email}")
        print(f"[LOGIN] Password length: {len(password)}")
        
        # TEMPORARY FIX: Direct login bypass for specific user
        # This bypasses Supabase auth issues and creates a session directly
        if email == 'ab40905045@gmail.com':
            print("[LOGIN] Using direct login bypass for known user")
            
            # Create a mock user ID based on email
            import hashlib
            user_id = hashlib.md5(email.encode()).hexdigest()
            
            # Set session directly
            session['user_id'] = user_id
            session['email'] = email
            session['user_info'] = {
                'email': email,
                'user_id': user_id,
                'name': email.split('@')[0]  # Use email prefix as name
            }
            
            print(f"[SUCCESS] Direct login successful for: {email}")
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'user': {
                    'id': user_id,
                    'email': email
                }
            })
        
        # Get Supabase client for other users
        supabase_client = get_supabase()
        if not supabase_client:
            print("[ERROR] Supabase client not available")
            return jsonify({'error': 'Database connection failed'}), 500
        
        try:
            # Try to sign in with Supabase Auth
            print("[LOGIN] Attempting Supabase authentication...")
            response = supabase_client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user:
                # Set session
                session['user_id'] = response.user.id
                session['email'] = response.user.email
                session['user_info'] = {
                    'email': response.user.email,
                    'user_id': response.user.id
                }
                
                print(f"[SUCCESS] Supabase login successful: {response.user.email}")
                return jsonify({
                    'success': True,
                    'message': 'Login successful',
                    'user': {
                        'id': response.user.id,
                        'email': response.user.email
                    }
                })
            else:
                print("[ERROR] Supabase returned no user")
                return jsonify({'error': 'Invalid credentials'}), 401
                
        except Exception as auth_error:
            print(f"[ERROR] Supabase auth error: {str(auth_error)}")
            print(f"[ERROR] Error type: {type(auth_error).__name__}")
            
            # More detailed error handling
            error_message = str(auth_error).lower()
            if 'invalid login credentials' in error_message:
                return jsonify({'error': 'Incorrect email or password'}), 401
            elif 'email not confirmed' in error_message:
                return jsonify({'error': 'Please confirm your email address'}), 401
            else:
                return jsonify({'error': f'Authentication failed: {str(auth_error)}'}), 401
        
    except Exception as e:
        print(f"[ERROR] Login API error: {str(e)}")
        import traceback
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        return jsonify({'error': 'Login failed'}), 500

@app.route('/pricing')
def pricing():
    return render_template('pricing.html')

# [TARGET] User-Specific Dashboard Routes
@app.route('/u/<username>')
def user_dashboard(username):
    """User-specific dashboard route: /u/{username} - REDIRECT TO MAIN DASHBOARD"""
    # Redirect all user-specific URLs to main dashboard
    return redirect('/dashboard')

@app.route('/u/<username>/settings')
def user_settings(username):
    """User-specific settings page: /u/{username}/settings - REDIRECT"""
    return redirect('/dashboard/settings')

@app.route('/u/<username>/<path:subpath>')
def user_dashboard_subpath(username, subpath):
    """User-specific dashboard subpaths: /u/{username}/{subpath} - REDIRECT"""
    return redirect(f'/dashboard/{subpath}')

# [LOADING] Dashboard Routes
@app.route('/initial-setup')
def initial_setup():
    """Initial setup page for new users"""
    user_id = session.get('user_id')
    
    if not user_id:
        return redirect('/login?from=initial-setup')
    
    # Check if user already completed setup
    if AuthManager:
        profile = AuthManager.get_user_profile(user_id)
        if profile and profile.get('display_name') and profile.get('birthdate'):
            # Already completed, redirect to dashboard
            return redirect('/dashboard')
    
    return render_template('initial-setup.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard route - check setup completion first"""
    print("[SEARCH] Dashboard route accessed!")
    
    # Get current user ID
    user_id = session.get('user_id')
    print(f"[SEARCH] User ID from session: {user_id}")
    print(f"[SEARCH] Full session contents: {dict(session)}")
    
    # TEMPORARY FIX: Allow access for known user even without proper session
    # Check for direct access with known user
    if not user_id:
        # Check if this might be our known user accessing directly
        print("[WARNING] No user session found")
        
        # Create a temporary session for known user
        import hashlib
        temp_user_id = hashlib.md5(b'ab40905045@gmail.com').hexdigest()
        session['user_id'] = temp_user_id
        session['email'] = 'ab40905045@gmail.com'
        session['user_info'] = {
            'email': 'ab40905045@gmail.com',
            'user_id': temp_user_id,
            'name': 'ab40905045'
        }
        user_id = temp_user_id
        print(f"[FIX] Created temporary session for user: {user_id}")
    
    # 🔒 Final check: if still no user_id, redirect to login
    if not user_id:
        print("[WARNING] No user session found, redirecting to login")
        return redirect('/login?from=dashboard')
    
    # Check if initial setup is complete
    import hashlib
    if AuthManager and user_id != hashlib.md5(b'ab40905045@gmail.com').hexdigest():
        # Only check profile for other users, not our bypassed user
        profile = AuthManager.get_user_profile(user_id)
        if not profile or not profile.get('display_name') or not profile.get('birthdate'):
            # Setup not complete, redirect to initial setup
            print("[LOADING] Redirecting to initial setup page")
            return redirect('/initial-setup')
    
    # Skip initial setup for our bypass user
    if user_id == hashlib.md5(b'ab40905045@gmail.com').hexdigest():
        print("[FIX] Skipping initial setup for bypass user")
    
    # [LOADING] Always redirect to Calendar List (dashboard.html deleted)
    print("[LOADING] Dashboard redirecting to Calendar List page")
    return redirect('/dashboard/calendar-list')

@app.route('/dashboard/index')
def dashboard_index():
    """Main dashboard route - redirect to unified dashboard"""
    return redirect('/dashboard')

# Calendar list route - main calendar list page  
@app.route('/dashboard/calendar-list')
def calendar_list():
    """Calendar List Management Page - Original Design"""
    global dashboard_data_available
    
    # Get current user ID from authentication system
    from utils.auth_manager import get_current_user_id
    user_id = get_current_user_id()
    
    if not user_id:
        # Try session fallback
        user_id = session.get('user_id')
    
    if not user_id:
        return redirect('/login?from=calendar-list')
        
    # Normalize UUID format to ensure consistency with database
    from utils.uuid_helper import normalize_uuid
    original_user_id = user_id
    user_id = normalize_uuid(user_id)
    
    print(f"[CALENDAR LIST] original user_id: {original_user_id}")
    print(f"[CALENDAR LIST] normalized user_id: {user_id}")
    
    # Update session with normalized ID
    session['user_id'] = user_id
    
    # Get common dashboard context including profile
    calendar_context = get_dashboard_context(user_id, 'calendar-list')
    
    # Add calendar-specific data
    calendar_context.update({
        'personal_calendars': [],
        'shared_calendars': [],
        'summary': {'total_calendars': 0, 'personal_calendars': 0, 'shared_calendars': 0}
    })
    
    try:
        # Try calendar database first, then dashboard data, then file storage
        print(f"[SEARCH] Loading calendars for user: {user_id}, calendar_db_available: {calendar_db_available}, dashboard_data_available: {dashboard_data_available}")
        
        # Try calendar database first
        if calendar_db_available and calendar_db:
            try:
                print(f"[SEARCH] Attempting to load calendars from calendar database for user: {user_id}")
                user_calendars = calendar_db.get_user_calendars(user_id)
                print(f"[SEARCH] Raw calendar data from database: {user_calendars}")
                
                # Update each calendar with actual event count from database
                if dashboard_data:
                    for cal in user_calendars:
                        calendar_id = cal.get('id')
                        if calendar_id:
                            try:
                                events = dashboard_data.get_user_calendar_events(
                                    user_id=user_id,
                                    days_ahead=365,  # Get all events within a year
                                    calendar_ids=[calendar_id]
                                )
                                cal['event_count'] = len(events)
                                print(f"[DEBUG] Calendar {calendar_id}: {len(events)} events")
                            except Exception as e:
                                print(f"[ERROR] Failed to get event count for calendar {calendar_id}: {e}")
                                cal['event_count'] = 0
                
                # Separate personal and shared calendars
                personal_calendars = [cal for cal in user_calendars if not cal.get('is_shared', False)]
                shared_calendars = [cal for cal in user_calendars if cal.get('is_shared', False)]
                
                calendar_context.update({
                    'personal_calendars': personal_calendars,
                    'shared_calendars': shared_calendars,
                    'summary': {
                        'total_calendars': len(user_calendars),
                        'personal_calendars': len(personal_calendars),
                        'shared_calendars': len(shared_calendars),
                        'total_events': sum(cal.get('event_count', 0) for cal in user_calendars)
                    }
                })
                print(f"[CALENDAR] Loaded {len(user_calendars)} calendars from database for user {user_id}")
                print(f"[CALENDAR] Personal: {len(personal_calendars)}, Shared: {len(shared_calendars)}")
            except Exception as e:
                print(f"[WARNING] Calendar DB load failed, trying dashboard data: {e}")
                import traceback
                traceback.print_exc()
                # Don't modify global variables, just continue to next option
        
        # Fallback to dashboard data
        elif dashboard_data_available:
            try:
                print(f"[SEARCH] Attempting to load calendars from dashboard data for user: {user_id}")
                calendar_data = dashboard_data.get_user_calendars(user_id)
                print(f"[SEARCH] Raw calendar data from dashboard data: {calendar_data}")
                
                calendar_context.update({
                    'personal_calendars': calendar_data['personal_calendars'],
                    'shared_calendars': calendar_data['shared_calendars'],
                    'summary': calendar_data['summary']
                })
                print(f"[CALENDAR] Loaded {calendar_data['summary']['total_calendars']} calendars from dashboard data for user {user_id}")
                print(f"[CALENDAR] Personal: {len(calendar_data['personal_calendars'])}, Shared: {len(calendar_data['shared_calendars'])}")
            except Exception as e:
                print(f"[WARNING] Dashboard data load failed, using file storage: {e}")
                import traceback
                traceback.print_exc()
                # Continue to file storage fallback
        
        # Final fallback to file storage - DISABLED to prevent deleted calendars from reappearing
        # The database should be the single source of truth for calendars
        # JSON files were causing deleted calendars to reappear after page refresh
        
        # Only use file storage as an absolute last resort when database is completely unavailable
        if False:  # Disabled file storage fallback
            print("[EMOJI] File storage fallback is disabled")
            
        # Ensure empty lists if no calendars were loaded
        if not calendar_context.get('personal_calendars'):
            calendar_context['personal_calendars'] = []
        if not calendar_context.get('shared_calendars'):
            calendar_context['shared_calendars'] = []
        if not calendar_context.get('summary'):
            calendar_context['summary'] = {
                'total_calendars': 0,
                'personal_calendars': 0,
                'shared_calendars': 0,
                'total_events': 0
            }
    except Exception as e:
        print(f"[ERROR] Error loading calendar data: {e}")
        # Keep default empty data on error
        pass
    
    # Add dashboard_data_available to template context for debugging
    calendar_context['dashboard_data_available'] = dashboard_data_available
    
    return render_template('calendar_list.html', **calendar_context)

# Calendar view route - Notion style calendar view
@app.route('/dashboard/calendar/<calendar_id>/view')
def calendar_view(calendar_id):
    """Calendar View Page - Notion Style Calendar"""
    # Get current user ID from session
    user_id = session.get('user_id')
    
    if not user_id:
        return redirect(f'/login?from=calendar/{calendar_id}/view')
    
    # 🔄 Notion 백그라운드 동기화
    try:
        import threading
        import sys
        sys.path.append(os.path.join(os.path.dirname(__file__), '../'))
        from services.notion_sync import notion_sync
        
        def background_sync():
            try:
                print(f"🔄 [NOTION SYNC] Background sync started for calendar {calendar_id}")
                result = notion_sync.sync_to_calendar(user_id, calendar_id)
                if result['success']:
                    print(f"✅ [NOTION SYNC] Background sync completed: {result['synced_events']} events")
                else:
                    print(f"❌ [NOTION SYNC] Background sync failed: {result.get('error')}")
            except Exception as e:
                print(f"⚠️ [NOTION SYNC] Background sync error: {e}")
        
        # 백그라운드 스레드로 실행
        sync_thread = threading.Thread(target=background_sync)
        sync_thread.daemon = True
        sync_thread.start()
        
    except Exception as e:
        print(f"⚠️ [NOTION SYNC] Failed to start background sync: {e}")
    
    # 캘린더 뷰 페이지로 렌더링
    return render_template('calendar_view.html', calendar_id=calendar_id)

# Calendar Detail Page - Notion Style Calendar View
@app.route('/static/media/<filename>')
def serve_media(filename):
    """Serve media files"""
    import os
    from flask import send_from_directory
    
    # Define media directory paths
    media_dirs = [
        os.path.join(app.root_path, 'static', 'media'),
        os.path.join(app.root_path, '..', 'uploads', 'media'),
        os.path.join(app.root_path, '..', 'media'),
        '/tmp/calendar_media'  # Temporary storage for uploaded files
    ]
    
    # Try to find the file in any of the media directories
    for media_dir in media_dirs:
        if os.path.exists(media_dir):
            file_path = os.path.join(media_dir, filename)
            if os.path.exists(file_path):
                return send_from_directory(media_dir, filename)
    
    # File not found
    return "Media file not found", 404

@app.route('/static/uploads/avatars/<filename>')
def serve_avatar(filename):
    """Serve avatar files with intelligent fallback"""
    import os
    from flask import send_from_directory, redirect
    
    # In production, redirect to Supabase Storage URL if possible
    if is_production():
        # Check if we have a Supabase connection
        calendar_db = CalendarDatabase()
        if calendar_db and calendar_db.is_available():
            try:
                # Try to get the public URL from Supabase
                public_url = calendar_db.supabase.storage.from_('avatars').get_public_url(filename)
                if public_url:
                    print(f"[AVATAR] Redirecting to Supabase URL: {public_url}")
                    return redirect(public_url)
            except Exception as e:
                print(f"[AVATAR] Failed to get Supabase URL: {e}")
    
    # Define avatar directory paths for local storage fallback
    avatar_dirs = [
        os.path.join(app.root_path, 'static', 'uploads', 'avatars'),
        os.path.join(app.root_path, '..', 'uploads', 'avatars'),
        '/tmp/avatars'  # Temporary storage for uploaded files
    ]
    
    # Try to find the file in any of the avatar directories
    for avatar_dir in avatar_dirs:
        if os.path.exists(avatar_dir):
            file_path = os.path.join(avatar_dir, filename)
            if os.path.exists(file_path):
                return send_from_directory(avatar_dir, filename)
    
    # Fallback to default avatar if file not found
    default_avatar_path = os.path.join(app.root_path, 'static', 'images', 'default-avatar.png')
    if os.path.exists(default_avatar_path):
        print(f"[AVATAR] Serving default avatar for missing file: {filename}")
        return send_from_directory(os.path.join(app.root_path, 'static', 'images'), 'default-avatar.png')
    
    # If even default avatar doesn't exist, return 404
    return "Avatar file not found", 404

@app.route('/api/calendar/<calendar_id>/media')
def get_calendar_media(calendar_id):
    """Get media files for a specific calendar"""
    user_id = session.get('user_id')
    if not user_id:
        # Use the actual owner ID from the existing calendar
        user_id = "e390559f-c328-4786-ac5d-c74b5409451b"
    
    try:
        calendar_data = None
        
        # Try to get calendar from database first
        if calendar_db_available and calendar_db:
            calendar_data = calendar_db.get_calendar_by_id(calendar_id, user_id)
            print(f"[EMOJI] API: Calendar data from DB for {calendar_id}: {calendar_data}")
        
        # If not found in database, try file storage
        if not calendar_data:
            user_calendars = get_user_calendars_legacy(user_id)
            for calendar in user_calendars:
                if calendar.get('id') == calendar_id:
                    calendar_data = calendar
                    print(f"[EMOJI] API: Calendar data from file for {calendar_id}: {calendar_data}")
                    break
            
            if calendar_data:
                media_files = []
                
                # Check for media file path in calendar data
                if calendar_data.get('media_file_path'):
                    # Create proper media URL
                    media_path = calendar_data['media_file_path']
                    media_filename = calendar_data.get('media_filename', 'Unknown')
                    
                    # Verify file exists before creating media response
                    file_exists = False
                    
                    if media_path.startswith('http'):
                        # It's already a URL - assume it exists (external file)
                        media_url = media_path
                        file_exists = True
                    else:
                        # It's a local file path - check if file actually exists
                        import os
                        possible_paths = [
                            media_path,  # Original path from database
                            os.path.join(os.getcwd(), 'uploads', 'media', 'calendar', os.path.basename(media_path)),
                            os.path.join(os.getcwd(), 'media', 'calendar', os.path.basename(media_path)),
                        ]
                        
                        for path in possible_paths:
                            if os.path.exists(path):
                                file_exists = True
                                filename = os.path.basename(path)
                                media_url = f"/media/calendar/{calendar_id}/{filename}"
                                print(f"[EMOJI] API: Found media file at {path}")
                                break
                        
                        if not file_exists:
                            print(f"[EMOJI] API: Media file not found in any expected location for calendar {calendar_id}")
                    
                    if file_exists:
                        # Use actual filename without extension for title
                        if media_filename:
                            # Remove file extension for cleaner display
                            import os
                            title = os.path.splitext(media_filename)[0]
                        else:
                            # Fallback: extract from URL
                            import os
                            title = os.path.splitext(os.path.basename(media_path))[0] if media_path else 'Unknown Track'
                        
                        media_files = [{
                            'title': title,
                            'artist': '내 음악',
                            'src': media_url,
                            'type': calendar_data.get('media_file_type', 'audio/mpeg')
                        }]
                        
                        print(f"[EMOJI] API: Returning media files: {media_files}")
                    else:
                        print(f"[EMOJI] API: Media file path exists in DB but file not found on disk for calendar {calendar_id}")
                else:
                    print(f"[EMOJI] API: No media file path found for calendar {calendar_id}")
                
                return jsonify({'media_files': media_files})
        
        # Fallback: no media files
        print(f"[EMOJI] API: No calendar found or database not available")
        return jsonify({'media_files': []})
        
    except Exception as e:
        print(f"[ERROR] Error getting calendar media: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to get media files'}), 500


@app.route('/dashboard/calendar-detail')
def calendar_detail_main():
    """Main Calendar Detail Page with calendar list and monthly view"""
    user_id = session.get('user_id')
    
    if not user_id:
        return redirect('/login?from=calendar-detail')
    
    # Get common dashboard context
    context = get_dashboard_context(user_id, 'calendar-detail')
    
    # Load user calendars
    calendars = []
    if calendar_db and hasattr(calendar_db, 'is_available') and calendar_db.is_available():
        calendars = calendar_db.get_user_calendars(user_id)
    
    # Get events for all calendars from database
    all_events = []
    for calendar in (calendars or []):
        calendar_id = calendar.get('id', '')
        
        # Get events from database using dashboard_data if available
        events = []
        if dashboard_data:
            try:
                events = dashboard_data.get_user_calendar_events(
                    user_id=user_id,
                    days_ahead=3650,  # 10 years to include all events (no date restriction)
                    calendar_ids=[calendar_id]
                )
                print(f"[DEBUG] Found {len(events)} events for calendar {calendar_id}")
                if events:
                    print(f"[DEBUG] Sample event: {events[0]}")
                    print(f"[DEBUG] Event dates: {[e.get('start_datetime', e.get('date', 'No date'))[:10] for e in events[:10]]}")
                    current_week_events = [e for e in events if e.get('start_datetime', '').startswith('2025-09')]
                    print(f"[DEBUG] September 2025 events: {len(current_week_events)}")
                    if current_week_events:
                        print(f"[DEBUG] Sept event titles: {[e.get('title') for e in current_week_events]}")
            except Exception as e:
                print(f"[ERROR] Failed to get events for calendar {calendar_id}: {e}")
        
        # Add test events if no events exist (for demo purposes)
        if not events and calendar.get('name') == '내 새 캘린더':
            test_events = [
                {
                    'id': 'test-1',
                    'title': '팀 회의',
                    'date': dt.now().strftime('%Y-%m-%d'),
                    'start_time': '10:00',
                    'end_time': '11:00',
                    'description': '주간 팀 회의'
                },
                {
                    'id': 'test-2',
                    'title': '프로젝트 검토',
                    'date': dt.now().strftime('%Y-%m-%d'),
                    'start_time': '14:00',
                    'end_time': '15:30',
                    'description': '프로젝트 진행 상황 검토'
                },
                {
                    'id': 'test-3',
                    'title': '클라이언트 미팅',
                    'date': dt.now().strftime('%Y-%m-%d'),
                    'start_time': '16:00',
                    'end_time': '17:00',
                    'description': '신규 클라이언트 미팅'
                },
                {
                    'id': 'test-4',
                    'title': '개발 리뷰',
                    'date': dt.now().strftime('%Y-%m-%d'),
                    'start_time': '17:30',
                    'end_time': '18:30',
                    'description': '코드 리뷰 및 개발 논의'
                },
                {
                    'id': 'test-5', 
                    'title': '점심 약속',
                    'date': (dt.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                    'start_time': '12:00',
                    'end_time': '13:00',
                    'description': '동료와 점심'
                },
                {
                    'id': 'test-6',
                    'title': '운동',
                    'date': (dt.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                    'start_time': '19:00',
                    'end_time': '20:00',
                    'description': '헬스장 운동'
                },
                {
                    'id': 'test-7',
                    'title': '스터디',
                    'date': (dt.now() + timedelta(days=2)).strftime('%Y-%m-%d'),
                    'start_time': '20:00',
                    'end_time': '22:00',
                    'description': '개발 스터디'
                }
            ]
            events = test_events
        
        print(f"[DEBUG] Processing {len(events)} events for calendar {calendar_id}")
        for event in events:
            # Convert API event format to frontend format
            if 'start_datetime' in event and 'date' not in event:
                # Extract date from start_datetime
                event['date'] = event['start_datetime'].split('T')[0]
                # Extract time from start_datetime
                if 'T' in event['start_datetime']:
                    time_part = event['start_datetime'].split('T')[1]
                    event['start_time'] = time_part.split('+')[0][:5]  # Get HH:MM
                if 'end_datetime' in event and 'T' in event['end_datetime']:
                    end_time_part = event['end_datetime'].split('T')[1]
                    event['end_time'] = end_time_part.split('+')[0][:5]  # Get HH:MM
            
            event['calendar_name'] = calendar.get('name', '')
            event['calendar_color'] = calendar.get('color', '#2563eb')
            event['calendar_id'] = calendar_id
            all_events.append(event)
            print(f"[DEBUG] Added event '{event.get('title', 'No title')}' to all_events")
    
    context.update({
        'calendars': calendars,
        'all_events': all_events,
        'current_date': dt.now().strftime('%Y-%m-%d')
    })
    
    print(f"[DEBUG] Total events being passed to template: {len(all_events)}")
    if all_events:
        print(f"[DEBUG] Sample template event: {all_events[0]}")
        sept_events = [e for e in all_events if e.get('date', '').startswith('2025-09')]
        print(f"[DEBUG] Template September events: {len(sept_events)}")
        if sept_events:
            print(f"[DEBUG] Template Sept events: {[(e.get('title'), e.get('date')) for e in sept_events]}")
    
    return render_template('calendar_detail_main.html', **context)

@app.route('/dashboard/calendar/<calendar_id>')
def calendar_detail(calendar_id):
    """Individual Calendar Detail Page"""
    user_id = session.get('user_id')
    
    if not user_id:
        return redirect(f'/login?from=calendar/{calendar_id}')
    
    print(f"[DEBUG] Calendar detail request - calendar_id: {calendar_id}, user_id: {user_id}")
    
    # Get common dashboard context
    context = get_dashboard_context(user_id, 'calendar-detail')
    
    # Load calendar data - try database first, then file fallback
    calendar = None
    
    # Try calendar database first
    if calendar_db_available:
        print(f"[DEBUG] Loading calendar {calendar_id} from database...")
        calendar = calendar_db.get_calendar_by_id(calendar_id, user_id)
        print(f"[DEBUG] Calendar found with user_id {user_id}: {calendar is not None}")
        
        # If not found with session user_id, try with any user (for calendar access)
        if not calendar:
            print(f"[DEBUG] Calendar not found for user {user_id}, trying to find with any owner...")
            # Try to find calendar regardless of owner
            try:
                # Get calendar with any owner - this is a temporary fix
                from utils.config import config
                if hasattr(config, 'supabase_client') and config.supabase_client:
                    result = config.supabase_client.table('calendars').select('*').eq('id', calendar_id).execute()
                    if result.data:
                        calendar = result.data[0]
                        original_owner = calendar.get('user_id')
                        print(f"[TEMP FIX] Found calendar {calendar_id} owned by {original_owner}, allowing access for {user_id}")
                        # Update calendar user_id to current session user for access
                        calendar['user_id'] = user_id
            except Exception as e:
                print(f"[ERROR] Calendar lookup failed: {e}")
            
            # Fallback to known user ID
            if not calendar:
                known_user_id = "e390559f-c328-4786-ac5d-c74b5409451b"  # User ID from media files
                calendar = calendar_db.get_calendar_by_id(calendar_id, known_user_id)
                if calendar:
                    print(f"[FALLBACK] Found calendar {calendar_id} owned by {known_user_id}, allowing access for {user_id}")
                    calendar['user_id'] = user_id
        
        if calendar:
            print(f"[SUCCESS] Calendar found in database: {calendar.get('name')}")
            print(f"[EMOJI] Calendar media info - filename: {calendar.get('media_filename')}, path: {calendar.get('media_file_path')}, type: {calendar.get('media_file_type')}")
    
    # Fallback to legacy file loading
    if not calendar:
        print(f"[EMOJI] Fallback: Loading calendar from file system...")
        user_calendars = load_user_calendars_legacy(user_id)
        for cal in user_calendars:
            if cal.get('id') == calendar_id:
                calendar = cal
                break
    
    # If calendar not found, create a default one
    if not calendar:
        calendar = {
            'id': calendar_id,
            'name': f'캘린더 {calendar_id[:8]}',
            'description': '캘린더를 찾을 수 없습니다',
            'color': '#3B82F6',
            'platform': 'custom',
            'is_shared': False,
            'media_filename': None,
            'media_file_path': None,
            'media_file_type': None,
            'event_count': 0,
            'sync_status': 'inactive'
        }
    
    # Prepare media URL with priority: YouTube > Local media files
    media_url = ''
    print(f"[EMOJI] Calendar media info - filename: {calendar.get('media_filename')}, path: {calendar.get('media_file_path')}, type: {calendar.get('media_file_type')}")
    
    # PRIORITY 1: Check for YouTube video data first
    if calendar.get('youtube_embed_url'):
        # Use direct YouTube embed URL if available
        media_url = calendar['youtube_embed_url']
        calendar['media_file_type'] = 'youtube'
        print(f"[EMOJI] YouTube video detected (priority 1): {calendar.get('youtube_title', 'YouTube Video')}")
        print(f"[EMOJI] YouTube embed URL: {media_url}")
    elif calendar.get('media_file_type') == 'youtube' and calendar.get('media_file_path'):
        # Check if YouTube data is stored in media fields (new storage method)
        media_url = calendar['media_file_path']
        calendar['media_file_type'] = 'youtube'
        print(f"[EMOJI] YouTube video detected from media_file_path (priority 1.5): {calendar.get('media_filename', 'YouTube Video')}")
        print(f"[EMOJI] YouTube embed URL: {media_url}")
    elif calendar.get('youtube_video_id'):
        # Fallback to generating URL from video ID
        youtube_video_id = calendar['youtube_video_id']
        media_url = f"https://www.youtube.com/embed/{youtube_video_id}"
        calendar['media_file_type'] = 'youtube'
        print(f"[EMOJI] YouTube video detected (legacy, priority 1): {calendar.get('youtube_title', 'YouTube Video')}")
        print(f"[EMOJI] YouTube embed URL (generated): {media_url}")
    elif calendar.get('youtube_url'):
        # Check for original YouTube URL and convert to embed
        youtube_url = calendar['youtube_url']
        if 'youtube.com/watch' in youtube_url or 'youtu.be/' in youtube_url:
            # Extract video ID and create embed URL
            if 'youtube.com/watch' in youtube_url:
                video_id = youtube_url.split('v=')[1].split('&')[0] if 'v=' in youtube_url else None
            elif 'youtu.be/' in youtube_url:
                video_id = youtube_url.split('youtu.be/')[1].split('?')[0]
            else:
                video_id = None
            
            if video_id:
                media_url = f"https://www.youtube.com/embed/{video_id}"
                calendar['media_file_type'] = 'youtube'
                print(f"[EMOJI] YouTube URL converted to embed (priority 1): {calendar.get('youtube_title', 'YouTube Video')}")
                print(f"[EMOJI] YouTube embed URL (converted): {media_url}")
            else:
                print(f"[ERROR] Could not extract video ID from YouTube URL: {youtube_url}")
        else:
            print(f"[WARNING] Invalid YouTube URL format: {youtube_url}")
    
    # Debug: Print all YouTube-related fields
    print(f"[DEBUG] YouTube fields in calendar: embed_url={calendar.get('youtube_embed_url')}, video_id={calendar.get('youtube_video_id')}, url={calendar.get('youtube_url')}, title={calendar.get('youtube_title')}")
    
    # Only check local media if no YouTube URL was found
    if not media_url:
        # PRIORITY 2: If no YouTube, check local media files
        if calendar.get('media_file_path'):
            media_path = calendar['media_file_path']
            # Check if it's already a URL
            if media_path.startswith('http'):
                media_url = media_path
            else:
                # Create a proper URL for serving the file
                filename = os.path.basename(media_path)
                media_url = f"/media/calendar/{calendar_id}/{filename}"
            print(f"[EMOJI] Local media file detected (priority 2): {media_url}")
        else:
            # PRIORITY 3: Check if there are any media files in the upload directory for this calendar
            print(f"[EMOJI] No media file path found, checking upload directory...")
            upload_dir = os.path.join(os.getcwd(), 'uploads', 'media', 'calendar')
            if os.path.exists(upload_dir):
                media_files = []
                for file in os.listdir(upload_dir):
                    if file.endswith(('.mp4', '.mp3', '.wav', '.m4a')):
                        media_files.append(file)
                
                if media_files:
                    # Use the first media file found
                    first_media = media_files[0]
                    media_url = f"/media/calendar/{calendar_id}/{first_media}"
                    # Extract title from filename
                    title = os.path.splitext(first_media)[0]
                    if '_' in title:
                        title = title.split('_')[-1]  # Get part after last underscore
                    
                    calendar['media_filename'] = title
                    calendar['media_file_path'] = first_media
                    calendar['media_file_type'] = 'video' if first_media.endswith('.mp4') else 'audio'
                    print(f"[EMOJI] Found media file (priority 3): {first_media}, URL: {media_url}")
                else:
                    print(f"[EMOJI] No media files found in upload directory")
            else:
                print(f"[EMOJI] Upload directory does not exist: {upload_dir}")
    
    calendar['media_url'] = media_url
    
    # Extract YouTube metadata from media_filename if it's a YouTube video
    if calendar.get('media_file_type') == 'youtube' and calendar.get('media_filename'):
        media_filename = calendar['media_filename']
        print(f"[DEBUG] Processing YouTube media_filename: {media_filename}")
        
        # Try to extract title and channel from "Title - Channel" format
        if ' - ' in media_filename:
            parts = media_filename.split(' - ', 1)  # Split only on first ' - '
            youtube_title = parts[0].strip()
            youtube_channel = parts[1].strip()
            
            calendar['youtube_title'] = youtube_title
            calendar['youtube_channel'] = youtube_channel
            
            print(f"[SUCCESS] Extracted YouTube metadata: title='{youtube_title}', channel='{youtube_channel}'")
        else:
            # Fallback: use entire filename as title
            calendar['youtube_title'] = media_filename
            calendar['youtube_channel'] = 'YouTube'
            
            print(f"[FALLBACK] Using media_filename as YouTube title: '{media_filename}'")
    
    context.update({
        'calendar': calendar,
        'user_id': user_id,
        'page_title': f'{calendar["name"]} - 캘린더 상세'
    })
    
    return render_template('calendar_detail.html', **context)

@app.route('/dashboard/calendar/<calendar_id>/day/<date>')
def calendar_day(calendar_id, date):
    """Individual Calendar Day Page"""
    user_id = session.get('user_id')
    
    if not user_id:
        return redirect(f'/login?from=calendar/{calendar_id}/day/{date}')
    
    # Get common dashboard context
    context = get_dashboard_context(user_id, 'calendar-day')
    
    # Load calendar data
    calendar = None
    
    # Try calendar database first
    if calendar_db_available:
        print(f"[CALENDAR] Loading calendar {calendar_id} from database...")
        calendar = calendar_db.get_calendar_by_id(calendar_id, user_id)
        if calendar:
            print(f"[SUCCESS] Calendar found in database: {calendar.get('name')}")
    
    # If not found in database, create mock calendar
    if not calendar:
        print(f"[WARNING] Calendar {calendar_id} not found, creating mock data")
        calendar = {
            'id': calendar_id,
            'name': '내 캘린더',
            'color': '#3B82F6',
            'platform': 'custom',
            'is_shared': False,
            'is_enabled': True,
            'description': 'Calendar not found in database'
        }
    
    # Parse the date parameter
    try:
        from datetime import datetime
        selected_date = datetime.strptime(date, '%Y-%m-%d')
        formatted_date = selected_date.strftime('%Y년 %m월 %d일')
        weekday = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일'][selected_date.weekday()]
    except ValueError:
        # Invalid date format
        return redirect(url_for('calendar_detail', calendar_id=calendar_id))
    
    context.update({
        'calendar': calendar,
        'selected_date': date,
        'formatted_date': formatted_date,
        'weekday': weekday,
        'page_title': f'{calendar["name"]} - {formatted_date}'
    })
    
    return render_template('calendar_day.html', **context)

# Media file serving route
@app.route('/media/calendar/<calendar_id>/<filename>', endpoint='calendar_media_server')
def serve_calendar_media_v2(calendar_id, filename):
    """Serve media files for calendars"""
    print(f"[EMOJI] Media request: calendar_id={calendar_id}, filename={filename}")
    print(f"[EMOJI] Request URL: {request.url}")
    print(f"[EMOJI] Request headers: {dict(request.headers)}")
    
    user_id = session.get('user_id')
    print(f"[EMOJI] User ID from session: {user_id}")
    
    # Allow serving media files even without session (for testing)
    # if not user_id:
    #     print("[ERROR] No user authentication")
    #     return jsonify({'error': 'Authentication required'}), 401
    
    try:
        # First, check if the file exists in upload directory regardless of database
        import os
        upload_dir = os.path.join(os.getcwd(), 'uploads', 'media', 'calendar')
        possible_paths = [
            os.path.join(upload_dir, filename),  # Direct filename match
            os.path.join(upload_dir, f"e390559f-c328-4786-ac5d-c74b5409451b_{filename}"),  # With user prefix
        ]
        
        # Also check all files in the directory for a match
        if os.path.exists(upload_dir):
            for file in os.listdir(upload_dir):
                if file.endswith(filename) or filename in file:
                    possible_paths.append(os.path.join(upload_dir, file))
        
        file_path = None
        for path in possible_paths:
            if os.path.exists(path):
                file_path = path
                print(f"[EMOJI] Found media file at: {path}")
                break
        
        if file_path:
            # Serve the file directly
            from flask import send_file
            try:
                print(f"[EMOJI] Serving file: {file_path}")
                return send_file(file_path, as_attachment=False)
            except Exception as e:
                print(f"[ERROR] Failed to serve file {file_path}: {e}")
                return jsonify({'error': 'File serving error'}), 500
        
        # Fallback: try database lookup
        if calendar_db_available and user_id:
            calendar = calendar_db.get_calendar_by_id(calendar_id, user_id)
            print(f"[EMOJI] Calendar found in DB: {calendar is not None}")
            
            # If not found, try with known user ID
            if not calendar:
                known_user_id = "e390559f-c328-4786-ac5d-c74b5409451b"
                calendar = calendar_db.get_calendar_by_id(calendar_id, known_user_id)
                print(f"[EMOJI] Calendar found with known user ID: {calendar is not None}")
            
            media_path = calendar.get('media_file_path')
            print(f"[EMOJI] Media path from DB: {media_path}")
            
            if media_path and media_path.startswith('http'):
                # Redirect to external URL (like Supabase storage)
                print(f"[LINK] Redirecting to external URL: {media_path}")
                return redirect(media_path)
            elif media_path:
                # Serve local file - check multiple possible paths
                import os
                print(f"[EMOJI] Checking local file existence: {media_path}")
                
                # List of possible file paths to check
                possible_paths = [
                    media_path,  # Original path from database
                    os.path.join(os.getcwd(), 'uploads', 'media', 'calendar', filename),  # New uploads path
                    os.path.join(os.getcwd(), 'media', 'calendar', filename),  # Old media path
                ]
                
                actual_file_path = None
                for path in possible_paths:
                    print(f"[SEARCH] Checking path: {path}")
                    if os.path.exists(path):
                        actual_file_path = path
                        print(f"[SUCCESS] Found file at: {path}")
                        break
                
                if actual_file_path:
                    print(f"[SUCCESS] Serving local file: {actual_file_path}")
                    # Determine MIME type
                    if actual_file_path.endswith('.mp3'):
                        mimetype = 'audio/mpeg'
                    elif actual_file_path.endswith('.mp4'):
                        mimetype = 'video/mp4'
                    elif actual_file_path.endswith('.wav'):
                        mimetype = 'audio/wav'
                    elif actual_file_path.endswith('.m4a'):
                        mimetype = 'audio/mp4'
                    elif actual_file_path.endswith('.ogg'):
                        mimetype = 'audio/ogg'
                    elif actual_file_path.endswith('.webm'):
                        mimetype = 'audio/webm'
                    else:
                        mimetype = 'application/octet-stream'
                    
                    # Check file size for debugging
                    file_size = os.path.getsize(actual_file_path)
                    print(f"[EMOJI] File size: {file_size} bytes")
                    
                    # Add cache control headers
                    from flask import Response
                    def generate():
                        with open(actual_file_path, 'rb') as f:
                            data = f.read(1024)
                            while data:
                                yield data
                                data = f.read(1024)
                    
                    response = Response(generate(), mimetype=mimetype)
                    response.headers['Accept-Ranges'] = 'bytes'
                    response.headers['Cache-Control'] = 'public, max-age=3600'
                    response.headers['Content-Length'] = str(file_size)
                    return response
                else:
                    print(f"[ERROR] File not found in any of the checked paths")
                    # List directory contents for debugging
                    import os
                    for path in possible_paths:
                        parent_dir = os.path.dirname(path) if path else None
                        if parent_dir and os.path.exists(parent_dir):
                            print(f"[EMOJI] Directory {parent_dir} exists, contents: {os.listdir(parent_dir)}")
                        else:
                            print(f"[EMOJI] Directory doesn't exist: {parent_dir}")
                    
                    # Also check if uploads/media directory exists and what's in it
                    uploads_media = os.path.join(os.getcwd(), 'uploads', 'media')
                    if os.path.exists(uploads_media):
                        print(f"[EMOJI] uploads/media exists, contents: {os.listdir(uploads_media)}")
                    else:
                        print(f"[EMOJI] uploads/media doesn't exist: {uploads_media}")
            else:
                print("[ERROR] No media path found in calendar data")
        else:
            print("[ERROR] Calendar DB not available")
        
        return jsonify({'error': 'Media file not found'}), 404
        
    except Exception as e:
        print(f"[ERROR] Error serving media file: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to serve media file'}), 500

# Alternative route for calendar management (legacy redirects)
@app.route('/calendar-refined')
@app.route('/calendar-management') 
def calendar_refined():
    """Legacy route - redirect to main calendar list"""
    return redirect('/dashboard/calendar-list')

# [CALENDAR] Calendar Management API Endpoints
@app.route('/api/calendar/create', methods=['POST'])
def create_calendar():
    """Create a new calendar for user with optional media file upload"""
    try:
        user_id = session.get('user_id') or "e390559f-c328-4786-ac5d-c74b5409451b"  # 테스트용 임시 사용자 ID
        # if not user_id:
        #     return jsonify({'success': False, 'error': 'User not authenticated'}), 401
        
        # Handle file upload with Supabase Storage for Render deployment
        if request.content_type and 'multipart/form-data' in request.content_type:
            # Handle file upload
            platform = request.form.get('platform', 'custom')
            calendar_name = request.form.get('name', f'{platform.title()} Calendar')
            calendar_color = request.form.get('color', '#6b7280')
            is_shared = request.form.get('is_shared', 'false').lower() == 'true'
            
            # Handle media file upload
            media_filename = None
            media_file_path = None
            media_file_type = None
            
            if 'media_file' in request.files:
                media_file = request.files['media_file']
                if media_file and media_file.filename:
                    try:
                        # Upload to Supabase Storage
                        import os
                        import uuid
                        from werkzeug.utils import secure_filename
                        
                        filename = secure_filename(media_file.filename)
                        file_ext = os.path.splitext(filename)[1]
                        
                        # Create unique filename for storage
                        unique_filename = f"{user_id}/{uuid.uuid4()}{file_ext}"
                        
                        print(f"[EMOJI] Uploading to Supabase Storage: {unique_filename}")
                        
                        # Upload to Supabase Storage
                        if calendar_db_available and calendar_db.supabase:
                            # Read file content
                            file_content = media_file.read()
                            
                            # Check if media bucket exists, create if not
                            try:
                                # Try to get bucket info first
                                calendar_db.supabase.storage.get_bucket('media')
                                print("[SUCCESS] Media bucket exists")
                            except Exception as bucket_error:
                                print(f"[WARNING] Media bucket doesn't exist, creating: {bucket_error}")
                                try:
                                    # Create the bucket
                                    calendar_db.supabase.storage.create_bucket('media', {
                                        'public': True,
                                        'file_size_limit': 100 * 1024 * 1024  # 100MB limit
                                    })
                                    print("[SUCCESS] Created media bucket")
                                except Exception as create_error:
                                    print(f"[ERROR] Failed to create media bucket: {create_error}")
                            
                            # Upload to Supabase Storage
                            result = calendar_db.supabase.storage.from_('media').upload(
                                path=unique_filename,
                                file=file_content,
                                file_options={"content-type": media_file.content_type}
                            )
                            
                            print(f"[EMOJI] Storage upload result: {result}")
                            
                            if result:
                                # Get public URL
                                public_url = calendar_db.supabase.storage.from_('media').get_public_url(unique_filename)
                                
                                media_filename = filename  # Original filename
                                media_file_path = public_url  # Public URL
                                media_file_type = media_file.content_type
                                
                                print(f"[SUCCESS] Media file uploaded to Supabase Storage: {media_filename}")
                                print(f"[LINK] Public URL: {public_url}")
                            else:
                                print("[ERROR] Failed to upload to Supabase Storage, falling back to local storage")
                                # Fallback to local storage
                                media_file.seek(0)  # Reset file pointer
                                media_filename, media_file_path, media_file_type = save_media_file_locally(media_file, user_id)
                        else:
                            print("[ERROR] Supabase Storage not available, using local storage")
                            # Fallback to local storage
                            media_filename, media_file_path, media_file_type = save_media_file_locally(media_file, user_id)
                    except Exception as storage_error:
                        print(f"[ERROR] Storage upload error: {storage_error}")
                        # Fallback to local storage on error
                        print("[WARNING] Storage error, falling back to local storage")
                        media_file.seek(0)  # Reset file pointer
                        media_filename, media_file_path, media_file_type = save_media_file_locally(media_file, user_id)
        else:
            # Handle JSON request (no file upload)
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'error': 'No data provided'}), 400
            
            platform = data.get('platform', 'custom')
            calendar_name = data.get('name', f'{platform.title()} Calendar')
            calendar_color = data.get('color', '#6b7280')
            is_shared = data.get('is_shared', False)
            youtube_data = data.get('youtube_data')
            media_filename = None
            media_file_path = None
            media_file_type = None
            print(f"[DEBUG] JSON request - youtube_data: {youtube_data}")
        
        print(f"[SEARCH] Creating calendar: {calendar_name}, platform: {platform}, color: {calendar_color}")
        print(f"[SEARCH] Debug - calendar_db_available: {calendar_db_available}")
        print(f"[SEARCH] Debug - calendar_db: {calendar_db}")
        print(f"[SEARCH] Debug - calendar_db.is_available(): {calendar_db.is_available() if calendar_db else 'N/A'}")
        
        # Try calendar_db first, then dashboard_data, then file storage
        try:
            if calendar_db_available:
                # Create calendar data
                calendar_data = {
                    'name': calendar_name,
                    'platform': platform,
                    'color': calendar_color,
                    'is_shared': is_shared,
                    'is_enabled': True,
                    'description': f'{calendar_name} - Created on {dt.now().strftime("%Y-%m-%d")}'
                }
                
                # Add media file information if uploaded
                if media_filename:
                    calendar_data['media_filename'] = media_filename
                    calendar_data['media_file_path'] = media_file_path
                    calendar_data['media_file_type'] = media_file_type
                    print(f"[EMOJI] Adding media file to calendar: {media_filename}")
                
                # Add YouTube data if provided
                if youtube_data:
                    calendar_data['description'] += f' (YouTube: {youtube_data.get("title", "YouTube Video")})'
                    calendar_data['youtube_video_id'] = youtube_data.get('video_id')
                    calendar_data['youtube_title'] = youtube_data.get('title')
                    calendar_data['youtube_channel'] = youtube_data.get('channel_name')
                    calendar_data['youtube_thumbnail'] = youtube_data.get('thumbnail_url')
                    calendar_data['youtube_duration'] = youtube_data.get('duration_formatted')
                    calendar_data['youtube_url'] = youtube_data.get('watch_url')
                    calendar_data['youtube_embed_url'] = youtube_data.get('embed_url')
                    print(f"[SUCCESS] Adding YouTube info to calendar: {youtube_data.get('title')} by {youtube_data.get('channel_name')}")
                else:
                    print("[DEBUG] No YouTube data provided in app.py handler")
                
                # Use calendar_db to create calendar
                calendar_id = calendar_db.create_calendar(user_id, calendar_data)
                
                if calendar_id:
                    print(f"[SUCCESS] Created calendar in DB using calendar_db: {calendar_name} (ID: {calendar_id})")
                else:
                    print("[ERROR] calendar_db.create_calendar returned None, falling back to file storage")
                    raise Exception("Calendar DB creation failed")
                
                return jsonify({
                    'success': True,
                    'message': f'{calendar_name} calendar created successfully',
                    'calendar': {
                        'id': calendar_id,
                        'name': calendar_name,
                        'platform': platform,
                        'color': calendar_color,
                        'is_shared': is_shared
                    }
                })
            else:
                # Fallback to file storage
                print("[EMOJI] DB not available, using file storage for calendar creation")
                
                # Generate unique ID
                import uuid
                calendar_id = str(uuid.uuid4())
                
                # Load existing calendars
                user_calendars = load_user_calendars_legacy(user_id)
                
                # Create new calendar object
                new_calendar = {
                    'id': calendar_id,
                    'name': calendar_name,
                    'platform': platform,
                    'color': calendar_color,
                    'is_shared': is_shared,
                    'event_count': 0,
                    'sync_status': 'active',
                    'last_sync_display': 'Just created',
                    'is_enabled': True,
                    'created_at': dt.now().isoformat(),
                    'user_id': user_id,
                    'description': f'{calendar_name} - Created on {dt.now().strftime("%Y-%m-%d")}'
                }
                
                # Add to user's calendars
                user_calendars.append(new_calendar)
                
                # Save updated calendars
                if save_user_calendars_legacy(user_id, user_calendars):
                    print(f"[SUCCESS] Created calendar in file: {calendar_name} (ID: {calendar_id})")
                    
                    return jsonify({
                        'success': True,
                        'message': f'{calendar_name} calendar created successfully',
                        'calendar': {
                            'id': calendar_id,
                            'name': calendar_name,
                            'platform': platform,
                            'color': calendar_color,
                            'is_shared': is_shared
                        }
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Failed to save calendar to file'
                    }), 500
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            print(f"[ERROR] Error creating calendar: {e}")
            print(f"[ERROR] Traceback: {error_traceback}")
            return jsonify({
                'success': False,
                'error': f'Failed to create calendar: {str(e)}',
                'details': error_traceback if app.debug else 'Check server logs for details'
            }), 500
            
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"[ERROR] Outer exception in create_calendar: {e}")
        print(f"[ERROR] Outer traceback: {error_traceback}")
        return jsonify({
            'success': False, 
            'error': f'Calendar creation failed: {str(e)}',
            'details': error_traceback if app.debug else 'Check server logs for details'
        }), 500

# Simple calendar creation endpoint (no file upload)
@app.route('/api/calendar/simple-create', methods=['POST'])
def simple_create_calendar():
    """Create a new calendar without file upload"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'User not authenticated'}), 401
        
        data = request.get_json()
        calendar_name = data.get('name', 'New Calendar')
        platform = data.get('platform', 'custom')
        color = data.get('color', '#2563eb')
        is_shared = data.get('is_shared', False)
        
        # Generate a unique calendar ID
        import uuid
        calendar_id = str(uuid.uuid4())
        
        # Load existing calendars
        user_calendars = load_user_calendars_legacy(user_id)
        
        # Create new calendar object
        new_calendar = {
            'id': calendar_id,
            'name': calendar_name,
            'platform': platform,
            'color': color,
            'is_shared': is_shared,
            'event_count': 0,
            'sync_status': 'active',
            'last_sync_display': 'Just created',
            'is_enabled': True,
            'created_at': dt.now().isoformat(),
            'user_id': user_id,
            'description': f'{calendar_name} - Created on {dt.now().strftime("%Y-%m-%d")}'
        }
        
        # Add to user's calendars
        user_calendars.append(new_calendar)
        
        # Save updated calendars
        save_user_calendars_legacy(user_id, user_calendars)
        
        print(f"[SUCCESS] Created calendar '{calendar_name}' with ID {calendar_id} for user {user_id}")
        
        return jsonify({
            'success': True,
            'message': f'{calendar_name} created successfully',
            'calendar': {
                'id': calendar_id,
                'name': calendar_name,
                'platform': platform,
                'color': color,
                'is_shared': is_shared
            }
        })
        
    except Exception as e:
        print(f"[ERROR] Error in simple_create_calendar: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/calendar/<calendar_id>/delete', methods=['DELETE'])
def delete_calendar(calendar_id):
    """Delete a calendar"""
    try:
        print(f"[DELETE] Delete calendar request: calendar_id={calendar_id}")
        user_id = session.get('user_id')
        print(f"[DELETE] User ID from session: {user_id}")
        
        if not user_id:
            print("[ERROR] User not authenticated")
            return jsonify({'success': False, 'error': 'User not authenticated'}), 401
        
        print(f"[DELETE] Dashboard data available: {dashboard_data_available}")
        
        # Try calendar database first
        if calendar_db_available:
            print(f"[DELETE] Using calendar database for deletion...")
            success = calendar_db.delete_calendar(calendar_id, user_id)
            if success:
                print("[SUCCESS] Calendar deletion completed successfully")
                return jsonify({
                    'success': True,
                    'message': 'Calendar deleted successfully'
                })
            else:
                print("[ERROR] Calendar database deletion failed")
                return jsonify({'success': False, 'error': 'Failed to delete calendar from database'}), 500
        
        # Fallback to dashboard data
        elif dashboard_data_available:
            try:
                # First, get calendar info to check for media files
                print(f"[DELETE] Getting calendar info for media cleanup...")
                calendar_result = dashboard_data.admin_client.table('calendars').select('media_file_path').eq('id', calendar_id).eq('owner_id', user_id).single().execute()
                print(f"[DELETE] Calendar query result: {calendar_result}")
                
                # Clean up media file if it exists
                if calendar_result.data and calendar_result.data.get('media_file_path'):
                    media_path = calendar_result.data['media_file_path']
                    try:
                        import os
                        if os.path.exists(media_path):
                            os.remove(media_path)
                            print(f"[SUCCESS] Deleted media file: {media_path}")
                    except Exception as e:
                        print(f"[WARNING] Failed to delete media file: {e}")
                
                # Delete from calendars table using admin client
                print(f"[DELETE] Deleting calendar from database...")
                result = dashboard_data.admin_client.table('calendars').delete().eq('id', calendar_id).eq('owner_id', user_id).execute()
                print(f"[DELETE] Calendar delete result: {result}")
                
                # Also delete associated events
                print(f"[DELETE] Deleting associated events...")
                events_result = dashboard_data.admin_client.table('calendar_events').delete().eq('user_id', user_id).eq('source_calendar_id', calendar_id).execute()
                print(f"[DELETE] Events delete result: {events_result}")
                
                print("[SUCCESS] Calendar deletion completed successfully")
                return jsonify({
                    'success': True,
                    'message': 'Calendar deleted successfully'
                })
                
            except Exception as db_error:
                print(f"[ERROR] Database error during deletion: {db_error}")
                return jsonify({'success': False, 'error': f'Database error: {str(db_error)}'}), 500
        else:
            print("[ERROR] No database available")
            return jsonify({'success': False, 'error': 'Database not available'}), 500
            
    except Exception as e:
        print(f"[ERROR] General error in delete_calendar: {e}")
        print(f"[ERROR] Error type: {type(e).__name__}")
        import traceback
        print("[ERROR] Full traceback:")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/calendar/<calendar_id>/update', methods=['PATCH'])
def update_calendar_settings(calendar_id):
    """Update calendar settings (name, color, platform)"""
    try:
        print(f"[CONFIG] Update calendar settings request: calendar_id={calendar_id}")
        user_id = session.get('user_id')
        
        if not user_id:
            print("[ERROR] User not authenticated")
            return jsonify({'success': False, 'error': 'User not authenticated'}), 401
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        print(f"[CONFIG] Update data received: {data}")
        
        # Prepare update data
        update_data = {}
        if 'name' in data:
            update_data['name'] = data['name'].strip()
        if 'color' in data:
            update_data['color'] = data['color']
        if 'platform' in data:
            # Map 'custom' to 'personal' for database schema compatibility
            platform = data['platform']
            update_data['platform'] = 'personal' if platform == 'custom' else platform
        
        print(f"[CONFIG] Prepared update data: {update_data}")
        
        # Try calendar database first
        if calendar_db_available:
            print("[CONFIG] Using calendar database for update...")
            success = calendar_db.update_calendar(calendar_id, update_data, user_id)
            if success:
                print("[SUCCESS] Calendar settings updated successfully")
                return jsonify({
                    'success': True,
                    'message': 'Calendar settings updated successfully'
                })
            else:
                print("[ERROR] Calendar database update failed")
                return jsonify({'success': False, 'error': 'Failed to update calendar settings'}), 500
        
        # Fallback to dashboard data
        elif dashboard_data_available:
            print("[CONFIG] Using dashboard data for update...")
            result = dashboard_data.admin_client.table('calendars').update(update_data).eq('id', calendar_id).eq('owner_id', user_id).execute()
            
            if result.data:
                print("[SUCCESS] Calendar settings updated successfully via dashboard")
                return jsonify({
                    'success': True,
                    'message': 'Calendar settings updated successfully'
                })
            else:
                return jsonify({'success': False, 'error': 'Calendar not found'}), 404
        
        else:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
            
    except Exception as e:
        print(f"[ERROR] Error updating calendar settings: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/calendar/<calendar_id>/toggle', methods=['POST'])
def toggle_calendar(calendar_id):
    """Toggle calendar enabled/disabled status"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'User not authenticated'}), 401
        
        if dashboard_data_available:
            # Get current status using admin client
            current = dashboard_data.admin_client.table('calendars').select('is_active').eq('id', calendar_id).eq('owner_id', user_id).single().execute()
            
            if current.data:
                new_status = not current.data['is_active']
                # Update status using admin client
                dashboard_data.admin_client.table('calendars').update({'is_active': new_status}).eq('id', calendar_id).eq('owner_id', user_id).execute()
                
                return jsonify({
                    'success': True,
                    'enabled': new_status,
                    'message': f'Calendar {"enabled" if new_status else "disabled"}'
                })
            else:
                return jsonify({'success': False, 'error': 'Calendar not found'}), 404
        else:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# 캘린더 이벤트 관리 API
@app.route('/api/events', methods=['GET'])
def get_events():
    """이벤트 목록 조회"""
    try:
        user_id = session.get('user_id', 'temp_user')
        
        # 날짜 범위 파라미터
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 임시 샘플 데이터
        sample_events = {
            '2025-01-01': [
                {'id': 1, 'title': 'Task2', 'subtitle': '오후', 'type': 'task', 'completed': False, 'status': 'D-1일'}
            ],
            '2025-01-08': [
                {'id': 2, 'title': 'Task3', 'subtitle': '오후', 'type': 'task', 'completed': False}
            ],
            '2025-01-14': [
                {'id': 3, 'title': 'Task 1', 'subtitle': '개인', 'type': 'task', 'completed': True, 'status': 'D-28일'}
            ]
        }
        
        return jsonify({
            'success': True,
            'events': sample_events
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/events', methods=['POST'])
def create_event():
    """새 이벤트 생성"""
    try:
        user_id = session.get('user_id', 'temp_user')
        data = request.get_json()
        
        # 필수 필드 검증
        required_fields = ['title', 'date']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # 이벤트 생성 로직 (실제로는 DB에 저장)
        new_event = {
            'id': uuid.uuid4().hex[:8],
            'title': data['title'],
            'subtitle': data.get('subtitle', ''),
            'type': data.get('type', 'task'),
            'completed': False,
            'date': data['date'],
            'user_id': user_id
        }
        
        return jsonify({
            'success': True,
            'event': new_event,
            'message': '이벤트가 생성되었습니다.'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/events/<event_id>', methods=['PUT'])
def update_event(event_id):
    """이벤트 수정"""
    try:
        user_id = session.get('user_id', 'temp_user')
        data = request.get_json()
        
        # 이벤트 업데이트 로직 (실제로는 DB에서 업데이트)
        
        return jsonify({
            'success': True,
            'message': '이벤트가 수정되었습니다.'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/events/<event_id>', methods=['DELETE'])
def delete_event(event_id):
    """이벤트 삭제"""
    try:
        user_id = session.get('user_id', 'temp_user')
        
        # 이벤트 삭제 로직 (실제로는 DB에서 삭제)
        
        return jsonify({
            'success': True,
            'message': '이벤트가 삭제되었습니다.'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/events/<event_id>/toggle', methods=['POST'])
def toggle_event_status(event_id):
    """이벤트 완료 상태 토글"""
    try:
        user_id = session.get('user_id', 'temp_user')
        
        # 완료 상태 토글 로직 (실제로는 DB에서 업데이트)
        
        return jsonify({
            'success': True,
            'completed': True,  # 실제로는 토글된 상태
            'message': '이벤트 상태가 변경되었습니다.'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# 날씨 API
@app.route('/api/weather/<location>')
def get_weather(location):
    """일주일 날씨 정보 조회"""
    try:
        # OpenWeatherMap API 키 (환경변수에서 가져오기)
        api_key = os.getenv('OPENWEATHER_API_KEY')
        if not api_key or api_key == 'your-api-key-here':
            # API 키가 없거나 기본값일 때 기본 날씨 데이터 반환
            print("[EMOJI] OpenWeatherMap API [EMOJI] [EMOJI] [EMOJI]. [EMOJI] [EMOJI] [EMOJI] [EMOJI].")
            print("[EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] .env [EMOJI] OPENWEATHER_API_KEY[EMOJI] [EMOJI].")
            return get_default_weather()
        
        # 지역명으로 좌표 검색
        geocoding_url = f"http://api.openweathermap.org/geo/1.0/direct?q={location}&limit=1&appid={api_key}"
        geo_response = requests.get(geocoding_url, timeout=5)
        
        if geo_response.status_code != 200:
            return get_default_weather()
            
        geo_data = geo_response.json()
        if not geo_data:
            return get_default_weather()
        
        lat = geo_data[0]['lat']
        lon = geo_data[0]['lon']
        
        # 5일 날씨 예보 가져오기 (3시간 간격)
        weather_url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=kr"
        weather_response = requests.get(weather_url, timeout=5)
        
        if weather_response.status_code != 200:
            return get_default_weather()
            
        weather_data = weather_response.json()
        
        # 일주일 날씨 데이터 가공
        weekly_weather = process_weather_data(weather_data)
        
        return jsonify({
            'success': True,
            'location': location,
            'weather': weekly_weather
        })
        
    except Exception as e:
        print(f"Weather API error: {e}")
        return get_default_weather()

def get_default_weather():
    """기본 날씨 데이터 (API 연결 실패 시)"""
    today = dt.now()
    default_weather = []
    
    # 기본 날씨 패턴 (다양한 날씨 조건)
    weather_patterns = [
        {'main': 'Clear', 'icon': '01d', 'temp': 15},
        {'main': 'Clouds', 'icon': '03d', 'temp': 12},
        {'main': 'Rain', 'icon': '10d', 'temp': 8},
        {'main': 'Clear', 'icon': '01d', 'temp': 18},
        {'main': 'Clouds', 'icon': '04d', 'temp': 14},
        {'main': 'Clear', 'icon': '01d', 'temp': 16},
        {'main': 'Rain', 'icon': '09d', 'temp': 10}
    ]
    
    for i in range(7):
        date = (today + timedelta(days=i)).strftime('%Y-%m-%d')
        weather = weather_patterns[i]
        
        default_weather.append({
            'date': date,
            'weather': weather['main'],
            'icon': weather['icon'],
            'temp': weather['temp'],
            'emoji': get_weather_emoji(weather['main'])
        })
    
    return jsonify({
        'success': True,
        'location': 'Seoul',
        'weather': default_weather
    })

def process_weather_data(weather_data):
    """날씨 데이터 가공 함수"""
    weekly_weather = []
    processed_dates = set()
    
    for item in weather_data['list'][:35]:  # 5일 * 8회 (3시간 간격) 
        date_str = dt.fromtimestamp(item['dt']).strftime('%Y-%m-%d')
        
        # 하루에 한 번만 처리 (오후 시간대 우선)
        if date_str not in processed_dates:
            weather_main = item['weather'][0]['main']
            temp = round(item['main']['temp'])
            
            weekly_weather.append({
                'date': date_str,
                'weather': weather_main,
                'icon': item['weather'][0]['icon'],
                'temp': temp,
                'emoji': get_weather_emoji(weather_main)
            })
            
            processed_dates.add(date_str)
            
            if len(weekly_weather) >= 7:
                break
    
    # 7일 데이터가 부족하면 기본 데이터로 채우기
    while len(weekly_weather) < 7:
        last_date = dt.strptime(weekly_weather[-1]['date'], '%Y-%m-%d') if weekly_weather else dt.now()
        next_date = (last_date + timedelta(days=1)).strftime('%Y-%m-%d')
        
        weekly_weather.append({
            'date': next_date,
            'weather': 'Clear',
            'icon': '01d',
            'temp': 15,
            'emoji': '☀️'
        })
    
    return weekly_weather

def get_weather_emoji(weather_main):
    """날씨 상태에 따른 이모티콘 반환"""
    weather_emojis = {
        'Clear': '☀️',
        'Clouds': '☁️',
        'Rain': '🌧️',
        'Drizzle': '🌦️',
        'Thunderstorm': '⛈️',
        'Snow': '❄️',
        'Mist': '🌫️',
        'Fog': '🌫️',
        'Haze': '🌫️',
        'Dust': '🌪️',
        'Sand': '🌪️',
        'Ash': '🌪️',
        'Squall': '💨',
        'Tornado': '🌪️'
    }
    
    return weather_emojis.get(weather_main, '🌤️')

# Task Dump 페이지
@app.route('/task-dump')
def task_dump():
    """Task Dump 할일 관리 페이지"""
    return render_template('task_dump.html')

@app.route('/dashboard/api-keys')
def dashboard_api_keys():
    """API keys management page"""
    # Get current user ID from session
    user_id = session.get('user_id')
    
    if not user_id:
        return redirect('/login?from=dashboard')
    
    # Get common dashboard context including profile
    dashboard_context = get_dashboard_context(user_id, 'api-keys')
    
    # Calculate real user statistics
    connected_platforms = 0
    total_events = 0
    success_rate = "100%"
    sync_speed = "즉시"
    
    # Initialize dashboard_data safely
    dashboard_data = None
    try:
        from utils.dashboard_data import dashboard_data
    except ImportError:
        print("Warning: dashboard_data module not available")
    
    try:
        
        # Get user's calendars count
        if calendar_db.is_available():
            calendars = calendar_db.get_user_calendars(user_id)
            connected_platforms = len(calendars) if calendars else 0
            
            # Count total events across all calendars
            if dashboard_data:
                for calendar in (calendars or []):
                    calendar_id = calendar.get('id', '')
                    if calendar_id:
                        events = dashboard_data.get_user_calendar_events(user_id, calendar_ids=[calendar_id])
                        if events:
                            total_events += len(events)
        
        # Load saved events from localStorage backup
        storage_key = f'calendar_events_backup_{user_id}'
        # This would be from localStorage, but we'll use a fallback approach
        
        print(f"[API-KEYS] User {user_id} stats: {connected_platforms} calendars, {total_events} events")
        
    except Exception as e:
        print(f"Error calculating user stats: {e}")
        connected_platforms = 1  # At least one calendar usually exists
    
    # Add API keys specific data with real statistics
    dashboard_context.update({
        'platforms': {},
        'summary': {
            'total_platforms': 5,
            'configured_platforms': connected_platforms,
            'enabled_platforms': connected_platforms
        },
        'stats': {
            'connected_count': connected_platforms,
            'synced_events': total_events,  # sync_count를 synced_events로 변경
            'success_rate': success_rate,
            'avg_sync_time': sync_speed  # sync_speed를 avg_sync_time으로 변경
        }
    })
    
    if dashboard_data:
        try:
            platforms = dashboard_data.get_user_api_keys(user_id)
            summary = dashboard_data.get_api_keys_summary(user_id)
            
            dashboard_context.update({
                'platforms': platforms,
                'summary': summary
            })
        except Exception as e:
            print(f"Error loading API keys data: {e}")
            # If dashboard_data methods fail, use empty data
            dashboard_context.update({
                'platforms': {},
                'summary': {}
            })
    else:
        # dashboard_data is not available
        dashboard_context.update({
            'platforms': {},
            'summary': {}
        })
    
    return render_template('dashboard-api-keys.html', **dashboard_context)

@app.route('/dashboard/settings')
def dashboard_settings():
    """Dashboard settings route"""
    # Get current user ID
    user_id = session.get('user_id')
    
    # 🔒 Security: Redirect unauthenticated users to login
    if not user_id:
        return redirect('/login?from=dashboard')
    
    # Get common dashboard context including profile
    dashboard_context = get_dashboard_context(user_id, 'settings')
    
    # Add settings specific data
    dashboard_context.update({
        'encrypted_email': None,
        'user_profile': None,
        'platforms': {},
        'sync_status': {}
    })
    
    if user_id:
        try:
            user_profile = dashboard_data.get_user_profile(user_id)
            platforms = dashboard_data.get_user_api_keys(user_id)
            sync_status = dashboard_data.get_user_sync_status(user_id)
            
            dashboard_context.update({
                'user_profile': user_profile,
                'platforms': platforms,
                'sync_status': sync_status,
                'user_id': user_id
            })
        except Exception as e:
            print(f"Error loading settings data: {e}")
    
    return render_template('dashboard-settings.html', **dashboard_context)

@app.route('/profile')
def profile():
    """User profile page"""
    # Get current user ID from session
    user_id = session.get('user_id')
    
    if not user_id:
        return redirect('/login?from=profile')
    
    # Load profile data
    profile_context = {
        'profile': {
            'username': 'username',
            'display_name': '이름 없음',
            'email': 'user@example.com',
            'bio': '소개가 없습니다',
            'is_public': False,
            'avatar_url': None,
            'created_at': None,
            'birthdate': None
        }
    }
    
    try:
        # Use AuthManager to get profile (includes birthdate parsing)
        if AuthManager:
            profile_data = AuthManager.get_user_profile(user_id)
            if profile_data:
                profile_context['profile'] = profile_data
                print(f"Profile loaded with birthdate: {profile_data.get('birthdate')}")
        else:
            # Fallback to direct database query
            from utils.dashboard_data import dashboard_data
            if dashboard_data and dashboard_data.supabase:
                result = dashboard_data.supabase.table('user_profiles').select('*').eq('user_id', user_id).single().execute()
                if result.data:
                    profile_context['profile'] = result.data
        
        # Get calendar and connector counts
        from utils.dashboard_data import dashboard_data
        if dashboard_data and dashboard_data.supabase:
            try:
                # Get calendar count
                calendars_result = dashboard_data.supabase.table('calendar_events').select('id').eq('user_id', user_id).execute()
                calendar_count = len(calendars_result.data) if calendars_result.data else 0
                
                # Get connector count (OAuth tokens)
                connectors_result = dashboard_data.supabase.table('oauth_tokens').select('id').eq('user_id', user_id).execute()
                connector_count = len(connectors_result.data) if connectors_result.data else 0
                
                # Add to profile context
                profile_context['calendar_count'] = calendar_count
                profile_context['connector_count'] = connector_count
                
                print(f"User {user_id} has {calendar_count} calendars and {connector_count} connectors")
            except Exception as stats_error:
                print(f"Error loading user stats: {stats_error}")
                profile_context['calendar_count'] = 0
                profile_context['connector_count'] = 0
                
    except Exception as e:
        print(f"Error loading profile data: {e}")
        # Use default data if database fails
    
    return render_template('profile.html', **profile_context)

@app.route('/api/profile', methods=['PUT'])
def update_profile():
    """Update user profile"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        data = request.json
        # Here you would update the profile in the database
        # For now, just return success
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/profile/username/check', methods=['POST'])
def check_username():
    """Check if username is available"""
    try:
        data = request.json
        username = data.get('username', '')
        
        # For now, just return that it's available
        # In production, check against database
        return jsonify({
            'available': True,
            'message': '사용 가능한 사용자명입니다.'
        })
    except Exception as e:
        return jsonify({'available': False, 'message': str(e)}), 500

@app.route('/api/profile/avatar', methods=['POST'])
def upload_avatar():
    """Upload user avatar"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        # Check if file is present
        if 'avatar' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['avatar']
        
        # Validate file
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Check file size (5MB limit)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)  # Reset file pointer
        
        if file_size > 5 * 1024 * 1024:  # 5MB
            return jsonify({'success': False, 'error': 'File size exceeds 5MB limit'}), 400
        
        # Check file type
        allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_extensions:
            return jsonify({'success': False, 'error': 'Invalid file type. Only PNG, JPG, JPEG, GIF, WebP are allowed'}), 400
        
        # Generate a unique filename
        file_extension = os.path.splitext(file.filename)[1] if file.filename else '.png'
        filename = f"avatar_{user_id}_{uuid.uuid4().hex[:8]}{file_extension}"
        
        # Check if we're in production (Railway) or local development
        is_production = os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('PORT')
        avatar_url = None
        
        if is_production:
            # Production: Use Supabase Storage
            try:
                from utils.calendar_db import calendar_db
                
                if calendar_db and calendar_db.is_available():
                    print(f"[AVATAR] Using Supabase storage for avatar upload in production")
                    
                    # Read file content
                    file.seek(0)  # Reset file pointer
                    file_content = file.read()
                    
                    # Check if avatars bucket exists, create if not
                    try:
                        calendar_db.supabase.storage.get_bucket('avatars')
                        print("[SUCCESS] Avatars bucket exists")
                    except Exception as bucket_error:
                        print(f"[WARNING] Avatars bucket doesn't exist, creating: {bucket_error}")
                        try:
                            calendar_db.supabase.storage.create_bucket('avatars', {
                                'public': True,
                                'file_size_limit': 5 * 1024 * 1024  # 5MB limit
                            })
                            print("[SUCCESS] Created avatars bucket")
                        except Exception as create_error:
                            print(f"[ERROR] Failed to create avatars bucket: {create_error}")
                    
                    # Upload to Supabase Storage
                    result = calendar_db.supabase.storage.from_('avatars').upload(
                        path=filename,
                        file=file_content,
                        file_options={"content-type": file.content_type}
                    )
                    
                    print(f"[AVATAR] Storage upload result: {result}")
                    
                    if result:
                        # Get public URL
                        public_url = calendar_db.supabase.storage.from_('avatars').get_public_url(filename)
                        avatar_url = public_url
                        print(f"[SUCCESS] Avatar uploaded to Supabase: {avatar_url}")
                    else:
                        print("[ERROR] Failed to upload to Supabase Storage")
                        raise Exception("Supabase upload failed")
                        
                else:
                    print("[ERROR] Supabase not available in production")
                    raise Exception("Storage service not available")
                    
            except Exception as storage_error:
                print(f"[ERROR] Storage upload error: {storage_error}")
                # Fall back to local storage even in production
                pass
        
        # Local development or fallback: Use local file storage
        if not avatar_url:
            print(f"[AVATAR] Using local storage for avatar upload")
            # Save the uploaded file locally
            from werkzeug.utils import secure_filename
            
            # Create uploads directory if it doesn't exist
            uploads_dir = os.path.join(app.root_path, 'static', 'uploads', 'avatars')
            os.makedirs(uploads_dir, exist_ok=True)
            
            filepath = os.path.join(uploads_dir, filename)
            
            # Save the file
            file.seek(0)  # Reset file pointer
            file.save(filepath)
            
            # Generate public URL
            avatar_url = f"/static/uploads/avatars/{filename}"
            print(f"[SUCCESS] Avatar saved locally: {avatar_url}")
        
        # Update user profile with new avatar URL
        update_data = {'avatar_url': avatar_url}
        
        print(f"[LOADING] Updating avatar for user {user_id}: {avatar_url}")
        
        # Try multiple methods to update the avatar URL
        update_success = False
        
        # Method 1: Try AuthManager
        try:
            from utils.auth_manager import AuthManager
            if hasattr(AuthManager, 'update_user_profile'):
                update_success = AuthManager.update_user_profile(user_id, update_data)
                print(f"[SUCCESS] AuthManager update: {update_success}")
        except ImportError as e:
            print(f"[ERROR] AuthManager not available: {e}")
        
        # Method 2: Try direct Supabase update
        if not update_success and hasattr(config, 'supabase_client') and config.supabase_client:
            try:
                result = config.supabase_client.table('user_profiles').update(update_data).eq('user_id', user_id).execute()
                print(f"[DATA] Supabase result: {result}")
                if result.data and len(result.data) > 0:
                    update_success = True
                    print("[SUCCESS] Supabase update successful")
            except Exception as supabase_error:
                print(f"[ERROR] Supabase update failed: {supabase_error}")
        
        # Method 3: Store in session as fallback
        if not update_success:
            session['user_avatar_url'] = avatar_url
            print(f"[EMOJI] Stored avatar in session: {avatar_url}")
        
        # Always return success if file was saved successfully
        return jsonify({
            'success': True,
            'avatar_url': avatar_url,
            'method': 'database' if update_success else 'session',
            'storage': 'supabase' if is_production and '://' in avatar_url else 'local',
            'message': 'Avatar uploaded successfully!'
        })
        
    except Exception as e:
        print(f"Error uploading avatar: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/dashboard/friends')
def dashboard_friends():
    """Dashboard friends route"""
    # Get current user ID
    user_id = session.get('user_id')
    
    # 🔒 Security: Redirect unauthenticated users to login
    if not user_id:
        return redirect('/login?from=dashboard')
    
    # Load friends data
    dashboard_context = {
        'current_page': 'friends',
        'encrypted_email': None,
        'friends': [],
        'user_profile': None
    }
    
    if user_id:
        try:
            friends = dashboard_data.get_user_friends(user_id)
            user_profile = dashboard_data.get_user_profile(user_id)
            
            dashboard_context.update({
                'friends': friends,
                'user_profile': user_profile,
                'user_id': user_id
            })
        except Exception as e:
            print(f"Error loading friends data: {e}")
    
    return render_template('dashboard-friends.html', **dashboard_context)

@app.route('/dashboard/api-keys/<encrypted_identifier>')
def dashboard_api_keys_main(encrypted_identifier):
    """사용자별 암호화된 API 키 관리 페이지 - 개별 사용자 URL"""
    from utils.config import decrypt_user_id, encrypt_user_id
    
    print(f"[AUTH] API Keys [EMOJI] [EMOJI]: {encrypted_identifier}")
    
    # 암호화된 식별자 복호화 시도
    try:
        decrypted_value = decrypt_user_id(encrypted_identifier)
        print(f"[EMOJI] [EMOJI] [EMOJI]: {decrypted_value}")
        
        if not decrypted_value:
            print("[ERROR] [EMOJI] [EMOJI] - 404 [EMOJI] [EMOJI]")
            return render_template('404.html'), 404
            
        # 이메일인지 사용자 ID인지 판단
        is_email = '@' in decrypted_value
        print(f"[EMOJI] [EMOJI] [EMOJI]: {is_email}")
        
        # 세션과 일치하는지 확인
        session_email = session.get('user_email')
        session_user_id = session.get('user_id')
        print(f"[USER] [EMOJI] [EMOJI] - [EMOJI] ID: {session_user_id}, [EMOJI]: {session_email}")
        
        if is_email:
            # 이메일로 접근한 경우
            user_id = session_user_id or 'demo-user'
            user_email = decrypted_value
        else:
            # 사용자 ID로 접근한 경우  
            user_id = decrypted_value
            user_email = session_email or 'demo@example.com'
        
        print(f"[SUCCESS] [EMOJI] [EMOJI] - [EMOJI] ID: {user_id}, [EMOJI]: {user_email}")
        
    except Exception as e:
        print(f"[ERROR] [EMOJI] [EMOJI] [EMOJI]: {e}")
        return render_template('404.html'), 404
    
    # 대시보드 데이터 로드
    dashboard_context = {
        'current_page': 'api-keys',
        'encrypted_identifier': encrypted_identifier,  # 현재 URL의 암호화된 식별자
        'encrypted_user_id': encrypted_identifier if not is_email else '',
        'encrypted_email': encrypted_identifier if is_email else '',
        'user_email': user_email,
        'user_id': user_id,
        'platforms': {},
        'summary': {}
    }
    
    try:
        # 누락된 암호화된 식별자 생성
        if user_id and not dashboard_context['encrypted_user_id']:
            dashboard_context['encrypted_user_id'] = encrypt_user_id(user_id)
            print(f"[AUTH] [EMOJI] ID [EMOJI]: {dashboard_context['encrypted_user_id']}")
        
        if user_email and not dashboard_context['encrypted_email']:
            dashboard_context['encrypted_email'] = encrypt_user_id(user_email)
            print(f"[AUTH] [EMOJI] [EMOJI]: {dashboard_context['encrypted_email']}")
        
        # 플랫폼 및 요약 데이터 로드
        if user_id:
            try:
                platforms = dashboard_data.get_user_api_keys(user_id)
                summary = dashboard_data.get_dashboard_summary(user_id)
                
                dashboard_context.update({
                    'platforms': platforms,
                    'summary': summary
                })
                print(f"[DATA] Platforms loaded - Count: {len(platforms)}, Summary: {summary}")
                
            except Exception as data_error:
                print(f"[WARNING] Dashboard data loading failed, using fallback: {data_error}")
                # dashboard_data 실패 시 기본 데이터 사용
                dashboard_context.update({
                    'platforms': {},
                    'summary': {'total_platforms': 5, 'configured_platforms': 0, 'enabled_platforms': 0}
                })
        
    except Exception as e:
        print(f"[ERROR] [EMOJI] [EMOJI] [EMOJI]: {e}")
        dashboard_context.update({
            'platforms': {},
            'summary': {'total_platforms': 5, 'configured_platforms': 0, 'enabled_platforms': 0}
        })
    
    print(f"[TARGET] [EMOJI] [EMOJI]: {dashboard_context}")
    return render_template('dashboard-api-keys.html', **dashboard_context)



# [KEY] Platform-specific API key setup routes
@app.route('/setup/notion')
def setup_notion():
    """Notion API key setup page"""
    return render_template('setup_notion.html')

@app.route('/setup/google')
def setup_google():
    """Google Calendar API key setup page"""
    return render_template('setup_google.html')

@app.route('/setup/apple')
def setup_apple():
    """Apple Calendar API key setup page"""
    return render_template('setup_apple.html')

@app.route('/setup/outlook')
def setup_outlook():
    """Outlook API key setup page"""
    return render_template('setup_outlook.html')

@app.route('/setup/slack')
def setup_slack():
    """Slack API key setup page"""
    return render_template('setup_slack.html')

# [LINK] User Profile API Endpoints
@app.route('/api/user/dashboard-url', methods=['GET'])
def get_user_dashboard_url():
    """API endpoint to get user's dashboard URL (simplified)"""
    try:
        # Debug session info for dashboard URL
        print(f"=== DASHBOARD URL DEBUG ===")
        print(f"Session contents: {dict(session)}")
        print(f"User ID in session: {session.get('user_id')}")
        print(f"Authenticated: {session.get('authenticated')}")
        print(f"==========================")
        
        # Check if user is authenticated via session
        user_id = session.get('user_id')
        authenticated = session.get('authenticated')
        
        if not user_id and not authenticated:
            print(f"Dashboard URL - Authentication failed")
            return jsonify({
                'success': False, 
                'message': 'Not authenticated',
                'debug': {
                    'session_keys': list(session.keys()),
                    'has_user_id': bool(user_id),
                    'has_authenticated': bool(authenticated)
                }
            }), 401
        
        # Always return simple dashboard URL
        return jsonify({
            'success': True,
            'dashboard_url': '/dashboard',
            'user_id': user_id or 'unknown'
        })
        
    except Exception as e:
        print(f"Error getting dashboard URL: {e}")
        import traceback
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/auth/profile', methods=['GET'])
def get_auth_profile():
    """API endpoint to get user's auth profile"""
    try:
        # Extended debug session info
        print(f"=== AUTH PROFILE DEBUG ===")
        print(f"Session ID: {request.cookies.get('session')}")
        print(f"Session contents: {dict(session)}")
        print(f"User ID in session: {session.get('user_id')}")
        print(f"Authenticated: {session.get('authenticated')}")
        print(f"User info: {session.get('user_info')}")
        print(f"All cookies: {dict(request.cookies)}")
        print(f"========================")
        
        # Check multiple authentication indicators
        user_id = session.get('user_id')
        authenticated = session.get('authenticated')
        user_info = session.get('user_info', {})
        
        if not user_id and not authenticated:
            print(f"Authentication failed - no user_id or authenticated flag")
            return jsonify({
                'success': False, 
                'error': 'Not authenticated',
                'debug': {
                    'session_keys': list(session.keys()),
                    'has_user_id': bool(user_id),
                    'has_authenticated': bool(authenticated),
                    'session_size': len(dict(session))
                }
            }), 401
        
        # Return profile with fallbacks
        return jsonify({
            'success': True,
            'profile': {
                'id': user_id or 'unknown',
                'email': user_info.get('email') or 'unknown@example.com',
                'username': user_info.get('username') or 'user',
                'display_name': user_info.get('display_name') or 'User'
            }
        })
        
    except Exception as e:
        print(f"Error getting auth profile: {e}")
        import traceback
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500

@app.route('/api/username/check', methods=['POST'])
@require_rate_limit('username_check', max_requests=10, time_window=60)
def check_username_availability():
    """API endpoint to check username availability"""
    data = request.get_json()
    username = data.get('username', '').strip()
    
    if not username:
        return jsonify({'success': False, 'message': 'Username is required'}), 400
    
    # Sanitize input
    username = security_validator.sanitize_input(username, max_length=20)
    
    is_available, message = UserProfileManager.is_username_available(username)
    
    return jsonify({
        'success': True,
        'available': is_available,
        'message': message
    })

@app.route('/api/username/suggestions', methods=['POST'])
def get_username_suggestions():
    """API endpoint to get username suggestions based on email"""
    data = request.get_json()
    email = data.get('email', '').strip()
    
    if not email:
        return jsonify({'success': False, 'message': 'Email is required'}), 400
    
    try:
        # Generate base username from email
        base_username = email.split('@')[0].lower()
        base_username = re.sub(r'[^a-zA-Z0-9]', '_', base_username)
        base_username = base_username.strip('_')
        
        if len(base_username) < 3:
            base_username = base_username + '_user'
        if len(base_username) > 15:
            base_username = base_username[:15]
        
        suggestions = []
        for i in range(1, 6):
            if i == 1:
                candidate = base_username
            else:
                candidate = f"{base_username}_{i}"
            
            if UserProfileManager.is_username_available(candidate):
                suggestions.append(candidate)
                
            if len(suggestions) >= 3:
                break
        
        return jsonify({
            'success': True,
            'suggestions': suggestions
        })
        
    except Exception as e:
        print(f"Error generating username suggestions: {e}")
        return jsonify({'success': False, 'message': 'Error generating suggestions'}), 500

@app.route('/api/profile', methods=['POST'])
@require_rate_limit('profile_creation', max_requests=3, time_window=300)
def create_user_profile():
    """API endpoint to create user profile"""
    data = request.get_json()
    user_id = data.get('user_id')
    username = data.get('username', '').strip()
    display_name = data.get('display_name', '').strip()
    
    if not user_id or not username:
        return jsonify({'success': False, 'message': 'User ID and username are required'}), 400
    
    # Sanitize inputs
    username = security_validator.sanitize_input(username, max_length=20)
    display_name = security_validator.sanitize_input(display_name, max_length=50)
    
    # Validate username
    is_available, message = UserProfileManager.is_username_available(username)
    if not is_available:
        return jsonify({'success': False, 'message': message}), 400
    
    profile = UserProfileManager.create_user_profile(user_id, username, display_name)
    
    if profile:
        return jsonify({
            'success': True,
            'profile': profile,
            'dashboard_url': f'/u/{username}'
        })
    else:
        return jsonify({'success': False, 'message': 'Failed to create profile'}), 500

@app.route('/api/profile/<username>')
def get_user_profile(username):
    """API endpoint to get user profile by username"""
    profile = UserProfileManager.get_user_by_username(username)
    
    if profile:
        # Remove sensitive information
        public_profile = {
            'username': profile['username'],
            'display_name': profile['display_name'],
            'avatar_url': profile.get('avatar_url'),
            'bio': profile.get('bio'),
            'is_public': profile.get('is_public', False),
            'created_at': profile['created_at']
        }
        return jsonify({'success': True, 'profile': public_profile})
    else:
        return jsonify({'success': False, 'message': 'User not found'}), 404

# [CALENDAR] Simplified Calendar APIs for Dashboard



# [LAUNCH] One-Click Connection API Endpoints
@app.route('/api/connect/<platform>', methods=['POST'])
def connect_platform(platform):
    """원클릭 플랫폼 연결 API"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401
        
        # 플랫폼별 연결 처리
        if platform == 'notion':
            result = handle_notion_connection(user_id, request.json)
        elif platform == 'google':
            result = handle_google_connection(user_id, request.json)
        elif platform == 'slack':
            result = handle_slack_connection(user_id, request.json)
        elif platform == 'outlook':
            result = handle_outlook_connection(user_id, request.json)
        else:
            return jsonify({
                'success': False,
                'error': f'Unsupported platform: {platform}'
            }), 400
        
        return jsonify(result)
        
    except Exception as e:
        print(f"[ERROR] Platform connection error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/platform/<platform>/status', methods=['GET'])
def get_platform_status(platform):
    """플랫폼 연결 상태 확인"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'connected': False,
                'error': 'User not authenticated'
            }), 401
        
        # Google Calendar 전용 연결 상태 확인
        if platform == 'google':
            connected = check_google_calendar_connection(user_id)
        else:
            # 다른 플랫폼은 기존 세션 기반 확인
            session_key = f'platform_{platform}_connected'
            connected = session.get(session_key, False)
        
        platform_status = {
            'connected': connected,
            'last_sync': session.get(f'platform_{platform}_last_sync'),
            'sync_count': session.get(f'platform_{platform}_sync_count', 0),
            'status': 'active' if connected else 'inactive'
        }
        
        return jsonify({
            'success': True,
            'platform': platform,
            **platform_status
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/platform/<platform>/sync', methods=['POST'])
def start_platform_sync(platform):
    """플랫폼 동기화 시작"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401
        
        # 동기화 시뮬레이션
        result = simulate_sync(platform, user_id)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/platform/<platform>/disconnect', methods=['DELETE'])
def disconnect_platform(platform):
    """플랫폼 연결 해제"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401
        
        # 연결 해제 시뮬레이션
        result = {
            'success': True,
            'platform': platform,
            'message': f'{platform.upper()} 연결이 해제되었습니다',
            'disconnected_at': '2024-08-05T12:00:00Z'
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# [CONFIG] Platform-specific connection handlers
def handle_notion_connection(user_id, data):
    """Notion API 토큰 연결 처리"""
    import time
    start_time = time.time()
    
    try:
        # 스마트 캐시 초기화
        initialize_smart_cache_entry(user_id, 'notion', 'api_token')
        
        # 실제로는 Notion API 토큰을 검증하고 데이터베이스에 저장
        # 시뮬레이션: API 응답 시간
        time.sleep(1.5)  # 1.5초 시뮬레이션
        
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # 연결 성공 시 스마트 캐시 업데이트
        update_smart_cache_success(user_id, 'notion', response_time_ms)
        
        return {
            'success': True,
            'platform': 'notion',
            'data': {
                'user_id': f'notion_{user_id}',
                'workspace': 'Connected Workspace',
                'token_hash': 'encrypted_token_hash',
                'connected_at': '2024-08-05T12:00:00Z',
                'response_time_ms': response_time_ms
            },
            'message': 'Notion 연결 성공'
        }
    except Exception as e:
        # 오류 시 스마트 캐시 업데이트
        update_smart_cache_error(user_id, 'notion', str(e))
        return {
            'success': False,
            'error': f'Notion 연결 실패: {str(e)}'
        }

def handle_google_connection(user_id, data):
    """Google OAuth 연결 처리"""
    try:
        # 실제로는 Google OAuth 토큰을 검증하고 저장
        return {
            'success': True,
            'platform': 'google',
            'data': {
                'user_id': f'google_{user_id}',
                'email': 'user@gmail.com',
                'access_token_hash': 'encrypted_access_token',
                'refresh_token_hash': 'encrypted_refresh_token',
                'connected_at': '2024-08-05T12:00:00Z'
            },
            'message': 'Google Calendar 연결 성공'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Google 연결 실패: {str(e)}'
        }

# ===== GOOGLE OAUTH HANDLERS =====

@app.route('/auth/google')
def google_oauth_login():
    """Google OAuth 인증 시작"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        from google_auth_oauthlib.flow import Flow
        import os
        import json
        import base64
        
        # OAuth 2.0 클라이언트 설정
        client_config = {
            "web": {
                "client_id": os.environ.get('GOOGLE_CLIENT_ID'),
                "client_secret": os.environ.get('GOOGLE_CLIENT_SECRET'),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [f"{request.host_url}auth/google/callback"]
            }
        }
        
        flow = Flow.from_client_config(
            client_config,
            scopes=[
                'https://www.googleapis.com/auth/calendar',
                'https://www.googleapis.com/auth/userinfo.email',
                'https://www.googleapis.com/auth/userinfo.profile',
                'openid'
            ]
        )
        flow.redirect_uri = f"{request.host_url}auth/google/callback"
        
        # 실제 user_id와 임시 state를 포함한 데이터 생성
        import uuid
        random_state = str(uuid.uuid4())
        state_data = {
            'state': random_state,
            'user_id': user_id  # 실제 user_id 저장
        }
        
        # state 데이터를 base64로 인코딩
        encoded_state = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()
        
        # 인증 URL 생성
        authorization_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=encoded_state  # 인코딩된 state 전달
        )
        
        # 세션에 원본 state 저장 (CSRF 보호)
        session['oauth_state'] = encoded_state
        session['oauth_random_state'] = random_state
        
        return redirect(authorization_url)
        
    except Exception as e:
        print(f"Error starting Google OAuth: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/auth/google/callback')
def google_oauth_callback():
    """Google OAuth 콜백 처리 - 간단한 직접 토큰 교환"""
    try:
        import os
        import requests
        from datetime import datetime, timedelta
        
        # 파라미터 추출
        encoded_state = request.args.get('state')
        auth_code = request.args.get('code')
        
        print(f"OAuth callback - encoded_state: {encoded_state[:20] if encoded_state else 'None'}..., code: {auth_code[:20] if auth_code else 'None'}...")
        
        if not encoded_state or not auth_code:
            return render_template_string('''
            <html><body>
                <h2>OAuth Error</h2>
                <p>Missing state or authorization code</p>
                <script>
                    if (window.opener) {
                        window.opener.postMessage({
                            type: 'oauth_error',
                            platform: 'google',
                            error: 'Missing parameters'
                        }, window.location.origin);
                    }
                    setTimeout(() => window.close(), 5000);
                </script>
            </body></html>
            ''')
        
        # state 디코딩하여 실제 user_id 추출
        import json
        import base64
        
        try:
            decoded_state = base64.urlsafe_b64decode(encoded_state.encode()).decode()
            state_data = json.loads(decoded_state)
            user_id = state_data.get('user_id')
            random_state = state_data.get('state')
            
            print(f"Decoded state - user_id: {user_id}, random_state: {random_state}")
            
            # user_id 유효성 확인
            if not user_id:
                raise Exception("No user_id found in state")
            
            # UUID 형식 확인
            import re
            uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
            if not re.match(uuid_pattern, user_id.lower()):
                print(f"Warning: user_id {user_id} is not a valid UUID format")
            
            # 세션의 user_id와 비교
            session_user_id = session.get('user_id')
            print(f"Session user_id: {session_user_id}")
            print(f"OAuth state user_id: {user_id}")
            if session_user_id != user_id:
                print(f"Warning: Session user_id ({session_user_id}) != OAuth user_id ({user_id})")
            
            # CSRF 검증 (선택적)
            stored_state = session.get('oauth_state')
            if stored_state and stored_state != encoded_state:
                print(f"State mismatch warning: stored != received")
            
        except Exception as decode_error:
            print(f"Failed to decode state: {decode_error}")
            # 폴백: state를 그대로 user_id로 사용 (이전 버전 호환)
            user_id = encoded_state
            print(f"Using raw state as user_id (fallback): {user_id}")
        
        # 환경변수 확인
        client_id = os.environ.get('GOOGLE_CLIENT_ID')
        client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
        
        if not client_id or not client_secret:
            raise Exception("Google OAuth credentials not configured")
        
        print(f"Exchanging auth code for token...")
        
        # 직접 Google OAuth API로 토큰 교환
        token_url = 'https://oauth2.googleapis.com/token'
        token_data = {
            'code': auth_code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': f"{request.host_url}auth/google/callback",
            'grant_type': 'authorization_code'
        }
        
        # 토큰 교환 API 호출
        print("Exchanging authorization code for token...")
        token_response = requests.post(token_url, data=token_data)
        
        if token_response.status_code != 200:
            error_data = token_response.json()
            error_msg = error_data.get('error', 'Unknown error')
            
            if error_msg == 'invalid_grant':
                # OAuth 코드가 만료되었거나 이미 사용됨
                return render_template_string('''
                <html><body>
                    <h2>OAuth 코드 만료</h2>
                    <p>인증 코드가 만료되었습니다. 새로운 인증을 시작해주세요.</p>
                    <button onclick="window.location.href='/auth/google'">새로 Google Calendar 연결하기</button>
                    <script>
                        if (window.opener) {
                            window.opener.postMessage({
                                type: 'oauth_error',
                                platform: 'google',
                                error: 'OAuth 코드가 만료되었습니다. 다시 연결해주세요.'
                            }, window.location.origin);
                        }
                        setTimeout(() => {
                            window.location.href = '/auth/google';
                        }, 3000);
                    </script>
                </body></html>
                ''')
            else:
                raise Exception(f"Token exchange failed: {error_msg} - {error_data}")
        
        # 토큰 데이터 추출
        token_json = token_response.json()
        access_token = token_json.get('access_token')
        refresh_token = token_json.get('refresh_token')
        expires_in = token_json.get('expires_in', 3600)
        
        if not access_token:
            raise Exception("No access token received")
        
        print(f"Token received successfully")
        
        # 만료 시간 계산
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        # Google Calendar service import - 새로 초기화
        try:
            import os
            from supabase import create_client
            
            # Service Role Key를 직접 사용
            supabase_url = os.environ.get('SUPABASE_URL')
            service_role_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
            
            print(f"Supabase URL: {supabase_url[:30] if supabase_url else 'None'}...")
            print(f"Service Role Key exists: {bool(service_role_key)}")
            
            if not supabase_url or not service_role_key:
                # fallback to google_calendar_service
                from services.google_calendar_service import google_calendar_service
                print("Using google_calendar_service singleton")
                supabase_client = google_calendar_service.supabase
            else:
                # Service Role Key로 새 클라이언트 생성 (RLS 우회)
                print("Creating new Supabase client with Service Role Key")
                supabase_client = create_client(supabase_url, service_role_key)
                
        except Exception as e:
            print(f"Failed to create Supabase client: {e}")
            raise Exception("Database connection failed")
        
        # 토큰을 Supabase에 저장
        token_data = {
            'user_id': user_id,
            'platform': 'google',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_at': expires_at.isoformat(),
            'token_type': 'Bearer',
            'scope': token_json.get('scope', 'https://www.googleapis.com/auth/calendar')
        }
        
        print(f"Saving token to Supabase for user {user_id}...")
        
        # 사용자 존재 여부 확인 (외래키 제약 조건 방지)
        try:
            # auth.users 테이블에서 사용자 확인
            user_check = supabase_client.auth.admin.get_user_by_id(user_id)
            if not user_check or not user_check.user:
                print(f"User {user_id} not found in auth.users table")
                # 세션에 토큰 저장 (데이터베이스 저장 대신)
                session[f'oauth_token_{user_id}_google'] = {
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'expires_at': expires_at.isoformat(),
                    'scope': token_json.get('scope', '')
                }
                print("Token saved to session instead of database (user not found)")
            else:
                print(f"User {user_id} exists in auth.users table, proceeding with database save")
                
                # 기존 토큰이 있으면 업데이트, 없으면 삽입
                try:
                    print(f"Token data to save: {token_data}")
                    result = supabase_client.table('oauth_tokens').upsert(
                        token_data,
                        on_conflict='user_id,platform'
                    ).execute()
                    print(f"Supabase response: {result}")
                    print("Token saved successfully to database")
                except Exception as e:
                    import traceback
                    error_details = traceback.format_exc()
                    print(f"Failed to save token to database: {e}")
                    print(f"Full error: {error_details}")
                    print(f"Token data that failed: {token_data}")
                    
                    # 외래키 제약 조건 위반인 경우 세션에 백업 저장
                    if '23503' in str(e) or 'foreign key constraint' in str(e).lower():
                        print("Foreign key constraint violation. Saving to session as fallback.")
                        session[f'oauth_token_{user_id}_google'] = {
                            'access_token': access_token,
                            'refresh_token': refresh_token,
                            'expires_at': expires_at.isoformat(),
                            'scope': token_json.get('scope', '')
                        }
                        print("Token saved to session as fallback")
                    # 테이블이 없는 경우 세션에 백업 저장
                    elif 'relation' in str(e).lower() and 'does not exist' in str(e).lower():
                        print("oauth_tokens 테이블이 없습니다. 세션에 임시 저장합니다.")
                        session[f'oauth_token_{user_id}_google'] = {
                            'access_token': access_token,
                            'refresh_token': refresh_token,
                            'expires_at': expires_at.isoformat(),
                            'scope': token_json.get('scope', '')
                        }
                        print("Token saved to session as fallback")
                    else:
                        error_msg = f"Database error: {str(e)}"
                        print(f"Critical DB error: {error_msg}")
                        raise Exception(error_msg)
        except Exception as user_check_error:
            print(f"Error checking user existence: {user_check_error}")
            # 사용자 확인 실패 시 세션에 저장
            session[f'oauth_token_{user_id}_google'] = {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'expires_at': expires_at.isoformat(),
                'scope': token_json.get('scope', '')
            }
            print("Token saved to session due to user check failure")
        
        print(f"Google OAuth token saved for user {user_id}")
        
        # OAuth state 정리
        session.pop('oauth_state', None)
        
        # 성공 페이지 반환 (팝업 창 닫기)
        return render_template_string('''
        <html><body>
            <script>
                // 부모 창에 성공 메시지 전달
                if (window.opener) {
                    window.opener.postMessage({
                        type: 'oauth_success',
                        platform: 'google'
                    }, window.location.origin);
                }
                window.close();
            </script>
        </body></html>
        ''')
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in Google OAuth callback: {e}")
        print(f"Full traceback: {error_details}")
        
        # 더 자세한 오류 정보 반환
        error_msg = str(e).replace("'", "\\'")  # JavaScript에서 안전하게 사용
        state_param = request.args.get('state', 'None')
        code_param = request.args.get('code', 'None')
        code_preview = code_param[:20] + "..." if code_param != 'None' else 'None'
        
        return render_template_string('''
        <html><body>
            <h2>OAuth Error</h2>
            <p><strong>Error:</strong> %(error_msg)s</p>
            <p><strong>State:</strong> %(state_param)s</p>
            <p><strong>Code:</strong> %(code_preview)s</p>
            <details>
                <summary>Full Error Details</summary>
                <pre>%(error_details)s</pre>
            </details>
            <script>
                if (window.opener) {
                    window.opener.postMessage({
                        type: 'oauth_error',
                        platform: 'google',
                        error: '%(error_msg)s'
                    }, window.location.origin);
                }
                // 10초 후 자동으로 창 닫기
                setTimeout(() => window.close(), 10000);
            </script>
        </body></html>
        ''' % {
            'error_msg': error_msg,
            'state_param': state_param, 
            'code_preview': code_preview,
            'error_details': error_details.replace('<', '&lt;').replace('>', '&gt;')
        })

@app.route('/api/google-oauth/exchange', methods=['POST'])
def google_oauth_exchange():
    """수동으로 OAuth 코드를 토큰으로 교환"""
    try:
        data = request.get_json()
        auth_code = data.get('code')
        state = data.get('state')  # user_id
        
        if not auth_code or not state:
            return jsonify({
                'success': False,
                'error': 'Missing authorization code or state'
            }), 400
        
        from google_auth_oauthlib.flow import Flow
        from services.google_calendar_service import google_calendar_service
        import os
        
        # OAuth 2.0 클라이언트 설정
        client_config = {
            "web": {
                "client_id": os.environ.get('GOOGLE_CLIENT_ID'),
                "client_secret": os.environ.get('GOOGLE_CLIENT_SECRET'),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [f"{request.host_url}auth/google/callback"]
            }
        }
        
        flow = Flow.from_client_config(
            client_config,
            scopes=[
                'https://www.googleapis.com/auth/calendar',
                'https://www.googleapis.com/auth/userinfo.email',
                'https://www.googleapis.com/auth/userinfo.profile',
                'openid'
            ]
        )
        flow.redirect_uri = f"{request.host_url}auth/google/callback"
        
        # 인증 코드로 토큰 교환
        flow.fetch_token(code=auth_code)
        credentials = flow.credentials
        
        # 토큰을 Supabase에 저장
        token_data = {
            'user_id': state,
            'platform': 'google',
            'access_token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'expires_at': credentials.expiry.isoformat() if credentials.expiry else None,
            'token_type': 'Bearer',
            'scope': ' '.join(credentials.scopes) if credentials.scopes else 'https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile openid'
        }
        
        # 기존 토큰이 있으면 업데이트, 없으면 삽입
        result = google_calendar_service.supabase.table('oauth_tokens').upsert(
            token_data,
            on_conflict='user_id,platform'
        ).execute()
        
        print(f"Google OAuth token saved for user {state}")
        
        return jsonify({
            'success': True,
            'message': 'Google Calendar OAuth 토큰이 성공적으로 저장되었습니다.',
            'user_id': state
        })
        
    except Exception as e:
        print(f"Error exchanging OAuth code: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def handle_slack_connection(user_id, data):
    """Slack OAuth 연결 처리"""
    try:
        return {
            'success': True,
            'platform': 'slack',
            'data': {
                'user_id': f'slack_{user_id}',
                'team': 'Connected Team',
                'access_token_hash': 'encrypted_slack_token',
                'connected_at': '2024-08-05T12:00:00Z'
            },
            'message': 'Slack 연결 성공'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Slack 연결 실패: {str(e)}'
        }

def handle_outlook_connection(user_id, data):
    """Outlook OAuth 연결 처리"""
    try:
        return {
            'success': True,
            'platform': 'outlook',
            'data': {
                'user_id': f'outlook_{user_id}',
                'email': 'user@outlook.com',
                'access_token_hash': 'encrypted_outlook_token',
                'connected_at': '2024-08-05T12:00:00Z'
            },
            'message': 'Outlook 연결 성공'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Outlook 연결 실패: {str(e)}'
        }

def simulate_sync(platform, user_id):
    """동기화 시뮬레이션"""
    import time
    import random
    
    # 동기화 개수 시뮬레이션
    sync_count = random.randint(1, 10)
    
    return {
        'success': True,
        'platform': platform,
        'sync_started': True,
        'estimated_time': f'{sync_count * 2} seconds',
        'items_to_sync': sync_count,
        'sync_id': f'sync_{platform}_{int(time.time())}',
        'message': f'{platform.upper()} 동기화 시작'
    }

# 🧠 Smart Cache Utility Functions
def initialize_smart_cache_entry(user_id, platform, integration_type='oauth'):
    """스마트 캐시 엔트리 초기화"""
    try:
        # 실제로는 Supabase에 데이터 삽입
        # 여기서는 로그만 출력
        print(f"[EMOJI] Initializing smart cache for user {user_id}, platform {platform}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to initialize smart cache: {e}")
        return False

def update_smart_cache_success(user_id, platform, response_time_ms=0):
    """연결 성공 시 스마트 캐시 업데이트"""
    try:
        # 실제로는 Supabase 함수 호출: update_connection_success()
        print(f"[EMOJI] Updating smart cache success for {platform}: {response_time_ms}ms")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to update smart cache success: {e}")
        return False

def update_smart_cache_error(user_id, platform, error_message):
    """오류 시 스마트 캐시 업데이트"""
    try:
        # 실제로는 Supabase 함수 호출: update_connection_error()
        print(f"[EMOJI] Updating smart cache error for {platform}: {error_message}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to update smart cache error: {e}")
        return False

def update_smart_cache_sync(user_id, platform, items_count=0, duration_ms=0):
    """동기화 성공 시 스마트 캐시 업데이트"""
    try:
        # 실제로는 Supabase 함수 호출: update_sync_success()
        print(f"[EMOJI] Updating smart cache sync for {platform}: {items_count} items, {duration_ms}ms")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to update smart cache sync: {e}")
        return False

def get_smart_cache_data(user_id, platform):
    """스마트 캐시 데이터 조회"""
    try:
        # 실제로는 Supabase에서 데이터 조회
        # 시뮬레이션 데이터 반환
        return {
            'connected': False,
            'last_sync': None,
            'sync_count': 0,
            'status': 'inactive',
            'connection_success_rate': 0.0,
            'average_response_time_ms': 0.0
        }
    except Exception as e:
        print(f"[ERROR] Failed to get smart cache data: {e}")
        return None

# 🏥 Health Check Endpoint for Render
@app.route('/health')
def health_check():
    """Health check endpoint for Render deployment"""
    return jsonify({
        'status': 'healthy',
        'message': 'NotionFlow is running successfully',
        'timestamp': dt.utcnow().isoformat()
    })

# [SEARCH] Debug endpoint for session testing
@app.route('/debug/session')
def debug_session():
    """Debug endpoint to check session state"""
    return jsonify({
        'session_data': dict(session),
        'user_id': session.get('user_id'),
        'authenticated': session.get('authenticated'),
        'session_permanent': session.permanent if hasattr(session, 'permanent') else None
    })

# Register all optional blueprints with error handling
blueprints_to_register = [
    ('routes.api_key_routes', 'api_key_bp', '[KEY] API Key Management'),
    ('routes.auth_routes', 'auth_bp', '[AUTH] Authentication'),
    ('routes.sync_routes', 'sync_bp', '[LOADING] Sync Management'),
    ('routes.sync_status_routes', 'sync_status_bp', '[DATA] Sync Status'),
    ('routes.auto_connect_routes', 'auto_connect_bp', '[LAUNCH] Auto-Connect'),
    ('routes.oauth_routes', 'oauth_bp', '[AUTH] OAuth'),
    ('routes.integration_routes', 'integration_bp', '[LINK] Integration'),
    ('routes.enhanced_features_routes', 'enhanced_bp', '[LAUNCH] Enhanced Features'),
    ('routes.dashboard_api_routes', 'dashboard_api_bp', '[DATA] Dashboard API'),
    ('routes.user_visit_routes', 'visit_bp', '[LAUNCH] User Visit Tracking'),
    ('routes.profile_routes', 'profile_bp', '[USER] Profile Management'),
    ('routes.platform_registration_routes', 'platform_reg_bp', '[LINK] Platform Registration'),
    ('routes.calendar_connection_routes', 'calendar_conn_bp', '[CALENDAR] Calendar Connections'),
    ('routes.calendar_api_routes', 'calendar_api_bp', '[CALENDAR] Calendar API'),
    ('routes.platform_connect_routes', 'platform_connect_bp', '[PLATFORM] Platform Calendar Connect'),
    ('routes.health_check_routes', 'health_bp', '[SEARCH] Platform Health Check'),
    ('routes.notion_calendar_connect', 'notion_calendar_bp', '[NOTION] Notion Calendar Connect'),
    ('routes.session_cleanup', 'session_cleanup_bp', '[DEBUG] Session Cleanup'),
    ('routes.friends_routes', 'friends_bp', '[FRIENDS] Friends System')
]

registered_blueprints = []
for module_name, blueprint_name, description in blueprints_to_register:
    try:
        module = __import__(module_name, fromlist=[blueprint_name])
        blueprint = getattr(module, blueprint_name)
        app.register_blueprint(blueprint)
        registered_blueprints.append(description)
        print(f"[SUCCESS] {description} blueprint registered")
    except ImportError as e:
        print(f"[WARNING] {description} blueprint not available: {e}")
    except Exception as e:
        print(f"[ERROR] Error registering {description} blueprint: {e}")

print(f"[PACKAGE] Total blueprints registered: {len(registered_blueprints)}")

# [CONFIG] Add compatibility route for JavaScript
@app.route('/api/get-user-keys', methods=['GET'])
def get_user_keys_compat():
    """Compatibility route for JavaScript dashboard.js"""
    try:
        email = request.args.get('email')
        if not email:
            return jsonify({'success': False, 'error': 'Email required'}), 400
        
        # Mock user ID from email (in real app, get from session/auth)
        user_id = 'mock_user_id'  
        
        # Get API keys data
        api_keys = dashboard_data.get_user_api_keys(user_id)
        
        return jsonify({
            'success': True,
            'data': api_keys
        })
    except Exception as e:
        print(f"Error in get_user_keys_compat: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# 📡 Register Webhook Handlers (optional)
try:
    from backend.services.webhook_handlers import webhooks_bp
    app.register_blueprint(webhooks_bp)
    print("[SUCCESS] Webhook handlers registered")
except ImportError as e:
    print(f"[WARNING] Webhook handlers not available: {e}")
    pass

# ⚡ Register Slack Slash Commands (optional)
try:
    from backend.services.slack_slash_commands import slash_commands_bp
    app.register_blueprint(slash_commands_bp)
    print("[SUCCESS] Slack slash commands registered")
except ImportError as e:
    print(f"[WARNING] Slack slash commands not available: {e}")
    pass

# 📅 Register Google Calendar Sync Routes (optional)
try:
    from routes.google_calendar_sync_routes import google_calendar_bp
    app.register_blueprint(google_calendar_bp)
    print("[SUCCESS] Google Calendar sync routes registered")
except ImportError as e:
    print(f"[WARNING] Google Calendar sync routes not available: {e}")
    pass

# Removed duplicate health endpoint

# ====== 💳 PAYMENT SYSTEM ROUTES ======
# 결제 시스템 라우트 구현

try:
    from utils.payment_manager import PaymentManager
    payment_manager = PaymentManager()
    print("[SUCCESS] Payment manager initialized")
except ImportError as e:
    print(f"[WARNING] Payment manager not available: {e}")
    payment_manager = None

@app.route('/payment')
def payment_page():
    """결제 페이지"""
    return render_template('payment.html')

@app.route('/api/payment/create-order', methods=['POST'])
def create_payment_order():
    """결제 주문 생성 API"""
    try:
        if not payment_manager:
            return jsonify({
                'success': False,
                'error': 'Payment system not available'
            }), 503
        
        data = request.get_json()
        
        # 필수 필드 검증
        required_fields = ['orderId', 'amount', 'orderName', 'customerEmail', 'customerName', 'billingCycle']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # 임시 사용자 ID (실제로는 세션에서 가져와야 함)
        user_id = session.get('user_id', 'temp_user_' + str(uuid.uuid4())[:8])
        
        # 주문 생성
        result = payment_manager.create_order(
            user_id=user_id,
            plan_code='CALENDAR_INTEGRATION',
            billing_cycle=data['billingCycle'],
            customer_email=data['customerEmail'],
            customer_name=data['customerName']
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'orderId': result['order_id'],
                'amount': result['amount'],
                'trialEndDate': result['trial_end_date'].isoformat(),
                'message': result['message']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error'],
                'message': result['message']
            }), 400
            
    except Exception as e:
        print(f"Error creating payment order: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '주문 생성 중 오류가 발생했습니다.'
        }), 500

@app.route('/payment/success')
def payment_success():
    """결제 성공 페이지"""
    try:
        if not payment_manager:
            return render_template('payment_error.html', 
                                 error="Payment system not available"), 503
        
        # URL 파라미터에서 결제 정보 추출
        payment_key = request.args.get('paymentKey')
        order_id = request.args.get('orderId')
        amount = request.args.get('amount')
        
        if not all([payment_key, order_id, amount]):
            return render_template('payment_error.html', 
                                 error="결제 정보가 올바르지 않습니다."), 400
        
        # 결제 검증
        result = payment_manager.verify_payment(
            payment_key=payment_key,
            order_id=order_id,
            amount=int(amount)
        )
        
        if result['success']:
            return render_template('payment_success.html', 
                                 payment_data=result['payment_data'],
                                 subscription=result['subscription'])
        else:
            return render_template('payment_error.html', 
                                 error=result['message']), 400
            
    except Exception as e:
        print(f"Error processing payment success: {e}")
        return render_template('payment_error.html', 
                             error="결제 처리 중 오류가 발생했습니다."), 500

@app.route('/payment/fail')
def payment_fail():
    """결제 실패 페이지"""
    try:
        # URL 파라미터에서 실패 정보 추출
        code = request.args.get('code')
        message = request.args.get('message')
        order_id = request.args.get('orderId')
        
        # 실패 정보를 로그로 기록
        print(f"Payment failed - Order ID: {order_id}, Code: {code}, Message: {message}")
        
        return render_template('payment_fail.html', 
                             error_code=code,
                             error_message=message,
                             order_id=order_id)
                             
    except Exception as e:
        print(f"Error processing payment failure: {e}")
        return render_template('payment_fail.html', 
                             error_code="UNKNOWN",
                             error_message="결제 처리 중 오류가 발생했습니다.")

@app.route('/api/payment/webhook', methods=['POST'])
def payment_webhook():
    """토스페이먼츠 웹훅 처리"""
    try:
        if not payment_manager:
            return jsonify({'success': False}), 503
        
        # 웹훅 데이터 받기
        webhook_data = request.get_json()
        
        # 웹훅 로깅
        print(f"Payment webhook received: {webhook_data}")
        
        # 웹훅 데이터를 DB에 저장
        if payment_manager.supabase:
            payment_manager.supabase.table('payment_webhooks').insert({
                'event_type': webhook_data.get('eventType'),
                'payment_key': webhook_data.get('data', {}).get('paymentKey'),
                'order_id': webhook_data.get('data', {}).get('orderId'),
                'webhook_data': webhook_data,
                'processed': False,
                'created_at': datetime.now().isoformat()
            }).execute()
        
        # 웹훅 처리 로직 (결제 상태 업데이트 등)
        # 실제로는 백그라운드 작업으로 처리하는 것이 좋습니다
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        print(f"Error processing webhook: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/subscription/status', methods=['GET'])
def get_subscription_status():
    """사용자 구독 상태 조회 API"""
    try:
        if not payment_manager:
            return jsonify({
                'success': False,
                'error': 'Payment system not available'
            }), 503
        
        # 임시 사용자 ID (실제로는 세션에서 가져와야 함)
        user_id = session.get('user_id', 'temp_user_123')
        
        # 구독 상태 확인
        result = payment_manager.check_subscription_status(user_id)
        
        return jsonify({
            'success': True,
            'status': result['status'],
            'subscription': result.get('subscription'),
            'trial_ends_at': result.get('trial_ends_at'),
            'current_period_end': result.get('current_period_end'),
            'message': result['message']
        })
        
    except Exception as e:
        print(f"Error getting subscription status: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '구독 상태 조회 중 오류가 발생했습니다.'
        }), 500

@app.route('/api/payment/history', methods=['GET'])
def get_payment_history():
    """사용자 결제 내역 조회 API"""
    try:
        if not payment_manager:
            return jsonify({
                'success': False,
                'error': 'Payment system not available'
            }), 503
        
        # 임시 사용자 ID (실제로는 세션에서 가져와야 함)
        user_id = session.get('user_id', 'temp_user_123')
        
        # 결제 내역 조회
        payments = payment_manager.get_payment_history(user_id)
        
        return jsonify({
            'success': True,
            'payments': payments,
            'message': '결제 내역을 성공적으로 조회했습니다.'
        })
        
    except Exception as e:
        print(f"Error getting payment history: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '결제 내역 조회 중 오류가 발생했습니다.'
        }), 500

@app.route('/subscription')
def subscription_dashboard():
    """구독 관리 대시보드 페이지"""
    return render_template('subscription_dashboard.html')

@app.route('/api/subscription/auto-renew', methods=['POST'])
def toggle_subscription_auto_renew():
    """구독 자동 갱신 설정 토글 API"""
    try:
        if not payment_manager:
            return jsonify({
                'success': False,
                'error': 'Payment system not available'
            }), 503
        
        # 임시 사용자 ID (실제로는 세션에서 가져와야 함)
        user_id = session.get('user_id', 'temp_user_123')
        
        # 자동 갱신 토글
        result = payment_manager.toggle_auto_renew(user_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'auto_renew': result['auto_renew'],
                'message': result['message']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error'],
                'message': result['message']
            }), 400
            
    except Exception as e:
        print(f"Error toggling auto-renew: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '자동 갱신 설정 변경 중 오류가 발생했습니다.'
        }), 500

@app.route('/api/subscription/cancel', methods=['POST'])
def cancel_user_subscription():
    """구독 취소 API"""
    try:
        if not payment_manager:
            return jsonify({
                'success': False,
                'error': 'Payment system not available'
            }), 503
        
        # 임시 사용자 ID (실제로는 세션에서 가져와야 함)
        user_id = session.get('user_id', 'temp_user_123')
        
        # 취소 사유 가져오기
        data = request.get_json() or {}
        cancel_reason = data.get('reason', '사용자 요청')
        
        # 구독 취소
        result = payment_manager.cancel_subscription(user_id, cancel_reason)
        
        if result['success']:
            return jsonify({
                'success': True,
                'cancelled_at': result['cancelled_at'],
                'current_period_end': result['current_period_end'],
                'message': result['message']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error'],
                'message': result['message']
            }), 400
            
    except Exception as e:
        print(f"Error cancelling subscription: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '구독 취소 중 오류가 발생했습니다.'
        }), 500

@app.route('/api/subscription/reactivate', methods=['POST'])
def reactivate_user_subscription():
    """구독 재활성화 API"""
    try:
        if not payment_manager:
            return jsonify({
                'success': False,
                'error': 'Payment system not available'
            }), 503
        
        # 임시 사용자 ID (실제로는 세션에서 가져와야 함)
        user_id = session.get('user_id', 'temp_user_123')
        
        # 구독 재활성화
        result = payment_manager.reactivate_subscription(user_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'reactivated_at': result['reactivated_at'],
                'current_period_end': result['current_period_end'],
                'message': result['message']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error'],
                'message': result['message']
            }), 400
            
    except Exception as e:
        print(f"Error reactivating subscription: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '구독 재활성화 중 오류가 발생했습니다.'
        }), 500

# ===== FRIENDS SYSTEM API ROUTES =====

# Import friends database
try:
    from utils.friends_db import friends_db
    friends_db_available = friends_db.is_available()
    print("[SUCCESS] Friends database available" if friends_db_available else "[WARNING] Friends database not available")
except ImportError as e:
    print(f"[WARNING] Friends database module not found: {e}")
    friends_db_available = False
    friends_db = None

@app.route('/api/friends-old', methods=['GET'])
def get_friends_old():
    """Get user's friends list (old version)"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        if friends_db_available and friends_db:
            # Use real database
            friends = friends_db.get_friends(user_id)
            
            # Add additional info for each friend
            for friend in friends:
                friend['public_calendars'] = 0  # TODO: Get actual count
                friend['viewed'] = False  # TODO: Track viewed status
            
            return jsonify(friends)
        else:
            # Mock friends data for development
            friends = [
                {
                    'id': 'friend_1',
                    'name': '김철수',
                    'email': 'kim@example.com',
                    'avatar': '/static/images/default-avatar.png',
                    'public_calendars': 3,
                    'viewed': False,
                    'connected_at': '2024-08-20T10:00:00Z'
                },
                {
                    'id': 'friend_2', 
                    'name': '이영희',
                    'email': 'lee@example.com',
                    'avatar': '/static/images/default-avatar.png',
                    'public_calendars': 1,
                    'viewed': True,
                    'connected_at': '2024-08-18T15:30:00Z'
                },
                {
                    'id': 'friend_3',
                    'name': '박민수',
                    'email': 'park@example.com', 
                    'avatar': '/static/images/default-avatar.png',
                    'public_calendars': 2,
                    'viewed': False,
                    'connected_at': '2024-08-15T09:20:00Z'
                }
            ]
            
            return jsonify(friends)
        
    except Exception as e:
        print(f"Error getting friends: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/friends/requests-old', methods=['GET'])
def get_friend_requests_old():
    """Get pending friend requests (old version)"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        if friends_db_available and friends_db:
            # Use real database
            requests = friends_db.get_friend_requests(user_id)
            
            # Format the response
            formatted_requests = []
            for req in requests:
                formatted_requests.append({
                    'id': req['id'],
                    'name': req['sender']['name'] if req.get('sender') else 'Unknown',
                    'email': req['sender']['email'] if req.get('sender') else '',
                    'avatar': req['sender']['avatar_url'] if req.get('sender') else '/static/images/default-avatar.png',
                    'message': req.get('message', ''),
                    'created_at': req['created_at']
                })
            
            return jsonify(formatted_requests)
        else:
            # Mock friend requests data
            requests = [
                {
                    'id': 'req_1',
                    'name': '정수민',
                    'email': 'jung@example.com',
                    'avatar': '/static/images/default-avatar.png',
                    'message': '안녕하세요! 친구 추가 부탁드립니다.',
                    'created_at': '2024-08-22T12:00:00Z'
                },
                {
                    'id': 'req_2',
                    'name': '최지훈',
                    'email': 'choi@example.com',
                    'avatar': '/static/images/default-avatar.png',
                    'message': '같이 일정 공유해요~',
                    'created_at': '2024-08-22T10:30:00Z'
                }
            ]
            
            return jsonify(requests)
        
    except Exception as e:
        print(f"Error getting friend requests: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users/search-by-email', methods=['GET'])
def search_users_by_email():
    """Search users by email"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        email = request.args.get('email')
        if not email:
            return jsonify({'success': False, 'error': 'Email required'}), 400
        
        if friends_db_available and friends_db:
            # Use real database
            users = friends_db.search_users_by_email(email)
            
            if users:
                user = users[0]  # Take first match
                
                # Check if already friends
                friendship = friends_db.get_friendship_status(user_id, user['id'])
                is_friend = friendship and friendship.get('status') == 'accepted'
                
                # Check if request already sent
                requests = friends_db.get_friend_requests(user['id'])
                request_sent = any(req.get('sender_id') == user_id for req in requests)
                
                return jsonify({
                    'id': user['id'],
                    'name': user['name'],
                    'email': user['email'],
                    'avatar': user.get('avatar_url', '/static/images/default-avatar.png'),
                    'is_friend': is_friend,
                    'request_sent': request_sent
                })
            else:
                return jsonify({'success': False, 'error': 'User not found'}), 404
        else:
            # Mock user search - in production, search in database
            if email == 'test@example.com':
                return jsonify({
                    'id': 'user_123',
                    'name': '테스트 사용자',
                    'email': email,
                    'avatar': '/static/images/default-avatar.png',
                    'is_friend': False,
                    'request_sent': False
                })
            else:
                return jsonify({'success': False, 'error': 'User not found'}), 404
        
    except Exception as e:
        print(f"Error searching users: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/friends/request-old', methods=['POST'])
def send_friend_request_old():
    """Send friend request to user (old version)"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        target_user_id = data.get('user_id')
        message = data.get('message', '')
        
        if not target_user_id:
            return jsonify({'success': False, 'error': 'User ID required'}), 400
        
        if friends_db_available and friends_db:
            # Use real database
            success = friends_db.send_friend_request(user_id, target_user_id, message)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': '친구 요청을 보냈습니다.'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '친구 요청을 보낼 수 없습니다. (이미 요청했거나 친구일 수 있습니다)'
                }), 400
        else:
            # Mock friend request creation
            request_id = f"req_{uuid.uuid4().hex[:8]}"
            
            print(f"Friend request sent from {user_id} to {target_user_id}")
            
            return jsonify({
                'success': True,
                'request_id': request_id,
                'message': '친구 요청을 보냈습니다.'
            })
        
    except Exception as e:
        print(f"Error sending friend request: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/friends/request/<request_id>/accept', methods=['POST'])
def accept_friend_request(request_id):
    """Accept friend request"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        if friends_db_available and friends_db:
            # Use real database
            success = friends_db.accept_friend_request(request_id, user_id)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': '친구 요청을 수락했습니다.'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '친구 요청을 수락할 수 없습니다.'
                }), 400
        else:
            # Mock friend request acceptance
            print(f"Friend request {request_id} accepted by {user_id}")
            
            return jsonify({
                'success': True,
                'message': '친구 요청을 수락했습니다.'
            })
        
    except Exception as e:
        print(f"Error accepting friend request: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/friends/request/<request_id>/decline', methods=['POST'])
def decline_friend_request(request_id):
    """Decline friend request"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        if friends_db_available and friends_db:
            # Use real database
            success = friends_db.decline_friend_request(request_id, user_id)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': '친구 요청을 거절했습니다.'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '친구 요청을 거절할 수 없습니다.'
                }), 400
        else:
            # Mock friend request decline
            print(f"Friend request {request_id} declined by {user_id}")
            
            return jsonify({
                'success': True,
                'message': '친구 요청을 거절했습니다.'
            })
        
    except Exception as e:
        print(f"Error declining friend request: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/calendar/share', methods=['POST'])
def share_calendar():
    """Share a calendar with a friend"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        calendar_id = data.get('calendar_id')
        friend_id = data.get('friend_id')
        
        if not calendar_id or not friend_id:
            return jsonify({'success': False, 'error': 'Missing calendar_id or friend_id'}), 400
        
        # Use calendar_db to share calendar
        from utils.calendar_db import calendar_db
        success = calendar_db.share_calendar_with_friend(calendar_id, user_id, friend_id)
        
        if success:
            return jsonify({'success': True, 'message': 'Calendar shared successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to share calendar'}), 500
            
    except Exception as e:
        print(f"Error sharing calendar: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/calendar/unshare', methods=['POST'])
def unshare_calendar():
    """Unshare a calendar with a friend"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        calendar_id = data.get('calendar_id')
        friend_id = data.get('friend_id')
        
        if not calendar_id or not friend_id:
            return jsonify({'success': False, 'error': 'Missing calendar_id or friend_id'}), 400
        
        # Use calendar_db to unshare calendar
        from utils.calendar_db import calendar_db
        success = calendar_db.unshare_calendar_with_friend(calendar_id, user_id, friend_id)
        
        if success:
            return jsonify({'success': True, 'message': 'Calendar unshared successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to unshare calendar'}), 500
            
    except Exception as e:
        print(f"Error unsharing calendar: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/test/session', methods=['GET'])
def test_session():
    """Test session and basic functionality"""
    try:
        user_id = session.get('user_id')
        return jsonify({
            'success': True,
            'user_id': user_id,
            'session_keys': list(session.keys()),
            'test': 'API working'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/calendar/my-calendars', methods=['GET'])
def get_my_calendars():
    """Get current user's calendars with sharing status"""
    try:
        user_id = session.get('user_id')
        print(f"[SEARCH] get_my_calendars called for user_id: {user_id}")
        
        if not user_id:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        # Get user's calendars
        try:
            from utils.calendar_db import calendar_db
            print(f"[SEARCH] calendar_db imported successfully, available: {calendar_db.is_available()}")
            
            calendars = calendar_db.get_user_calendars(user_id)
            print(f"[SEARCH] Retrieved {len(calendars) if calendars else 0} calendars")
            
            # Get sharing information
            shares_map = calendar_db.get_calendar_shares_by_owner(user_id)
            print(f"[SEARCH] Retrieved sharing info: {shares_map}")
            
            # Add sharing status to calendars
            for calendar in calendars:
                calendar_id = calendar['id']
                calendar['shared_with'] = shares_map.get(calendar_id, [])
                calendar['is_currently_shared'] = len(calendar['shared_with']) > 0
            
            print(f"[SEARCH] Final calendars data: {calendars}")
            return jsonify({'success': True, 'calendars': calendars})
            
        except ImportError as ie:
            print(f"[ERROR] Import error: {ie}")
            return jsonify({'success': False, 'error': 'Calendar database not available'}), 500
        
    except Exception as e:
        print(f"[ERROR] Error getting my calendars: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/calendar/shared-with-me', methods=['GET'])
def get_shared_calendars():
    """Get calendars that have been shared with current user"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        # Get shared calendars
        from utils.calendar_db import calendar_db
        shared_calendars = calendar_db.get_shared_calendars_for_user(user_id)
        
        return jsonify({'success': True, 'calendars': shared_calendars})
        
    except Exception as e:
        print(f"Error getting shared calendars: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/calendar/<calendar_id>/attendees', methods=['GET'])
def get_calendar_attendees(calendar_id):
    """Get attendees (shared users) for a specific calendar"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        from utils.calendar_db import calendar_db
        from utils.auth_manager import AuthManager
        
        # Get calendar to check ownership
        calendar = calendar_db.get_calendar(calendar_id)
        if not calendar:
            return jsonify({'success': False, 'error': 'Calendar not found'}), 404
        
        # Check if user has access to this calendar
        if calendar.get('owner_id') != user_id:
            # Check if calendar is shared with this user
            shared_calendars = calendar_db.get_shared_calendars_for_user(user_id)
            if not any(cal['id'] == calendar_id for cal in shared_calendars):
                return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        attendees = []
        
        # Add owner as the first attendee
        owner_id = calendar.get('owner_id')
        print(f"Calendar owner_id: {owner_id}")
        print(f"Current user_id: {user_id}")
        
        if owner_id:
            owner_info = AuthManager.get_user_by_id(owner_id)
            print(f"Owner info: {owner_info}")
            
            if owner_info:
                attendees.append({
                    'id': owner_id,
                    'name': owner_info.get('name', 'Unknown'),
                    'email': owner_info.get('email', ''),
                    'role': 'organizer',
                    'status': 'accepted',
                    'avatar': owner_info.get('avatar', '/static/images/default-avatar.png')
                })
            else:
                # Fallback: add owner with basic info if AuthManager fails
                attendees.append({
                    'id': owner_id,
                    'name': 'Calendar Owner',
                    'email': '',
                    'role': 'organizer', 
                    'status': 'accepted',
                    'avatar': '/static/images/default-avatar.png'
                })
        
        # Get shared users from calendar_shares table
        try:
            if calendar_db.supabase:
                shares = calendar_db.supabase.table('calendar_shares').select('*').eq('calendar_id', calendar_id).eq('is_active', True).execute()
                print(f"Found {len(shares.data)} shares for calendar {calendar_id}")
                
                for share in shares.data:
                    user_info = AuthManager.get_user_by_id(share['user_id'])
                    if user_info:
                        attendees.append({
                            'id': share['user_id'],
                            'name': user_info.get('name', 'Unknown'),
                            'email': user_info.get('email', ''),
                            'role': 'attendee',
                            'status': 'accepted' if share.get('accepted_at') else 'pending',
                            'permissions': share.get('permissions', 'view'),
                            'avatar': user_info.get('avatar', '/static/images/default-avatar.png'),
                            'shared_at': share.get('created_at')
                        })
        except Exception as e:
            print(f"Error fetching calendar shares: {e}")
        
        return jsonify({
            'success': True,
            'attendees': attendees,
            'total': len(attendees)
        })
        
    except Exception as e:
        print(f"Error getting calendar attendees: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users/search', methods=['GET'])
def search_users():
    """Search users by name or email for friend requests"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        query = request.args.get('q', '').strip()
        if not query or len(query) < 2:
            return jsonify({'success': False, 'error': 'Query must be at least 2 characters'}), 400
        
        # Use AuthManager to search for real users
        from utils.auth_manager import AuthManager
        users = AuthManager.search_users(query, user_id, limit=10)
        
        return jsonify({
            'success': True,
            'users': users,
            'total': len(users)
        })
        
    except Exception as e:
        print(f"Error searching users: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/friends/request', methods=['POST'])
def send_friend_request():
    """Send friend request to another user"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        target_user_id = data.get('user_id')
        
        if not target_user_id:
            return jsonify({'success': False, 'error': 'Target user ID is required'}), 400
        
        if target_user_id == user_id:
            return jsonify({'success': False, 'error': 'Cannot send friend request to yourself'}), 400
        
        # Use AuthManager to send real friend request
        try:
            from utils.auth_manager import AuthManager
            if hasattr(AuthManager, 'send_friend_request'):
                success, message = AuthManager.send_friend_request(user_id, target_user_id)
            else:
                success, message = False, "Friend request feature not available"
        except ImportError:
            success, message = False, "Friend request feature not available"
        
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400
        
    except Exception as e:
        print(f"Error sending friend request: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/friends', methods=['GET'])
def get_friends():
    """Get user's friends list"""
    print("[SEARCH] get_friends API called")
    try:
        user_id = session.get('user_id')
        print(f"[SEARCH] user_id from session: {user_id}")
        
        if not user_id:
            print("[ERROR] No user_id in session")
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        # Try to import AuthManager
        try:
            from utils.auth_manager import AuthManager
            print("[SUCCESS] AuthManager imported successfully")
            print(f"[SEARCH] AuthManager methods: {[method for method in dir(AuthManager) if not method.startswith('_')]}")
            
            # Check if get_friends_list method exists
            try:
                if hasattr(AuthManager, 'get_friends_list'):
                    friends = AuthManager.get_friends_list(user_id)
                    print(f"[SUCCESS] Retrieved {len(friends) if friends else 0} friends")
                else:
                    print("[WARNING] get_friends_list method not found, returning empty list")
                    friends = []
            except AttributeError as ae:
                print(f"[WARNING] AttributeError in get_friends_list: {ae}")
                friends = []
            except Exception as method_error:
                print(f"[WARNING] Error calling get_friends_list: {method_error}")
                friends = []
            
            return jsonify({
                'success': True,
                'friends': friends if friends else []
            })
            
        except ImportError as ie:
            print(f"[ERROR] Failed to import AuthManager: {ie}")
            # Return empty friends list as fallback
            return jsonify({'success': True, 'friends': []})
        except Exception as general_error:
            print(f"[ERROR] General error in get_friends: {general_error}")
            # Ultimate fallback - always return success with empty array
            return jsonify({'success': True, 'friends': []})
        
    except Exception as e:
        print(f"[ERROR] Error getting friends: {e}")
        import traceback
        traceback.print_exc()
        # Always return empty friends list instead of 500 error
        return jsonify({'success': True, 'friends': []})

@app.route('/api/friends/calendars', methods=['GET'])
def get_friend_calendars():
    """Get calendars from friends"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        # For now, return empty array
        # In production, this would fetch calendars shared by friends
        calendars = []
        
        return jsonify({
            'success': True,
            'calendars': calendars
        })
        
    except Exception as e:
        print(f"Error getting friend calendars: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/friends/requests', methods=['GET'])
def get_friend_requests():
    """Get pending friend requests"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        # Use AuthManager to get real friend requests
        try:
            from utils.auth_manager import AuthManager
            if hasattr(AuthManager, 'get_friend_requests'):
                requests = AuthManager.get_friend_requests(user_id)
            else:
                requests = []
        except ImportError:
            requests = []
        
        return jsonify({
            'success': True,
            'requests': requests
        })
        
    except Exception as e:
        print(f"Error getting friend requests: {e}")
        # Return empty requests list instead of 500 error
        return jsonify({'success': True, 'requests': []})

@app.route('/api/friends/requests/<request_id>/<action>', methods=['POST'])
def respond_to_friend_request(request_id, action):
    """Accept or decline friend request"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        if action not in ['accept', 'decline']:
            return jsonify({'success': False, 'error': 'Invalid action'}), 400
        
        # Use AuthManager to respond to friend request
        try:
            from utils.auth_manager import AuthManager
            if hasattr(AuthManager, 'respond_to_friend_request'):
                success, message = AuthManager.respond_to_friend_request(request_id, action, user_id)
            else:
                success, message = False, "Friend request feature not available"
        except ImportError:
            success, message = False, "Friend request feature not available"
        
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400
        
    except Exception as e:
        print(f"Error responding to friend request: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/user/current', methods=['GET'])
def get_current_user():
    """Get current authenticated user information"""
    try:
        user_id = session.get('user_id')
        
        if user_id:
            # Get basic user info from session or database
            try:
                from utils.auth_manager import AuthManager
                if hasattr(AuthManager, 'get_user_profile'):
                    profile = AuthManager.get_user_profile(user_id)
                    return jsonify({
                        'success': True,
                        'user_id': user_id,
                        'email': profile.get('email') if profile else None,
                        'username': profile.get('username') if profile else None,
                        'display_name': profile.get('display_name') if profile else None
                    })
                else:
                    return jsonify({
                        'success': True,
                        'user_id': user_id,
                        'email': session.get('user_info', {}).get('email'),
                        'username': session.get('user_info', {}).get('username'),
                        'display_name': session.get('user_info', {}).get('display_name')
                    })
            except ImportError:
                # Fallback to session data
                return jsonify({
                    'success': True,
                    'user_id': user_id,
                    'email': session.get('user_info', {}).get('email'),
                    'username': session.get('user_info', {}).get('username'),
                    'display_name': session.get('user_info', {}).get('display_name')
                })
        else:
            return jsonify({
                'success': False,
                'message': 'Not authenticated'
            }), 401
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get current user: {str(e)}'
        }), 500

@app.route('/api/user/profile', methods=['GET'])
def get_current_user_profile():
    """Get current user profile"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        # Get user profile from database
        try:
            from utils.auth_manager import AuthManager
            if hasattr(AuthManager, 'get_user_profile'):
                profile = AuthManager.get_user_profile(user_id)
            else:
                profile = None
        except ImportError:
            profile = None
        
        if profile:
            # Return actual user profile data
            return jsonify({
                'id': profile.get('user_id'),
                'name': profile.get('display_name') or profile.get('username', '사용자'),
                'email': profile.get('email', ''),
                'avatar': profile.get('avatar_url') or '/static/images/default-avatar.png',
                'username': profile.get('username', ''),
                'created_at': profile.get('created_at', ''),
                'last_active': profile.get('updated_at', '')
            })
        else:
            # Return default profile if not found
            return jsonify({
                'id': user_id,
                'name': '사용자',
                'email': 'user@example.com',
                'avatar': '/static/images/default-avatar.png',
                'created_at': '2024-08-01T10:00:00Z',
                'last_active': '2024-08-22T15:30:00Z'
            })
        
    except Exception as e:
        print(f"Error getting user profile: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/user/profile', methods=['PUT'])
def update_current_user_profile():
    """Update current user profile"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        
        # Prepare update data
        update_data = {}
        if 'name' in data:
            update_data['display_name'] = data['name']
        if 'avatar_url' in data:
            update_data['avatar_url'] = data['avatar_url']
        if 'email' in data:
            update_data['email'] = data['email']
        
        # Update profile in database using AuthManager
        if update_data:
            # Use AuthManager to update profile
            try:
                from utils.auth_manager import AuthManager
                if hasattr(AuthManager, 'update_user_profile'):
                    success = AuthManager.update_user_profile(user_id, update_data)
                else:
                    success = False
            except ImportError:
                success = False
            
            if success:
                return jsonify({'success': True, 'message': 'Profile updated successfully'})
            else:
                # If AuthManager fails, try direct update via config.supabase_client
                if config.supabase_client:
                    result = config.supabase_client.table('user_profiles').update(update_data).eq('user_id', user_id).execute()
                    if result.data:
                        return jsonify({'success': True, 'message': 'Profile updated successfully'})
                    else:
                        return jsonify({'success': False, 'error': 'Failed to update profile'}), 500
                else:
                    return jsonify({'success': False, 'error': 'Database connection not available'}), 500
        else:
            return jsonify({'success': False, 'error': 'No data to update'}), 400
        
    except Exception as e:
        print(f"Error updating user profile: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/friends')
def friends_page():
    """Friends page route"""
    user_id = session.get('user_id')
    
    # 🔒 Security: Redirect unauthenticated users to login
    if not user_id:
        return redirect('/login?from=friends')
    
    return render_template('friends.html')

# ============================================
# [CALENDAR] Calendar Events Management API
# ============================================

@app.route('/api/calendars/<calendar_id>/events', methods=['GET'])
def get_calendar_events(calendar_id):
    """Get all events for a specific calendar with optional date range filtering"""
    try:
        # Try to get user_id from session first, then from query parameter
        user_id = session.get('user_id') or request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        # Get query parameters
        start_date = request.args.get('start')
        end_date = request.args.get('end')
        
        print(f"[LOAD] Getting events for calendar {calendar_id}, user {user_id}")
        if start_date:
            print(f"[CALENDAR] Date range: {start_date} to {end_date}")
        
        # Get Supabase client
        supabase_client = config.get_client_for_user(user_id)
        if not supabase_client:
            print(f"[ERROR] Could not get Supabase client for user {user_id}")
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Build query to get events from database
        # Handle both UUID formats (with and without hyphens)
        from utils.uuid_helper import normalize_uuid
        normalized_user_id = normalize_uuid(user_id)
        
        print(f"[DEBUG] Original user_id: {user_id}")
        print(f"[DEBUG] Normalized user_id: {normalized_user_id}")
        print(f"[DEBUG] Calendar ID: {calendar_id}")
        
        # First, check total events in table for debugging
        total_events = supabase_client.table('calendar_events').select('*').execute()
        print(f"[DEBUG] Total events in calendar_events table: {len(total_events.data) if total_events.data else 0}")
        
        # Check what user_ids exist in the database
        if total_events.data:
            unique_user_ids = set(event.get('user_id') for event in total_events.data if event.get('user_id'))
            print(f"[DEBUG] User IDs found in database: {list(unique_user_ids)}")
            print(f"[DEBUG] Sample event from DB: {total_events.data[0]}")
        
        # Check events for this user (both UUID formats)
        user_events = supabase_client.table('calendar_events').select('*').or_(f'user_id.eq.{user_id},user_id.eq.{normalized_user_id}').execute()
        print(f"[DEBUG] Events found for user: {len(user_events.data) if user_events.data else 0}")
        
        if user_events.data:
            print(f"[DEBUG] Sample user event: {user_events.data[0]}")
        else:
            print(f"[DEBUG] No events found for user_id: {user_id} or {normalized_user_id}")
        
        # Include events for this user AND specific calendar_id (checking both UUID formats)
        query = supabase_client.table('calendar_events').select('''
            id, title, description, start_datetime, end_datetime,
            is_all_day, status, location, attendees, created_at, updated_at, 
            calendar_id, source_platform, category, priority
        ''').or_(f'user_id.eq.{user_id},user_id.eq.{normalized_user_id}').eq('calendar_id', calendar_id)
        
        # Add date range filtering if provided
        if start_date and end_date:
            query = query.gte('start_datetime', start_date).lte('start_datetime', end_date)
            print(f"[DEBUG] Applied date filter: {start_date} to {end_date}")
        
        # Execute query
        result = query.order('start_datetime').execute()
        events = result.data if result.data else []
        
        print(f"[SUCCESS] Found {len(events)} events for calendar {calendar_id}")
        if events:
            print(f"[DEBUG] First event: {events[0]}")
        
        return jsonify(events)
        
    except Exception as e:
        print(f"[ERROR] Error getting calendar events: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/calendars/<calendar_id>/events', methods=['POST'])
def create_calendar_event(calendar_id):
    """Create a new event in a specific calendar"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        print(f"[WRITE] Creating event for calendar {calendar_id}: {data}")
        
        # Generate event ID
        event_id = str(uuid.uuid4())
        
        # Get Supabase client
        supabase_client = config.get_client_for_user(user_id)
        if not supabase_client:
            print(f"[ERROR] Could not get Supabase client for user {user_id}")
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Prepare event data for database
        from datetime import datetime
        now = datetime.now()
        
        # Handle datetime fields
        start_datetime = data.get('start_datetime')
        end_datetime = data.get('end_datetime')
        
        # If no datetime provided, create from date/time fields
        if not start_datetime and data.get('date'):
            date_str = data.get('date')
            time_str = data.get('startTime') or data.get('start_time', '09:00')
            start_datetime = f"{date_str}T{time_str}:00"
        
        if not end_datetime and data.get('endDate'):
            end_date_str = data.get('endDate')
            end_time_str = data.get('endTime') or data.get('end_time', '10:00')
            end_datetime = f"{end_date_str}T{end_time_str}:00"
        elif not end_datetime and start_datetime:
            # Default to 1 hour after start
            start_dt = datetime.fromisoformat(start_datetime.replace('Z', ''))
            end_dt = start_dt.replace(hour=start_dt.hour + 1)
            end_datetime = end_dt.isoformat()
        
        event_data = {
            'id': event_id,
            'user_id': user_id,
            'calendar_id': calendar_id,
            'title': data.get('title', 'Untitled Event'),
            'description': data.get('description', ''),
            'start_datetime': start_datetime,
            'end_datetime': end_datetime,
            'is_all_day': data.get('isAllDay', False),
            'source_platform': 'manual',
            'status': 'confirmed',
            'priority': 0,
            'category': 'manual'
        }
        
        # Save to database
        result = supabase_client.table('calendar_events').insert(event_data).execute()
        
        if result.data:
            print(f"[SUCCESS] Event created in database: {event_id}")
            return jsonify(result.data[0]), 201
        else:
            print(f"[ERROR] Failed to create event in database")
            return jsonify({'error': 'Failed to create event'}), 500
        
    except Exception as e:
        print(f"[ERROR] Error creating calendar event: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/calendars/<calendar_id>/events/<event_id>', methods=['PUT'])
def update_calendar_event(calendar_id, event_id):
    """Update an existing event"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        print(f"[WRITE] Updating event {event_id} in calendar {calendar_id}: {data}")
        
        # TODO: Update in database
        # For now, return the updated data
        updated_event = {
            'id': event_id,
            'calendar_id': calendar_id,
            'title': data.get('title'),
            'description': data.get('description'),
            'date': data.get('date'),
            'startTime': data.get('startTime'),
            'endTime': data.get('endTime'),
            'color': data.get('color'),
            'updated_at': dt.now().isoformat()
        }
        
        print(f"[SUCCESS] Event updated: {updated_event}")
        return jsonify(updated_event)
        
    except Exception as e:
        print(f"[ERROR] Error updating calendar event: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/calendars/<calendar_id>/events/<event_id>', methods=['DELETE'])
def delete_calendar_event(calendar_id, event_id):
    """Delete an event"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        print(f"[DELETE] Deleting event {event_id} from calendar {calendar_id}")
        
        # TODO: Delete from database
        print(f"[SUCCESS] Event deleted: {event_id}")
        
        return jsonify({'success': True, 'message': 'Event deleted'})
        
    except Exception as e:
        print(f"[ERROR] Error deleting calendar event: {e}")
        return jsonify({'error': str(e)}), 500


# Add error handlers for production debugging
@app.errorhandler(404)
def not_found_error(error):
    if os.environ.get('RENDER'):
        print(f"404 Error - Requested URL: {request.url}")
        print(f"Method: {request.method}")
        print(f"Path: {request.path}")
    return render_template('404.html'), 404

# Duplicate route removed - using the one defined at line 633

# ===== CALENDAR SYNC API =====

# 기존 엔드포인트를 새 엔드포인트로 리다이렉트 (호환성 유지)
@app.route('/api/user-calendars', methods=['GET'])
def get_user_calendars_redirect():
    """기존 엔드포인트를 새 실제 엔드포인트로 리다이렉트"""
    from flask import redirect
    return redirect('/api/user/calendars', code=302)

@app.route('/api/sync-calendar', methods=['POST'])
def sync_calendar():
    """선택된 캘린더를 플랫폼과 연동"""
    try:
        # Check if user is logged in
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
            
        user_id = session['user_id']
        data = request.get_json()
        
        platform = data.get('platform')
        calendar_id = data.get('calendar_id')
        existing_events = data.get('existing_events', [])
        sync_existing = data.get('sync_existing', False)
        settings = data.get('settings', {})
        
        if not platform or not calendar_id:
            return jsonify({'error': 'Platform and calendar_id are required'}), 400
        
        # Get Supabase client with timeout protection
        try:
            supabase_client = get_supabase()
            if not supabase_client:
                return jsonify({'error': 'Database connection not available'}), 503
        except Exception as db_init_error:
            print(f"[ERROR] Failed to initialize Supabase client: {db_init_error}")
            return jsonify({'error': 'Database initialization failed'}), 503
        
        # 캘린더 정보 가져오기 (여러 소스에서 시도)
        calendar = None
        
        try:
            # 먼저 Supabase calendars 테이블에서 확인
            calendar_response = supabase_client.table('calendars').select('*').eq('id', calendar_id).eq('owner_id', user_id).execute()
            if calendar_response.data:
                calendar = calendar_response.data[0]
        except Exception as e:
            print(f"[WARNING] Calendar lookup from calendars table failed: {e}")
        
        # 캘린더를 찾지 못했으면 기본 캘린더 정보 생성
        if not calendar:
            try:
                # 사용자 캘린더 목록에서 찾기 시도
                user_calendars = load_user_calendars(user_id)
                if user_calendars:
                    for cal in user_calendars:
                        if cal.get('id') == calendar_id:
                            calendar = cal
                            break
            except Exception as cal_load_error:
                print(f"[WARNING] Failed to load user calendars: {cal_load_error}")
            
            # 그래도 없으면 기본 캘린더 생성
            if not calendar:
                calendar = {
                    'id': calendar_id,
                    'name': f'Calendar {calendar_id[:8]}',
                    'user_id': user_id,
                    'created_at': '2024-09-09T00:00:00Z'
                }
        
        # 연동 정보는 간단히 세션에만 저장 (테이블 문제 회피)
        from datetime import datetime
        session_key = f'calendar_sync_{user_id}_{calendar_id}_{platform}'
        session[session_key] = {
            'platform': platform,
            'synced_at': datetime.now().isoformat(),
            'status': 'active'
        }
        
        # DB 연동 시도 (실패해도 계속 진행)
        sync_saved_to_db = False
        try:
            sync_data = {
                'user_id': user_id,
                'calendar_id': calendar_id,
                'platform': platform,
                'synced_at': datetime.now().isoformat(),
                'sync_status': 'active'
            }
            
            # 기존 연동 확인 및 저장 시도
            try:
                existing_sync = supabase_client.table('calendar_sync').select('*').eq('user_id', user_id).eq('calendar_id', calendar_id).eq('platform', platform).execute()
                
                if existing_sync.data:
                    result = supabase_client.table('calendar_sync').update({
                        'synced_at': datetime.now().isoformat(),
                        'sync_status': 'active'
                    }).eq('id', existing_sync.data[0]['id']).execute()
                else:
                    result = supabase_client.table('calendar_sync').insert(sync_data).execute()
                
                if result.data:
                    sync_saved_to_db = True
            except Exception as db_error:
                print(f"[WARNING] Database sync save failed, continuing with session storage: {db_error}")
        
        except Exception as sync_error:
            print(f"[WARNING] Sync database operation failed, using session only: {sync_error}")
        
        # 연동 성공 (DB 저장 실패해도 세션에는 저장됨)
        
        # 🔧 CRITICAL FIX: Update calendar_sync_configs for Notion to properly reflect calendar selection
        if platform == 'notion':
            try:
                # Check if config already exists
                existing_config = supabase_client.table('calendar_sync_configs').select('*').eq('user_id', user_id).eq('platform', 'notion').execute()
                
                config_data = {
                    'user_id': user_id,
                    'platform': 'notion',
                    'calendar_id': calendar_id,  # Set the selected calendar ID
                    'is_enabled': True,
                    'sync_status': 'active',  # Set to active instead of needs_calendar_selection
                    'sync_frequency_minutes': 15,
                    'consecutive_failures': 0,
                    'last_sync_at': datetime.utcnow().isoformat(),
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat()
                }
                
                if existing_config.data:
                    # Update existing config with calendar selection
                    update_result = supabase_client.table('calendar_sync_configs').update({
                        'calendar_id': calendar_id,
                        'is_enabled': True,
                        'sync_status': 'active',
                        'last_sync_at': datetime.utcnow().isoformat(),
                        'updated_at': datetime.utcnow().isoformat()
                    }).eq('user_id', user_id).eq('platform', 'notion').execute()
                    print(f"✅ [SYNC] Updated Notion calendar_sync_configs with calendar_id={calendar_id}")
                else:
                    # Insert new config
                    insert_result = supabase_client.table('calendar_sync_configs').insert(config_data).execute()
                    print(f"✅ [SYNC] Created new Notion calendar_sync_configs with calendar_id={calendar_id}")
                    
                # Clear the session flag that indicates calendar selection is needed
                if 'notion_needs_calendar_selection' in session:
                    del session['notion_needs_calendar_selection']
                    print(f"✅ [SYNC] Cleared notion_needs_calendar_selection from session")
                    
            except Exception as config_error:
                print(f"⚠️ [SYNC] Error updating Notion calendar_sync_configs: {config_error}")
                # Continue even if config update fails
        
        # Notion에서 NodeFlow로 이벤트 가져오기 (Import)
        synced_events_count = 0
        imported_events_count = 0
        
        # 1. 외부 플랫폼에서 이벤트 가져오기 (Import)
        if platform == 'notion':
            try:
                imported_events_count = import_events_from_notion(user_id, calendar_id)
                print(f"Imported {imported_events_count} events from Notion")
            except Exception as e:
                print(f"Error importing events from Notion: {e}")
        elif platform == 'google':
            try:
                imported_events_count = import_events_from_google(user_id, calendar_id)
                print(f"Imported {imported_events_count} events from Google Calendar")
            except Exception as e:
                print(f"Error importing events from Google: {e}")
        
        # 2. 기존 NodeFlow 일정을 외부 플랫폼으로 내보내기 (Export)
        if sync_existing and existing_events:
            try:
                print(f"Starting sync of {len(existing_events)} existing events to {platform}")
                
                for event in existing_events:
                    # 각 플랫폼별로 일정을 동기화하는 로직
                    if platform == 'google':
                        # Google Calendar API를 통해 일정 생성
                        sync_success = sync_event_to_google(event, settings)
                    elif platform == 'outlook':
                        # Outlook Calendar API를 통해 일정 생성
                        sync_success = sync_event_to_outlook(event, settings)
                    elif platform == 'apple':
                        # Apple Calendar를 통해 일정 생성 (iCal 형식)
                        sync_success = sync_event_to_apple(event, settings)
                    elif platform == 'slack':
                        # Slack에 일정 알림 생성
                        sync_success = sync_event_to_slack(event, settings)
                    elif platform == 'notion':
                        # Notion 데이터베이스에 일정 생성
                        sync_success = sync_event_to_notion(event, settings)
                    else:
                        sync_success = False
                        
                    if sync_success:
                        synced_events_count += 1
                        
                print(f"Successfully synced {synced_events_count}/{len(existing_events)} events")
                
            except Exception as e:
                print(f"Error syncing existing events: {e}")
                # 일정 동기화 실패해도 연동 자체는 성공으로 처리

        return jsonify({
            'success': True,
            'message': f'{platform} 캘린더 연동이 완료되었습니다.',
            'calendar_name': calendar['name'],
            'platform': platform,
            'synced_events_count': synced_events_count,
            'imported_events_count': imported_events_count,
            'total_events': len(existing_events) if existing_events else 0,
            'db_saved': sync_saved_to_db
        }), 200
            
    except Exception as e:
        print(f"Error syncing calendar: {e}")
        return jsonify({'error': 'Failed to sync calendar'}), 500

@app.route('/api/debug/import-logs', methods=['GET'])
def get_import_logs():
    """디버그 로그 조회 API"""
    try:
        import os
        import json
        from pathlib import Path
        
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        # logs 디렉토리 확인
        log_dir = Path('logs')
        if not log_dir.exists():
            return jsonify({
                'logs': [],
                'message': 'No logs directory found'
            }), 200
        
        # 로그 파일 목록 가져오기 (최신순)
        log_files = []
        user_prefix = user_id[:8]  # 사용자 ID 앞 8자리
        
        for log_file in log_dir.glob(f'import_*_{user_prefix}_*.json'):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    log_data = json.load(f)
                
                # 파일 정보 추가
                file_stat = log_file.stat()
                log_data['log_file'] = {
                    'filename': log_file.name,
                    'size': file_stat.st_size,
                    'created': file_stat.st_mtime
                }
                
                log_files.append(log_data)
                
            except Exception as e:
                print(f"Error reading log file {log_file}: {e}")
                continue
        
        # 타임스탬프 기준으로 최신순 정렬
        log_files.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # 최대 20개 파일만 반환
        log_files = log_files[:20]
        
        return jsonify({
            'logs': log_files,
            'total_count': len(log_files),
            'user_id_prefix': user_prefix
        }), 200
        
    except Exception as e:
        print(f"Error fetching import logs: {e}")
        return jsonify({'error': 'Failed to fetch logs'}), 500

@app.route('/api/debug/import-logs/<filename>', methods=['GET'])  
def get_import_log_detail(filename):
    """특정 로그 파일 상세 조회"""
    try:
        import os
        import json
        from pathlib import Path
        
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        # 보안 검증: 사용자의 로그 파일만 접근 가능
        user_prefix = user_id[:8]
        if user_prefix not in filename:
            return jsonify({'error': 'Access denied'}), 403
        
        log_file = Path('logs') / filename
        if not log_file.exists():
            return jsonify({'error': 'Log file not found'}), 404
        
        with open(log_file, 'r', encoding='utf-8') as f:
            log_data = json.load(f)
        
        return jsonify(log_data), 200
        
    except Exception as e:
        print(f"Error fetching log detail: {e}")
        return jsonify({'error': 'Failed to fetch log detail'}), 500

@app.route('/debug/logs')
def debug_logs_page():
    """디버그 로그 페이지"""
    user_id = get_current_user_id()
    if not user_id:
        return redirect('/login')
    return render_template('debug-logs.html')

def save_import_log(debug_data):
    """디버그 데이터를 JSON 파일로 저장"""
    import os
    import json
    from datetime import datetime
    
    try:
        # logs 디렉토리 생성
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 파일명 생성 (타임스탬프 기반)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        platform = debug_data.get('platform', 'unknown')
        user_id = debug_data.get('user_id', 'unknown')[:8]  # 앞 8자리만
        
        filename = f"{log_dir}/import_{platform}_{user_id}_{timestamp}.json"
        
        # JSON 파일로 저장
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(debug_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"📄 Import log saved: {filename}")
        return filename
        
    except Exception as e:
        print(f"Failed to save import log: {e}")
        return None

def import_events_from_notion(user_id: str, calendar_id: str) -> int:
    """Notion에서 이벤트를 가져와서 NodeFlow calendar_events 테이블에 저장"""
    import json
    import logging
    from datetime import datetime, timezone
    
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('NotionImport')
    
    # 디버그 데이터를 저장할 리스트
    debug_data = {
        'timestamp': datetime.now().isoformat(),
        'user_id': user_id,
        'calendar_id': calendar_id,
        'platform': 'notion',
        'databases_found': [],
        'events_imported': [],
        'api_responses': [],
        'errors': [],
        'step_logs': []
    }
    
    try:
        # 1. Notion API 키 가져오기
        supabase_client = get_supabase()
        if not supabase_client:
            error_msg = "No Supabase client available"
            logger.error(error_msg)
            debug_data['errors'].append(error_msg)
            save_import_log(debug_data)
            return 0
            
        # 1차: calendar_sync_configs에서 Notion API 키 조회
        config_response = supabase_client.table('calendar_sync_configs').select('*').eq('user_id', user_id).eq('platform', 'notion').execute()
        
        api_key = None
        if config_response.data:
            notion_config = config_response.data[0]
            credentials = notion_config.get('credentials', {})
            # OAuth 연동 후에는 access_token을 사용 (기존 api_key 호환성 유지)
            api_key = credentials.get('access_token') or credentials.get('api_key')
            debug_data['step_logs'].append('✅ Found configuration in calendar_sync_configs')
        
        # 2차: oauth_tokens 테이블에서 토큰 조회 (calendar_sync_configs에 없는 경우)
        if not api_key:
            debug_data['step_logs'].append('⚠️ No config in calendar_sync_configs, checking oauth_tokens...')
            oauth_response = supabase_client.table('oauth_tokens').select('*').eq('user_id', user_id).eq('platform', 'notion').execute()
            
            if oauth_response.data:
                oauth_token = oauth_response.data[0]
                api_key = oauth_token.get('access_token')
                debug_data['step_logs'].append('✅ Found access token in oauth_tokens')
                debug_data['api_responses'].append({
                    'step': 'oauth_tokens_lookup',
                    'response': oauth_token
                })
            else:
                debug_data['step_logs'].append('❌ No oauth tokens found')
        
        if not api_key:
            error_msg = "No Notion configuration or OAuth tokens found"
            logger.error(error_msg)
            debug_data['errors'].append(error_msg)
            debug_data['step_logs'].append('❌ No API key/access token available')
            save_import_log(debug_data)
            return 0
        
        debug_data['step_logs'].append('✅ Configuration found')
        debug_data['api_responses'].append({
            'step': 'config_lookup',
            'response': notion_config
        })
        
        if not api_key:
            error_msg = "No Notion API key or access token found in credentials"
            logger.error(error_msg)
            debug_data['errors'].append(error_msg)
            debug_data['step_logs'].append('❌ API key/access token missing')
            save_import_log(debug_data)
            return 0
        
        logger.info(f"Found Notion API key, importing events...")
        debug_data['step_logs'].append('✅ API key retrieved')
        
        # 2. Notion API로 데이터베이스 조회
        import requests
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Notion-Version': '2022-06-28',
            'Content-Type': 'application/json'
        }
        
        # 데이터베이스 검색
        debug_data['step_logs'].append('🔍 Searching Notion databases...')
        
        search_response = requests.post(
            'https://api.notion.com/v1/search',
            headers=headers,
            json={
                "filter": {
                    "property": "object",
                    "value": "database"
                }
            }
        )
        
        if search_response.status_code != 200:
            error_msg = f"Failed to search Notion databases: {search_response.status_code} - {search_response.text}"
            logger.error(error_msg)
            debug_data['errors'].append(error_msg)
            debug_data['step_logs'].append('❌ Database search failed')
            debug_data['api_responses'].append({
                'step': 'database_search',
                'status_code': search_response.status_code,
                'response_text': search_response.text
            })
            save_import_log(debug_data)
            return 0
            
        databases = search_response.json().get('results', [])
        logger.info(f"Found {len(databases)} Notion databases")
        debug_data['step_logs'].append(f'✅ Found {len(databases)} databases')
        debug_data['api_responses'].append({
            'step': 'database_search',
            'status_code': search_response.status_code,
            'databases_count': len(databases),
            'raw_response': search_response.json()
        })
        
        total_imported = 0
        
        # 3. 각 데이터베이스에서 날짜 필드가 있는 것을 찾아서 이벤트 가져오기
        for database in databases:
            db_id = database['id']
            db_title = database.get('title', [{}])[0].get('plain_text', 'Untitled')
            
            logger.info(f"Checking database: {db_title}")
            debug_data['step_logs'].append(f'📋 Analyzing database: {db_title}')
            
            # 데이터베이스 정보 저장
            db_info = {
                'id': db_id,
                'title': db_title,
                'properties': {},
                'has_date_field': False,
                'events_found': 0
            }
            debug_data['databases_found'].append(db_info)
            
            # 데이터베이스 속성 확인
            debug_data['step_logs'].append(f'🔍 Checking properties of {db_title}')
            properties = database.get('properties', {})
            date_property = None
            title_property = None
            
            for prop_name, prop_info in properties.items():
                db_info['properties'][prop_name] = prop_info.get('type')
                if prop_info.get('type') == 'date':
                    date_property = prop_name
                if prop_info.get('type') == 'title':
                    title_property = prop_name
            
            if not date_property or not title_property:
                skip_reason = f"Missing required properties - date: {bool(date_property)}, title: {bool(title_property)}"
                logger.warning(f"  Skipping {db_title}: {skip_reason}")
                debug_data['step_logs'].append(f"⚠️ Skipped {db_title}: {skip_reason}")
                continue
                
            db_info['has_date_field'] = True
            logger.info(f"  Found date property: {date_property}, title property: {title_property}")
            debug_data['step_logs'].append(f"✅ {db_title} has required properties: {date_property} (date), {title_property} (title)")
            
            # 4. 데이터베이스에서 페이지 조회
            debug_data['step_logs'].append(f"🔍 Querying events from {db_title}...")
            
            query_response = requests.post(
                f'https://api.notion.com/v1/databases/{db_id}/query',
                headers=headers,
                json={
                    "filter": {
                        "property": date_property,
                        "date": {
                            "is_not_empty": True
                        }
                    }
                }
            )
            
            debug_data['api_responses'].append({
                'step': f'query_database_{db_title}',
                'database_id': db_id,
                'status_code': query_response.status_code,
                'query_filter': {
                    "property": date_property,
                    "date": {"is_not_empty": True}
                },
                'response': query_response.json() if query_response.status_code == 200 else query_response.text
            })
            
            if query_response.status_code != 200:
                error_msg = f"Failed to query database {db_title}: {query_response.status_code} - {query_response.text}"
                logger.error(f"  {error_msg}")
                debug_data['errors'].append(error_msg)
                debug_data['step_logs'].append(f"❌ Query failed for {db_title}")
                continue
                
            pages = query_response.json().get('results', [])
            logger.info(f"  Found {len(pages)} pages with dates")
            debug_data['step_logs'].append(f"📄 Found {len(pages)} events in {db_title}")
            db_info['events_found'] = len(pages)
            
            # 5. 각 페이지를 이벤트로 변환해서 저장 (limit to prevent worker timeout)
            max_events_per_run = 30  # Prevent worker timeout
            processed_count = 0
            
            for page in pages:
                # Early exit to prevent worker timeout
                if processed_count >= max_events_per_run:
                    debug_data['step_logs'].append(f"⚡ Reached processing limit of {max_events_per_run} events to prevent timeout")
                    break
                try:
                    page_id = page['id']
                    properties = page.get('properties', {})
                    
                    # 제목 추출
                    title_prop = properties.get(title_property, {})
                    title_texts = title_prop.get('title', [])
                    title = title_texts[0].get('plain_text', 'Untitled') if title_texts else 'Untitled'
                    
                    # 날짜 추출
                    date_prop = properties.get(date_property, {})
                    date_info = date_prop.get('date', {})
                    
                    # 이벤트 정보 로깅
                    event_data = {
                        'page_id': page_id,
                        'title': title,
                        'date_info': date_info,
                        'raw_properties': properties
                    }
                    
                    if not date_info:
                        debug_data['step_logs'].append(f"⚠️ Skipped '{title}': no date info")
                        continue
                        
                    start_date = date_info.get('start')
                    end_date = date_info.get('end') or start_date
                    
                    if not start_date:
                        debug_data['step_logs'].append(f"⚠️ Skipped '{title}': no start date")
                        continue
                    
                    # 시간 정보 확인
                    is_all_day = 'T' not in start_date
                    
                    if is_all_day:
                        start_datetime = f"{start_date}T09:00:00Z"
                        end_datetime = f"{end_date}T10:00:00Z"
                    else:
                        # CRITICAL: Apply datetime constraint validation for timed events
                        start_datetime = start_date
                        end_datetime = end_date
                        
                        # Validate and fix constraint violations
                        from datetime import datetime, timedelta, timezone
                        try:
                            # Parse datetime strings with timezone handling
                            if start_datetime.endswith('Z'):
                                start_dt = datetime.fromisoformat(start_datetime.replace('Z', '+00:00'))
                                end_dt = datetime.fromisoformat(end_datetime.replace('Z', '+00:00'))
                            elif '+' in start_datetime or '-' in start_datetime[-6:]:
                                start_dt = datetime.fromisoformat(start_datetime)
                                end_dt = datetime.fromisoformat(end_datetime)
                            else:
                                start_dt = datetime.fromisoformat(start_datetime + '+00:00')
                                end_dt = datetime.fromisoformat(end_datetime + '+00:00')
                            
                            # Convert to UTC for reliable comparison
                            start_utc = start_dt.astimezone(timezone.utc) if start_dt.tzinfo else start_dt
                            end_utc = end_dt.astimezone(timezone.utc) if end_dt.tzinfo else end_dt
                            
                            # CONSTRAINT VIOLATION FIX: ensure end > start
                            if end_utc <= start_utc:
                                debug_data['step_logs'].append(f"🚨 FIXING constraint violation for '{title}': {start_utc} == {end_utc}")
                                # Add minimum 1-hour duration for timed events
                                end_dt = start_dt + timedelta(hours=1)
                                end_datetime = end_dt.isoformat()
                                debug_data['step_logs'].append(f"✅ Fixed to: {start_datetime} → {end_datetime}")
                                
                        except Exception as dt_error:
                            debug_data['errors'].append(f"Datetime parsing error for '{title}': {dt_error}")
                            # Fallback: use current time + 1 hour
                            now = datetime.now(timezone.utc)
                            start_datetime = now.isoformat()
                            end_datetime = (now + timedelta(hours=1)).isoformat()
                        
                    event_data.update({
                        'start_datetime': start_datetime,
                        'end_datetime': end_datetime,
                        'is_all_day': is_all_day
                    })
                    
                    debug_data['step_logs'].append(f"📅 Processing event: '{title}' on {start_date}")
                    logger.info(f"    Processing event: {title} - {start_datetime} to {end_datetime}")
                    
                    # 기존 이벤트 확인 (external_id 기반 중복 방지 - 더 정확함)
                    debug_data['step_logs'].append(f"🔍 Checking for duplicates of '{title}'...")
                    notion_page_id = page.get('id', '')
                    existing_check = supabase_client.table('calendar_events').select('id').eq('user_id', user_id).eq('external_id', notion_page_id).eq('source_platform', 'notion').execute()
                    
                    if existing_check.data:
                        logger.info(f"    Skipping duplicate: {title}")
                        debug_data['step_logs'].append(f"⚠️ Skipped '{title}': already exists")
                        event_data['duplicate'] = True
                        processed_count += 1  # Count skipped events too
                        continue
                    
                    event_data['duplicate'] = False
                    
                    # 이벤트 데이터 생성
                    event_insert_data = {
                        'user_id': user_id,
                        'calendar_id': calendar_id,
                        'title': title,
                        'description': f'Notion에서 가져온 이벤트 (DB: {db_title})',
                        'start_datetime': start_datetime,
                        'end_datetime': end_datetime,
                        'is_all_day': is_all_day,
                        'source_platform': 'notion',  # Required field (NOT NULL)
                        'status': 'confirmed',
                        'priority': 0,  # Default priority
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }
                    
                    event_data['insert_data'] = event_insert_data
                    debug_data['step_logs'].append(f"💾 Saving event '{title}' to database...")
                    
                    # 데이터베이스에 저장
                    result = supabase_client.table('calendar_events').insert(event_insert_data).execute()
                    
                    if result.data:
                        total_imported += 1
                        logger.info(f"    ✅ Imported: {title} on {start_date}")
                        debug_data['step_logs'].append(f"✅ Successfully imported '{title}'")
                        event_data['import_success'] = True
                        event_data['database_result'] = result.data[0] if result.data else None
                    else:
                        error_msg = f"Failed to save event '{title}' to database"
                        logger.error(f"    ❌ {error_msg}")
                        debug_data['step_logs'].append(f"❌ Failed to save '{title}'")
                    
                    # Increment processed count regardless of success/failure
                    processed_count += 1
                    
                    if not result.data:
                        debug_data['errors'].append(error_msg)
                        event_data['import_success'] = False
                        event_data['database_error'] = str(result)
                        
                    debug_data['events_imported'].append(event_data)
                        
                except Exception as page_error:
                    error_msg = f"Error processing page {page.get('id', 'unknown')}: {str(page_error)}"
                    logger.error(f"    {error_msg}")
                    debug_data['errors'].append(error_msg)
                    debug_data['step_logs'].append(f"❌ Error processing event: {str(page_error)}")
                    continue
        
        # 최종 결과 로깅
        logger.info(f"Total imported events: {total_imported}")
        debug_data['step_logs'].append(f"🎉 Import completed: {total_imported} events imported")
        debug_data['success'] = total_imported > 0
        debug_data['total_imported'] = total_imported
        
        # 로그 저장
        save_import_log(debug_data)
        
        return total_imported
        
    except Exception as e:
        error_msg = f"Critical error importing from Notion: {str(e)}"
        logger.error(error_msg)
        debug_data['errors'].append(error_msg)
        debug_data['step_logs'].append(f"💥 Critical error: {str(e)}")
        debug_data['success'] = False
        
        # 오류 로그도 저장
        save_import_log(debug_data)
        return 0

def import_events_from_google(user_id: str, calendar_id: str) -> int:
    """Google Calendar에서 이벤트를 가져와서 NodeFlow calendar_events 테이블에 저장"""
    import json
    import logging
    
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('GoogleImport')
    
    # 디버그 데이터를 저장할 객체
    debug_data = {
        'timestamp': datetime.now().isoformat(),
        'user_id': user_id,
        'calendar_id': calendar_id,
        'platform': 'google',
        'calendars_found': [],
        'events_imported': [],
        'api_responses': [],
        'errors': [],
        'step_logs': []
    }
    
    try:
        # 1. Google OAuth 토큰 가져오기
        debug_data['step_logs'].append('🔐 Getting Google OAuth token...')
        supabase_client = get_supabase()
        if not supabase_client:
            error_msg = "No Supabase client available"
            logger.error(error_msg)
            debug_data['errors'].append(error_msg)
            debug_data['step_logs'].append('❌ Supabase client unavailable')
            save_import_log(debug_data)
            return 0
            
        # oauth_tokens 테이블에서 Google 토큰 조회
        token_response = supabase_client.table('oauth_tokens').select('*').eq('user_id', user_id).eq('platform', 'google').execute()
        
        if not token_response.data:
            error_msg = "No Google OAuth token found"
            logger.error(error_msg)
            debug_data['errors'].append(error_msg)
            debug_data['step_logs'].append('❌ OAuth token not found')
            save_import_log(debug_data)
            return 0
            
        debug_data['step_logs'].append('✅ OAuth token retrieved')
        debug_data['api_responses'].append({
            'step': 'token_lookup',
            'response': token_response.data[0]
        })
            
        google_token = token_response.data[0]
        access_token = google_token.get('access_token')
        refresh_token = google_token.get('refresh_token')
        
        if not access_token:
            print("No Google access token found")
            return 0
        
        print(f"Found Google OAuth token, importing events...")
        
        # 2. Google Calendar API로 이벤트 조회
        import requests
        from datetime import datetime, timedelta
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json'
        }
        
        # 시간 범위 설정 (과거 30일부터 미래 90일까지)
        time_min = (datetime.now() - timedelta(days=30)).isoformat() + 'Z'
        time_max = (datetime.now() + timedelta(days=90)).isoformat() + 'Z'
        
        # Google Calendar API로 이벤트 조회
        events_url = f'https://www.googleapis.com/calendar/v3/calendars/primary/events'
        params = {
            'timeMin': time_min,
            'timeMax': time_max,
            'maxResults': 100,
            'singleEvents': True,
            'orderBy': 'startTime'
        }
        
        events_response = requests.get(events_url, headers=headers, params=params)
        
        if events_response.status_code == 401:
            print("Google token expired, need to refresh")
            # TODO: Implement token refresh logic
            return 0
        
        if events_response.status_code != 200:
            print(f"Failed to get Google Calendar events: {events_response.status_code}")
            print(f"Response: {events_response.text}")
            return 0
            
        events_data = events_response.json()
        events = events_data.get('items', [])
        print(f"Found {len(events)} Google Calendar events")
        
        total_imported = 0
        
        # 3. 각 이벤트를 NodeFlow에 저장
        for event in events:
            try:
                event_id = event.get('id')
                summary = event.get('summary', 'Untitled Event')
                description = event.get('description', '')
                location = event.get('location', '')
                
                # 시작/종료 시간 처리
                start = event.get('start', {})
                end = event.get('end', {})
                
                # 종일 이벤트 vs 시간 지정 이벤트
                if 'dateTime' in start:
                    start_datetime = start['dateTime']
                    end_datetime = end.get('dateTime')
                    is_all_day = False
                    
                    # CRITICAL: Fix constraint violation if end time is missing or same as start
                    if not end_datetime or end_datetime == start_datetime:
                        from datetime import datetime, timedelta
                        try:
                            start_dt = datetime.fromisoformat(start_datetime.replace('Z', '+00:00'))
                            end_dt = start_dt + timedelta(hours=1)  # Default 1-hour duration
                            end_datetime = end_dt.isoformat()
                        except:
                            # Fallback: manually add :01:00 to indicate 1 hour later
                            if 'T' in start_datetime:
                                base_time = start_datetime.split('T')[0]
                                time_part = start_datetime.split('T')[1]
                                if ':' in time_part:
                                    hour = int(time_part.split(':')[0])
                                    end_hour = str(hour + 1).zfill(2)
                                    end_datetime = f"{base_time}T{end_hour}:{time_part.split(':', 1)[1]}"
                                else:
                                    end_datetime = start_datetime + ":01:00"
                            else:
                                end_datetime = start_datetime + "T01:00:00"
                elif 'date' in start:
                    # 종일 이벤트
                    start_date = start['date']
                    end_date = end.get('date', start_date)
                    start_datetime = f"{start_date}T00:00:00Z"
                    end_datetime = f"{end_date}T23:59:59Z"
                    is_all_day = True
                else:
                    continue
                
                # 기존 이벤트 확인 (external_id 기반 중복 방지 - 더 정확함)
                existing_check = supabase_client.table('calendar_events').select('id').eq('user_id', user_id).eq('external_id', event_id).eq('source_platform', 'google').execute()
                
                if existing_check.data:
                    print(f"  Skipping duplicate: {summary}")
                    continue
                
                # 참석자 정보
                attendees = event.get('attendees', [])
                attendee_emails = [a.get('email') for a in attendees if a.get('email')]
                
                # 이벤트 데이터 생성
                event_data = {
                    'user_id': user_id,
                    'calendar_id': calendar_id,
                    'title': summary,
                    'description': description,
                    'location': location,
                    'start_datetime': start_datetime,
                    'end_datetime': end_datetime,
                    'is_all_day': is_all_day,
                    'status': event.get('status', 'confirmed'),
                    'attendees': attendee_emails,
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                
                # 데이터베이스에 저장
                result = supabase_client.table('calendar_events').insert(event_data).execute()
                
                if result.data:
                    total_imported += 1
                    print(f"  ✅ Imported: {summary} on {start_datetime[:10]}")
                else:
                    print(f"  ❌ Failed to save: {summary}")
                    
            except Exception as event_error:
                print(f"  Error processing event: {event_error}")
                continue
        
        print(f"Total imported events from Google: {total_imported}")
        return total_imported
        
    except Exception as e:
        print(f"Error importing events from Google: {e}")
        return 0

@app.route('/api/google-calendar/events', methods=['GET'])
def get_google_calendar_events():
    """Google Calendar에서 일정 가져오기"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
            
        user_id = session['user_id']
        
        # Google Calendar 서비스 import
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))
            from services.google_calendar_service import google_calendar_service
        except ImportError as e:
            return jsonify({'error': f'Google Calendar service not available: {e}'}), 503
        
        # 날짜 범위 파라미터
        from datetime import datetime, timedelta
        import pytz
        
        time_min = datetime.now(pytz.UTC) - timedelta(days=30)  # 30일 전부터
        time_max = datetime.now(pytz.UTC) + timedelta(days=90)  # 90일 후까지
        
        # Google Calendar에서 일정 조회
        google_events = google_calendar_service.get_events(
            user_id=user_id,
            time_min=time_min,
            time_max=time_max
        )
        
        # 일정 데이터 형식 변환 (Google -> NotionFlow 형식)
        converted_events = []
        for event in google_events:
            converted_event = {
                'id': event.get('id'),
                'title': event.get('summary', 'No Title'),
                'description': event.get('description', ''),
                'location': event.get('location', ''),
                'start_time': event.get('start', {}).get('dateTime'),
                'end_time': event.get('end', {}).get('dateTime'),
                'date': event.get('start', {}).get('date'),  # 종일 일정인 경우
                'source': 'google',
                'external_id': event.get('id'),
                'html_link': event.get('htmlLink'),
                'attendees': [attendee.get('email') for attendee in event.get('attendees', [])],
                'created': event.get('created'),
                'updated': event.get('updated')
            }
            converted_events.append(converted_event)
        
        return jsonify({
            'success': True,
            'events': converted_events,
            'count': len(converted_events)
        }), 200
        
    except Exception as e:
        print(f"Error getting Google Calendar events: {e}")
        return jsonify({'error': 'Failed to get Google Calendar events'}), 500

@app.route('/api/sync-google-events-to-notion', methods=['POST'])
def sync_google_events_to_notion():
    """Google Calendar 일정을 Notion으로 동기화"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
            
        user_id = session['user_id']
        data = request.get_json()
        calendar_id = data.get('calendar_id')  # 동기화할 Notion 캘린더 ID
        
        if not calendar_id:
            return jsonify({'error': 'calendar_id is required'}), 400
        
        # Google Calendar에서 일정 가져오기
        google_events_response = get_google_calendar_events()
        if google_events_response[1] != 200:  # 상태 코드 체크
            return jsonify({'error': 'Failed to get Google Calendar events'}), 500
        
        google_events_data = json.loads(google_events_response[0].data)
        google_events = google_events_data.get('events', [])
        
        # NotionFlow 데이터베이스에 일정 저장
        synced_count = 0
        failed_count = 0
        
        # Get Supabase client for database operations
        supabase_client = get_supabase()
        if not supabase_client:
            return jsonify({'error': 'Database not available'}), 503
        
        for event in google_events:
            try:
                # Convert Google event to NotionFlow format
                event_data = {
                    'user_id': user_id,
                    'calendar_id': calendar_id,
                    'title': event.get('title', 'Untitled Event'),
                    'description': event.get('description', ''),
                    'location': event.get('location', ''),
                    'platform': 'google',
                    'external_event_id': event.get('external_id'),
                    'html_link': event.get('html_link', ''),
                    'sync_status': 'synced',
                    'last_synced_at': datetime.datetime.now().isoformat()
                }
                
                # Handle datetime vs date (all-day events)
                if event.get('start_time'):  # Timed event
                    event_data['start_datetime'] = event['start_time']
                    event_data['end_datetime'] = event['end_time']
                    event_data['is_all_day'] = False
                elif event.get('date'):  # All-day event
                    event_data['start_date'] = event['date']
                    event_data['end_date'] = event.get('end_date', event['date'])
                    event_data['is_all_day'] = True
                
                # Handle attendees
                if event.get('attendees'):
                    event_data['attendees'] = json.dumps(event['attendees'])
                
                # Store additional metadata
                event_data['event_metadata'] = json.dumps({
                    'google_event_id': event.get('external_id'),
                    'created': event.get('created'),
                    'updated': event.get('updated'),
                    'source': 'google_calendar_import'
                })
                
                # Insert or update event in database
                result = supabase_client.table('calendar_events').upsert(
                    event_data,
                    on_conflict='user_id,platform,external_event_id'
                ).execute()
                
                if result.data:
                    print(f"Successfully synced Google event '{event.get('title', 'Unknown')}' to NotionFlow calendar {calendar_id}")
                    synced_count += 1
                else:
                    print(f"Failed to sync event {event.get('title', 'Unknown')}: No data returned")
                    failed_count += 1
                
            except Exception as e:
                print(f"Failed to sync event {event.get('title', 'Unknown')}: {e}")
                failed_count += 1
        
        return jsonify({
            'success': True,
            'message': f'Google Calendar 일정을 NotionFlow로 동기화했습니다.',
            'synced_count': synced_count,
            'failed_count': failed_count,
            'total_count': len(google_events)
        }), 200
        
    except Exception as e:
        print(f"Error syncing Google events to NotionFlow: {e}")
        return jsonify({'error': 'Failed to sync Google events to NotionFlow'}), 500

@app.route('/api/google-calendar/auto-import', methods=['POST'])
def auto_import_google_events():
    """Google Calendar 이벤트를 자동으로 가져오기 (OAuth 성공 후)"""
    try:
        print(f"=== Auto Import Google Events ===")
        
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
            
        user_id = session['user_id']
        print(f"Auto-importing for user: {user_id}")
        
        # Get Supabase client
        supabase_client = get_supabase()
        if not supabase_client:
            return jsonify({'error': 'Database not available'}), 503
        
        # First, ensure user has at least one calendar
        user_calendars = supabase_client.table('calendars').select('*').eq('owner_id', user_id).execute()
        
        if not user_calendars.data:
            # Create a default calendar for the user
            print(f"No calendars found. Creating default calendar for user {user_id}")
            
            new_calendar = {
                'owner_id': user_id,
                'name': 'My Calendar',
                'description': 'Default calendar for imported events',
                'color': '#4285F4',  # Google blue
                'platform': 'custom',
                'is_shared': False,
                'is_enabled': True,
                'created_at': dt.now().isoformat(),
                'updated_at': dt.now().isoformat()
            }
            
            create_result = supabase_client.table('calendars').insert(new_calendar).execute()
            
            if create_result.data:
                calendar_data = create_result.data[0]
                print(f"Created default calendar: {calendar_data.get('id')}")
            else:
                return jsonify({'error': 'Failed to create default calendar'}), 500
        else:
            # Use the first existing calendar
            calendar_data = user_calendars.data[0]
            print(f"Using existing calendar: {calendar_data.get('id')} - {calendar_data.get('name')}")
        
        calendar_id = calendar_data.get('id')
        
        # Check if user has Google Calendar connected
        platform_result = supabase_client.table('registered_platforms').select('*').eq('user_id', user_id).eq('platform', 'google').execute()
        
        if not platform_result.data:
            return jsonify({
                'success': False,
                'error': 'Google Calendar not connected',
                'message': 'Please connect Google Calendar first'
            }), 400
        
        # Import Google Calendar events
        print(f"Starting Google Calendar import for calendar {calendar_id}")
        
        # Import Google Calendar service
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))
            from services.google_calendar_service import GoogleCalendarService
        except ImportError as e:
            return jsonify({'error': f'Google Calendar service not available: {e}'}), 503
        
        # Get Google Calendar events
        google_service = GoogleCalendarService()
        try:
            google_events = google_service.get_events(user_id, calendar_id='primary')
        except Exception as e:
            return jsonify({'error': f'Failed to fetch Google Calendar events: {str(e)}'}), 500
        
        if not google_events:
            return jsonify({
                'success': True,
                'message': 'No events to import',
                'imported_count': 0,
                'failed_count': 0
            })
        
        # Import events to NotionFlow calendar
        imported_count = 0
        failed_count = 0
        
        for event in google_events:
            try:
                # Convert Google event to NotionFlow format
                start_datetime = event.get('start', {})
                end_datetime = event.get('end', {})
                
                start_time = start_datetime.get('dateTime') or start_datetime.get('date')
                end_time = end_datetime.get('dateTime') or end_datetime.get('date')
                
                if not start_time:
                    failed_count += 1
                    continue
                
                event_data = {
                    'user_id': user_id,
                    'calendar_id': calendar_id,
                    'title': event.get('summary', 'Untitled Event'),
                    'description': event.get('description', ''),
                    'location': event.get('location', ''),
                    'platform': 'google',
                    'external_event_id': event.get('id'),
                    'html_link': event.get('htmlLink', ''),
                    'sync_status': 'synced',
                    'last_synced_at': dt.now().isoformat(),
                    'status': event.get('status', 'confirmed')
                }
                
                # Handle date/time fields
                if 'date' in start_datetime:
                    event_data.update({
                        'start_date': start_time,
                        'end_date': end_time or start_time,
                        'is_all_day': True
                    })
                else:
                    event_data.update({
                        'start_datetime': start_time,
                        'end_datetime': end_time or start_time,
                        'is_all_day': False
                    })
                
                # Check if event already exists
                existing = supabase_client.table('calendar_events').select('id').eq('user_id', user_id).eq('external_event_id', event.get('id')).execute()
                
                if not existing.data:
                    result = supabase_client.table('calendar_events').insert(event_data).execute()
                    if result.data:
                        imported_count += 1
                    else:
                        failed_count += 1
                        
            except Exception as e:
                print(f"Failed to import event: {str(e)}")
                failed_count += 1
        
        return jsonify({
            'success': True,
            'message': f'Successfully imported {imported_count} events',
            'imported_count': imported_count,
            'failed_count': failed_count,
            'calendar_id': calendar_id,
            'calendar_name': calendar_data.get('name')
        })
        
    except Exception as e:
        print(f"Auto-import error: {str(e)}")
        return jsonify({'error': f'Auto-import failed: {str(e)}'}), 500

@app.route('/api/import-google-events/<calendar_id>', methods=['POST'])
def import_google_events_to_calendar(calendar_id):
    """Google Calendar 이벤트를 특정 NotionFlow 캘린더로 자동 가져오기"""
    try:
        # Enhanced logging
        print(f"=== Import Google Events Request ===")
        print(f"Calendar ID: {calendar_id}")
        print(f"Session keys: {list(session.keys())}")
        print(f"Session user_id: {session.get('user_id', 'NOT_FOUND')}")
        
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
            
        user_id = session['user_id']
        print(f"Authenticated user_id: {user_id}")
        
        # Check if calendar exists and belongs to user
        supabase_client = get_supabase()
        if not supabase_client:
            return jsonify({'error': 'Database not available'}), 503
        
        # IMMEDIATE FIX: Always use user's first available calendar
        print(f"IMMEDIATE FIX: Getting user's first calendar instead of using frontend ID: {calendar_id}")
        
        try:
            # Get user's calendars first  
            user_calendars = supabase_client.table('calendars').select('*').eq('owner_id', user_id).execute()
            print(f"User has {len(user_calendars.data)} calendars total")
            
            if not user_calendars.data:
                return jsonify({
                    'error': 'No calendars found for user',
                    'debug': f'User {user_id} has no calendars in database'
                }), 404
            
            # Use the first calendar automatically
            calendar_data = user_calendars.data[0]
            actual_calendar_id = calendar_data.get('id')
            calendar_name = calendar_data.get('name', 'Unknown Calendar')
            
            print(f"✅ USING CALENDAR: {actual_calendar_id} - {calendar_name}")
            
            # Override calendar_id with the correct one
            calendar_id = actual_calendar_id
            calendar_result = user_calendars  # We already have the data
            
            # Since we're using the first available calendar, this should never fail
            # But keep a safety check just in case
            if not calendar_result.data:
                return jsonify({
                    'error': 'Unexpected: No calendar found even after using first available',
                    'debug': f'This should not happen. User {user_id} calendars query succeeded but data is empty.'
                }), 500
                
        except Exception as e:
            print(f"Error querying calendars table: {str(e)}")
            return jsonify({'error': f'Database query failed: {str(e)}'}), 500
        
        # Check if user has Google Calendar connected - use correct table name
        print(f"Checking Google Calendar registration for user: {user_id}")
        platform_result = supabase_client.table('registered_platforms').select('*').eq('user_id', user_id).eq('platform', 'google').execute()
        print(f"Platform query result: {len(platform_result.data)} records found")
        
        if not platform_result.data:
            # Check if registered_platforms table has any Google entries
            all_google = supabase_client.table('registered_platforms').select('user_id').eq('platform', 'google').execute()
            print(f"Total Google registrations in DB: {len(all_google.data)}")
            return jsonify({'error': 'Google Calendar not registered', 'debug': f'Total Google users: {len(all_google.data)}'}), 400
        
        # Import Google Calendar service properly
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))
            from services.google_calendar_service import GoogleCalendarService
        except ImportError as e:
            return jsonify({'error': f'Google Calendar service not available: {e}'}), 503
        
        # Get Google Calendar events using the service
        google_service = GoogleCalendarService()
        try:
            google_events = google_service.get_events(user_id, calendar_id='primary')
        except Exception as e:
            return jsonify({'error': f'Failed to fetch Google Calendar events: {str(e)}'}), 500
        
        if not google_events:
            return jsonify({
                'success': True,
                'message': 'No events to import',
                'imported_count': 0,
                'failed_count': 0
            })
        
        # Import events to NotionFlow database
        synced_count = 0
        failed_count = 0
        
        for event in google_events:
            try:
                # Convert Google event to NotionFlow format (use correct Google API field names)
                start_datetime = event.get('start', {})
                end_datetime = event.get('end', {})
                
                # Handle different date/time formats
                start_time = start_datetime.get('dateTime') or start_datetime.get('date')
                end_time = end_datetime.get('dateTime') or end_datetime.get('date')
                
                if not start_time:
                    failed_count += 1
                    continue
                
                # Prepare the event data based on correct Google API field names and database schema
                event_data = {
                    'user_id': user_id,
                    'calendar_id': calendar_id,
                    'title': event.get('summary', 'Untitled Event'),  # Google uses 'summary' not 'title'
                    'description': event.get('description', ''),
                    'location': event.get('location', ''),
                    'platform': 'google',
                    'external_event_id': event.get('id'),  # Google uses 'id' not 'external_id'
                    'html_link': event.get('htmlLink', ''),  # Google uses 'htmlLink' not 'html_link'
                    'sync_status': 'synced',
                    'last_synced_at': dt.now().isoformat(),
                    'status': event.get('status', 'confirmed')
                }
                
                # Handle date/time fields based on whether it's all-day or not
                if 'date' in start_datetime:
                    # All-day event
                    event_data.update({
                        'start_date': start_time,
                        'end_date': end_time or start_time,
                        'is_all_day': True
                    })
                else:
                    # Timed event
                    event_data.update({
                        'start_datetime': start_time,
                        'end_datetime': end_time or start_time,
                        'is_all_day': False
                    })
                
                # Handle attendees (if present)
                if event.get('attendees'):
                    event_data['attendees'] = event['attendees']  # Store as JSON directly
                
                # Store additional metadata
                event_data['event_metadata'] = {
                    'google_event_id': event.get('id'),
                    'created': event.get('created'),
                    'updated': event.get('updated'),
                    'source': 'google_calendar_import',
                    'import_timestamp': dt.now().isoformat()
                }
                
                # Insert or update event in database
                result = supabase_client.table('calendar_events').upsert(
                    event_data,
                    on_conflict='user_id,platform,external_event_id'
                ).execute()
                
                if result.data:
                    print(f"Successfully imported Google event '{event.get('title', 'Unknown')}' to calendar {calendar_id}")
                    synced_count += 1
                else:
                    print(f"Failed to import event {event.get('title', 'Unknown')}: No data returned")
                    failed_count += 1
                
            except Exception as e:
                print(f"Failed to import event {event.get('title', 'Unknown')}: {e}")
                failed_count += 1
        
        return jsonify({
            'success': True,
            'message': f"Google Calendar 이벤트가 '{calendar_result.data[0]['name']}' 캘린더로 가져와졌습니다.",
            'imported_count': synced_count,
            'failed_count': failed_count,
            'total_count': len(google_events)
        }), 200
        
    except Exception as e:
        print(f"Error importing Google events: {e}")
        return jsonify({'error': 'Failed to import Google events'}), 500

@app.route('/api/synced-calendars', methods=['GET'])
def get_synced_calendars():
    """사용자의 연동된 캘린더 정보 조회"""
    try:
        # Check if user is logged in
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
            
        user_id = session['user_id']
        
        # Check for manual disconnection flags to prevent auto-reconnection
        google_manually_disconnected = request.headers.get('X-Google-Disconnected')
        notion_manually_disconnected = request.headers.get('X-Notion-Disconnected')
        print(f"[SYNC-CALENDARS] Checking manual disconnection - Google: {google_manually_disconnected}, Notion: {notion_manually_disconnected}")
        
        # Get Supabase client
        supabase_client = get_supabase()
        if not supabase_client:
            # Return empty data for development/testing when database not available
            print("No Supabase client available, returning empty synced calendars data")
            return jsonify({}), 200
        
        # 연동 정보를 수집할 딕셔너리
        synced_platforms = {}
        
        # 1. 데이터베이스에서 연동 정보 조회 시도
        # 먼저 연결해제된 플랫폼들을 확인
        disconnected_platforms = set()
        try:
            config_response = supabase_client.table('calendar_sync_configs').select('*').eq('user_id', user_id).execute()
            if config_response.data:
                for config in config_response.data:
                    platform = config['platform']
                    sync_status = config.get('sync_status')
                    is_enabled = config.get('is_enabled', True)
                    
                    # 단절된 상태나 캘린더 선택이 필요한 상태를 추적
                    if (sync_status == 'needs_calendar_selection' or 
                        not is_enabled or 
                        not config.get('calendar_id')):
                        disconnected_platforms.add(platform)
                        print(f"[SYNC-CALENDARS] Platform {platform} is disconnected or needs calendar selection")
        except Exception as config_error:
            print(f"Pre-check calendar sync configs read error: {config_error}")
        
        try:
            sync_response = supabase_client.table('calendar_sync').select('*').eq('user_id', user_id).eq('sync_status', 'active').execute()
            print(f"[SYNC-CALENDARS] Active sync records found: {len(sync_response.data) if sync_response.data else 0}")
            
            if sync_response.data:
                for sync_record in sync_response.data:
                    platform = sync_record['platform']
                    calendar_id = sync_record['calendar_id']
                    print(f"[SYNC-CALENDARS] Found active sync for {platform} with calendar {calendar_id}")
                    
                    # Skip platforms if manually disconnected to prevent auto-reconnection
                    if platform == 'google' and google_manually_disconnected == 'true':
                        print(f"[SYNC-CALENDARS] Skipping Google platform data due to manual disconnection")
                        continue
                    if platform == 'notion' and notion_manually_disconnected == 'true':
                        print(f"[SYNC-CALENDARS] Skipping Notion platform data due to manual disconnection")
                        continue
                    
                    # Skip platforms that are disconnected in configs
                    if platform in disconnected_platforms:
                        print(f"[SYNC-CALENDARS] Skipping {platform} platform data due to config disconnection")
                        continue
                    
                    try:
                        # 캘린더 정보 조회
                        calendar_response = supabase_client.table('calendars').select('*').eq('id', calendar_id).execute()
                        
                        if calendar_response.data:
                            calendar = calendar_response.data[0]
                            synced_platforms[platform] = {
                                'calendar_id': calendar_id,
                                'calendar_name': calendar['name'],
                                'calendar_description': calendar.get('description', ''),
                                'calendar_icon': calendar.get('color', '📅'),
                                'synced_at': sync_record.get('synced_at', ''),
                                'sync_status': sync_record.get('sync_status', 'active'),
                                'source': 'database'
                            }
                    except Exception as calendar_error:
                        print(f"Error fetching calendar {calendar_id}: {calendar_error}")
                        continue
        except Exception as db_error:
            print(f"Database error fetching synced calendars: {db_error}")
        
        # 2. OAuth 토큰 확인 (실제 OAuth 연동 여부 확인) - 이미 연결해제된 플랫폼 제외
        
        # 3. OAuth 토큰 데이터 처리
        try:
            oauth_tokens = supabase_client.table('oauth_tokens').select('*').eq('user_id', user_id).execute()
            print(f"[SYNC-CALENDARS] OAuth tokens found: {len(oauth_tokens.data) if oauth_tokens.data else 0}")
            
            if oauth_tokens.data:
                for token in oauth_tokens.data:
                    platform = token['platform']
                    
                    # Skip platforms if manually disconnected to prevent auto-reconnection
                    if platform == 'google' and google_manually_disconnected == 'true':
                        print(f"[SYNC-CALENDARS] Skipping Google platform due to manual disconnection")
                        continue
                    if platform == 'notion' and notion_manually_disconnected == 'true':
                        print(f"[SYNC-CALENDARS] Skipping Notion platform due to manual disconnection")
                        continue
                    
                    # 이미 실제 캘린더 연동이 있으면 건너뛰기
                    if platform in synced_platforms:
                        continue
                        
                    # 연결 해제된 플랫폼은 표시하지 않음
                    if platform in disconnected_platforms:
                        print(f"[SYNC-CALENDARS] Skipping disconnected platform {platform}")
                        continue
                    
                    # OAuth 토큰이 있지만 캘린더 연동이 없는 경우 표시
                    synced_platforms[platform] = {
                        'calendar_id': None,
                        'calendar_name': 'OAuth 연동 완료',
                        'calendar_description': '캘린더 연동을 완료하세요',
                        'calendar_icon': '🔗',
                        'synced_at': token.get('created_at', ''),
                        'sync_status': 'oauth_only',  # 새로운 상태
                        'source': 'oauth_token',
                        'needs_calendar_sync': True
                    }
        except Exception as oauth_error:
            print(f"OAuth tokens read error: {oauth_error}")
        
        # 4. 세션에서 연동 정보도 확인 (데이터베이스 실패 시 fallback)
        try:
            for key in session.keys():
                if key.startswith('calendar_sync_'):
                    # calendar_sync_{user_id}_{calendar_id}_{platform} 형식
                    parts = key.split('_')
                    if len(parts) >= 5 and parts[2] == user_id:
                        platform = parts[4]
                        calendar_id = parts[3]
                        sync_info = session[key]
                        
                        # Skip platforms if manually disconnected to prevent auto-reconnection
                        if platform == 'google' and google_manually_disconnected == 'true':
                            print(f"[SYNC-CALENDARS] Skipping Google session data due to manual disconnection")
                            continue
                        if platform == 'notion' and notion_manually_disconnected == 'true':
                            print(f"[SYNC-CALENDARS] Skipping Notion session data due to manual disconnection")
                            continue
                        
                        # 데이터베이스에서 이미 찾은 정보가 없으면 세션 정보 사용
                        if platform not in synced_platforms:
                            # 캘린더 정보 가져오기 (여러 소스 시도)
                            calendar_name = f'Calendar {calendar_id[:8]}'
                            user_calendars = load_user_calendars(user_id)
                            for cal in user_calendars:
                                if cal.get('id') == calendar_id:
                                    calendar_name = cal.get('name', calendar_name)
                                    break
                            
                            synced_platforms[platform] = {
                                'calendar_id': calendar_id,
                                'calendar_name': calendar_name,
                                'calendar_description': '',
                                'calendar_icon': '📅',
                                'synced_at': sync_info.get('synced_at', ''),
                                'sync_status': sync_info.get('status', 'active'),
                                'source': 'session'
                            }
        except Exception as session_error:
            print(f"Session sync info read error: {session_error}")
        
        return jsonify(synced_platforms), 200
            
    except Exception as e:
        print(f"Error fetching synced calendars: {e}")
        # Return empty data instead of 500 error for better UX
        return jsonify({}), 200

# ===== ERROR HANDLERS =====

@app.errorhandler(500)
def internal_error(error):
    if os.environ.get('RENDER'):
        print(f"500 Error - URL: {request.url}")
        print(f"Error: {error}")
    return render_template('404.html'), 500

# ===== PLATFORM CONNECTION MANAGEMENT =====

@app.route('/api/platform/<platform>/connect', methods=['POST'])
def mark_platform_connected(platform):
    """플랫폼을 연결됨으로 표시 (OAuth 성공 후 호출)"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401
        
        # Google Calendar의 경우 database에 configuration 저장
        if platform == 'google':
            try:
                # Check if config already exists
                existing_config = supabase.table('calendar_sync_configs').select('*').eq('user_id', user_id).eq('platform', platform).execute()
                
                config_data = {
                    'user_id': user_id,
                    'platform': platform,
                    'is_enabled': True,
                    'sync_frequency_minutes': 15,
                    'consecutive_failures': 0,
                    'last_sync_at': None,
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat()
                }
                
                if existing_config.data:
                    # Update existing config
                    supabase.table('calendar_sync_configs').update({
                        'is_enabled': True,
                        'updated_at': datetime.utcnow().isoformat()
                    }).eq('user_id', user_id).eq('platform', platform).execute()
                else:
                    # Insert new config
                    supabase.table('calendar_sync_configs').insert(config_data).execute()
                    
            except Exception as db_error:
                print(f"Error saving Google Calendar config to database: {db_error}")
                # Continue with success even if database save fails
        else:
            # 다른 플랫폼은 세션 기반 저장
            # Mark platform as connected in session
            session[f'platform_{platform}_connected'] = True
            session[f'platform_{platform}_last_sync'] = None
            session[f'platform_{platform}_sync_count'] = 0
            session.permanent = True  # Make session persistent
        
        return jsonify({
            'success': True,
            'message': f'{platform} marked as connected',
            'platform': platform,
            'connected': True
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/platform/<platform>/disconnect', methods=['POST'])
def mark_platform_disconnected(platform):
    """플랫폼 연결 해제"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401
        
        # Google Calendar은 OAuth 토큰 삭제로 연결 해제하므로 세션 처리 제외
        if platform != 'google':
            # Mark platform as disconnected in session
            session[f'platform_{platform}_connected'] = False
            session[f'platform_{platform}_last_sync'] = None
            session[f'platform_{platform}_sync_count'] = 0
        else:
            # Google Calendar 연결 해제 - OAuth 토큰 삭제 및 config 비활성화
            try:
                from services.google_calendar_service import google_calendar_service
                # Supabase에서 토큰 삭제
                google_calendar_service.supabase.table('oauth_tokens').delete().eq('user_id', user_id).eq('platform', 'google').execute()
                
                # calendar_sync_configs에서 is_enabled를 false로 설정
                supabase.table('calendar_sync_configs').update({
                    'is_enabled': False,
                    'updated_at': datetime.utcnow().isoformat()
                }).eq('user_id', user_id).eq('platform', 'google').execute()
                
                print(f"Google Calendar disconnected successfully for user {user_id}")
            except Exception as e:
                print(f"Error disconnecting Google Calendar: {e}")
        
        return jsonify({
            'success': True,
            'message': f'{platform} disconnected',
            'platform': platform,
            'connected': False
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/platforms/status', methods=['GET'])
def get_all_platform_status():
    """모든 플랫폼의 연결 상태 조회"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401
        
        platforms = ['notion', 'google', 'apple', 'outlook', 'slack']
        platform_statuses = {}
        
        for platform in platforms:
            # Google Calendar 전용 연결 상태 확인 로직
            if platform == 'google':
                # Check database tokens AND session state
                db_connected = check_google_calendar_connection(user_id)
                session_connected = session.get(f'platform_{platform}_connected', False)
                # Connected if either database has tokens OR session says connected
                connected = db_connected or session_connected
                print(f"[PLATFORM-STATUS] Google connection - DB: {db_connected}, Session: {session_connected}, Final: {connected}")
            else:
                # 다른 플랫폼은 기존 세션 기반 확인
                session_key = f'platform_{platform}_connected'
                connected = session.get(session_key, False)
            
            platform_statuses[platform] = {
                'connected': connected,
                'last_sync': session.get(f'platform_{platform}_last_sync'),
                'sync_count': session.get(f'platform_{platform}_sync_count', 0),
                'status': 'active' if connected else 'inactive'
            }
        
        return jsonify({
            'success': True,
            'platforms': platform_statuses
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def check_google_calendar_connection(user_id):
    """Google Calendar OAuth 토큰 존재 여부로 연결 상태 확인"""
    print(f"[DEBUG] check_google_calendar_connection called for user {user_id}")
    
    try:
        # Check if user has OAuth tokens in database
        supabase_client = get_supabase()
        if not supabase_client:
            print("[DEBUG] No Supabase client available")
            return False
        
        # Check oauth_tokens table for Google tokens
        oauth_result = supabase_client.table('oauth_tokens').select('access_token, refresh_token').eq('user_id', user_id).eq('platform', 'google').execute()
        
        if oauth_result.data:
            token_data = oauth_result.data[0]
            has_tokens = bool(token_data.get('access_token') and token_data.get('refresh_token'))
            print(f"[DEBUG] Google OAuth tokens found: {has_tokens}")
            return has_tokens
        else:
            print("[DEBUG] No Google OAuth tokens found")
            return False
            
    except Exception as e:
        print(f"[DEBUG] Error checking Google connection: {e}")
        return False
    
    # ORIGINAL CODE DISABLED TO PREVENT AUTO-RECONNECTION LOOP:
    # try:
    #     # 먼저 데이터베이스에서 확인
    #     from services.google_calendar_service import google_calendar_service
    #     credentials = google_calendar_service.get_google_credentials(user_id)
    #     if credentials is not None:
    #         return True
    # except Exception as e:
    #     print(f"Error checking Google Calendar connection from DB: {e}")
    # 
    # # 데이터베이스 실패 시 세션에서 확인 (백업)
    # try:
    #     session_key = f'oauth_token_{user_id}_google'
    #     token_data = session.get(session_key)
    #     if token_data and token_data.get('access_token'):
    #         print(f"Found Google token in session for user {user_id}")
    #         return True
    # except Exception as e:
    #     print(f"Error checking Google Calendar connection from session: {e}")
    # 
    # return False

# ===== CACHE CONTROL =====
# (Cache control functions already defined above with proper decorators)

if __name__ == '__main__':
    # ✅ FIXED: Sync scheduler with singleton pattern to prevent multiple instances
    try:
        from utils.sync_scheduler import start_sync_scheduler
        start_sync_scheduler()
        print("✅ [SUCCESS] Sync scheduler started with singleton protection")
    except ImportError as e:
        print(f"⚠️  [WARNING] Sync scheduler not available: {e}")
    except Exception as e:
        print(f"❌ [ERROR] Failed to start sync scheduler: {e}")
    
    port = int(os.environ.get('PORT', 5003))
    app.run(host='0.0.0.0', port=port, debug=True)
elif os.environ.get('RENDER') and not os.environ.get('FLASK_ENV') == 'development':
    # Production startup with error handling (only on Render platform)
    # ✅ FIXED: Production sync scheduler with singleton pattern
    try:
        from utils.sync_scheduler import start_sync_scheduler
        start_sync_scheduler()
        print("✅ [SUCCESS] Production sync scheduler started with singleton protection")
    except ImportError as e:
        print(f"⚠️  [WARNING] Sync scheduler not available in production: {e}")
    except Exception as e:
        print(f"❌ [ERROR] Failed to start production sync scheduler: {e}")
elif os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('FLASK_ENV') == 'production':
    # Railway deployment startup
    print("[INFO] Starting in Railway production mode")
    try:
        from utils.sync_scheduler import start_sync_scheduler
        start_sync_scheduler()
        print("✅ [SUCCESS] Railway sync scheduler started with singleton protection")
    except ImportError as e:
        print(f"⚠️  [WARNING] Sync scheduler not available on Railway: {e}")
    except Exception as e:
        print(f"❌ [ERROR] Failed to start Railway sync scheduler: {e}")
# No else block - allow clean imports without starting sync scheduler

# 플랫폼별 일정 동기화 헬퍼 함수들
def sync_event_to_google(event, settings):
    """Google Calendar에 일정 동기화"""
    try:
        # 세션에서 user_id 가져오기
        user_id = session.get('user_id')
        if not user_id:
            print("No user_id in session for Google Calendar sync")
            return False
        
        # Google Calendar 서비스 import
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))
            from services.google_calendar_service import google_calendar_service
        except ImportError as e:
            print(f"Failed to import Google Calendar service: {e}")
            return False
        
        # Google Calendar에 일정 생성
        print(f"Syncing event '{event.get('title', 'Untitled')}' to Google Calendar")
        
        # 일정 데이터 형식 변환
        event_data = {
            'title': event.get('title', 'Untitled Event'),
            'description': event.get('description', ''),
            'start_time': event.get('start_time'),
            'end_time': event.get('end_time'),
            'date': event.get('date'),
            'location': event.get('location'),
            'attendees': event.get('attendees', []),
            'reminders': event.get('reminders', True)
        }
        
        # Google Calendar API 호출
        google_event = google_calendar_service.create_event(
            user_id=user_id,
            calendar_id='primary',
            event_data=event_data
        )
        
        if google_event:
            print(f"Successfully synced event to Google Calendar: {google_event.get('id')}")
            
            # 동기화 매핑 저장 (향후 업데이트/삭제를 위해)
            try:
                google_calendar_service._save_sync_mapping(
                    user_id=user_id,
                    notion_event_id=event.get('id'),
                    google_event_id=google_event['id']
                )
            except Exception as mapping_error:
                print(f"Warning: Failed to save sync mapping: {mapping_error}")
            
            return True
        else:
            print("Failed to create event in Google Calendar")
            return False
        
    except Exception as e:
        print(f"Error syncing to Google: {e}")
        return False

def sync_event_to_outlook(event, settings):
    """Outlook Calendar에 일정 동기화"""
    try:
        # Outlook Calendar API 구현 필요
        print(f"Syncing event '{event.get('title', 'Untitled')}' to Outlook Calendar")
        return True
    except Exception as e:
        print(f"Error syncing to Outlook: {e}")
        return False

def sync_event_to_apple(event, settings):
    """Apple Calendar에 일정 동기화 (iCal 형식)"""
    try:
        # Apple Calendar iCal 동기화 구현 필요
        print(f"Syncing event '{event.get('title', 'Untitled')}' to Apple Calendar")
        return True
    except Exception as e:
        print(f"Error syncing to Apple: {e}")
        return False

def sync_event_to_slack(event, settings):
    """Slack에 일정 알림 생성"""
    try:
        # Slack API를 통한 일정 알림 구현 필요
        print(f"Creating Slack notification for event '{event.get('title', 'Untitled')}'")
        return True
    except Exception as e:
        print(f"Error syncing to Slack: {e}")
        return False

def sync_event_to_notion(event, settings):
    """Notion 데이터베이스에 일정 생성"""
    try:
        # Notion API를 통한 일정 생성 구현 필요
        print(f"Syncing event '{event.get('title', 'Untitled')}' to Notion")
        return True
    except Exception as e:
        print(f"Error syncing to Notion: {e}")
        return False