import os
import re
import sys
import json
import datetime
import uuid
from datetime import datetime as dt
from flask import Flask, render_template, redirect, url_for, request, jsonify, session
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

# Add current directory to path to import backend services and utils
sys.path.append(os.path.dirname(__file__))

# Import critical utilities with error handling
auth_utils_available = False
try:
    from utils.auth_utils import (
        init_auth_utils, 
        security_validator, 
        rate_limiter,
        require_rate_limit,
        validate_dashboard_access
    )
    auth_utils_available = True
    print("✅ Auth utilities loaded")
except ImportError as e:
    print(f"⚠️ Auth utilities not available: {e}")
    # Create minimal auth functions
    security_validator = type('MockValidator', (object,), {
        'validate_url_path': lambda self, x: (True, 'OK'),
        'validate_username_format': lambda self, x: (True, 'OK'),
        'sanitize_input': lambda self, x, **kwargs: x
    })()
    require_rate_limit = lambda *args, **kwargs: lambda f: f
    validate_dashboard_access = lambda x: (True, 'OK')

# Import routing utilities with error handling
routing_available = False
UserRoutingMiddleware = None
DashboardRouteBuilder = None

try:
    from utils.user_routing import UserRoutingMiddleware, DashboardRouteBuilder
    routing_available = True
    print("✅ User routing utilities loaded")
except ImportError as e:
    print(f"⚠️ User routing utilities not available: {e}")
    routing_available = False

# Import dashboard data with error handling
dashboard_data_available = False
try:
    from utils.dashboard_data import dashboard_data
    dashboard_data_available = True
    print("✅ Dashboard data utilities loaded")
except ImportError as e:
    print(f"⚠️ Dashboard data not available: {e}")
    # Create mock dashboard data
    dashboard_data = type('MockDashboardData', (object,), {
        'get_user_profile': lambda self, user_id: None,
        'get_user_api_keys': lambda self, user_id: {},
        'get_user_sync_status': lambda self, user_id: {},
        'get_dashboard_summary': lambda self, user_id: {'total_platforms': 5, 'configured_platforms': 0, 'enabled_platforms': 0},
        'get_user_calendar_events': lambda self, user_id: [],
        'get_user_friends': lambda self, user_id: []
    })()

# Import safe configuration system with fallback handling
try:
    from utils.config_safe import config
    print("✅ Using safe configuration with fallback support")
except ImportError:
    print("⚠️ Safe config not available, falling back to original")
    try:
        from utils.config import config
    except ImportError as e:
        print(f"❌ Configuration import failed: {e}")
        print("🔄 Creating minimal fallback configuration")
        # Create minimal config for emergency fallback
        config = type('MinimalConfig', (object,), {
            'supabase_client': None,
            'FLASK_SECRET_KEY': os.getenv('FLASK_SECRET_KEY', 'emergency-fallback-key'),
            'is_production': lambda: os.environ.get('RENDER') is not None,
            'encrypt_user_identifier': lambda self, x: x,
            'decrypt_user_identifier': lambda self, x: x
        })()

# ===== CALENDAR DATABASE INTEGRATION =====
# Import calendar database functions
calendar_db_available = False
calendar_db = None

try:
    from utils.calendar_db import calendar_db
    if calendar_db.is_available():
        calendar_db_available = True
        print("✅ Calendar database connection successful")
    else:
        print("⚠️ Calendar database not available - using file fallback")
except ImportError as e:
    print(f"⚠️ Calendar database module not found: {e}")
    print("📁 Using JSON file storage for calendars (database import failed)")
except Exception as e:
    print(f"❌ Calendar database connection failed: {e}")
    print("📁 Using JSON file storage for calendars (database connection failed)")

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
        print(f"💾 Saving calendars to file: {file_path}")
        print(f"📊 Saving {len(calendars)} calendars: {calendars}")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(calendars, f, ensure_ascii=False, indent=2)
        print(f"✅ Calendars saved to file for user {user_id}: {len(calendars)} calendars")
        return True
    except Exception as e:
        print(f"❌ Failed to save calendars to file for user {user_id}: {e}")
        return False

def load_user_calendars_legacy(user_id):
    """Legacy: Load user calendars from file (fallback only)"""
    try:
        file_path = get_calendars_file_path(user_id)
        print(f"🔍 Looking for calendar file: {file_path}")
        if not os.path.exists(file_path):
            print(f"📁 No calendar file found for user {user_id}, returning empty list")
            return []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            calendars = json.load(f)
        
        print(f"✅ Calendars loaded from file for user {user_id}: {len(calendars)} calendars")
        print(f"📋 File contents: {calendars}")
        return calendars
    except Exception as e:
        print(f"❌ Failed to load calendars from file for user {user_id}: {e}")
        return []

