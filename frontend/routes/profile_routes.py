"""
🎯 프로필 관리 라우트
사용자 프로필 CRUD API 엔드포인트
"""

# OS 모듈을 가장 먼저 import (Railway 호환성)
import os
import sys

# 환경 변수를 즉시 로드
from dotenv import load_dotenv
load_dotenv()

# 나머지 imports
from flask import Blueprint, request, jsonify, session, render_template
from utils.auth_manager import AuthManager, require_auth
from datetime import datetime
import uuid
import base64
import traceback
import re
import random
from werkzeug.utils import secure_filename
from supabase import create_client

profile_bp = Blueprint('profile', __name__)

# 허용된 파일 확장자
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Supabase 설정 (전역) - Railway 호환성 체크
# os 모듈이 정상적으로 로드되었는지 확인
try:
    SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
    SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY') or os.environ.get('SUPABASE_API_KEY', '')
    SUPABASE_API_KEY = os.environ.get('SUPABASE_API_KEY') or os.environ.get('SUPABASE_ANON_KEY', '')
    SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('SUPABASE_SERVICE_KEY', '')
except Exception as e:
    print(f"⚠️ Error loading environment variables: {e}")
    SUPABASE_URL = ''
    SUPABASE_ANON_KEY = ''
    SUPABASE_API_KEY = ''
    SUPABASE_SERVICE_KEY = ''

# 디버그 정보
print(f"🔧 SUPABASE_URL: {SUPABASE_URL[:30] + '...' if SUPABASE_URL else 'None'}")
print(f"🔧 SUPABASE_ANON_KEY: {'✅ Set' if SUPABASE_ANON_KEY else '❌ Missing'}")
print(f"🔧 SUPABASE_API_KEY: {'✅ Set' if SUPABASE_API_KEY else '❌ Missing'}")
print(f"🔧 SUPABASE_SERVICE_KEY: {'✅ Set' if SUPABASE_SERVICE_KEY else '❌ Missing'}")

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
                supabase = create_client(SUPABASE_URL, SUPABASE_API_KEY)
                
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
                if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
                    return jsonify({'error': 'Invalid username format. Use 3-20 characters (letters, numbers, underscore only)'}), 400
                
                update_data['username'] = username
        
        # 데이터베이스 업데이트
        if update_data:
            supabase = create_client(SUPABASE_URL, SUPABASE_API_KEY)
            
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
    import traceback as tb
    import uuid as uuid_gen
    from datetime import datetime as dt
    
    print("🔍 Avatar upload started")
    
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
        filename = f"avatar_{user_id}_{uuid_gen.uuid4().hex[:8]}.{file_extension}"
        
        # Supabase Storage에 업로드
        if not SUPABASE_URL or not SUPABASE_ANON_KEY:
            return jsonify({'error': 'Supabase configuration missing'}), 500
        
        try:
            supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
            
            # 파일을 바이트로 읽기
            file_data = file.read()
            file.seek(0)  # 파일 포인터 리셋
            
            # Supabase Storage에 업로드
            result = supabase.storage.from_('avatars').upload(filename, file_data, {
                'content-type': f'image/{file_extension}',
                'cache-control': '3600'
            })
            
            if result.error:
                print(f"Storage upload error: {result.error}")
                return jsonify({'error': 'Failed to upload to storage'}), 500
            
            # 공개 URL 생성
            avatar_url = supabase.storage.from_('avatars').get_public_url(filename)
            
            # 데이터베이스에 아바타 URL 업데이트
            db_result = supabase.table('user_profiles').update({
                'avatar_url': avatar_url,
                'updated_at': dt.now().isoformat()
            }).eq('user_id', user_id).execute()
            
            if db_result.data:
                return jsonify({
                    'success': True,
                    'message': 'Avatar uploaded successfully',
                    'avatar_url': avatar_url
                })
            else:
                return jsonify({'error': 'Failed to update avatar in database'}), 500
                
        except Exception as storage_error:
            print(f"Supabase storage error: {storage_error}")
            return jsonify({'error': 'Storage service unavailable'}), 500
            
    except Exception as e:
        print(f"Error uploading avatar: {e}")
        print(f"Traceback: {tb.format_exc()}")
        return jsonify({'error': f'Failed to upload avatar: {str(e)}'}), 500

