#!/usr/bin/env python3
"""
🌊 NotionFlow - Unified Calendar & Email Management Application
Simplified version without encrypted URLs
"""

import os
import sys
import logging
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, send_from_directory
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Flask app initialization
app = Flask(__name__, template_folder='frontend/templates', static_folder='frontend/static')
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Import utilities
from utils.user_profile_manager import UserProfileManager
from utils.dashboard_data import dashboard_data
from utils.auth_manager import AuthManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 🏠 Home Routes
@app.route('/')
def index():
    """Landing page"""
    return render_template('index.html')

@app.route('/login')
def login():
    """Login page"""
    return render_template('login.html')

@app.route('/signup')
def signup():
    """Signup page"""
    return render_template('signup.html')

@app.route('/logout')
def logout():
    """Logout route"""
    session.clear()
    return redirect('/')

# 🔄 Dashboard Routes (Simplified)
@app.route('/dashboard')
def dashboard():
    """Main dashboard route"""
    # Check authentication
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/login')
    
    # Load dashboard data
    dashboard_context = {
        'current_page': 'dashboard',
        'user_id': user_id,
        'current_year': datetime.now().year,
        'current_month': datetime.now().month,
        'events': [],
        'sync_status': {},
        'summary': {}
    }
    
    try:
        # Get dashboard data
        events = dashboard_data.get_user_calendar_events(user_id)
        sync_status = dashboard_data.get_user_sync_status(user_id)
        summary = dashboard_data.get_dashboard_summary(user_id)
        
        dashboard_context.update({
            'events': events,
            'sync_status': sync_status,
            'summary': summary
        })
    except Exception as e:
        logger.error(f"Error loading dashboard data: {e}")
    
    return render_template('dashboard.html', **dashboard_context)

@app.route('/dashboard/calendar')
def dashboard_calendar():
    """Calendar page"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/login')
    
    dashboard_context = {
        'current_page': 'calendar',
        'user_id': user_id,
        'events': [],
        'calendars': []
    }
    
    try:
        events = dashboard_data.get_user_calendar_events(user_id)
        calendars = dashboard_data.get_user_calendars(user_id)
        
        dashboard_context.update({
            'events': events,
            'calendars': calendars
        })
    except Exception as e:
        logger.error(f"Error loading calendar data: {e}")
    
    return render_template('dashboard-calendar.html', **dashboard_context)

@app.route('/dashboard/api-keys')
def dashboard_api_keys():
    """API keys management page"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/login')
    
    dashboard_context = {
        'current_page': 'api-keys',
        'user_id': user_id,
        'platforms': {},
        'summary': {'total_platforms': 5, 'configured_platforms': 0, 'enabled_platforms': 0}
    }
    
    try:
        platforms = dashboard_data.get_user_api_keys(user_id)
        summary = dashboard_data.get_api_keys_summary(user_id)
        
        dashboard_context.update({
            'platforms': platforms,
            'summary': summary
        })
    except Exception as e:
        logger.error(f"Error loading API keys data: {e}")
    
    return render_template('dashboard-api-keys.html', **dashboard_context)

@app.route('/dashboard/settings')
def dashboard_settings():
    """Settings page"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/login')
    
    dashboard_context = {
        'current_page': 'settings',
        'user_id': user_id,
        'user_profile': None,
        'platforms': {},
        'sync_status': {}
    }
    
    try:
        user_profile = dashboard_data.get_user_profile(user_id)
        platforms = dashboard_data.get_user_api_keys(user_id)
        sync_status = dashboard_data.get_user_sync_status(user_id)
        
        dashboard_context.update({
            'user_profile': user_profile,
            'platforms': platforms,
            'sync_status': sync_status
        })
    except Exception as e:
        logger.error(f"Error loading settings data: {e}")
    
    return render_template('dashboard-settings.html', **dashboard_context)

@app.route('/dashboard/friends')
def dashboard_friends():
    """Friends page"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/login')
    
    dashboard_context = {
        'current_page': 'friends',
        'user_id': user_id,
        'friends': []
    }
    
    try:
        friends = dashboard_data.get_user_friends(user_id)
        dashboard_context['friends'] = friends
    except Exception as e:
        logger.error(f"Error loading friends data: {e}")
    
    return render_template('dashboard-friends.html', **dashboard_context)

