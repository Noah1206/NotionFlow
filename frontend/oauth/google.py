from flask import Blueprint, redirect, url_for, session, request, current_app
from .base_oauth import register_oauth_service
import requests
import os
from datetime import datetime

# Environment-based configuration - SECURITY FIX
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_API_KEY = os.getenv('SUPABASE_API_KEY')
SUPABASE_USERS_ENDPOINT = f"{SUPABASE_URL}/rest/v1/user_api_keys" if SUPABASE_URL else None

GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')

google_bp = Blueprint('google_bp', __name__)
google_oauth = None

def get_google_oauth(app):
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise ValueError("Google OAuth credentials not found in environment variables")
    
    return register_oauth_service(
        app,
        name='google',
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        authorize_url='https://accounts.google.com/o/oauth2/auth',
        access_token_url='https://oauth2.googleapis.com/token',
        api_base_url='https://www.googleapis.com/oauth2/v1/',
        scope='email profile'
    )
def upsert_user_to_supabase(user_info):
    if not SUPABASE_URL or not SUPABASE_API_KEY:
        raise ValueError("Supabase credentials not found in environment variables")
    
    headers = {
        "apikey": SUPABASE_API_KEY,
        "Authorization": f"Bearer {SUPABASE_API_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation,resolution=merge-duplicates"
    }
    data = {
        "user_email": user_info["email"],
        "name": user_info["name"],
        "avatar_url": user_info.get("picture"),
        "created_at": datetime.utcnow().isoformat()  # ✅ 선택적 (Supabase default면 생략 가능)
    }
    resp = requests.post(
        SUPABASE_USERS_ENDPOINT,  # 이제 user_api_keys로
        headers=headers,
        json=data
    )
    if resp.ok:
        returned = resp.json()
        current_app.logger.info(f"Supabase user creation successful: {returned}")

        user_id = returned[0]["id"]

        api_keys_data = {
            "id": user_id,  # ✅ uuid 사용
            "user_email": user_info["email"],
        }

        api_keys_resp = requests.post(
            f"{SUPABASE_URL}/rest/v1/user_api_keys",
            headers=headers,
            json=api_keys_data
        )

        if api_keys_resp.ok:
            current_app.logger.info(f"API keys created successfully: {api_keys_resp.json()}")
        else:
            current_app.logger.error(f"Failed to create API keys: {api_keys_resp.text}")

        return user_id
    return None