@profile_bp.route('/api/profile/initial-setup', methods=['POST'])
@require_auth
def initial_setup():
    """초기 설정 - 이름과 생년월일 저장"""
    try:
        user_id = AuthManager.get_current_user_id()
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # 이미 설정이 완료된 사용자인지 체크
        existing_profile = AuthManager.get_user_profile(user_id)
        if existing_profile and existing_profile.get('display_name') and (existing_profile.get('birthdate') or 'birthdate:' in str(existing_profile.get('bio', ''))):
            return jsonify({
                'success': True,
                'message': 'Initial setup already completed',
                'profile': existing_profile,
                'already_completed': True
            })
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # 필수 필드 체크
        display_name = data.get('display_name', '').strip()
        birthdate = data.get('birthdate', '').strip()
        
        if not display_name or not birthdate:
            return jsonify({'error': 'Name and birthdate are required'}), 400
        
        # 선택 필드
        email = data.get('email', '').strip() if data.get('email') else None
        
        # 이메일 형식 검증 (제공된 경우)
        if email:
            email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
            if not re.match(email_pattern, email):
                return jsonify({'error': 'Invalid email format'}), 400
        
        # 데이터베이스 연결 - 서비스 키 사용으로 RLS 우회
        
        # 반드시 서비스 키를 사용 (RLS 우회를 위해)
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            print("Missing Supabase service key - required for initial setup")
            return jsonify({'error': 'Database configuration error - service key required'}), 500
            
        # 서비스 키로 새로운 클라이언트 생성
        supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        print(f"Supabase admin client created with service key")
        
        # 프로필 업데이트 또는 생성 (먼저 birthdate 포함하여 시도)
        profile_data = {
            'display_name': display_name,
            'birthdate': birthdate,
            'updated_at': datetime.now().isoformat()
        }
        print(f"Profile data: {profile_data}")
        
        if email:
            profile_data['email'] = email
        
        # AuthManager를 통해 프로필 업데이트 (RLS 정책 우회)
        print(f"Using AuthManager to update profile for user_id: {user_id}")
        
        # 기존 프로필 확인
        existing_profile = AuthManager.get_user_profile(user_id)
        print(f"Existing profile: {existing_profile}")
        
        # 프로필이 없으면 먼저 생성 - 서비스 키로 직접 생성
        if not existing_profile:
            print("No existing profile, creating new one directly with admin privileges")
            try:
                # 사용자 먼저 생성 (필요한 경우)
                try:
                    user_data = {
                        'id': user_id,
                        'email': email or '',
                        'name': display_name,
                        'created_at': datetime.now().isoformat()
                    }
                    supabase_admin.table('users').insert(user_data).execute()
                    print(f"Created user record for {user_id}")
                except Exception as user_error:
                    print(f"User creation skipped (may already exist): {user_error}")
                
                # 프로필 생성 - username을 display_name 기반으로 생성
                # display_name에서 영문자, 숫자만 추출하여 username 생성
                base_username = re.sub(r'[^a-zA-Z0-9]', '', display_name.lower())
                if not base_username:
                    base_username = f"user{user_id[:8]}"
                
                # username 중복 체크 및 고유 username 생성
                username = base_username
                counter = 1
                while True:
                    try:
                        existing = supabase_admin.table('user_profiles').select('id').eq('username', username).execute()
                        if not existing.data:
                            break
                        username = f"{base_username}{counter}"
                        counter += 1
                    except:
                        break
                
                profile_data_create = {
                    'user_id': user_id,
                    'username': username,
                    'display_name': display_name,
                    'email': email,
                    'is_public': False,
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                
                create_result = supabase_admin.table('user_profiles').insert(profile_data_create).execute()
                print(f"Created profile result: {create_result}")
                
            except Exception as create_error:
                print(f"Profile creation error: {create_error}")
                # 계속 진행하여 업데이트 시도
        
        # 직접 데이터베이스 업데이트 시도 (서비스 키 사용)
        try:
            update_data = {
                'display_name': display_name,
                'updated_at': datetime.now().isoformat()
            }
            
            # username도 display_name 기반으로 업데이트 (기존 프로필이 있는 경우)
            if existing_profile and (not existing_profile.get('username') or existing_profile.get('username').startswith('user_')):
                base_username = re.sub(r'[^a-zA-Z0-9]', '', display_name.lower())
                if not base_username:
                    base_username = f"user{user_id[:8]}"
                
                # username 중복 체크
                username = base_username
                counter = 1
                while True:
                    try:
                        existing = supabase_admin.table('user_profiles').select('id').eq('username', username).neq('user_id', user_id).execute()
                        if not existing.data:
                            break
                        username = f"{base_username}{counter}"
                        counter += 1
                    except:
                        break
                
                update_data['username'] = username
                print(f"Updating username to: {username}")
            
            if email:
                update_data['email'] = email
            
            # birthdate 컬럼 추가 시도 (있으면 업데이트, 없으면 무시) - 서비스 키로 실행
            try:
                update_data['birthdate'] = birthdate
                print(f"Updating profile with birthdate: {update_data}")
                result = supabase_admin.table('user_profiles').update(update_data).eq('user_id', user_id).execute()
                print(f"Update with birthdate result: {result}")
            except Exception as birthdate_error:
                print(f"Birthdate column not found, updating without it: {birthdate_error}")
                # birthdate 제외하고 다시 시도
                update_data_no_birthdate = update_data.copy()
                if 'birthdate' in update_data_no_birthdate:
                    del update_data_no_birthdate['birthdate']
                
                result = supabase_admin.table('user_profiles').update(update_data_no_birthdate).eq('user_id', user_id).execute()
                print(f"Update without birthdate result: {result}")
                
                # birthdate를 bio에 메타데이터로 저장
                try:
                    bio_with_birthdate = f"birthdate:{birthdate}"
                    supabase_admin.table('user_profiles').update({'bio': bio_with_birthdate}).eq('user_id', user_id).execute()
                    print(f"Stored birthdate in bio field: {bio_with_birthdate}")
                except Exception as bio_error:
                    print(f"Failed to store birthdate in bio: {bio_error}")
            
        except Exception as db_error:
            print(f"Database error: {db_error}")
            return jsonify({'error': f'Database update failed: {str(db_error)}'}), 500
        
        if result.data:
            return jsonify({
                'success': True,
                'message': 'Initial setup completed successfully',
                'profile': result.data[0]
            })
        else:
            return jsonify({'error': 'Failed to save initial setup'}), 500
            
    except Exception as e:
        print(f"Error in initial setup: {e}")
        print(f"Error type: {type(e)}")
        print(f"Error details: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Failed to complete initial setup: {str(e)}'}), 500

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
        email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_pattern, email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # 데이터베이스 업데이트
        supabase = create_client(SUPABASE_URL, SUPABASE_API_KEY)
        
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
        supabase = create_client(SUPABASE_URL, SUPABASE_API_KEY)
        
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
        base_name = re.sub(r'[^a-zA-Z0-9]', '_', base_name.lower())
        base_name = base_name.strip('_')
        
        if len(base_name) < 3:
            base_name = base_name + '_user'
        elif len(base_name) > 15:
            base_name = base_name[:15]
        
        # 추천 사용자명 생성
        suggestions = []
        supabase = create_client(SUPABASE_URL, SUPABASE_API_KEY)
        
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