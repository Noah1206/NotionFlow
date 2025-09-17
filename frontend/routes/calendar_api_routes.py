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

# Dashboard data manager import
try:
    from utils.dashboard_data import DashboardDataManager
    dashboard_data = DashboardDataManager()
except ImportError:
    dashboard_data = None

# Auth utilities import
try:
    from utils.auth_utils import require_auth, get_current_user_id
except ImportError:
    def require_auth():
        return None
    def get_current_user_id():
        return session.get('user_id')

# 임시 테스트 엔드포인트
@calendar_api_bp.route('/test', methods=['GET'])
def test_endpoint():
    return jsonify({
        'success': True,
        'message': 'API is working',
        'timestamp': datetime.now().isoformat()
    })

@calendar_api_bp.route('/calendar/notion-sync', methods=['POST'])
def manual_notion_sync():
    """Manual Notion sync endpoint for testing"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            user_id = "87875eda6797f839f8c70aa90efb1352"  # Use your actual user ID
        
        data = request.get_json() or {}
        calendar_id = data.get('calendar_id', '3e7f438e-b233-43f7-9329-1656acd82682')  # Your calendar ID
        
        import sys
        sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
        from services.notion_sync import notion_sync
        
        print(f"🔄 [MANUAL SYNC] Starting manual Notion sync for user {user_id}, calendar {calendar_id}")
        result = notion_sync.sync_to_calendar(user_id, calendar_id)
        
        return jsonify(result)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@calendar_api_bp.route('/calendar/events', methods=['GET'])
def get_calendar_events():
    """Get calendar events for selected calendars"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            # Use the actual owner ID from the existing calendar
            user_id = "e390559f-c328-4786-ac5d-c74b5409451b"
        
        # Get calendar IDs from query params
        calendar_ids = request.args.getlist('calendar_ids[]')
        days_ahead = int(request.args.get('days_ahead', 30))
        
        # 🔄 Notion 자동 동기화 (첫 번째 캘린더에 대해서만)
        print(f"🔍 [NOTION SYNC] Checking sync: calendar_ids={calendar_ids}, user_id={user_id}")
        if calendar_ids and len(calendar_ids) > 0:
            try:
                import sys
                sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
                from services.notion_sync import notion_sync
                
                print(f"🔄 [NOTION SYNC] Starting auto-sync for calendar {calendar_ids[0]}")
                result = notion_sync.sync_to_calendar(user_id, calendar_ids[0])
                print(f"📋 [NOTION SYNC] Sync result: {result}")
                
                if result['success']:
                    print(f"✅ [NOTION SYNC] Successfully synced {result['synced_events']} events from {result.get('databases_processed', 0)} databases")
                else:
                    print(f"❌ [NOTION SYNC] Failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"⚠️ [NOTION SYNC] Auto-sync error: {e}")
                import traceback
                traceback.print_exc()
        
        if not dashboard_data:
            return jsonify({'error': 'Dashboard data manager not available'}), 500
        
        # Get events for selected calendars (now includes Notion-synced events)
        events = dashboard_data.get_user_calendar_events(
            user_id=user_id,
            days_ahead=days_ahead,
            calendar_ids=calendar_ids if calendar_ids else None
        )
        
        return jsonify({
            'success': True,
            'events': events,
            'count': len(events)
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Failed to get events: {str(e)}'
        }), 500

@calendar_api_bp.route('/user/calendars', methods=['GET'])
def get_user_calendars():
    """Get user's calendar list"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            # Use the actual owner ID from the existing calendar
            user_id = "e390559f-c328-4786-ac5d-c74b5409451b"
        
        print(f"🔍 API: user_id = {user_id}")
        print(f"🔍 API: dashboard_data available = {dashboard_data is not None}")
        
        if not dashboard_data:
            return jsonify({'error': 'Dashboard data manager not available'}), 500
        
        # Get user calendars
        print(f"🔍 API: Calling dashboard_data.get_user_calendars({user_id})")
        calendars_data = dashboard_data.get_user_calendars(user_id)
        print(f"🔍 API: calendars_data = {calendars_data}")
        
        return jsonify({
            'success': True,
            'personal_calendars': calendars_data.get('personal_calendars', []),
            'shared_calendars': calendars_data.get('shared_calendars', []),
            'summary': calendars_data.get('summary', {})
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Failed to get calendars: {str(e)}'
        }), 500

# 간단한 캘린더 생성 엔드포인트 (파일 없이)
@calendar_api_bp.route('/calendar/simple-create', methods=['POST'])
def simple_create_calendar():
    """간단한 캘린더 생성 (JSON만, 파일 없음)"""
    try:
        # JSON 데이터만 받음
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'JSON data required'
            }), 400
        
        name = data.get('name', '새 캘린더')
        platform = data.get('platform', 'custom')
        color = data.get('color', '#3B82F6')
        is_shared = data.get('is_shared', False)
        
        # 임시 사용자 ID
        user_id = str(uuid.uuid4())
        
        # Supabase 없이 성공 응답만 반환
        return jsonify({
            'success': True,
            'message': 'Calendar created successfully',
            'calendar': {
                'id': str(uuid.uuid4()),
                'name': name,
                'platform': platform,
                'color': color,
                'is_shared': is_shared,
                'user_id': user_id
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

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
    
    # Content-Type 디버깅 (안전한 방식)
    try:
        print(f"🔍 create_calendar() called at {datetime.now()}")
        print(f"Content-Type: {request.content_type}")
        import sys
        sys.stdout.flush()
    except (BrokenPipeError, IOError):
        # stdout 문제 시 무시하고 계속 진행
        pass
    
    # multipart/form-data와 JSON 모두 지원
    if request.is_json:
        # JSON 요청 (파일 없음)
        data = request.get_json()
        name = data.get('name')
        platform = data.get('platform', 'custom')
        color = data.get('color', '#3B82F6')
        is_shared = data.get('is_shared', False)
        media_filename = data.get('media_filename')
        youtube_data = data.get('youtube_data')
        media_file = None
        print(f"[DEBUG] JSON request - youtube_data: {youtube_data}")
    else:
        # Form 요청 (파일 포함 가능)
        name = request.form.get('name')
        platform = request.form.get('platform', 'custom')
        color = request.form.get('color', '#3B82F6')
        is_shared = request.form.get('is_shared', 'false').lower() == 'true'
        media_filename = request.form.get('media_filename')
        youtube_data_str = request.form.get('youtube_data')
        youtube_data = None
        if youtube_data_str:
            try:
                import json
                youtube_data = json.loads(youtube_data_str)
                print(f"[DEBUG] Form request - parsed youtube_data: {youtube_data}")
            except Exception as parse_error:
                print(f"[ERROR] Failed to parse youtube_data: {parse_error}")
                youtube_data = None
        media_file = request.files.get('media_file')
        print(f"[DEBUG] Form request - youtube_data_str: {youtube_data_str}")
        print(f"[DEBUG] Form request - final youtube_data: {youtube_data}")
    
    # 임시로 인증 체크 비활성화 (테스트용)
    # auth_error = require_auth()
    # if auth_error:
    #     return auth_error
    
    user_id = get_current_user_id() or "e390559f-c328-4786-ac5d-c74b5409451b"  # 실제 캘린더 소유자 ID
    
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
        
        # 파일 처리
        media_file_path = None
        media_file_type = None
        
        if media_file and media_file.filename:
            # 파일 유효성 검사
            is_allowed, file_type = allowed_file(media_file.filename)
            if not is_allowed:
                return jsonify({
                    'success': False,
                    'error': 'Unsupported file type. Please upload MP3, MP4, MOV, AVI, WMV, WAV, or M4A files.'
                }), 400
            
            # 파일 크기 검사 (50MB 제한)
            media_file.seek(0, 2)  # 파일 끝으로 이동
            file_size = media_file.tell()
            media_file.seek(0)  # 파일 시작으로 돌아가기
            
            if file_size > 50 * 1024 * 1024:  # 50MB
                return jsonify({
                    'success': False,
                    'error': 'File size must be less than 50MB'
                }), 400
            
            # 고유한 파일명 생성
            file_extension = media_file.filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
            
            # 파일 저장
            upload_folder = get_upload_folder()
            file_path = os.path.join(upload_folder, unique_filename)
            media_file.save(file_path)
            
            media_file_path = unique_filename
            media_file_type = file_type
            
            # 사용자가 지정한 파일명이 없으면 원본 파일명 사용
            if not media_filename:
                media_filename = media_file.filename
        
        # 캘린더 데이터 생성 (실제 calendars 테이블 구조에 맞춤)
        calendar_data = {
            'id': str(uuid.uuid4()),
            'owner_id': user_id,
            'name': name,
            'type': platform,
            'color': color,
            'description': f'{name} - Created on {datetime.now().strftime("%Y-%m-%d")}',
            'is_active': True,
            'public_access': is_shared,
            'allow_editing': True,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # 미디어 파일 정보가 있다면 description에 추가하고 전용 필드에도 저장
        if media_filename:
            calendar_data['description'] += f' (Media: {media_filename})'
            calendar_data['media_filename'] = media_filename
            calendar_data['media_file_path'] = media_file_path
            calendar_data['media_file_type'] = media_file_type
            print(f"[SUCCESS] Adding media info to calendar: filename={media_filename}, path={media_file_path}, type={media_file_type}")
        
        # YouTube 데이터가 있다면 기존 media 필드에 저장 (기존 DB 스키마 사용)
        if youtube_data:
            try:
                title = youtube_data.get('video_info', {}).get('title', 'YouTube Video')
                channel_name = youtube_data.get('video_info', {}).get('channel_name', 'Unknown')
                embed_url = youtube_data.get('video_info', {}).get('embed_url', '')
                
                calendar_data['description'] += f' (YouTube: {title})'
                # YouTube 데이터를 기존 media 필드에 저장
                calendar_data['media_file_path'] = embed_url  # embed URL을 path로 사용
                calendar_data['media_file_type'] = 'youtube'  # 타입을 youtube로 설정
                calendar_data['media_filename'] = f"{title} - {channel_name}"
                
                # 안전한 로깅
                try:
                    print(f"[SUCCESS] Adding YouTube info to calendar: {title} by {channel_name}")
                    sys.stdout.flush()
                except (BrokenPipeError, IOError):
                    pass
            except Exception as youtube_error:
                try:
                    print(f"[ERROR] YouTube data processing failed: {youtube_error}")
                    sys.stdout.flush()
                except (BrokenPipeError, IOError):
                    pass
        
        # 데이터베이스에 저장하기 전에 전체 데이터 로그 (안전한 방식)
        try:
            print("[DEBUG] Attempting to insert calendar into database...")
            sys.stdout.flush()
        except (BrokenPipeError, IOError):
            pass
        
        # Supabase에 저장
        try:
            result = supabase.table('calendars').insert(calendar_data).execute()
            try:
                print(f"[SUCCESS] Database insert completed")
                sys.stdout.flush()
            except (BrokenPipeError, IOError):
                pass
        except Exception as db_error:
            try:
                print(f"[ERROR] Database insert failed: {db_error}")
                sys.stdout.flush()
            except (BrokenPipeError, IOError):
                pass
            raise db_error
        
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

@calendar_api_bp.route('/calendars/list', methods=['GET'])
def list_calendars():
    """모든 캘린더 목록 조회 (디버그용)"""
    try:
        from supabase import create_client
        SUPABASE_URL = os.environ.get('SUPABASE_URL')
        SUPABASE_KEY = os.environ.get('SUPABASE_API_KEY')
        
        if not SUPABASE_URL or not SUPABASE_KEY:
            return jsonify({'error': 'Supabase credentials not configured'}), 500
            
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        result = supabase.table('calendars').select('id, name, owner_id').execute()
        
        return jsonify({
            'success': True,
            'calendars': result.data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@calendar_api_bp.route('/calendars/<calendar_id>')
def get_calendar(calendar_id):
    """캘린더 정보 조회"""
    print(f"🚨 [CALENDAR API] NEW FUNCTION CALLED with calendar_id: {calendar_id}")
    print(f"🔍 [CALENDAR API] Function get_calendar is definitely being called!")
    
    try:
        # dashboard_data는 이미 파일 상단에서 DashboardDataManager() 인스턴스로 생성됨
        print(f"🔍 [CALENDAR API] Using dashboard_data.admin_client for query")
        
        if not dashboard_data or not dashboard_data.admin_client:
            print(f"❌ [CALENDAR API] Dashboard data or admin_client not available")
            return jsonify({
                'success': False,
                'error': 'Database not available'
            }), 500
        
        # dashboard_data.admin_client 사용 (성공적으로 작동하는 방법)
        print(f"🔍 [CALENDAR API] Querying calendar with id: {calendar_id} using admin_client")
        result = dashboard_data.admin_client.table('calendars').select('*').eq('id', calendar_id).execute()
        print(f"🔍 [CALENDAR API] Query result: {result.data}")
        
        if result.data and len(result.data) > 0:
            calendar = result.data[0]
            print(f"✅ [CALENDAR API] Calendar found: {calendar.get('name', 'Unknown')}")
            
            return jsonify({
                'success': True,
                'calendar': calendar
            })
        else:
            print(f"❌ [CALENDAR API] Calendar not found for ID: {calendar_id}")
            return jsonify({
                'success': False,
                'error': 'Calendar not found'
            }), 404
            
    except Exception as e:
        print(f"💥 [CALENDAR API ERROR] Exception in get_calendar: {str(e)}")
        import traceback
        print(f"💥 [CALENDAR API ERROR] Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@calendar_api_bp.route('/calendars/<calendar_id>/media-title', methods=['PUT'])
def update_media_title(calendar_id):
    """미디어 제목 업데이트"""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    user_id = get_current_user_id()
    
    try:
        data = request.get_json()
        if not data or 'title' not in data:
            return jsonify({
                'success': False,
                'error': 'Title is required'
            }), 400
        
        new_title = data['title'].strip()
        if not new_title:
            return jsonify({
                'success': False,
                'error': 'Title cannot be empty'
            }), 400
        
        try:
            from supabase import create_client
        except ImportError:
            return jsonify({
                'success': False,
                'error': 'Supabase client not available'
            }), 500
        
        # Supabase 연결
        SUPABASE_URL = os.environ.get('SUPABASE_URL')
        SUPABASE_KEY = os.environ.get('SUPABASE_API_KEY')
        
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise Exception("Supabase credentials not configured")
        
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # 캘린더 존재 확인 및 권한 체크
        calendar_result = supabase.table('calendars').select('*').eq('id', calendar_id).eq('owner_id', user_id).execute()
        
        if not calendar_result.data:
            return jsonify({
                'success': False,
                'error': 'Calendar not found or access denied'
            }), 404
        
        # 미디어 제목 업데이트 (media_title 컬럼이 없는 경우 description으로 임시 저장)
        try:
            # 먼저 media_title 컬럼으로 업데이트 시도
            update_result = supabase.table('calendars').update({
                'media_title': new_title,
                'updated_at': 'now()'
            }).eq('id', calendar_id).eq('owner_id', user_id).execute()
            
            if update_result.data:
                return jsonify({
                    'success': True,
                    'message': 'Media title updated successfully',
                    'title': new_title
                })
        except Exception as db_error:
            print(f"media_title 컬럼 업데이트 실패, description 사용: {db_error}")
            # media_title 컬럼이 없는 경우 description에 저장
            try:
                update_result = supabase.table('calendars').update({
                    'description': f"미디어: {new_title}",
                    'updated_at': 'now()'
                }).eq('id', calendar_id).eq('owner_id', user_id).execute()
                
                if update_result.data:
                    return jsonify({
                        'success': True,
                        'message': 'Media title updated successfully (stored in description)',
                        'title': new_title
                    })
            except Exception as fallback_error:
                print(f"description 업데이트도 실패: {fallback_error}")
        
        return jsonify({
            'success': False,
            'error': 'Failed to update media title'
        }), 500
        
    except Exception as e:
        print(f"Error updating media title: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to update media title'
        }), 500

@calendar_api_bp.route('/calendar/<calendar_id>/delete', methods=['DELETE'])
@calendar_api_bp.route('/calendars/<calendar_id>', methods=['DELETE'])
def delete_calendar(calendar_id):
    """캘린더 삭제 (미디어 파일 포함)"""
    # 인증 확인 (옵션)
    user_id = get_current_user_id()
    if not user_id:
        # 기본 사용자 ID 사용
        user_id = "e390559f-c328-4786-ac5d-c74b5409451b"
    
    print(f"🗑️ Attempting to delete calendar: {calendar_id} for user: {user_id}")
    
    try:
        from supabase import create_client
        
        # Supabase 연결
        SUPABASE_URL = os.environ.get('SUPABASE_URL')
        SUPABASE_KEY = os.environ.get('SUPABASE_API_KEY')
        
        if not SUPABASE_URL or not SUPABASE_KEY:
            print("❌ Supabase credentials not found")
            raise Exception("Supabase credentials not configured")
        
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # 먼저 관련 이벤트들 삭제
        try:
            print(f"🗑️ Deleting events for calendar: {calendar_id}")
            events_delete = supabase.table('events').delete().eq('calendar_id', calendar_id).execute()
            print(f"✅ Deleted {len(events_delete.data) if events_delete.data else 0} events")
        except Exception as e:
            print(f"⚠️ Warning: Failed to delete events: {e}")
            # Continue even if event deletion fails
        
        # 캘린더 정보 조회 (미디어 파일 경로 확인용)
        calendar_result = supabase.table('calendars').select('*').eq('id', calendar_id).execute()
        
        if not calendar_result.data:
            print(f"❌ Calendar not found: {calendar_id}")
            # 이미 삭제된 경우도 성공으로 처리
            return jsonify({
                'success': True,
                'message': 'Calendar already deleted or not found'
            })
        
        calendar = calendar_result.data[0]
        print(f"📋 Found calendar: {calendar.get('name', 'Unknown')}")
        
        # 미디어 파일 삭제 시도 (실패해도 계속)
        if calendar.get('media_file_path'):
            try:
                upload_folder = get_upload_folder()
                file_path = os.path.join(upload_folder, calendar['media_file_path'])
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"✅ Deleted media file: {file_path}")
            except Exception as e:
                print(f"⚠️ Warning: Failed to delete media file: {e}")
                # Continue even if file deletion fails
        
        # 캘린더 삭제
        delete_result = supabase.table('calendars').delete().eq('id', calendar_id).execute()
        
        if delete_result.data:
            print(f"✅ Successfully deleted calendar: {calendar_id}")
        else:
            print(f"⚠️ No data returned from delete, but operation may have succeeded")
        
        return jsonify({
            'success': True,
            'message': 'Calendar deleted successfully'
        })
        
    except Exception as e:
        print(f"❌ Error deleting calendar {calendar_id}: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': f'Failed to delete calendar: {str(e)}'
        }), 500

@calendar_api_bp.route('/google-calendars', methods=['GET'])
def get_google_calendars():
    """구글 캘린더 목록 가져오기"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            user_id = "e390559f-c328-4786-ac5d-c74b5409451b"  # 임시 사용자 ID
        
        # Google Calendar 서비스 import
        sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend'))
        from services.google_calendar_service import get_google_calendar_service
        
        # Google Calendar 서비스 인스턴스 가져오기
        google_service = get_google_calendar_service()
        
        # 구글 캘린더 목록 가져오기
        google_calendars = google_service.get_calendar_list(user_id)
        
        return jsonify({
            'success': True,
            'calendars': google_calendars,
            'count': len(google_calendars),
            'message': f'Found {len(google_calendars)} Google Calendars'
        })
        
    except Exception as e:
        print(f"Error getting Google calendars: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get Google calendars: {str(e)}',
            'calendars': []
        }), 500

