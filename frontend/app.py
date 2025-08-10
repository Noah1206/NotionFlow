import os
import re
import sys
import datetime
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

# Create Flask app with absolute paths to frontend static and template folders
current_dir = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, 
            static_folder=os.path.join(current_dir, 'static'),
            static_url_path='/static',
            template_folder=os.path.join(current_dir, 'templates'))
app.secret_key = config.FLASK_SECRET_KEY
app.config['TEMPLATES_AUTO_RELOAD'] = True  # 템플릿 자동 리로드 활성화
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
    """Calendar List Management Page - New Refined Design"""
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
        # Get user's actual calendar data from database
        if dashboard_data_available:
            calendar_data = dashboard_data.get_user_calendars(user_id)
            calendar_context.update({
                'personal_calendars': calendar_data['personal_calendars'],
                'shared_calendars': calendar_data['shared_calendars'],
                'summary': calendar_data['summary']
            })
            print(f"📅 Loaded {calendar_data['summary']['total_calendars']} calendars for user {user_id}")
        else:
            print("⚠️ Dashboard data not available, using sample data")
            # Provide sample data for demonstration
            calendar_context.update({
                'personal_calendars': [
                    {
                        'id': 'sample_work',
                        'name': 'Work Calendar',
                        'platform': 'notion',
                        'color': '#2563eb',
                        'event_count': 24,
                        'sync_status': 'synced',
                        'last_sync_display': 'Synced 2 min ago',
                        'is_enabled': True
                    },
                    {
                        'id': 'sample_personal',
                        'name': 'Personal Life',
                        'platform': 'google',
                        'color': '#059669',
                        'event_count': 18,
                        'sync_status': 'synced',
                        'last_sync_display': 'Synced 5 min ago',
                        'is_enabled': True
                    }
                ],
                'shared_calendars': [
                    {
                        'id': 'sample_team',
                        'name': 'Team Meetings',
                        'platform': 'outlook',
                        'color': '#7c3aed',
                        'event_count': 31,
                        'sync_status': 'synced',
                        'last_sync_display': 'Synced 1 min ago',
                        'is_enabled': True,
                        'shared_with_count': 5
                    }
                ],
                'summary': {'total_calendars': 3, 'personal_calendars': 2, 'shared_calendars': 1, 'total_events': 73}
            })
    except Exception as e:
        print(f"❌ Error loading calendar data: {e}")
        # Keep default empty data on error
        pass
    
    return render_template('calendar_list.html', **calendar_context)

# Alternative route for calendar management (legacy redirects)
@app.route('/calendar-refined')
@app.route('/calendar-management') 
def calendar_refined():
    """Legacy route - redirect to main calendar list"""
    return redirect('/dashboard/calendar-list')

# 📅 Calendar Management API Endpoints
@app.route('/api/calendar/create', methods=['POST'])
def create_calendar():
    """Create a new calendar for user"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'User not authenticated'}), 401
        
        data = request.get_json()
        platform = data.get('platform', 'custom')
        calendar_name = data.get('name', f'{platform.title()} Calendar')
        calendar_color = data.get('color', '#6b7280')
        is_shared = data.get('is_shared', False)
        
        # Insert into calendar_sync_configs table
        try:
            if dashboard_data_available:
                # Use Supabase to create calendar config
                result = dashboard_data.supabase.table('calendar_sync_configs').insert({
                    'user_id': user_id,
                    'platform': platform,
                    'calendar_name': calendar_name,
                    'calendar_color': calendar_color,
                    'is_enabled': True,
                    'is_shared': is_shared,
                    'sync_frequency_minutes': 15,
                    'consecutive_failures': 0,
                    'created_at': 'now()'
                }).execute()
                
                return jsonify({
                    'success': True,
                    'message': f'{calendar_name} calendar created successfully',
                    'calendar': {
                        'id': result.data[0]['id'] if result.data else f"{platform}_{user_id}",
                        'name': calendar_name,
                        'platform': platform,
                        'color': calendar_color,
                        'is_shared': is_shared
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Database not available'
                }), 500
        except Exception as e:
            print(f"Error creating calendar: {e}")
            return jsonify({
                'success': False,
                'error': f'Failed to create calendar: {str(e)}'
            }), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/calendar/<calendar_id>/delete', methods=['DELETE'])
def delete_calendar(calendar_id):
    """Delete a calendar"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'User not authenticated'}), 401
        
        if dashboard_data_available:
            # Delete from calendar_sync_configs
            result = dashboard_data.supabase.table('calendar_sync_configs').delete().eq('id', calendar_id).eq('user_id', user_id).execute()
            
            # Also delete associated events
            dashboard_data.supabase.table('calendar_events').delete().eq('user_id', user_id).eq('source_platform', calendar_id.split('_')[0]).execute()
            
            return jsonify({
                'success': True,
                'message': 'Calendar deleted successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/calendar/<calendar_id>/toggle', methods=['POST'])
def toggle_calendar(calendar_id):
    """Toggle calendar enabled/disabled status"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'User not authenticated'}), 401
        
        if dashboard_data_available:
            # Get current status
            current = dashboard_data.supabase.table('calendar_sync_configs').select('is_enabled').eq('id', calendar_id).eq('user_id', user_id).single().execute()
            
            if current.data:
                new_status = not current.data['is_enabled']
                # Update status
                dashboard_data.supabase.table('calendar_sync_configs').update({'is_enabled': new_status}).eq('id', calendar_id).eq('user_id', user_id).execute()
                
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
            'created_at': None
        }
    }
    
    try:
        from utils.dashboard_data import dashboard_data
        if dashboard_data and dashboard_data.supabase:
            # Try to get user profile from user_profiles table (correct table name)
            result = dashboard_data.supabase.table('user_profiles').select('*').eq('user_id', user_id).single().execute()
            if result.data:
                profile_context['profile'] = result.data
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
    ('routes.profile_routes', 'profile_bp', '👤 Profile Management')
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

# Add error handlers for production debugging
@app.errorhandler(404)
def not_found_error(error):
    if os.environ.get('RENDER'):
        print(f"404 Error - Requested URL: {request.url}")
        print(f"Method: {request.method}")
        print(f"Path: {request.path}")
    return render_template('404.html'), 404

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