def register_google_routes(app):
    google = get_google_oauth(app)

    @google_bp.route("/login/google")
    def login_google():
        # Railway 환경에서는 항상 명시적으로 redirect_uri 설정 (HTTPS 프록시 문제 해결)
        base_url = os.getenv('BASE_URL')
        if base_url:
            redirect_uri = f"{base_url}/auth/google/callback"
        else:
            # 로컬 개발 환경
            redirect_uri = url_for("google_bp.google_auth_callback", _external=True)
            # HTTP로 생성되면 HTTPS로 강제 변경
            if redirect_uri.startswith('http://') and os.getenv('FLASK_ENV') == 'production':
                redirect_uri = redirect_uri.replace('http://', 'https://', 1)
        
        current_app.logger.info(f"Google OAuth redirect URI being used: {redirect_uri}")
        print(f"[OAUTH DEBUG] Redirect URI: {redirect_uri}")
        return google.authorize_redirect(redirect_uri)

    @google_bp.route("/auth/google/callback")
    def google_auth_callback():
        token = google.authorize_access_token()
        resp = google.get("userinfo")
        user_info = resp.json()
        # Supabase에 유저 정보 저장
        user_id = upsert_user_to_supabase(user_info)
        
        # Save OAuth tokens to oauth_tokens table for GoogleCalendarService
        try:
            if SUPABASE_URL and SUPABASE_API_KEY:
                headers = {
                    "apikey": SUPABASE_API_KEY,
                    "Authorization": f"Bearer {SUPABASE_API_KEY}",
                    "Content-Type": "application/json",
                    "Prefer": "return=representation,resolution=merge-duplicates"
                }
                
                # Calculate expiry time (1 hour from now if not provided)
                expires_at = None
                if token.get('expires_in'):
                    from datetime import timedelta
                    expires_at = (datetime.utcnow() + timedelta(seconds=token['expires_in'])).isoformat()
                
                oauth_token_data = {
                    "user_id": user_id,
                    "platform": "google",
                    "access_token": token.get('access_token'),
                    "refresh_token": token.get('refresh_token'),
                    "token_type": token.get('token_type', 'Bearer'),
                    "expires_at": expires_at,
                    "scope": token.get('scope', 'email profile https://www.googleapis.com/auth/calendar'),
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
                
                oauth_resp = requests.post(
                    f"{SUPABASE_URL}/rest/v1/oauth_tokens",
                    headers=headers,
                    json=oauth_token_data
                )
                
                if oauth_resp.ok:
                    current_app.logger.info(f"OAuth tokens saved successfully for user {user_id}")
                    
                    # Trigger auto-import after successful token save
                    try:
                        import threading
                        import sys
                        import os
                        
                        def auto_import_async():
                            try:
                                # Import Google Calendar service
                                sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend'))
                                from services.google_calendar_service import GoogleCalendarService
                                
                                # Get Supabase client
                                from app import get_supabase
                                supabase_client = get_supabase()
                                if not supabase_client:
                                    current_app.logger.error("Database not available for auto-import")
                                    return
                                
                                # Check/create default calendar
                                user_calendars = supabase_client.table('calendars').select('*').eq('owner_id', user_id).execute()
                                
                                if not user_calendars.data:
                                    new_calendar = {
                                        'owner_id': user_id,
                                        'name': 'My Calendar',
                                        'description': 'Default calendar for imported events',
                                        'color': '#4285F4',
                                        'platform': 'custom',
                                        'is_shared': False,
                                        'is_enabled': True,
                                        'created_at': datetime.utcnow().isoformat(),
                                        'updated_at': datetime.utcnow().isoformat()
                                    }
                                    create_result = supabase_client.table('calendars').insert(new_calendar).execute()
                                    calendar_data = create_result.data[0] if create_result.data else None
                                else:
                                    calendar_data = user_calendars.data[0]
                                
                                if not calendar_data:
                                    current_app.logger.error("Failed to get/create calendar for auto-import")
                                    return
                                
                                calendar_id = calendar_data.get('id')
                                current_app.logger.info(f"Starting auto-import for user {user_id}, calendar {calendar_id}")
                                
                                # Import Google Calendar events
                                google_service = GoogleCalendarService()
                                google_events = google_service.get_events(user_id, calendar_id='primary')
                                
                                if not google_events:
                                    current_app.logger.info(f"No Google events found for user {user_id}")
                                    return
                                
                                # Import events to NotionFlow calendar
                                imported_count = 0
                                for event in google_events:
                                    try:
                                        start_datetime = event.get('start', {})
                                        end_datetime = event.get('end', {})
                                        
                                        start_time = start_datetime.get('dateTime') or start_datetime.get('date')
                                        end_time = end_datetime.get('dateTime') or end_datetime.get('date')
                                        
                                        if not start_time:
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
                                            'last_synced_at': datetime.utcnow().isoformat(),
                                            'status': event.get('status', 'confirmed')
                                        }
                                        
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
                                        
                                    except Exception as e:
                                        current_app.logger.error(f"Failed to import single event: {str(e)}")
                                
                                current_app.logger.info(f"Auto-import completed: {imported_count} events imported for user {user_id}")
                                
                            except Exception as e:
                                current_app.logger.error(f"Auto-import thread error: {str(e)}")
                        
                        # Run auto-import in background thread
                        thread = threading.Thread(target=auto_import_async)
                        thread.daemon = True
                        thread.start()
                        
                    except Exception as e:
                        current_app.logger.error(f"Failed to start auto-import thread: {str(e)}")
                        
                else:
                    current_app.logger.error(f"Failed to save OAuth tokens: {oauth_resp.text}")
        except Exception as e:
            current_app.logger.error(f"Error saving OAuth tokens: {str(e)}")
        
        # JWT 발급을 위해 user_info를 세션에 저장
        session["user_info"] = {
            "email": user_info["email"],
            "name": user_info["name"],
            "user_id": user_id 
        }
        session['user_id'] = user_id  # Also set user_id directly for auto-import
        
        # Railway 배포 환경에 맞게 수정
        base_url = os.getenv('BASE_URL', 'http://127.0.0.1:5003')
        return redirect(f'{base_url}/dashboard')

    app.register_blueprint(google_bp)
