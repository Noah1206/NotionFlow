"""
Google Calendar 동기화 서비스
Notion 동기화 패턴과 동일한 구조로 구현
"""

import os
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any

# Google Calendar API 클래스
class GoogleCalendarAPI:
    """Google Calendar API 호출을 담당하는 클래스"""
    
    def __init__(self, credentials):
        self.credentials = credentials
        self.service = None
        self._build_service()
    
    def _build_service(self):
        """Google Calendar API 서비스 빌드"""
        try:
            from googleapiclient.discovery import build
            self.service = build('calendar', 'v3', credentials=self.credentials)
            print("✅ [GOOGLE API] Service built successfully")
        except Exception as e:
            print(f"❌ [GOOGLE API] Failed to build service: {e}")
            self.service = None
    
    def list_calendars(self) -> List[Dict]:
        """사용자의 모든 캘린더 목록 조회"""
        try:
            if not self.service:
                return []
            
            calendars_result = self.service.calendarList().list().execute()
            calendars = calendars_result.get('items', [])
            
            print(f"✅ [GOOGLE API] Found {len(calendars)} calendars")
            return calendars
            
        except Exception as e:
            print(f"❌ [GOOGLE API] Error listing calendars: {e}")
            return []
    
    def get_events(self, calendar_id: str = 'primary', time_min: datetime = None, time_max: datetime = None, max_results: int = 250) -> List[Dict]:
        """특정 캘린더의 이벤트들 조회"""
        try:
            if not self.service:
                return []
            
            # 기본 시간 범위 설정 (지난 1개월 ~ 앞으로 6개월)
            if not time_min:
                time_min = datetime.now(timezone.utc) - timedelta(days=30)
            if not time_max:
                time_max = datetime.now(timezone.utc) + timedelta(days=180)
            
            print(f"📡 [GOOGLE API] Fetching events from {calendar_id}")
            print(f"📅 [GOOGLE API] Time range: {time_min.isoformat()} - {time_max.isoformat()}")
            
            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=time_min.isoformat(),
                timeMax=time_max.isoformat(),
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            print(f"✅ [GOOGLE API] Found {len(events)} events in {calendar_id}")
            
            return events
            
        except Exception as e:
            print(f"❌ [GOOGLE API] Error fetching events from {calendar_id}: {e}")
            return []