@calendar_api_bp.route('/youtube/info', methods=['POST'])
def get_youtube_info():
    """YouTube 비디오 정보 조회"""
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({
                'success': False,
                'error': 'YouTube URL is required'
            }), 400
        
        url = data['url'].strip()
        if not url:
            return jsonify({
                'success': False,
                'error': 'YouTube URL cannot be empty'
            }), 400
        
        # YouTube API Key 확인
        youtube_api_key = os.environ.get('YOUTUBE_API_KEY')
        if not youtube_api_key or youtube_api_key == 'YOUR_API_KEY_HERE':
            return jsonify({
                'success': False,
                'error': 'YouTube API key not configured. Please set YOUTUBE_API_KEY in your .env file with a valid Google Cloud API key.'
            }), 500
        
        # YouTube 유틸리티 함수 사용
        try:
            from utils.youtube_utils import process_youtube_url
        except ImportError:
            return jsonify({
                'success': False,
                'error': 'YouTube utility not available'
            }), 500
        
        # YouTube URL 처리
        success, result = process_youtube_url(url, youtube_api_key)
        
        if not success:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to process YouTube URL')
            }), 400
        
        return jsonify({
            'success': True,
            'video_info': result
        })
        
    except Exception as e:
        print(f"Error getting YouTube info: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get YouTube video information'
        }), 500

@calendar_api_bp.route('/calendar/<calendar_id>/events/<event_id>', methods=['DELETE'])
def delete_calendar_event(calendar_id, event_id):
    """Delete a calendar event"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            # For now, allow deletion without authentication for demo purposes
            pass
        
        # Here you would normally delete the event from the database
        # For now, just return success
        return jsonify({
            'success': True,
            'message': 'Event deleted successfully',
            'event_id': event_id
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to delete event: {str(e)}'
        }), 500

# Error handlers
@calendar_api_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Calendar API endpoint not found'}), 404

@calendar_api_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500