# 🔗 API Endpoints
@app.route('/api/auth/status', methods=['GET'])
def auth_status():
    """Check authentication status"""
    is_authenticated = 'user_id' in session
    return jsonify({
        'authenticated': is_authenticated,
        'user_id': session.get('user_id'),
        'username': session.get('username')
    })

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """Login API endpoint"""
    try:
        data = request.json
        login_identifier = data.get('login_identifier')
        password = data.get('password')
        
        if not login_identifier or not password:
            return jsonify({'success': False, 'message': '이메일/사용자명과 비밀번호를 입력해주세요'}), 400
        
        # Authenticate with AuthManager
        success, user_data, access_token = AuthManager.authenticate_with_supabase(login_identifier, password)
        
        if success and user_data:
            # Create session
            session['user_id'] = user_data['id']
            session['username'] = user_data.get('username')
            session['email'] = user_data.get('email')
            session['authenticated'] = True
            
            return jsonify({
                'success': True,
                'message': '로그인 성공',
                'user': {
                    'id': user_data['id'],
                    'email': user_data.get('email'),
                    'username': user_data.get('username')
                }
            })
        else:
            return jsonify({'success': False, 'message': '로그인 실패'}), 401
            
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    """Register API endpoint"""
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        username = data.get('username')
        display_name = data.get('display_name')
        
        if not email or not password:
            return jsonify({'success': False, 'message': '이메일과 비밀번호를 입력해주세요'}), 400
        
        # Register with AuthManager
        success, user_data, access_token = AuthManager.register_with_supabase(email, password, username, display_name)
        
        if success and user_data:
            return jsonify({
                'success': True,
                'message': '회원가입 성공',
                'user': {
                    'id': user_data['id'],
                    'email': user_data.get('email'),
                    'username': user_data.get('username')
                }
            })
        else:
            return jsonify({'success': False, 'message': '회원가입 실패'}), 400
            
    except Exception as e:
        logger.error(f"Register error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/user/dashboard-url', methods=['GET'])
def get_user_dashboard_url():
    """Get user dashboard URL (simplified)"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    # Always return simple dashboard URL
    return jsonify({
        'success': True,
        'dashboard_url': '/dashboard',
        'user_id': session.get('user_id')
    })

@app.route('/api/connect/<platform>', methods=['POST'])
def connect_platform(platform):
    """원클릭 플랫폼 연결 API"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '로그인이 필요합니다'}), 401
    
    user_id = session.get('user_id')
    
    try:
        # Platform-specific connection logic
        if platform == 'notion':
            # Notion 연결 로직
            return jsonify({
                'success': True,
                'message': 'Notion 연결 성공',
                'redirect_url': f'https://api.notion.com/v1/oauth/authorize?client_id={os.environ.get("NOTION_CLIENT_ID")}&response_type=code&redirect_uri={request.host_url}callback/notion'
            })
        elif platform == 'google':
            # Google 연결 로직
            return jsonify({
                'success': True,
                'message': 'Google 연결 시작',
                'redirect_url': f'/auth/google?user_id={user_id}'
            })
        elif platform == 'outlook':
            # Outlook 연결 로직
            return jsonify({
                'success': True,
                'message': 'Outlook 연결 시작',
                'redirect_url': f'/auth/outlook?user_id={user_id}'
            })
        elif platform == 'slack':
            # Slack 연결 로직
            return jsonify({
                'success': True,
                'message': 'Slack 연결 시작',
                'redirect_url': f'https://slack.com/oauth/v2/authorize?client_id={os.environ.get("SLACK_CLIENT_ID")}&scope=channels:read,chat:write&redirect_uri={request.host_url}callback/slack'
            })
        elif platform == 'todoist':
            # Todoist 연결 로직
            return jsonify({
                'success': True,
                'message': 'Todoist 연결 시작',
                'redirect_url': f'https://todoist.com/oauth/authorize?client_id={os.environ.get("TODOIST_CLIENT_ID")}&scope=read,write&redirect_uri={request.host_url}callback/todoist'
            })
        else:
            return jsonify({'success': False, 'message': '지원하지 않는 플랫폼입니다'}), 400
            
    except Exception as e:
        logger.error(f"Platform connection error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/credentials/save', methods=['POST'])
def save_credentials():
    """Save API credentials"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '로그인이 필요합니다'}), 401
    
    user_id = session.get('user_id')
    data = request.json
    
    platform = data.get('platform')
    credentials = data.get('credentials', {})
    
    try:
        # Save credentials to database
        from utils.api_credential_manager import save_platform_credentials
        success = save_platform_credentials(user_id, platform, credentials)
        
        if success:
            return jsonify({'success': True, 'message': f'{platform} 인증 정보가 저장되었습니다'})
        else:
            return jsonify({'success': False, 'message': '인증 정보 저장 실패'}), 500
            
    except Exception as e:
        logger.error(f"Credential save error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 🏥 Health check endpoint
@app.route('/health')
def health():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

# 🚀 Run the application
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)