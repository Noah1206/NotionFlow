"""
🎯 프로필 관리 라우트
사용자 프로필 CRUD API 엔드포인트
"""

from flask import Blueprint, request, jsonify, session, render_template
from utils.auth_manager import AuthManager, require_auth
from datetime import datetime
import os
import uuid
import base64
from werkzeug.utils import secure_filename

profile_bp = Blueprint('profile', __name__)

# 허용된 파일 확장자
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    """허용된 파일 확장자 체크"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@profile_bp.route('/api/profile', methods=['GET'])
@require_auth
def get_profile():
    """현재 사용자 프로필 조회"""
    try:
        user_id = AuthManager.get_current_user_id()
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        profile = AuthManager.get_user_profile(user_id)
        if not profile:
            # 기본 프로필 생성
            user_info = session.get('user_info', {})
            email = user_info.get('email', '')
            profile = {
                'user_id': user_id,
                'username': f'user_{user_id[:8]}',
                'display_name': email.split('@')[0] if email else f'User {user_id[:8]}',
                'email': email,
                'bio': '',
                'avatar_url': None,
                'is_public': False,
                'created_at': datetime.now().isoformat()
            }
            
        return jsonify({
            'success': True,
            'profile': profile
        })
        
    except Exception as e:
        print(f"Error getting profile: {e}")
        return jsonify({'error': 'Failed to get profile'}), 500

@profile_bp.route('/api/profile', methods=['PUT'])
@require_auth
def update_profile():
    """사용자 프로필 업데이트"""
    try:
        user_id = AuthManager.get_current_user_id()
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # 업데이트 가능한 필드들
        allowed_fields = ['username', 'display_name', 'bio', 'is_public', 'email']
        update_data = {}
        
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]
        
        # 사용자명 중복 체크
        if 'username' in update_data:
            username = update_data['username'].lower().strip()
            
            # 현재 사용자의 기존 사용자명과 다른 경우에만 중복 체크
            current_profile = AuthManager.get_user_profile(user_id)
            if current_profile and current_profile.get('username') != username:
                from supabase import create_client
                SUPABASE_URL = os.getenv('SUPABASE_URL')
                SUPABASE_KEY = os.getenv('SUPABASE_API_KEY')
                supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
                
                # 사용자명 중복 체크
                existing = supabase.table('user_profiles').select('id').eq('username', username).execute()
                if existing.data:
                    return jsonify({'error': 'Username already taken'}), 400
                
                # 예약된 사용자명 체크
                reserved_usernames = [
                    'admin', 'api', 'www', 'dashboard', 'login', 'signup', 'logout',
                    'settings', 'profile', 'help', 'support', 'about', 'contact',
                    'privacy', 'terms', 'legal', 'pricing', 'billing', 'payment',
                    'app', 'mobile', 'desktop', 'web', 'ios', 'android',
                    'notionflow', 'notion', 'flow', 'calendar', 'schedule',
                    'root', 'system', 'config', 'static', 'assets', 'public'
                ]
                
                if username in reserved_usernames:
                    return jsonify({'error': 'Username is reserved'}), 400
                
                # 사용자명 형식 체크 (3-20자, 영숫자와 언더스코어만)
                import re
                if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
                    return jsonify({'error': 'Invalid username format. Use 3-20 characters (letters, numbers, underscore only)'}), 400
                
                update_data['username'] = username
        
        # 데이터베이스 업데이트
        if update_data:
            from supabase import create_client
            SUPABASE_URL = os.getenv('SUPABASE_URL')
            SUPABASE_KEY = os.getenv('SUPABASE_API_KEY')
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            
            update_data['updated_at'] = datetime.now().isoformat()
            
            result = supabase.table('user_profiles').update(update_data).eq('user_id', user_id).execute()
            
            if result.data:
                return jsonify({
                    'success': True,
                    'message': 'Profile updated successfully',
                    'profile': result.data[0]
                })
            else:
                return jsonify({'error': 'Failed to update profile'}), 500
        else:
            return jsonify({'error': 'No valid fields to update'}), 400
            
    except Exception as e:
        print(f"Error updating profile: {e}")
        return jsonify({'error': 'Failed to update profile'}), 500

@profile_bp.route('/api/profile/avatar', methods=['POST'])
@require_auth
def upload_avatar():
    """아바타 이미지 업로드"""
    try:
        user_id = AuthManager.get_current_user_id()
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        if 'avatar' not in request.files:
            return jsonify({'error': 'No avatar file provided'}), 400
        
        file = request.files['avatar']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Use PNG, JPG, JPEG, GIF, or WebP'}), 400
        
        # 파일 크기 체크
        file.seek(0, 2)  # 파일 끝으로 이동
        file_size = file.tell()
        file.seek(0)  # 다시 시작으로 이동
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({'error': 'File too large. Maximum size is 5MB'}), 400
        
        # 파일명 생성
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        filename = f"avatar_{user_id}_{uuid.uuid4().hex[:8]}.{file_extension}"
        
        # 아바타 디렉토리 생성
        avatar_dir = os.path.join('static', 'avatars')
        os.makedirs(avatar_dir, exist_ok=True)
        
        # 파일 저장
        file_path = os.path.join(avatar_dir, filename)
        file.save(file_path)
        
        # 데이터베이스에 아바타 URL 업데이트
        avatar_url = f"/static/avatars/{filename}"
        
        from supabase import create_client
        SUPABASE_URL = os.getenv('SUPABASE_URL')
        SUPABASE_KEY = os.getenv('SUPABASE_API_KEY')
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        result = supabase.table('user_profiles').update({
            'avatar_url': avatar_url,
            'updated_at': datetime.now().isoformat()
        }).eq('user_id', user_id).execute()
        
        if result.data:
            return jsonify({
                'success': True,
                'message': 'Avatar uploaded successfully',
                'avatar_url': avatar_url
            })
        else:
            # 파일 삭제 (DB 업데이트 실패시)
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({'error': 'Failed to update avatar in database'}), 500
            
    except Exception as e:
        print(f"Error uploading avatar: {e}")
        return jsonify({'error': 'Failed to upload avatar'}), 500

@profile_bp.route('/api/profile/email', methods=['PUT'])
@require_auth
def update_email():
    """사용자 이메일 업데이트"""
    try:
        user_id = AuthManager.get_current_user_id()
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        data = request.get_json()
        if not data or 'email' not in data:
            return jsonify({'error': 'Email is required'}), 400
        
        email = data['email'].strip()
        
        # 이메일 형식 검증
        import re
        email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_pattern, email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # 데이터베이스 업데이트
        from supabase import create_client
        SUPABASE_URL = os.getenv('SUPABASE_URL')
        SUPABASE_KEY = os.getenv('SUPABASE_API_KEY')
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # user_profiles 테이블에 이메일 업데이트
        result = supabase.table('user_profiles').update({
            'email': email,
            'updated_at': datetime.now().isoformat()
        }).eq('user_id', user_id).execute()
        
        if result.data:
            return jsonify({
                'success': True,
                'message': 'Email updated successfully',
                'email': email
            })
        else:
            # 프로필이 없으면 생성
            user_info = session.get('user_info', {})
            profile_data = {
                'user_id': user_id,
                'username': f'user_{user_id[:8]}',
                'display_name': email.split('@')[0],
                'email': email,
                'bio': '',
                'is_public': False,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            result = supabase.table('user_profiles').insert(profile_data).execute()
            
            if result.data:
                return jsonify({
                    'success': True,
                    'message': 'Email saved successfully',
                    'email': email
                })
            else:
                return jsonify({'error': 'Failed to save email'}), 500
            
    except Exception as e:
        print(f"Error updating email: {e}")
        return jsonify({'error': 'Failed to update email'}), 500

@profile_bp.route('/api/profile/username/check', methods=['POST'])
@require_auth
def check_username():
    """사용자명 사용 가능 여부 체크"""
    try:
        data = request.get_json()
        if not data or 'username' not in data:
            return jsonify({'error': 'Username is required'}), 400
        
        username = data['username'].lower().strip()
        
        # 현재 사용자 ID
        user_id = AuthManager.get_current_user_id()
        
        # 현재 사용자의 기존 사용자명인지 체크
        current_profile = AuthManager.get_user_profile(user_id)
        if current_profile and current_profile.get('username') == username:
            return jsonify({
                'available': True,
                'message': 'This is your current username'
            })
        
        # 형식 체크
        import re
        if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
            return jsonify({
                'available': False,
                'message': 'Username must be 3-20 characters (letters, numbers, underscore only)'
            })
        
        # 예약된 사용자명 체크
        reserved_usernames = [
            'admin', 'api', 'www', 'dashboard', 'login', 'signup', 'logout',
            'settings', 'profile', 'help', 'support', 'about', 'contact',
            'privacy', 'terms', 'legal', 'pricing', 'billing', 'payment',
            'app', 'mobile', 'desktop', 'web', 'ios', 'android',
            'notionflow', 'notion', 'flow', 'calendar', 'schedule',
            'root', 'system', 'config', 'static', 'assets', 'public'
        ]
        
        if username in reserved_usernames:
            return jsonify({
                'available': False,
                'message': 'This username is reserved'
            })
        
        # 중복 체크
        from supabase import create_client
        SUPABASE_URL = os.getenv('SUPABASE_URL')
        SUPABASE_KEY = os.getenv('SUPABASE_API_KEY')
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        result = supabase.table('user_profiles').select('id').eq('username', username).execute()
        
        if result.data:
            return jsonify({
                'available': False,
                'message': 'Username is already taken'
            })
        else:
            return jsonify({
                'available': True,
                'message': 'Username is available'
            })
            
    except Exception as e:
        print(f"Error checking username: {e}")
        return jsonify({'error': 'Failed to check username'}), 500

@profile_bp.route('/api/profile/username/suggestions', methods=['POST'])
@require_auth
def get_username_suggestions():
    """사용자명 추천"""
    try:
        data = request.get_json()
        base_name = data.get('base_name', '')
        
        if not base_name:
            # 현재 사용자 이메일에서 추천
            user_info = session.get('user_info', {})
            email = user_info.get('email', '')
            if email:
                base_name = email.split('@')[0]
            else:
                base_name = 'user'
        
        # 베이스 이름 정리
        import re
        base_name = re.sub(r'[^a-zA-Z0-9]', '_', base_name.lower())
        base_name = base_name.strip('_')
        
        if len(base_name) < 3:
            base_name = base_name + '_user'
        elif len(base_name) > 15:
            base_name = base_name[:15]
        
        # 추천 사용자명 생성
        suggestions = []
        from supabase import create_client
        SUPABASE_URL = os.getenv('SUPABASE_URL')
        SUPABASE_KEY = os.getenv('SUPABASE_API_KEY')
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # 베이스 이름으로 시작
        for i in range(5):
            if i == 0:
                suggestion = base_name
            else:
                suggestion = f"{base_name}_{i}"
            
            # 중복 체크
            result = supabase.table('user_profiles').select('id').eq('username', suggestion).execute()
            if not result.data:
                suggestions.append(suggestion)
            
            if len(suggestions) >= 5:
                break
        
        # 추가 변형 (부족한 경우)
        if len(suggestions) < 5:
            import random
            for suffix in ['_dev', '_pro', '_code', '_tech', '_flow']:
                suggestion = base_name + suffix
                if len(suggestion) <= 20:
                    result = supabase.table('user_profiles').select('id').eq('username', suggestion).execute()
                    if not result.data:
                        suggestions.append(suggestion)
                    
                    if len(suggestions) >= 5:
                        break
        
        return jsonify({
            'success': True,
            'suggestions': suggestions[:5]
        })
        
    except Exception as e:
        print(f"Error getting username suggestions: {e}")
        return jsonify({'error': 'Failed to get suggestions'}), 500

# Profile page route
@profile_bp.route('/profile')
@require_auth
def profile_page():
    """프로필 관리 페이지"""
    try:
        user_id = AuthManager.get_current_user_id()
        profile = AuthManager.get_user_profile(user_id)
        
        return render_template('profile.html', 
                             current_page='profile',
                             profile=profile)
    except Exception as e:
        print(f"Error loading profile page: {e}")
        return render_template('profile.html', 
                             current_page='profile',
                             profile=None)