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
                    
                    # Auto-import Google Calendar events - only if not manually disconnected
                    try:
                        print(f"[OAUTH] Checking for auto-import opportunity for user {user_id}")
                        # This is a fresh OAuth connection, so auto-import should be safe
                        # The manual disconnection flag is only set AFTER connection, not during OAuth
                        
                        # Try to auto-import Google Calendar events
                        import requests
                        import_url = f"{request.host_url}api/google/import"
                        print(f"[OAUTH] Attempting auto-import from {import_url}")
                        
                        # Use a short timeout to avoid hanging
                        import_resp = requests.post(import_url, 
                            json={'user_id': user_id, 'source': 'oauth_callback'},
                            timeout=10,
                            cookies=request.cookies
                        )
                        
                        if import_resp.ok:
                            print(f"[OAUTH] Auto-import successful for user {user_id}")
                        else:
                            print(f"[OAUTH] Auto-import failed: {import_resp.text}")
                            
                    except Exception as import_error:
                        print(f"[OAUTH] Auto-import error: {import_error}")
                        # Don't fail the OAuth flow if auto-import fails
                        
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
        
        # Mark Google platform as connected in session
        session['platform_google_connected'] = True
        session['platform_google_last_sync'] = datetime.utcnow().isoformat()
        print(f"[OAUTH] Google platform marked as connected in session for user {user_id}")
        
        # Railway 배포 환경에 맞게 수정
        base_url = os.getenv('BASE_URL', 'http://127.0.0.1:5003')
        return redirect(f'{base_url}/dashboard?from_oauth=google')

    app.register_blueprint(google_bp)
