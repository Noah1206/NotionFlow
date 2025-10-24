"""
Google Calendar API 서비스
Google Calendar와 실제 일정을 동기화하는 서비스
"""

import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
try:
    import pytz
except ImportError:
    # pytz가 없는 경우 datetime의 timezone 사용
    from datetime import timezone as pytz_tz
    pytz = None

from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

class GoogleCalendarService:
    def __init__(self):
        self.supabase_url = os.environ.get('SUPABASE_URL')
        # SERVICE_ROLE_KEY를 사용해야 RLS를 우회할 수 있음
        self.supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('SUPABASE_API_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise Exception("Supabase credentials not found")
            
        self.supabase = create_client(self.supabase_url, self.supabase_key)
    
    def get_google_credentials(self, user_id: str) -> Optional[Credentials]:
        """사용자의 Google OAuth 토큰으로 Credentials 객체 생성"""
        try:
            # UUID 정규화 (하이픈 포함 형식으로 통일)
            try:
                from utils.uuid_helper import normalize_uuid
                normalized_user_id = normalize_uuid(user_id)
                print(f"🔍 [GOOGLE-CREDS] Original user_id: {user_id}, Normalized: {normalized_user_id}")
            except Exception as e:
                print(f"⚠️ [GOOGLE-CREDS] UUID normalization failed, using original: {e}")
                normalized_user_id = user_id

            # 먼저 oauth_tokens 테이블에서 찾기
            response = self.supabase.table('oauth_tokens').select('*').eq('user_id', normalized_user_id).eq('platform', 'google').execute()

            token_data = None
            if response.data:
                token_data = response.data[0]
                print(f"✅ Found Google OAuth token in oauth_tokens for user {normalized_user_id}")
            else:
                # oauth_tokens에 없으면 calendar_sync_configs에서 찾기
                print(f"⚠️ No OAuth token in oauth_tokens, checking calendar_sync_configs for user {normalized_user_id}")
                sync_response = self.supabase.table('calendar_sync_configs').select('*').eq('user_id', normalized_user_id).eq('platform', 'google').eq('is_enabled', True).execute()

                if sync_response.data:
                    sync_data = sync_response.data[0]
                    credentials_data = sync_data.get('credentials', {})
                    if credentials_data.get('access_token'):
                        token_data = {
                            'access_token': credentials_data.get('access_token'),
                            'refresh_token': credentials_data.get('refresh_token'),
                            'expires_at': credentials_data.get('expires_at')
                        }
                        print(f"✅ Found Google credentials in calendar_sync_configs for user {normalized_user_id}")
                    else:
                        print(f"❌ No valid access_token in calendar_sync_configs for user {normalized_user_id}")
                else:
                    print(f"❌ No Google sync config found for user {normalized_user_id}")

            if not token_data:
                print(f"❌ No Google credentials found for user {normalized_user_id} in any table")
                return None

            if not token_data.get('refresh_token'):
                print(f"❌ Missing refresh_token for user {normalized_user_id}")
                return None

            if not os.environ.get('GOOGLE_CLIENT_ID') or not os.environ.get('GOOGLE_CLIENT_SECRET'):
                print(f"❌ Missing Google OAuth environment variables")
                return None

            # Google Credentials 객체 생성 (만료 시간 없이 먼저 생성)
            credentials = Credentials(
                token=token_data.get('access_token'),
                refresh_token=token_data.get('refresh_token'),
                token_uri='https://oauth2.googleapis.com/token',
                client_id=os.environ.get('GOOGLE_CLIENT_ID'),
                client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
                scopes=['https://www.googleapis.com/auth/calendar']
            )

            # 토큰 만료 시간 설정은 일시적으로 비활성화 (datetime 비교 에러 방지)
            # Google API 라이브러리가 자동으로 토큰 갱신을 처리할 것임
            # if token_data.get('expires_at'):
            #     ... (비활성화됨)

            return credentials

        except Exception as e:
            print(f"❌ Error getting Google credentials for user {normalized_user_id if 'normalized_user_id' in locals() else user_id}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_calendar_service(self, user_id: str):
        """Google Calendar API 서비스 객체 생성"""
        credentials = self.get_google_credentials(user_id)
        if not credentials:
            return None
        
        try:
            service = build('calendar', 'v3', credentials=credentials)
            return service
        except Exception as e:
            print(f"Error building Google Calendar service: {e}")
            return None

    def get_selected_calendar(self, user_id: str, calendar_id: str) -> Optional[Dict]:
        """선택된 캘린더 정보 확인"""
        try:
            # UUID 정규화
            try:
                from utils.uuid_helper import normalize_uuid
                normalized_user_id = normalize_uuid(user_id)
            except Exception as e:
                print(f"⚠️ UUID normalization failed, using original: {e}")
                normalized_user_id = user_id

            # 먼저 user_calendars 테이블에서 선택된 캘린더인지 확인 (calendars 테이블은 owner_id 사용)
            response = self.supabase.table('calendars').select('*').eq('id', calendar_id).eq('owner_id', normalized_user_id).execute()

            if not response.data:
                print(f"캘린더 {calendar_id}를 찾을 수 없습니다.")
                return None

            calendar_data = response.data[0]

            # 캘린더가 활성화되어 있는지 확인
            if not calendar_data.get('is_active', True):
                print(f"캘린더 {calendar_id}가 비활성화되어 있습니다.")
                return None

            return {
                'id': calendar_data['id'],
                'name': calendar_data['name'],
                'google_calendar_id': calendar_data.get('google_calendar_id', 'primary'),
                'color': calendar_data.get('color', '#4285f4')
            }

        except Exception as e:
            print(f"Error checking selected calendar: {e}")
            return None
    
    def create_event(self, user_id: str, calendar_id: str, event_data: Dict[str, Any]) -> Optional[Dict]:
        """Google Calendar에 일정 생성"""
        service = self.get_calendar_service(user_id)
        if not service:
            return None

        # 선택된 캘린더가 있는지 확인
        selected_calendar = self.get_selected_calendar(user_id, calendar_id)
        if not selected_calendar:
            print(f"캘린더 {calendar_id}가 선택되지 않았거나 존재하지 않습니다.")
            return None

        try:
            # Google Calendar 일정 형식으로 변환
            google_event = self._convert_to_google_event(event_data)

            # 선택된 캘린더에 일정 생성
            created_event = service.events().insert(
                calendarId=selected_calendar['google_calendar_id'],
                body=google_event
            ).execute()

            print(f"Google Calendar 일정 생성 완료: {created_event['id']}")
            return created_event
            
        except HttpError as e:
            print(f"Google Calendar API error: {e}")
            return None
        except Exception as e:
            print(f"Error creating Google Calendar event: {e}")
            return None
    
    def update_event(self, user_id: str, event_id: str, event_data: Dict[str, Any]) -> Optional[Dict]:
        """Google Calendar 일정 업데이트"""
        service = self.get_calendar_service(user_id)
        if not service:
            return None
        
        try:
            google_event = self._convert_to_google_event(event_data)
            
            updated_event = service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=google_event
            ).execute()
            
            print(f"Google Calendar 일정 업데이트 완료: {event_id}")
            return updated_event
            
        except HttpError as e:
            print(f"Google Calendar API error: {e}")
            return None
        except Exception as e:
            print(f"Error updating Google Calendar event: {e}")
            return None
    
    def delete_event(self, user_id: str, event_id: str) -> bool:
        """Google Calendar 일정 삭제"""
        service = self.get_calendar_service(user_id)
        if not service:
            return False
        
        try:
            service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            print(f"Google Calendar 일정 삭제 완료: {event_id}")
            return True
            
        except HttpError as e:
            print(f"Google Calendar API error: {e}")
            return False
        except Exception as e:
            print(f"Error deleting Google Calendar event: {e}")
            return False
    
    def get_calendar_list(self, user_id: str) -> List[Dict]:
        """사용자의 Google Calendar 목록 가져오기"""
        service = self.get_calendar_service(user_id)
        if not service:
            print(f"[Google Calendar] No service available for user {user_id}")
            return []

        try:
            # Google Calendar 목록 조회
            calendar_list_result = service.calendarList().list().execute()
            calendars = calendar_list_result.get('items', [])

            # 캘린더 정보 정리
            formatted_calendars = []
            for calendar in calendars:
                try:
                    calendar_info = {
                        'id': calendar.get('id'),
                        'name': calendar.get('summary', 'Untitled Calendar'),
                        'description': calendar.get('description', ''),
                        'color': calendar.get('backgroundColor', '#3B82F6'),
                        'timezone': calendar.get('timeZone', 'Asia/Seoul'),
                        'access_role': calendar.get('accessRole', 'reader'),
                        'is_primary': calendar.get('primary', False),
                        'is_selected': calendar.get('selected', True)
                    }
                    formatted_calendars.append(calendar_info)
                except Exception as calendar_error:
                    print(f"Error processing calendar {calendar.get('id', 'unknown')}: {calendar_error}")
                    # 에러가 발생한 캘린더는 건너뛰고 계속 진행
                    continue

            print(f"Google Calendar에서 {len(formatted_calendars)}개 캘린더 조회")
            return formatted_calendars

        except HttpError as e:
            print(f"Google Calendar API error: {e}")
            return []
        except Exception as e:
            print(f"Error getting Google Calendar list: {e}")
            # 상세한 에러 정보 출력
            import traceback
            print(f"Detailed error traceback: {traceback.format_exc()}")
            return []
    
    def get_events(self, user_id: str, calendar_id: str = 'primary', time_min: datetime = None, time_max: datetime = None) -> List[Dict]:
        """Google Calendar에서 일정 가져오기"""
        service = self.get_calendar_service(user_id)
        if not service:
            return []
        
        try:
            # 기본값 설정 - timezone-aware datetime 사용
            if not time_min:
                if pytz:
                    time_min = datetime.now(pytz.UTC) - timedelta(days=30)
                else:
                    from datetime import timezone
                    time_min = datetime.now(timezone.utc) - timedelta(days=30)
            elif hasattr(time_min, 'tzinfo') and time_min.tzinfo is None:
                # timezone-naive datetime인 경우 UTC로 변환
                from datetime import timezone
                time_min = time_min.replace(tzinfo=timezone.utc)

            if not time_max:
                if pytz:
                    time_max = datetime.now(pytz.UTC) + timedelta(days=90)
                else:
                    from datetime import timezone
                    time_max = datetime.now(timezone.utc) + timedelta(days=90)
            elif hasattr(time_max, 'tzinfo') and time_max.tzinfo is None:
                # timezone-naive datetime인 경우 UTC로 변환
                from datetime import timezone
                time_max = time_max.replace(tzinfo=timezone.utc)
            
            # Google Calendar에서 일정 조회
            events_result = service.events().list(
                calendarId=calendar_id,
                timeMin=time_min.isoformat(),
                timeMax=time_max.isoformat(),
                maxResults=100,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            print(f"Google Calendar({calendar_id})에서 {len(events)}개 일정 조회")
            
            return events
            
        except HttpError as e:
            print(f"Google Calendar API error: {e}")
            return []
        except Exception as e:
            print(f"Error getting Google Calendar events: {e}")
            return []
    
    def _convert_to_google_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Notion 일정 데이터를 Google Calendar 형식으로 변환"""
        google_event = {
            'summary': event_data.get('title', 'Untitled Event'),
            'description': event_data.get('description', ''),
        }
        
        # 시간 설정
        if event_data.get('start_time') and event_data.get('end_time'):
            # 시간이 있는 일정
            google_event['start'] = {
                'dateTime': event_data['start_time'],
                'timeZone': 'Asia/Seoul'
            }
            google_event['end'] = {
                'dateTime': event_data['end_time'], 
                'timeZone': 'Asia/Seoul'
            }
        elif event_data.get('date'):
            # 종일 일정
            google_event['start'] = {'date': event_data['date']}
            google_event['end'] = {'date': event_data['date']}
        
        # 위치 설정
        if event_data.get('location'):
            google_event['location'] = event_data['location']
        
        # 참석자 설정 (옵션)
        if event_data.get('attendees'):
            google_event['attendees'] = [
                {'email': email} for email in event_data['attendees']
            ]
        
        # 알림 설정
        if event_data.get('reminders'):
            google_event['reminders'] = {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},  # 1일 전 이메일
                    {'method': 'popup', 'minutes': 10}        # 10분 전 팝업
                ]
            }
        
        return google_event
    
    def sync_notion_events_to_google(self, user_id: str, notion_events: List[Dict]) -> Dict[str, int]:
        """Notion 일정들을 Google Calendar에 동기화"""
        synced_count = 0
        failed_count = 0
        
        for event in notion_events:
            try:
                # Google Calendar에 일정 생성
                google_event = self.create_event(user_id, 'primary', event)
                
                if google_event:
                    # 연동 정보 저장 (향후 업데이트/삭제를 위해)
                    self._save_sync_mapping(
                        user_id=user_id,
                        notion_event_id=event.get('id'),
                        google_event_id=google_event['id']
                    )
                    synced_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                print(f"Error syncing event {event.get('id', 'unknown')}: {e}")
                failed_count += 1
        
        return {
            'synced_count': synced_count,
            'failed_count': failed_count,
            'total_count': len(notion_events)
        }
    
    def _save_sync_mapping(self, user_id: str, notion_event_id: str, google_event_id: str):
        """일정 동기화 매핑 정보 저장"""
        try:
            self.supabase.table('event_sync_mapping').upsert({
                'user_id': user_id,
                'notion_event_id': notion_event_id,
                'google_event_id': google_event_id,
                'platform': 'google',
                'synced_at': datetime.now().isoformat(),
                'sync_status': 'synced'
            }).execute()
        except Exception as e:
            print(f"Error saving sync mapping: {e}")

# 싱글톤 인스턴스 - 지연 생성
_google_calendar_service = None

def get_google_calendar_service():
    global _google_calendar_service
    if _google_calendar_service is None:
        _google_calendar_service = GoogleCalendarService()
    return _google_calendar_service

# 하위 호환성을 위한 속성
google_calendar_service = get_google_calendar_service()