# Google Calendar 동기화 서비스
class GoogleCalendarSyncService:
    """Google Calendar와 SupaBase 동기화를 담당하는 서비스"""
    
    def __init__(self):
        from supabase import create_client
        
        # SupaBase 초기화
        self.supabase_url = os.environ.get('SUPABASE_URL')
        # SERVICE_ROLE_KEY 사용으로 RLS 우회
        self.supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('SUPABASE_API_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise Exception("SupaBase credentials not found")
        
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        print("✅ [GOOGLE SYNC] SupaBase initialized")

    def get_selected_calendars(self, user_id: str) -> List[str]:
        """사용자가 선택한 캘린더 ID 목록을 조회"""
        try:
            # calendar_sync_configs 테이블에서 Google 연동 정보 조회
            config_result = self.supabase.table('calendar_sync_configs').select('credentials').eq('user_id', user_id).eq('platform', 'google').execute()

            if not config_result.data:
                print(f"⚠️ [GOOGLE SYNC] No Google Calendar config found for user {user_id}")
                return []

            # credentials JSON에서 calendar_id 가져오기 (이메일 주소)
            credentials = config_result.data[0].get('credentials', {})
            calendar_id = credentials.get('calendar_id')

            if calendar_id:
                # 현재는 하나의 캘린더만 저장하므로 리스트로 반환
                selected_calendar_ids = [calendar_id]
                print(f"✅ [GOOGLE SYNC] Found calendar for user {user_id}: {calendar_id}")
                return selected_calendar_ids
            else:
                print(f"⚠️ [GOOGLE SYNC] No calendar_id in credentials for user {user_id}")
                return []

        except Exception as e:
            print(f"❌ [GOOGLE SYNC] Error getting selected calendars for user {user_id}: {e}")
            return []
    
    def get_user_credentials(self, user_id: str):
        """사용자의 Google OAuth 토큰으로 Credentials 생성"""
        try:
            from google.oauth2.credentials import Credentials
            
            # SupaBase에서 OAuth 토큰 조회
            response = self.supabase.table('oauth_tokens').select('*').eq('user_id', user_id).eq('platform', 'google').execute()
            
            if not response.data:
                print(f"❌ [GOOGLE SYNC] No Google OAuth token found for user {user_id}")
                return None
            
            token_data = response.data[0]
            print(f"✅ [GOOGLE SYNC] Found OAuth token for user {user_id}")
            
            # Google Credentials 객체 생성
            credentials = Credentials(
                token=token_data.get('access_token'),
                refresh_token=token_data.get('refresh_token'),
                token_uri='https://oauth2.googleapis.com/token',
                client_id=os.environ.get('GOOGLE_CLIENT_ID'),
                client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
                scopes=['https://www.googleapis.com/auth/calendar']
            )
            
            # 토큰 만료시간 설정
            if token_data.get('expires_at'):
                expires_at = datetime.fromisoformat(token_data.get('expires_at').replace('Z', '+00:00'))
                credentials.expiry = expires_at
            
            return credentials
            
        except Exception as e:
            print(f"❌ [GOOGLE SYNC] Error getting credentials for user {user_id}: {e}")
            return None
    
    def sync_user_events(self, user_id: str) -> Dict[str, Any]:
        """사용자의 Google Calendar 이벤트를 SupaBase에 동기화"""
        try:
            print(f"🚀 [GOOGLE SYNC] Starting sync for user {user_id}")
            
            # 1. 사용자 인증 정보 획득
            credentials = self.get_user_credentials(user_id)
            if not credentials:
                return {
                    'success': False,
                    'error': 'Google OAuth 토큰을 찾을 수 없습니다',
                    'events_processed': 0
                }
            
            # 2. Google Calendar API 초기화
            google_api = GoogleCalendarAPI(credentials)
            if not google_api.service:
                return {
                    'success': False,
                    'error': 'Google Calendar API 서비스를 초기화할 수 없습니다',
                    'events_processed': 0
                }
            
            # 3. 캘린더 목록 및 선택된 캘린더 조회
            calendars = google_api.list_calendars()
            selected_calendar_ids = self.get_selected_calendars(user_id)

            if not selected_calendar_ids:
                print(f"⚠️ [GOOGLE SYNC] No calendars selected for user {user_id}. Skipping sync.")
                return {
                    'success': False,
                    'error': '동기화할 캘린더가 선택되지 않았습니다. API 키 연결 페이지에서 캘린더를 선택해주세요.',
                    'events_processed': 0
                }

            total_events = 0
            processed_events = 0
            errors = []

            # 4. 선택된 캘린더만 동기화
            for calendar in calendars:
                calendar_id = calendar.get('id', 'primary')
                calendar_name = calendar.get('summary', 'Unknown Calendar')

                # 선택된 캘린더인지 확인
                if calendar_id not in selected_calendar_ids:
                    print(f"⏭️ [GOOGLE SYNC] Skipping unselected calendar: {calendar_name} ({calendar_id})")
                    continue

                print(f"📅 [GOOGLE SYNC] Processing selected calendar: {calendar_name} ({calendar_id})")
                
                try:
                    # 이벤트 조회
                    events = google_api.get_events(calendar_id)
                    total_events += len(events)
                    
                    # 이벤트를 SupaBase에 저장
                    for event in events:
                        try:
                            self._save_event_to_database(event, user_id, calendar_id, calendar_name)
                            processed_events += 1
                        except Exception as e:
                            error_msg = f"Event save error in {calendar_name}: {str(e)}"
                            errors.append(error_msg)
                            print(f"❌ [GOOGLE SYNC] {error_msg}")
                    
                except Exception as e:
                    error_msg = f"Calendar processing error for {calendar_name}: {str(e)}"
                    errors.append(error_msg)
                    print(f"❌ [GOOGLE SYNC] {error_msg}")
            
            # 5. 결과 반환
            success = len(errors) == 0 or processed_events > 0
            print(f"✅ [GOOGLE SYNC] Sync completed for user {user_id}")
            print(f"📊 [GOOGLE SYNC] Selected calendars: {len(selected_calendar_ids)}")
            print(f"📊 [GOOGLE SYNC] Total events found: {total_events}")
            print(f"📊 [GOOGLE SYNC] Events processed: {processed_events}")
            print(f"📊 [GOOGLE SYNC] Errors: {len(errors)}")

            return {
                'success': success,
                'selected_calendars_count': len(selected_calendar_ids),
                'events_found': total_events,
                'events_processed': processed_events,
                'errors': errors,
                'message': f'선택된 {len(selected_calendar_ids)}개 캘린더에서 {processed_events}개 이벤트 동기화 완료'
            }
            
        except Exception as e:
            error_msg = f"Sync process error for user {user_id}: {str(e)}"
            print(f"❌ [GOOGLE SYNC] {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'events_processed': 0
            }
    
    def _save_event_to_database(self, event: Dict, user_id: str, calendar_id: str, calendar_name: str):
        """Google Calendar 이벤트를 SupaBase에 저장"""
        try:
            # 이벤트 데이터 파싱
            event_data = self._parse_google_event(event, calendar_id, calendar_name)
            if not event_data:
                return

            # 기존 이벤트 확인 (중복 방지)
            existing = self.supabase.table('calendar_events').select('*').eq('user_id', user_id).eq('external_id', event.get('id')).execute()

            if existing.data:
                # 기존 이벤트 업데이트
                update_data = {
                    **event_data,
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }

                result = self.supabase.table('calendar_events').update(update_data).eq('user_id', user_id).eq('external_id', event.get('id')).execute()
                print(f"📝 [GOOGLE SYNC] Updated event: {event_data['title']}")

            else:
                # 새 이벤트 삽입
                insert_data = {
                    **event_data,
                    'user_id': user_id,
                    'source_platform': 'google',  # Changed from 'source'
                    'external_id': event.get('id'),  # Changed from google_event_id
                    'source_calendar_id': calendar_id,  # Changed from google_calendar_id
                    'source_calendar_name': calendar_name,  # Changed from google_calendar_name
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }

                result = self.supabase.table('calendar_events').insert(insert_data).execute()
                print(f"➕ [GOOGLE SYNC] Inserted new event: {event_data['title']}")
        
        except Exception as e:
            print(f"❌ [GOOGLE SYNC] Error saving event '{event.get('summary', 'Unknown')}': {e}")
            raise
    
    def _parse_google_event(self, event: Dict, calendar_id: str, calendar_name: str) -> Optional[Dict]:
        """Google Calendar 이벤트를 SupaBase 형식으로 변환"""
        try:
            # 필수 필드 확인
            if not event.get('id') or not event.get('summary'):
                return None

            # 시작/종료 시간 파싱
            start_info = event.get('start', {})
            end_info = event.get('end', {})

            # All-day 이벤트 확인
            is_all_day = 'date' in start_info

            if is_all_day:
                # All-day 이벤트
                start_date = start_info.get('date')
                end_date = end_info.get('date')

                # Convert date string to datetime with time zone
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')

                # Set times for all-day events (start at 00:00, end at 23:59)
                start_datetime = datetime.combine(start_dt.date(), datetime.min.time(), tzinfo=timezone.utc)
                end_datetime = datetime.combine(end_dt.date(), datetime.max.time(), tzinfo=timezone.utc)

                event_data = {
                    'title': event.get('summary', '제목 없음'),
                    'description': event.get('description', ''),
                    'start_datetime': start_datetime.isoformat(),
                    'end_datetime': end_datetime.isoformat(),
                    'is_all_day': True
                }
            else:
                # 시간이 지정된 이벤트
                start_datetime_str = start_info.get('dateTime')
                end_datetime_str = end_info.get('dateTime')

                if not start_datetime_str or not end_datetime_str:
                    return None

                # ISO 형식 파싱 (already includes timezone)
                start_dt = datetime.fromisoformat(start_datetime_str.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_datetime_str.replace('Z', '+00:00'))

                event_data = {
                    'title': event.get('summary', '제목 없음'),
                    'description': event.get('description', ''),
                    'start_datetime': start_dt.isoformat(),
                    'end_datetime': end_dt.isoformat(),
                    'is_all_day': False
                }
            
            # 추가 메타데이터
            event_data.update({
                'location': event.get('location', ''),
                'attendees_count': len(event.get('attendees', [])),
                'event_status': event.get('status', 'confirmed'),
                'google_link': event.get('htmlLink', ''),
                'google_meet_link': self._extract_meet_link(event),
                'recurring': 'recurringEventId' in event
            })
            
            return event_data
            
        except Exception as e:
            print(f"❌ [GOOGLE SYNC] Error parsing event {event.get('id', 'unknown')}: {e}")
            return None
    
    def _extract_meet_link(self, event: Dict) -> str:
        """Google Meet 링크 추출"""
        try:
            # conferenceData에서 Meet 링크 찾기
            conference_data = event.get('conferenceData', {})
            if conference_data:
                entry_points = conference_data.get('entryPoints', [])
                for entry in entry_points:
                    if entry.get('entryPointType') == 'video':
                        return entry.get('uri', '')
            
            # description에서 Meet 링크 찾기
            description = event.get('description', '')
            if 'meet.google.com' in description:
                import re
                meet_pattern = r'https://meet\.google\.com/[a-zA-Z0-9-]+'
                match = re.search(meet_pattern, description)
                if match:
                    return match.group()
            
            return ''
            
        except Exception as e:
            print(f"❌ [GOOGLE SYNC] Error extracting Meet link: {e}")
            return ''

# 간편 사용을 위한 함수
def sync_google_calendar_for_user(user_id: str) -> Dict[str, Any]:
    """사용자의 Google Calendar 동기화 실행"""
    service = GoogleCalendarSyncService()
    return service.sync_user_events(user_id)

# 테스트용 함수
if __name__ == "__main__":
    # 테스트 실행
    import sys
    if len(sys.argv) > 1:
        user_id = sys.argv[1]
        print(f"🧪 Testing Google Calendar sync for user: {user_id}")
        result = sync_google_calendar_for_user(user_id)
        print(f"🧪 Test result: {json.dumps(result, indent=2, ensure_ascii=False)}")
    else:
        print("Usage: python google_calendar_sync.py <user_id>")