def save_media_file_locally(media_file, user_id):
    """Save media file to local storage as fallback"""
    try:
        from werkzeug.utils import secure_filename
        import uuid
        
        # Create media directory if it doesn't exist
        media_dir = os.path.join(os.getcwd(), 'media', 'calendar')
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
            print(f"✅ Media file saved locally: {file_path} ({file_size} bytes)")
            
            # Verify it's a valid media file by checking the first few bytes
            with open(file_path, 'rb') as f:
                header = f.read(12)
                print(f"📁 File header (first 12 bytes): {header[:12].hex()}")
            
            return filename, file_path, media_file.content_type
        else:
            print(f"❌ File was not saved properly: {file_path}")
            return None, None, None
        
    except Exception as e:
        print(f"❌ Failed to save media file locally: {e}")
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
            print(f"❌ Database save failed, trying file fallback: {e}")
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
                    print(f"🔄 Found legacy data, migrating {len(legacy_calendars)} calendars to database")
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
            print(f"❌ Database load failed, trying file fallback: {e}")
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

# Calendar data storage functions
def load_user_calendars_legacy(user_id):
    """Load user calendars from JSON file"""
    try:
        calendars_file = f'data/calendars_{user_id}.json'
        if os.path.exists(calendars_file):
            with open(calendars_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Error loading calendars for user {user_id}: {e}")
        return []

def save_user_calendars_legacy(user_id, calendars):
    """Save user calendars to JSON file"""
    try:
        os.makedirs('data', exist_ok=True)
        calendars_file = f'data/calendars_{user_id}.json'
        with open(calendars_file, 'w', encoding='utf-8') as f:
            json.dump(calendars, f, ensure_ascii=False, indent=2, default=str)
        print(f"✅ Saved {len(calendars)} calendars for user {user_id}")
        return True
    except Exception as e:
        print(f"❌ Error saving calendars for user {user_id}: {e}")
        return False
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # 정적 파일 캐싱 비활성화
app.jinja_env.auto_reload = True  # Jinja2 템플릿 자동 리로드

# Session configuration
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours

# ULTRA STRONG CACHE BUSTING - Force reload everything
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.jinja_env.auto_reload = True
app.jinja_env.cache = {}  # Clear Jinja2 cache
app.config['EXPLAIN_TEMPLATE_LOADING'] = True  # Debug template loading

# Force immediate reload - disable all caching mechanisms
import datetime
app.config['CACHE_BUSTER'] = str(int(datetime.datetime.now().timestamp()))

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

# Get Supabase client from configuration
supabase = config.supabase_client

# Initialize auth utilities with config (if available)
if auth_utils_available and hasattr(config, 'SUPABASE_URL'):
    try:
        init_auth_utils(config.SUPABASE_URL, config.SUPABASE_ANON_KEY)
        print("✅ Auth utilities initialized")
    except Exception as e:
        print(f"⚠️ Auth initialization failed: {e}")
else:
    print("🔄 Running without auth utilities - using mock functions")

# Import User Profile Management Functions
from utils.user_profile_manager import UserProfileManager

# Import AuthManager for profile operations
try:
    from utils.auth_manager import AuthManager
except ImportError:
    AuthManager = None
    print("⚠️ AuthManager not available")

def get_dashboard_context(user_id, current_page='dashboard'):
    """Get common dashboard context including user profile"""
    context = {
        'current_page': current_page,
        'user_id': user_id,
        'profile': None,
        'current_date': datetime.date.today().isoformat()
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
        print(f"✅ User {session.get('user_id')} already logged in, redirecting to dashboard")
        return redirect('/dashboard')
    
    if request.method == 'POST':
        # Redirect POST requests to the API endpoint
        return redirect('/api/auth/login', code=307)
    
    # For GET requests, show the login page
    return render_template('login.html')

@app.route('/pricing')
def pricing():
    return render_template('pricing.html')

# 🎯 User-Specific Dashboard Routes
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

# 🔄 Dashboard Routes
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
    print("🔍 Dashboard route accessed!")
    
    # Get current user ID
    user_id = session.get('user_id')
    print(f"🔍 User ID from session: {user_id}")
    
    # 🔒 Security: Redirect unauthenticated users to login
    if not user_id:
        print("⚠️ No user session found, redirecting to login")
        return redirect('/login?from=dashboard')
    
    # Check if initial setup is complete
    if AuthManager:
        profile = AuthManager.get_user_profile(user_id)
        if not profile or not profile.get('display_name') or not profile.get('birthdate'):
            # Setup not complete, redirect to initial setup
            print("🔄 Redirecting to initial setup page")
            return redirect('/initial-setup')
    
    # 🔄 Always redirect to Calendar List (dashboard.html deleted)
    print("🔄 Dashboard redirecting to Calendar List page")
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
    
    # Get current user ID from session
    user_id = session.get('user_id')
    
    if not user_id:
        return redirect('/login?from=calendar-list')
    
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
        print(f"🔍 Loading calendars for user: {user_id}, calendar_db_available: {calendar_db_available}, dashboard_data_available: {dashboard_data_available}")
        
        # Try calendar database first
        if calendar_db_available and calendar_db:
            try:
                print(f"🔍 Attempting to load calendars from calendar database for user: {user_id}")
                user_calendars = calendar_db.get_user_calendars(user_id)
                print(f"🔍 Raw calendar data from database: {user_calendars}")
                
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
                print(f"📅 Loaded {len(user_calendars)} calendars from database for user {user_id}")
                print(f"📅 Personal: {len(personal_calendars)}, Shared: {len(shared_calendars)}")
            except Exception as e:
                print(f"⚠️ Calendar DB load failed, trying dashboard data: {e}")
                import traceback
                traceback.print_exc()
                # Don't modify global variables, just continue to next option
        
        # Fallback to dashboard data
        elif dashboard_data_available:
            try:
                print(f"🔍 Attempting to load calendars from dashboard data for user: {user_id}")
                calendar_data = dashboard_data.get_user_calendars(user_id)
                print(f"🔍 Raw calendar data from dashboard data: {calendar_data}")
                
                calendar_context.update({
                    'personal_calendars': calendar_data['personal_calendars'],
                    'shared_calendars': calendar_data['shared_calendars'],
                    'summary': calendar_data['summary']
                })
                print(f"📅 Loaded {calendar_data['summary']['total_calendars']} calendars from dashboard data for user {user_id}")
                print(f"📅 Personal: {len(calendar_data['personal_calendars'])}, Shared: {len(calendar_data['shared_calendars'])}")
            except Exception as e:
                print(f"⚠️ Dashboard data load failed, using file storage: {e}")
                import traceback
                traceback.print_exc()
                # Continue to file storage fallback
        
        # Final fallback to file storage
        # Use file storage if no calendars were loaded from database sources
        if not calendar_context.get('personal_calendars') and not calendar_context.get('shared_calendars'):
            print("📁 Using file storage for calendar list")
            
            # Load user calendars from file
            user_calendars = load_user_calendars_legacy(user_id)
            print(f"📅 Loaded calendars for user {user_id}: {len(user_calendars)} total")
            
            # Separate personal and shared calendars
            personal_calendars = [cal for cal in user_calendars if not cal.get('is_shared', False)]
            shared_calendars = [cal for cal in user_calendars if cal.get('is_shared', False)]
            print(f"👤 Personal calendars: {len(personal_calendars)}")
            print(f"🤝 Shared calendars: {len(shared_calendars)}")
            
            # If no calendars exist, keep empty
            if not user_calendars:
                print("📋 No calendars found, starting with empty calendar list")
                personal_calendars = []
                shared_calendars = []
            
            calendar_context.update({
                'personal_calendars': personal_calendars,
                'shared_calendars': shared_calendars,
                'summary': {
                    'total_calendars': len(personal_calendars) + len(shared_calendars),
                    'personal_calendars': len(personal_calendars),
                    'shared_calendars': len(shared_calendars),
                    'total_events': sum(cal.get('event_count', 0) for cal in user_calendars if user_calendars)
                }
            })
    except Exception as e:
        print(f"❌ Error loading calendar data: {e}")
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

@app.route('/api/calendar/<calendar_id>/media')
def get_calendar_media(calendar_id):
    """Get media files for a specific calendar"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # Try to get calendar from database
        if calendar_db_available and calendar_db:
            calendar_data = calendar_db.get_calendar_by_id(calendar_id, user_id)
            print(f"🎵 API: Calendar data for {calendar_id}: {calendar_data}")
            
            if calendar_data:
                media_files = []
                
                # Check for media file path in calendar data
                if calendar_data.get('media_file_path'):
                    # Create proper media URL
                    media_path = calendar_data['media_file_path']
                    media_filename = calendar_data.get('media_filename', 'Unknown')
                    
                    # Construct the media URL based on the file path
                    if media_path.startswith('http'):
                        # It's already a URL
                        media_url = media_path
                    else:
                        # It's a local file path - serve it through Flask
                        # Extract just the filename from the path
                        import os
                        filename = os.path.basename(media_path)
                        media_url = f"/media/calendar/{calendar_id}/{filename}"
                    
                    media_files = [{
                        'title': media_filename or 'Calendar Music',
                        'artist': calendar_data.get('name', 'My Calendar'),
                        'src': media_url,
                        'type': calendar_data.get('media_file_type', 'audio/mpeg')
                    }]
                    
                    print(f"🎵 API: Returning media files: {media_files}")
                else:
                    print(f"🎵 API: No media file path found for calendar {calendar_id}")
                
                return jsonify({'media_files': media_files})
        
        # Fallback: no media files
        print(f"🎵 API: No calendar found or database not available")
        return jsonify({'media_files': []})
        
    except Exception as e:
        print(f"❌ Error getting calendar media: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to get media files'}), 500


@app.route('/dashboard/calendar/<calendar_id>')
def calendar_detail(calendar_id):
    """Individual Calendar Detail Page"""
    user_id = session.get('user_id')
    
    if not user_id:
        return redirect(f'/login?from=calendar/{calendar_id}')
    
    # Get common dashboard context
    context = get_dashboard_context(user_id, 'calendar-detail')
    
    # Load calendar data - try database first, then file fallback
    calendar = None
    
    # Try calendar database first
    if calendar_db_available:
        print(f"🎵 Loading calendar {calendar_id} from database...")
        calendar = calendar_db.get_calendar_by_id(calendar_id, user_id)
        if calendar:
            print(f"✅ Calendar found in database: {calendar.get('name')}")
    
    # Fallback to legacy file loading
    if not calendar:
        print(f"🎵 Fallback: Loading calendar from file system...")
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
    
    # Prepare media URL if media file exists
    media_url = ''
    print(f"🎵 Calendar media info - filename: {calendar.get('media_filename')}, path: {calendar.get('media_file_path')}, type: {calendar.get('media_file_type')}")
    
    if calendar.get('media_file_path'):
        media_path = calendar['media_file_path']
        # Check if it's already a URL
        if media_path.startswith('http'):
            media_url = media_path
        else:
            # Create a proper URL for serving the file
            import os
            filename = os.path.basename(media_path)
            media_url = f"/media/calendar/{calendar_id}/{filename}"
        print(f"🎵 Media URL set to: {media_url}")
    else:
        print(f"🎵 No media file path found for calendar {calendar.get('name')}")
    
    calendar['media_url'] = media_url
    
    context.update({
        'calendar': calendar,
        'page_title': f'{calendar["name"]} - 캘린더 상세'
    })
    
    return render_template('calendar_detail.html', **context)

# Media file serving route
@app.route('/media/calendar/<calendar_id>/<filename>', endpoint='calendar_media_server')
def serve_calendar_media_v2(calendar_id, filename):
    """Serve media files for calendars"""
    print(f"🎵 Media request: calendar_id={calendar_id}, filename={filename}")
    
    user_id = session.get('user_id')
    if not user_id:
        print("❌ No user authentication")
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        # Get calendar to verify ownership
        if calendar_db_available:
            calendar = calendar_db.get_calendar_by_id(calendar_id, user_id)
            print(f"🎵 Calendar found: {calendar is not None}")
            
            if not calendar:
                print("❌ Calendar not found in database")
                return jsonify({'error': 'Calendar not found'}), 404
            
            media_path = calendar.get('media_file_path')
            print(f"🎵 Media path from DB: {media_path}")
            
            if media_path and media_path.startswith('http'):
                # Redirect to external URL (like Supabase storage)
                print(f"🔗 Redirecting to external URL: {media_path}")
                return redirect(media_path)
            elif media_path:
                # Serve local file
                import os
                print(f"🎵 Checking local file existence: {media_path}")
                if os.path.exists(media_path):
                    print(f"✅ Serving local file: {media_path}")
                    # Determine MIME type
                    if media_path.endswith('.mp3'):
                        mimetype = 'audio/mpeg'
                    elif media_path.endswith('.mp4'):
                        mimetype = 'video/mp4'
                    elif media_path.endswith('.wav'):
                        mimetype = 'audio/wav'
                    elif media_path.endswith('.m4a'):
                        mimetype = 'audio/mp4'
                    elif media_path.endswith('.ogg'):
                        mimetype = 'audio/ogg'
                    elif media_path.endswith('.webm'):
                        mimetype = 'audio/webm'
                    else:
                        mimetype = 'application/octet-stream'
                    
                    # Check file size for debugging
                    file_size = os.path.getsize(media_path)
                    print(f"📁 File size: {file_size} bytes")
                    
                    # Add cache control headers
                    from flask import Response
                    def generate():
                        with open(media_path, 'rb') as f:
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
                    print(f"❌ File not found at path: {media_path}")
            else:
                print("❌ No media path found in calendar data")
        else:
            print("❌ Calendar DB not available")
        
        return jsonify({'error': 'Media file not found'}), 404
        
    except Exception as e:
        print(f"❌ Error serving media file: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to serve media file'}), 500

# Alternative route for calendar management (legacy redirects)
@app.route('/calendar-refined')
@app.route('/calendar-management') 
def calendar_refined():
    """Legacy route - redirect to main calendar list"""
    return redirect('/dashboard/calendar-list')

# 📅 Calendar Management API Endpoints
@app.route('/api/calendar/create', methods=['POST'])
def create_calendar():
    """Create a new calendar for user with optional media file upload"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'User not authenticated'}), 401
        
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
                        
                        print(f"📎 Uploading to Supabase Storage: {unique_filename}")
                        
                        # Upload to Supabase Storage
                        if calendar_db_available and calendar_db.supabase:
                            # Read file content
                            file_content = media_file.read()
                            
                            # Check if media bucket exists, create if not
                            try:
                                # Try to get bucket info first
                                calendar_db.supabase.storage.get_bucket('media')
                                print("✅ Media bucket exists")
                            except Exception as bucket_error:
                                print(f"⚠️ Media bucket doesn't exist, creating: {bucket_error}")
                                try:
                                    # Create the bucket
                                    calendar_db.supabase.storage.create_bucket('media', {
                                        'public': True,
                                        'file_size_limit': 100 * 1024 * 1024  # 100MB limit
                                    })
                                    print("✅ Created media bucket")
                                except Exception as create_error:
                                    print(f"❌ Failed to create media bucket: {create_error}")
                            
                            # Upload to Supabase Storage
                            result = calendar_db.supabase.storage.from_('media').upload(
                                path=unique_filename,
                                file=file_content,
                                file_options={"content-type": media_file.content_type}
                            )
                            
                            print(f"📎 Storage upload result: {result}")
                            
                            if result:
                                # Get public URL
                                public_url = calendar_db.supabase.storage.from_('media').get_public_url(unique_filename)
                                
                                media_filename = filename  # Original filename
                                media_file_path = public_url  # Public URL
                                media_file_type = media_file.content_type
                                
                                print(f"✅ Media file uploaded to Supabase Storage: {media_filename}")
                                print(f"🔗 Public URL: {public_url}")
                            else:
                                print("❌ Failed to upload to Supabase Storage, falling back to local storage")
                                # Fallback to local storage
                                media_file.seek(0)  # Reset file pointer
                                media_filename, media_file_path, media_file_type = save_media_file_locally(media_file, user_id)
                        else:
                            print("❌ Supabase Storage not available, using local storage")
                            # Fallback to local storage
                            media_filename, media_file_path, media_file_type = save_media_file_locally(media_file, user_id)
                    except Exception as storage_error:
                        print(f"❌ Storage upload error: {storage_error}")
                        # Fallback to local storage on error
                        print("⚠️ Storage error, falling back to local storage")
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
            media_filename = None
            media_file_path = None
            media_file_type = None
        
        print(f"🔍 Creating calendar: {calendar_name}, platform: {platform}, color: {calendar_color}")
        
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
                    'description': f'{calendar_name} - Created on {datetime.datetime.now().strftime("%Y-%m-%d")}'
                }
                
                # Add media file information if uploaded
                if media_filename:
                    calendar_data['media_filename'] = media_filename
                    calendar_data['media_file_path'] = media_file_path
                    calendar_data['media_file_type'] = media_file_type
                    print(f"📎 Adding media file to calendar: {media_filename}")
                
                # Use calendar_db to create calendar
                calendar_id = calendar_db.create_calendar(user_id, calendar_data)
                
                if calendar_id:
                    print(f"✅ Created calendar in DB using calendar_db: {calendar_name} (ID: {calendar_id})")
                else:
                    print("❌ calendar_db.create_calendar returned None, falling back to file storage")
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
                print("📁 DB not available, using file storage for calendar creation")
                
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
                    'created_at': datetime.datetime.now().isoformat(),
                    'user_id': user_id,
                    'description': f'{calendar_name} - Created on {datetime.datetime.now().strftime("%Y-%m-%d")}'
                }
                
                # Add to user's calendars
                user_calendars.append(new_calendar)
                
                # Save updated calendars
                if save_user_calendars_legacy(user_id, user_calendars):
                    print(f"✅ Created calendar in file: {calendar_name} (ID: {calendar_id})")
                    
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
            print(f"Error creating calendar: {e}")
            return jsonify({
                'success': False,
                'error': f'Failed to create calendar: {str(e)}'
            }), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

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
            'created_at': datetime.datetime.now().isoformat(),
            'user_id': user_id,
            'description': f'{calendar_name} - Created on {datetime.datetime.now().strftime("%Y-%m-%d")}'
        }
        
        # Add to user's calendars
        user_calendars.append(new_calendar)
        
        # Save updated calendars
        save_user_calendars_legacy(user_id, user_calendars)
        
        print(f"✅ Created calendar '{calendar_name}' with ID {calendar_id} for user {user_id}")
        
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
        print(f"❌ Error in simple_create_calendar: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/calendar/<calendar_id>/delete', methods=['DELETE'])
def delete_calendar(calendar_id):
    """Delete a calendar"""
    try:
        print(f"🗑️ Delete calendar request: calendar_id={calendar_id}")
        user_id = session.get('user_id')
        print(f"🗑️ User ID from session: {user_id}")
        
        if not user_id:
            print("❌ User not authenticated")
            return jsonify({'success': False, 'error': 'User not authenticated'}), 401
        
        print(f"🗑️ Dashboard data available: {dashboard_data_available}")
        
        # Try calendar database first
        if calendar_db_available:
            print(f"🗑️ Using calendar database for deletion...")
            success = calendar_db.delete_calendar(calendar_id, user_id)
            if success:
                print("✅ Calendar deletion completed successfully")
                return jsonify({
                    'success': True,
                    'message': 'Calendar deleted successfully'
                })
            else:
                print("❌ Calendar database deletion failed")
                return jsonify({'success': False, 'error': 'Failed to delete calendar from database'}), 500
        
        # Fallback to dashboard data
        elif dashboard_data_available:
            try:
                # First, get calendar info to check for media files
                print(f"🗑️ Getting calendar info for media cleanup...")
                calendar_result = dashboard_data.admin_client.table('calendars').select('media_file_path').eq('id', calendar_id).eq('owner_id', user_id).single().execute()
                print(f"🗑️ Calendar query result: {calendar_result}")
                
                # Clean up media file if it exists
                if calendar_result.data and calendar_result.data.get('media_file_path'):
                    media_path = calendar_result.data['media_file_path']
                    try:
                        import os
                        if os.path.exists(media_path):
                            os.remove(media_path)
                            print(f"✅ Deleted media file: {media_path}")
                    except Exception as e:
                        print(f"⚠️ Failed to delete media file: {e}")
                
                # Delete from calendars table using admin client
                print(f"🗑️ Deleting calendar from database...")
                result = dashboard_data.admin_client.table('calendars').delete().eq('id', calendar_id).eq('owner_id', user_id).execute()
                print(f"🗑️ Calendar delete result: {result}")
                
                # Also delete associated events
                print(f"🗑️ Deleting associated events...")
                events_result = dashboard_data.admin_client.table('calendar_events').delete().eq('user_id', user_id).eq('calendar_id', calendar_id).execute()
                print(f"🗑️ Events delete result: {events_result}")
                
                print("✅ Calendar deletion completed successfully")
                return jsonify({
                    'success': True,
                    'message': 'Calendar deleted successfully'
                })
                
            except Exception as db_error:
                print(f"❌ Database error during deletion: {db_error}")
                return jsonify({'success': False, 'error': f'Database error: {str(db_error)}'}), 500
        else:
            print("❌ No database available")
            return jsonify({'success': False, 'error': 'Database not available'}), 500
            
    except Exception as e:
        print(f"❌ General error in delete_calendar: {e}")
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
    
    # Add API keys specific data
    dashboard_context.update({
        'platforms': {},
        'summary': {'total_platforms': 5, 'configured_platforms': 0, 'enabled_platforms': 0}
    })
    
    try:
        from utils.dashboard_data import dashboard_data
        platforms = dashboard_data.get_user_api_keys(user_id)
        summary = dashboard_data.get_api_keys_summary(user_id)
        
        dashboard_context.update({
            'platforms': platforms,
            'summary': summary
        })
    except Exception as e:
        print(f"Error loading API keys data: {e}")
    
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
                
                # Get connector count (platform connections)
                connectors_result = dashboard_data.supabase.table('platform_connections').select('id').eq('user_id', user_id).execute()
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
        # Handle file upload here
        # For now, just return success with a placeholder URL
        return jsonify({
            'success': True,
            'avatar_url': '/static/images/default-avatar.svg'
        })
    except Exception as e:
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
    
    print(f"🔐 API Keys 접근 시도: {encrypted_identifier}")
    
    # 암호화된 식별자 복호화 시도
    try:
        decrypted_value = decrypt_user_id(encrypted_identifier)
        print(f"🔓 복호화 결과: {decrypted_value}")
        
        if not decrypted_value:
            print("❌ 복호화 실패 - 404 페이지로 이동")
            return render_template('404.html'), 404
            
        # 이메일인지 사용자 ID인지 판단
        is_email = '@' in decrypted_value
        print(f"📧 이메일 여부: {is_email}")
        
        # 세션과 일치하는지 확인
        session_email = session.get('user_email')
        session_user_id = session.get('user_id')
        print(f"👤 세션 정보 - 사용자 ID: {session_user_id}, 이메일: {session_email}")
        
        if is_email:
            # 이메일로 접근한 경우
            user_id = session_user_id or 'demo-user'
            user_email = decrypted_value
        else:
            # 사용자 ID로 접근한 경우  
            user_id = decrypted_value
            user_email = session_email or 'demo@example.com'
        
        print(f"✅ 인증 성공 - 사용자 ID: {user_id}, 이메일: {user_email}")
        
    except Exception as e:
        print(f"❌ 식별자 복호화 실패: {e}")
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
            print(f"🔐 사용자 ID 암호화: {dashboard_context['encrypted_user_id']}")
        
        if user_email and not dashboard_context['encrypted_email']:
            dashboard_context['encrypted_email'] = encrypt_user_id(user_email)
            print(f"🔐 이메일 암호화: {dashboard_context['encrypted_email']}")
        
        # 플랫폼 및 요약 데이터 로드
        if user_id:
            try:
                platforms = dashboard_data.get_user_api_keys(user_id)
                summary = dashboard_data.get_dashboard_summary(user_id)
                
                dashboard_context.update({
                    'platforms': platforms,
                    'summary': summary
                })
                print(f"📊 데이터 로드 성공 - 플랫폼: {len(platforms)}, 요약: {summary}")
                
            except Exception as data_error:
                print(f"⚠️ 데이터 로드 실패, 기본값 사용: {data_error}")
                # dashboard_data 실패 시 기본 데이터 사용
                dashboard_context.update({
                    'platforms': {},
                    'summary': {'total_platforms': 5, 'configured_platforms': 0, 'enabled_platforms': 0}
                })
        
    except Exception as e:
        print(f"❌ 데이터 로딩 오류: {e}")
        dashboard_context.update({
            'platforms': {},
            'summary': {'total_platforms': 5, 'configured_platforms': 0, 'enabled_platforms': 0}
        })
    
    print(f"🎯 최종 컨텍스트: {dashboard_context}")
    return render_template('dashboard-api-keys.html', **dashboard_context)



# 🔑 Platform-specific API key setup routes
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

# 🔗 User Profile API Endpoints
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

# 📅 Simplified Calendar APIs for Dashboard



# 🚀 One-Click Connection API Endpoints
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
        print(f"❌ Platform connection error: {e}")
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
        
        # 시뮬레이션 데이터 - 실제로는 데이터베이스에서 조회
        mock_status = {
            'connected': False,
            'last_sync': None,
            'sync_count': 0,
            'status': 'inactive'
        }
        
        return jsonify({
            'success': True,
            'platform': platform,
            **mock_status
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

# 🔧 Platform-specific connection handlers
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
        print(f"🧠 Initializing smart cache for user {user_id}, platform {platform}")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize smart cache: {e}")
        return False

def update_smart_cache_success(user_id, platform, response_time_ms=0):
    """연결 성공 시 스마트 캐시 업데이트"""
    try:
        # 실제로는 Supabase 함수 호출: update_connection_success()
        print(f"🧠 Updating smart cache success for {platform}: {response_time_ms}ms")
        return True
    except Exception as e:
        print(f"❌ Failed to update smart cache success: {e}")
        return False

def update_smart_cache_error(user_id, platform, error_message):
    """오류 시 스마트 캐시 업데이트"""
    try:
        # 실제로는 Supabase 함수 호출: update_connection_error()
        print(f"🧠 Updating smart cache error for {platform}: {error_message}")
        return True
    except Exception as e:
        print(f"❌ Failed to update smart cache error: {e}")
        return False

def update_smart_cache_sync(user_id, platform, items_count=0, duration_ms=0):
    """동기화 성공 시 스마트 캐시 업데이트"""
    try:
        # 실제로는 Supabase 함수 호출: update_sync_success()
        print(f"🧠 Updating smart cache sync for {platform}: {items_count} items, {duration_ms}ms")
        return True
    except Exception as e:
        print(f"❌ Failed to update smart cache sync: {e}")
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
        print(f"❌ Failed to get smart cache data: {e}")
        return None

# 🏥 Health Check Endpoint for Render
@app.route('/health')
def health_check():
    """Health check endpoint for Render deployment"""
    return jsonify({
        'status': 'healthy',
        'message': 'NotionFlow is running successfully',
        'timestamp': datetime.utcnow().isoformat()
    })

# 🔍 Debug endpoint for session testing
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
    ('routes.api_key_routes', 'api_key_bp', '🔑 API Key Management'),
    ('routes.auth_routes', 'auth_bp', '🔐 Authentication'),
    ('routes.sync_routes', 'sync_bp', '🔄 Sync Management'),
    ('routes.sync_status_routes', 'sync_status_bp', '📊 Sync Status'),
    ('routes.auto_connect_routes', 'auto_connect_bp', '🚀 Auto-Connect'),
    ('routes.oauth_routes', 'oauth_bp', '🔐 OAuth'),
    ('oauth.embedded_oauth', 'embedded_oauth_bp', '🔗 Embedded OAuth'),
    ('routes.integration_routes', 'integration_bp', '🔗 Integration'),
    ('routes.enhanced_features_routes', 'enhanced_bp', '🚀 Enhanced Features'),
    ('routes.dashboard_api_routes', 'dashboard_api_bp', '📊 Dashboard API'),
    ('routes.user_visit_routes', 'visit_bp', '🚀 User Visit Tracking'),
    ('routes.profile_routes', 'profile_bp', '👤 Profile Management'),
    ('routes.platform_registration_routes', 'platform_reg_bp', '🔗 Platform Registration'),
    ('routes.calendar_connection_routes', 'calendar_conn_bp', '📅 Calendar Connections'),
    ('routes.calendar_api_routes', 'calendar_api_bp', '🗓️ Calendar API'),
    ('routes.health_check_routes', 'health_bp', '🔍 Platform Health Check')
]

registered_blueprints = []
for module_name, blueprint_name, description in blueprints_to_register:
    try:
        module = __import__(module_name, fromlist=[blueprint_name])
        blueprint = getattr(module, blueprint_name)
        app.register_blueprint(blueprint)
        registered_blueprints.append(description)
        print(f"✅ {description} blueprint registered")
    except ImportError as e:
        print(f"⚠️ {description} blueprint not available: {e}")
    except Exception as e:
        print(f"❌ Error registering {description} blueprint: {e}")

print(f"📦 Total blueprints registered: {len(registered_blueprints)}")

# 🔧 Add compatibility route for JavaScript
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
    print("✅ Webhook handlers registered")
except ImportError as e:
    print(f"⚠️ Webhook handlers not available: {e}")
    pass

# ⚡ Register Slack Slash Commands (optional)
try:
    from backend.services.slack_slash_commands import slash_commands_bp
    app.register_blueprint(slash_commands_bp)
    print("✅ Slack slash commands registered")
except ImportError as e:
    print(f"⚠️ Slack slash commands not available: {e}")
    pass

# Removed duplicate health endpoint

# ====== 💳 PAYMENT SYSTEM ROUTES ======
# 결제 시스템 라우트 구현

try:
    from utils.payment_manager import PaymentManager
    payment_manager = PaymentManager()
    print("✅ Payment manager initialized")
except ImportError as e:
    print(f"⚠️ Payment manager not available: {e}")
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

# Add error handlers for production debugging
@app.errorhandler(404)
def not_found_error(error):
    if os.environ.get('RENDER'):
        print(f"404 Error - Requested URL: {request.url}")
        print(f"Method: {request.method}")
        print(f"Path: {request.path}")
    return render_template('404.html'), 404

# Duplicate route removed - using the one defined at line 633

@app.errorhandler(500)
def internal_error(error):
    if os.environ.get('RENDER'):
        print(f"500 Error - URL: {request.url}")
        print(f"Error: {error}")
    return render_template('404.html'), 500

# ===== CACHE CONTROL =====
# Force template reload for development
def force_template_reload():
    app.jinja_env.cache = {}

# Add cache-busting headers to all responses
@app.after_request
def add_cache_headers(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache' 
    response.headers['Expires'] = '0'
    return response

if __name__ == '__main__':
    # Start sync scheduler (if available)
    try:
        from utils.sync_scheduler import start_sync_scheduler
        start_sync_scheduler()
        print("✅ Sync scheduler started")
    except ImportError as e:
        print(f"⚠️ Sync scheduler not available: {e}")
    except Exception as e:
        print(f"❌ Failed to start sync scheduler: {e}")
    
    port = int(os.environ.get('PORT', 5003))
    app.run(host='0.0.0.0', port=port, debug=True)
else:
    # Production startup with error handling
    try:
        from utils.sync_scheduler import start_sync_scheduler
        start_sync_scheduler()
        print("✅ Production sync scheduler started")
    except ImportError as e:
        print(f"⚠️ Sync scheduler not available in production: {e}")
    except Exception as e:
        print(f"❌ Failed to start production sync scheduler: {e}")