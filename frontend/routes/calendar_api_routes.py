"""
🗓️ Calendar API Routes
캘린더 생성, 수정, 삭제 및 미디어 파일 관리 API
"""

import os
import sys
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, session, send_file
from werkzeug.utils import secure_filename

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../utils'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../utils'))

calendar_api_bp = Blueprint('calendar_api', __name__, url_prefix='/api')

def get_current_user_id():
    """Get current authenticated user ID from session"""
    return session.get('user_id')

def require_auth():
    """Decorator to require authentication"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    return None

# 허용된 파일 확장자
ALLOWED_EXTENSIONS = {
    'audio': {'mp3', 'wav', 'm4a', 'aac'},
    'video': {'mp4', 'mov', 'avi', 'wmv', 'webm'}
}

def allowed_file(filename):
    """파일 확장자가 허용되는지 확인"""
    if '.' not in filename:
        return False, None
    
    ext = filename.rsplit('.', 1)[1].lower()
    
    if ext in ALLOWED_EXTENSIONS['audio']:
        return True, 'audio'
    elif ext in ALLOWED_EXTENSIONS['video']:
        return True, 'video'
    else:
        return False, None

def get_upload_folder():
    """업로드 폴더 경로 반환"""
    upload_folder = os.path.join(os.path.dirname(__file__), '../../uploads/media')
    os.makedirs(upload_folder, exist_ok=True)
    return upload_folder

@calendar_api_bp.route('/calendar/create', methods=['POST', 'OPTIONS'])
def create_calendar():
    """새 캘린더 생성 (파일 업로드 지원)"""
    # OPTIONS 요청 처리 (CORS)
    if request.method == 'OPTIONS':
        return '', 200
    
    # Content-Type 디버깅
    print(f"Content-Type: {request.content_type}")
    print(f"Request Headers: {dict(request.headers)}")
    
    # JSON 요청만 처리 (간단한 캘린더 생성)
    if not request.is_json:
        return jsonify({
            'success': False,
            'error': 'Content-Type must be application/json'
        }), 415
    
    data = request.get_json()
    name = data.get('name')
    platform = data.get('platform', 'custom')
    color = data.get('color', '#3B82F6')
    is_shared = data.get('is_shared', False)
    media_filename = data.get('media_filename')  # 파일명만 받음
    
    # 파일 업로드는 별도 API로 분리 예정
    media_file = None
    media_file_path = None
    media_file_type = None
    
    # 임시로 인증 체크 비활성화 (테스트용)
    # auth_error = require_auth()
    # if auth_error:
    #     return auth_error
    
    user_id = get_current_user_id() or str(uuid.uuid4())  # 임시 사용자 ID 생성
    
    try:
        from supabase import create_client
        
        # Supabase 연결
        SUPABASE_URL = os.environ.get('SUPABASE_URL')
        SUPABASE_KEY = os.environ.get('SUPABASE_API_KEY')
        
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise Exception("Supabase credentials not configured")
        
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # 이미 위에서 폼 데이터를 추출했으므로 중복 제거
        if not name:
            return jsonify({
                'success': False,
                'error': 'Calendar name is required'
            }), 400
        
        # 파일 업로드는 나중에 별도 API로 구현
        
        # 캘린더 데이터 생성 (파일 필드 제거)
        calendar_data = {
            'user_id': user_id,
            'name': name,
            'platform': platform,
            'color': color,
            'is_shared': is_shared,
            'media_filename': media_filename,  # 파일명만 저장
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Supabase에 저장
        result = supabase.table('calendars').insert(calendar_data).execute()
        
        if result.data:
            return jsonify({
                'success': True,
                'calendar': result.data[0],
                'message': 'Calendar created successfully'
            })
        else:
            # 파일이 저장되었다면 삭제
            if media_file_path:
                try:
                    os.remove(os.path.join(upload_folder, media_file_path))
                except:
                    pass
            
            return jsonify({
                'success': False,
                'error': 'Failed to create calendar'
            }), 500
            
    except Exception as e:
        print(f"Error creating calendar: {e}")
        
        # 에러 발생 시 업로드된 파일 삭제
        if 'media_file_path' in locals() and media_file_path:
            try:
                os.remove(os.path.join(get_upload_folder(), media_file_path))
            except:
                pass
        
        return jsonify({
            'success': False,
            'error': 'Failed to create calendar'
        }), 500

@calendar_api_bp.route('/calendars/<calendar_id>/media-filename', methods=['PUT'])
def update_media_filename(calendar_id):
    """미디어 파일명 업데이트"""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    user_id = get_current_user_id()
    
    try:
        from supabase import create_client
        
        # Supabase 연결
        SUPABASE_URL = os.environ.get('SUPABASE_URL')
        SUPABASE_KEY = os.environ.get('SUPABASE_API_KEY')
        
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise Exception("Supabase credentials not configured")
        
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        data = request.get_json()
        new_filename = data.get('media_filename', '').strip()
        
        if not new_filename:
            return jsonify({
                'success': False,
                'error': 'Filename cannot be empty'
            }), 400
        
        # 캘린더 소유권 확인
        calendar_result = supabase.table('calendars').select('*').eq('id', calendar_id).eq('user_id', user_id).execute()
        
        if not calendar_result.data:
            return jsonify({
                'success': False,
                'error': 'Calendar not found or access denied'
            }), 404
        
        # 파일명 업데이트
        update_result = supabase.table('calendars').update({
            'media_filename': new_filename,
            'updated_at': datetime.now().isoformat()
        }).eq('id', calendar_id).eq('user_id', user_id).execute()
        
        if update_result.data:
            return jsonify({
                'success': True,
                'message': 'Media filename updated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to update filename'
            }), 500
            
    except Exception as e:
        print(f"Error updating media filename: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to update filename'
        }), 500

@calendar_api_bp.route('/calendars/<calendar_id>/media/<filename>')
def serve_media_file(calendar_id, filename):
    """미디어 파일 제공"""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    user_id = get_current_user_id()
    
    try:
        from supabase import create_client
        
        # Supabase 연결
        SUPABASE_URL = os.environ.get('SUPABASE_URL')
        SUPABASE_KEY = os.environ.get('SUPABASE_API_KEY')
        
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise Exception("Supabase credentials not configured")
        
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # 캘린더 및 미디어 파일 정보 확인
        calendar_result = supabase.table('calendars').select('*').eq('id', calendar_id).eq('user_id', user_id).execute()
        
        if not calendar_result.data:
            return jsonify({
                'success': False,
                'error': 'Calendar not found or access denied'
            }), 404
        
        calendar = calendar_result.data[0]
        
        if not calendar.get('media_file_path'):
            return jsonify({
                'success': False,
                'error': 'No media file associated with this calendar'
            }), 404
        
        # 파일 경로 확인
        upload_folder = get_upload_folder()
        file_path = os.path.join(upload_folder, calendar['media_file_path'])
        
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': 'Media file not found'
            }), 404
        
        # 파일 타입에 따른 MIME 타입 설정
        file_extension = calendar['media_file_path'].split('.')[-1].lower()
        mime_types = {
            'mp3': 'audio/mpeg',
            'wav': 'audio/wav',
            'm4a': 'audio/mp4',
            'aac': 'audio/aac',
            'mp4': 'video/mp4',
            'mov': 'video/quicktime',
            'avi': 'video/x-msvideo',
            'wmv': 'video/x-ms-wmv',
            'webm': 'video/webm'
        }
        
        mimetype = mime_types.get(file_extension, 'application/octet-stream')
        
        # 파일 전송
        return send_file(
            file_path,
            mimetype=mimetype,
            as_attachment=False,
            download_name=calendar.get('media_filename', calendar['media_file_path'])
        )
        
    except Exception as e:
        print(f"Error serving media file: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to serve media file'
        }), 500

@calendar_api_bp.route('/calendars/<calendar_id>')
def get_calendar(calendar_id):
    """캘린더 정보 조회"""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    user_id = get_current_user_id()
    
    try:
        from supabase import create_client
        
        # Supabase 연결
        SUPABASE_URL = os.environ.get('SUPABASE_URL')
        SUPABASE_KEY = os.environ.get('SUPABASE_API_KEY')
        
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise Exception("Supabase credentials not configured")
        
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # 캘린더 조회
        calendar_result = supabase.table('calendars').select('*').eq('id', calendar_id).eq('user_id', user_id).execute()
        
        if not calendar_result.data:
            return jsonify({
                'success': False,
                'error': 'Calendar not found or access denied'
            }), 404
        
        return jsonify({
            'success': True,
            'calendar': calendar_result.data[0]
        })
        
    except Exception as e:
        print(f"Error getting calendar: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get calendar'
        }), 500

@calendar_api_bp.route('/calendars/<calendar_id>', methods=['DELETE'])
def delete_calendar(calendar_id):
    """캘린더 삭제 (미디어 파일 포함)"""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    user_id = get_current_user_id()
    
    try:
        from supabase import create_client
        
        # Supabase 연결
        SUPABASE_URL = os.environ.get('SUPABASE_URL')
        SUPABASE_KEY = os.environ.get('SUPABASE_API_KEY')
        
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise Exception("Supabase credentials not configured")
        
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # 캘린더 정보 조회 (미디어 파일 경로 확인용)
        calendar_result = supabase.table('calendars').select('*').eq('id', calendar_id).eq('user_id', user_id).execute()
        
        if not calendar_result.data:
            return jsonify({
                'success': False,
                'error': 'Calendar not found or access denied'
            }), 404
        
        calendar = calendar_result.data[0]
        
        # 미디어 파일 삭제
        if calendar.get('media_file_path'):
            try:
                upload_folder = get_upload_folder()
                file_path = os.path.join(upload_folder, calendar['media_file_path'])
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Warning: Failed to delete media file: {e}")
        
        # 캘린더 삭제
        delete_result = supabase.table('calendars').delete().eq('id', calendar_id).eq('user_id', user_id).execute()
        
        return jsonify({
            'success': True,
            'message': 'Calendar deleted successfully'
        })
        
    except Exception as e:
        print(f"Error deleting calendar: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to delete calendar'
        }), 500

# Error handlers
@calendar_api_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Calendar API endpoint not found'}), 404

@calendar_api_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500