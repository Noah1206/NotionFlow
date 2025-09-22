"""
새로운 Notion 캘린더 동기화 서비스
간단하고 깔끔한 구조로 재작성
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

# Notion API 클래스
class NotionAPI:
    """Notion API 호출을 담당하는 간단한 클래스"""
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Notion-Version': '2022-06-28',
            'Content-Type': 'application/json'
        }
    
    def search_databases(self) -> List[Dict]:
        """모든 데이터베이스 검색"""
        try:
            import requests
            
            print(f"🔍 [NOTION API] Searching databases with token: {self.token[:20]}...")
            
            response = requests.post(
                f"{self.base_url}/search",
                headers=self.headers,
                json={
                    "filter": {
                        "property": "object",
                        "value": "database"
                    }
                },
                timeout=10
            )
            
            print(f"📡 [NOTION API] Response status: {response.status_code}")
            
            if response.status_code == 200:
                results = response.json().get('results', [])
                print(f"✅ [NOTION API] Found {len(results)} databases")
                return results
            else:
                print(f"❌ [NOTION API] Database search failed: {response.status_code}")
                print(f"❌ [NOTION API] Error response: {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ Error searching databases: {e}")
            return []
    
    def query_database(self, database_id: str, page_size: int = 50, start_cursor: str = None) -> Dict:
        """데이터베이스의 페이지들 조회 (페이지네이션 지원)"""
        try:
            import requests
            from datetime import datetime, timedelta
            
            # 최근 3개월 데이터만 가져오기 (성능 최적화)
            three_months_ago = (datetime.now() - timedelta(days=90)).isoformat()
            
            # 간단한 쿼리로 시작 (속성 필터 제거)
            query_payload = {
                "page_size": page_size,
                "sorts": [
                    {
                        "timestamp": "last_edited_time",
                        "direction": "descending"
                    }
                ]
            }
            
            if start_cursor:
                query_payload["start_cursor"] = start_cursor
            
            response = requests.post(
                f"{self.base_url}/databases/{database_id}/query",
                headers=self.headers,
                json=query_payload,
                timeout=30  # 타임아웃 증가
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'results': result.get('results', []),
                    'has_more': result.get('has_more', False),
                    'next_cursor': result.get('next_cursor'),
                    'total_count': len(result.get('results', []))
                }
            else:
                print(f"❌ Database query failed: {response.status_code}")
                print(f"Response: {response.text}")
                return {'results': [], 'has_more': False, 'next_cursor': None, 'total_count': 0}
                
        except Exception as e:
            print(f"❌ Error querying database: {e}")
            return {'results': [], 'has_more': False, 'next_cursor': None, 'total_count': 0}


# Notion 캘린더 동기화 클래스
class NotionCalendarSync:
    """Notion과 NotionFlow 캘린더 동기화"""
    
    def __init__(self):
        self.logger = logging.getLogger('NotionSync')
    
    def get_user_notion_token(self, user_id: str) -> Optional[str]:
        """사용자의 Notion 토큰 가져오기"""
        try:
            from utils.config import config
            from utils.uuid_helper import normalize_uuid
            
            # UUID 정규화 (통일된 형식 - 하이픈 없음)
            normalized_user_id = normalize_uuid(user_id)
            print(f"🔍 [TOKEN] Searching for user {user_id} (normalized: {normalized_user_id})")
            
            # 통일된 형식 사용 - 더 이상 여러 형식을 시도하지 않음
            print(f"🔍 [TOKEN] Using unified format: {normalized_user_id}")
            
            supabase = config.get_client_for_user(user_id)
            
            if not supabase:
                print("❌ Supabase client not available")
                return None
            
            # 1. calendar_sync_configs 테이블에서 검색 (새로운 주요 저장소)
            print(f"🔍 [TOKEN] Checking calendar_sync_configs for user {normalized_user_id}")
            config_result = supabase.table('calendar_sync_configs').select('*').eq(
                'user_id', normalized_user_id
            ).eq('platform', 'notion').execute()
            
            if config_result.data:
                print(f"📋 [TOKEN] Found config data: {config_result.data}")
                creds = config_result.data[0].get('credentials', {})
                if isinstance(creds, dict):
                    token = creds.get('access_token')
                    if token:
                        print(f"✅ [TOKEN] Found Notion token in calendar_sync_configs: {token[:20]}...")
                        return token
                    else:
                        print(f"⚠️ [TOKEN] No access_token in credentials: {creds.keys()}")
                else:
                    print(f"⚠️ [TOKEN] Credentials not in dict format: {type(creds)}")
            else:
                print(f"⚠️ [TOKEN] No calendar_sync_configs found for Notion user {normalized_user_id}")
            
            # 2. platform_connections 테이블에서 검색 (백업 - access_token 컬럼이 없을 수 있음)
            try:
                result = supabase.table('platform_connections').select('*').eq(
                    'user_id', user_id
                ).eq('platform', 'notion').eq('is_connected', True).execute()
                
                if result.data:
                    print(f"✅ Found Notion connection in platform_connections but no token field")
                    # platform_connections에는 토큰이 없으므로 oauth_tokens에서 다시 확인
            except:
                pass
            
            # 3. oauth_tokens 테이블에서 검색 (백업 - 외래키 제약조건 문제 있을 수 있음)
            try:
                oauth_result = supabase.table('oauth_tokens').select('access_token').eq(
                    'user_id', user_id
                ).eq('platform', 'notion').execute()
                
                if oauth_result.data and oauth_result.data[0].get('access_token'):
                    token = oauth_result.data[0].get('access_token')
                    print(f"✅ Found Notion token in oauth_tokens (backup): {token[:20]}...")
                    return token
            except Exception as oauth_error:
                print(f"⚠️ Could not check oauth_tokens (expected due to constraints): {oauth_error}")
            
            # 4. Session fallback (if database storage failed)
            try:
                from flask import session
                if session and session.get('platform_tokens', {}).get('notion', {}).get('access_token'):
                    token = session['platform_tokens']['notion']['access_token']
                    print(f"💾 Using session token for user {user_id}: {token[:20]}...")
                    return token
            except Exception as session_error:
                print(f"⚠️ Could not check session tokens: {session_error}")
            
            print("❌ No Notion token found in any table or session")
            return None
            
        except Exception as e:
            print(f"❌ Error getting Notion token: {e}")
            # Try session as final fallback
            try:
                from flask import session
                if session and session.get('platform_tokens', {}).get('notion', {}).get('access_token'):
                    token = session['platform_tokens']['notion']['access_token']
                    print(f"💾 Using session token fallback for user {user_id}: {token[:20]}...")
                    return token
            except:
                pass
            import traceback
            traceback.print_exc()
            return None
    
    def find_calendar_databases(self, notion_api: NotionAPI) -> List[Dict]:
        """캘린더/일정 관련 데이터베이스 찾기"""
        databases = notion_api.search_databases()
        calendar_dbs = []
        
        for db in databases:
            # 데이터베이스 제목 추출
            title = self._get_db_title(db)
            
            # 캘린더 관련 키워드 체크
            calendar_keywords = ['calendar', 'schedule', 'event', 'task', 'todo', 
                               '일정', '캘린더', '스케줄', '할일', '업무']
            
            if any(keyword in title.lower() for keyword in calendar_keywords):
                calendar_dbs.append(db)
                print(f"📅 Found calendar database: {title}")
            
            # 날짜 속성이 있는지 체크
            elif self._has_date_property(db):
                calendar_dbs.append(db)
                print(f"📅 Found database with date property: {title}")
        
        return calendar_dbs
    
    def get_user_calendar_id(self, user_id: str) -> Optional[str]:
        """Get the correct calendar_id for a user from the calendar_sync table"""
        try:
            from utils.config import config
            supabase = config.get_client_for_user(user_id)
            
            if not supabase:
                print(f"❌ [CALENDAR_ID] No Supabase client for user {user_id}")
                return None
            
            # Look up calendar_id from calendar_sync table
            sync_result = supabase.table('calendar_sync').select('calendar_id').eq('user_id', user_id).eq('platform', 'notion').eq('sync_status', 'active').execute()
            
            if sync_result.data:
                calendar_id = sync_result.data[0]['calendar_id']
                print(f"✅ [CALENDAR_ID] Found calendar_id for user {user_id}: {calendar_id}")
                return calendar_id
            else:
                print(f"⚠️ [CALENDAR_ID] No active calendar_sync found for user {user_id}")
                
                # Try to get user's first calendar as fallback
                calendars_result = supabase.table('calendars').select('id').eq('user_id', user_id).execute()
                if calendars_result.data:
                    calendar_id = calendars_result.data[0]['id']
                    print(f"ℹ️ [CALENDAR_ID] Using fallback calendar_id: {calendar_id}")
                    return calendar_id
                
                return None
                
        except Exception as e:
            print(f"❌ [CALENDAR_ID] Error getting calendar_id for user {user_id}: {e}")
            return None

    def sync_to_calendar(self, user_id: str, calendar_id: str = None) -> Dict[str, Any]:
        """Notion 데이터를 NotionFlow 캘린더로 동기화"""
        try:
            # If no calendar_id provided, get it from database
            if not calendar_id:
                calendar_id = self.get_user_calendar_id(user_id)
                if not calendar_id:
                    return {
                        'success': False,
                        'error': 'No calendar found for user. Please connect a calendar first.',
                        'synced_events': 0
                    }
            
            print(f"🔄 [NOTION] Starting Notion sync for user {user_id}, calendar {calendar_id}")
            
            # 1. Notion 토큰 확인
            token = self.get_user_notion_token(user_id)
            print(f"🔍 [NOTION] Token check result: {'Found' if token else 'Not found'}")
            
            if not token:
                print(f"❌ [NOTION] No token found for user {user_id}")
                return {
                    'success': False,
                    'error': 'No Notion token found',
                    'synced_events': 0
                }
            
            # 2. Notion API 초기화
            print(f"🔧 [NOTION] Initializing Notion API with token: {token[:20]}...")
            notion_api = NotionAPI(token)
            
            # 3. 캘린더 데이터베이스 찾기
            print(f"🔍 [NOTION] Searching for calendar databases...")
            calendar_dbs = self.find_calendar_databases(notion_api)
            print(f"📚 [NOTION] Found {len(calendar_dbs)} calendar databases")
            
            if not calendar_dbs:
                print(f"⚠️ [NOTION] No calendar databases found in Notion workspace")
                return {
                    'success': True,
                    'message': 'No calendar databases found in Notion',
                    'synced_events': 0
                }
            
            # 4. 각 데이터베이스에서 이벤트 추출 및 동기화
            total_synced = 0
            max_initial_load = 100  # 초기 로드 시 최대 이벤트 수 제한
            
            for db in calendar_dbs:
                db_id = db['id']
                db_title = self._get_db_title(db)
                
                print(f"📋 Processing database: {db_title}")
                
                # 페이지네이션으로 페이지들 조회
                start_cursor = None
                db_synced = 0
                
                while True:
                    # 한 번에 25개씩 처리 (API 부하 감소)
                    result = notion_api.query_database(db_id, page_size=25, start_cursor=start_cursor)
                    pages = result.get('results', [])
                    
                    if not pages:
                        break
                    
                    print(f"📄 Processing {len(pages)} pages from {db_title}")
                    
                    # 배치로 이벤트 처리
                    events_batch = []
                    for page in pages:
                        # Notion 페이지를 캘린더 이벤트로 변환
                        event = self._convert_page_to_event(page, calendar_id, user_id)
                        if event:
                            events_batch.append(event)
                    
                    # 배치 저장
                    for event in events_batch:
                        if self._save_event_to_calendar(event):
                            total_synced += 1
                            db_synced += 1
                            print(f"✅ Synced: {event['title']}")
                        else:
                            print(f"❌ Failed to save: {event['title']}")
                    
                    # 초기 로드 제한 확인
                    if total_synced >= max_initial_load:
                        print(f"⚡ Initial load limit reached ({max_initial_load} events). Remaining data will be synced in background.")
                        break
                    
                    # 다음 페이지가 있는지 확인
                    if not result.get('has_more', False):
                        break
                    
                    start_cursor = result.get('next_cursor')
                    
                    # CPU 부하 방지를 위한 짧은 대기
                    import time
                    time.sleep(0.1)
                
                print(f"📊 Database {db_title}: {db_synced} events synced")
                
                # 초기 로드 제한에 도달했으면 중단
                if total_synced >= max_initial_load:
                    break
            
            result = {
                'success': True,
                'synced_events': total_synced,
                'databases_processed': len(calendar_dbs),
                'limited_initial_load': total_synced >= max_initial_load,
                'message': f"Successfully synced {total_synced} events" + 
                          (f" (limited to {max_initial_load} for initial load)" if total_synced >= max_initial_load else "")
            }
            
            # 초기 로드 제한에 도달한 경우 백그라운드에서 나머지 동기화 예약
            if total_synced >= max_initial_load:
                try:
                    self._schedule_background_sync(user_id, calendar_id, access_token)
                    result['background_sync_scheduled'] = True
                except Exception as bg_error:
                    print(f"⚠️ Failed to schedule background sync: {bg_error}")
                    result['background_sync_scheduled'] = False
            
            return result
            
        except Exception as e:
            print(f"❌ Sync failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'synced_events': 0
            }
    
    def _get_db_title(self, database: Dict) -> str:
        """데이터베이스 제목 추출"""
        try:
            title_obj = database.get('title', [])
            if title_obj and len(title_obj) > 0:
                return title_obj[0].get('plain_text', 'Untitled')
            return 'Untitled'
        except:
            return 'Untitled'
    
    def _has_date_property(self, database: Dict) -> bool:
        """데이터베이스에 날짜 속성이 있는지 확인"""
        try:
            properties = database.get('properties', {})
            for prop_name, prop_data in properties.items():
                if prop_data.get('type') == 'date':
                    return True
            return False
        except:
            return False
    
    def _convert_page_to_event(self, page: Dict, calendar_id: str, user_id: str) -> Optional[Dict]:
        """Notion 페이지를 NotionFlow 이벤트로 변환"""
        try:
            properties = page.get('properties', {})
            
            # 1. 제목 추출
            title = self._extract_title(properties)
            if not title:
                return None
            
            # 2. 날짜 추출
            date_info = self._extract_date(properties)
            if not date_info:
                return None
            
            # 3. 설명 추출
            description = self._extract_description(properties)
            
            # 4. 날짜/시간 정규화
            start_datetime, end_datetime = self._normalize_datetime(date_info)
            
            # 5. NotionFlow 이벤트 생성
            event = {
                'calendar_id': calendar_id,
                'user_id': user_id,
                'title': title,
                'description': description or '',
                'start_datetime': start_datetime,
                'end_datetime': end_datetime,
                'all_day': date_info.get('all_day', False),
                'external_id': f"notion_{page['id']}",
                'external_platform': 'notion',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat(),
                'metadata': {
                    'notion_page_id': page['id'],
                    'notion_url': page.get('url', ''),
                    'last_edited': page.get('last_edited_time', '')
                }
            }
            
            return event
            
        except Exception as e:
            print(f"❌ Error converting page: {e}")
            return None
    
    def _extract_title(self, properties: Dict) -> Optional[str]:
        """페이지에서 제목 추출"""
        # 일반적인 제목 속성명들
        title_keys = ['Name', 'Title', '제목', 'Task', '작업', 'Event', '이벤트', '할일']
        
        for key in title_keys:
            if key in properties:
                prop = properties[key]
                if prop.get('type') == 'title' and prop.get('title'):
                    return prop['title'][0].get('plain_text', '')
                elif prop.get('type') == 'rich_text' and prop.get('rich_text'):
                    return prop['rich_text'][0].get('plain_text', '')
        
        # 첫 번째 title 타입 속성 사용
        for prop_name, prop_data in properties.items():
            if prop_data.get('type') == 'title' and prop_data.get('title'):
                return prop_data['title'][0].get('plain_text', '')
        
        return None
    
    def _extract_date(self, properties: Dict) -> Optional[Dict]:
        """페이지에서 날짜 정보 추출"""
        # 일반적인 날짜 속성명들
        date_keys = ['Date', 'Due', 'When', '날짜', '일정', 'Start', 'End', '시작', '종료', 'Deadline']
        
        for key in date_keys:
            if key in properties and properties[key].get('type') == 'date':
                date_prop = properties[key].get('date')
                if date_prop:
                    start = date_prop.get('start')
                    end = date_prop.get('end') or start
                    
                    if start:
                        # 시간 정보가 없으면 종일 이벤트
                        all_day = 'T' not in start
                        
                        return {
                            'start': start,
                            'end': end,
                            'all_day': all_day
                        }
        
        return None
    
    def _normalize_datetime(self, date_info: Dict) -> tuple:
        """날짜/시간을 정규화하고 검증"""
        try:
            start_str = date_info['start']
            end_str = date_info['end']
            
            print(f"🔧 [NORMALIZE] Input dates: start={start_str}, end={end_str}")
            
            # ISO 형식 파싱
            from datetime import datetime, timedelta
            import re
            
            # 시간 정보가 있는지 확인
            has_time = 'T' in start_str
            print(f"🔧 [NORMALIZE] Has time: {has_time}")
            
            if has_time:
                # 시간 정보가 있는 경우
                if '+' in start_str or 'Z' in start_str:
                    # 이미 timezone 정보가 있음
                    start_dt = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                    end_dt = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
                else:
                    # timezone 정보가 없으면 UTC로 가정
                    start_dt = datetime.fromisoformat(start_str + '+00:00')
                    end_dt = datetime.fromisoformat(end_str + '+00:00')
            else:
                # 날짜만 있는 경우 (종일 이벤트)
                start_dt = datetime.fromisoformat(start_str + 'T00:00:00+00:00')
                end_dt = datetime.fromisoformat(end_str + 'T23:59:59+00:00')
            
            print(f"🔧 [NORMALIZE] Parsed dates: start={start_dt}, end={end_dt}")
            
            # end_date가 start_date보다 이전이거나 같으면 수정
            if end_dt <= start_dt:
                print(f"⚠️ [NORMALIZE] End date is not after start date, fixing...")
                if not has_time:
                    # 종일 이벤트인 경우: 시작은 00:00, 끝은 23:59
                    start_dt = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
                    end_dt = start_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
                    print(f"📅 [NORMALIZE] All-day event fixed: {start_dt} → {end_dt}")
                else:
                    # 시간 이벤트인 경우: 최소 1시간 duration
                    end_dt = start_dt + timedelta(hours=1)
                    print(f"⏰ [NORMALIZE] Timed event fixed: {start_dt} → {end_dt}")
            
            # 최종 검증: end가 여전히 start와 같거나 이전이면 강제로 1분 추가
            if end_dt <= start_dt:
                print(f"🚨 [NORMALIZE] Final check failed, adding 1 minute")
                end_dt = start_dt + timedelta(minutes=1)
            
            # ISO 형식으로 반환
            result_start = start_dt.isoformat()
            result_end = end_dt.isoformat()
            
            print(f"✅ [NORMALIZE] Final result: {result_start} → {result_end}")
            return result_start, result_end
            
        except Exception as e:
            print(f"❌ Error normalizing datetime: {e}")
            print(f"📊 Error details: start={date_info.get('start')}, end={date_info.get('end')}")
            
            # 안전한 기본값 반환 (1시간 duration)
            now = datetime.now(timezone.utc)
            start_default = now.isoformat()
            end_default = (now + timedelta(hours=1)).isoformat()
            
            print(f"🔄 [NORMALIZE] Using safe defaults: {start_default} → {end_default}")
            return start_default, end_default
    
    def _extract_description(self, properties: Dict) -> Optional[str]:
        """페이지에서 설명 추출"""
        desc_keys = ['Description', 'Notes', '설명', '메모', 'Details', '상세', 'Content']
        
        for key in desc_keys:
            if key in properties:
                prop = properties[key]
                if prop.get('type') == 'rich_text' and prop.get('rich_text'):
                    texts = [t.get('plain_text', '') for t in prop['rich_text']]
                    return ' '.join(texts)
        
        return None
    
    def _normalize_uuid(self, uuid_str: str) -> str:
        """UUID를 DB 저장 형식으로 정규화 (하이픈 없는 형식)"""
        if not uuid_str:
            return uuid_str
            
        # 이메일이 UUID로 잘못 인식된 경우 처리
        if '@' in uuid_str:
            print(f"⚠️ [UUID] Email detected instead of UUID: {uuid_str}")
            # 이메일에서 UUID 생성 (일관성을 위해)
            import hashlib
            email_hash = hashlib.md5(uuid_str.encode()).hexdigest()
            # DB 저장 형식으로 변환 (하이픈 없음)
            uuid_str = email_hash
            print(f"🔄 [UUID] Generated UUID from email: {uuid_str}")
            return uuid_str
            
        # 하이픈 제거 후 재포맷
        clean_uuid = uuid_str.replace('-', '')
        
        # 32자리 hex 문자열이 아니면 에러
        if len(clean_uuid) != 32:
            print(f"⚠️ [UUID] Invalid UUID length: {len(clean_uuid)} (expected 32)")
            return uuid_str
            
        # DB 저장 형식으로 포맷 (하이픈 없음)
        formatted_uuid = clean_uuid.lower()
        
        if formatted_uuid != uuid_str.replace('-', '').lower():
            print(f"🔧 [UUID] Normalized: {uuid_str} → {formatted_uuid}")
            
        return formatted_uuid

    def _save_event_to_calendar(self, event: Dict) -> bool:
        """이벤트를 NotionFlow 캘린더에 저장"""
        try:
            from utils.config import config
            from flask import session
            
            # Use admin client to bypass RLS policies
            supabase = config.supabase_admin if hasattr(config, 'supabase_admin') and config.supabase_admin else config.get_client_for_user(event['user_id'])
            
            if not supabase:
                print("❌ Supabase client not available")
                return False
            
            # UUID 정규화
            user_id = self._normalize_uuid(event['user_id'])
            event['user_id'] = user_id  # 정규화된 UUID로 업데이트
            try:
                # Check if user exists in users table
                user_check = supabase.table('users').select('id').eq('id', user_id).execute()
                
                if not user_check.data:
                    print(f"📝 [SAVE] Creating user record for {user_id}")
                    # Get user email from session or platform tokens
                    user_email = session.get('user_email')
                    if not user_email:
                        # Try to get from platform tokens in session
                        platform_tokens = session.get('platform_tokens', {})
                        notion_info = platform_tokens.get('notion', {})
                        user_email = notion_info.get('user_email') or f'{user_id[:8]}@notionflow.app'
                    
                    # Create user using proper helper function
                    from utils.uuid_helper import ensure_auth_user_exists
                    if ensure_auth_user_exists(user_id, user_email, 'Notion User'):
                        print(f"✅ [SAVE] Created/verified user record: {user_id}")
                    else:
                        print(f"❌ [SAVE] Failed to create user record")
                        return False
                else:
                    print(f"✅ [SAVE] User already exists: {user_id}")
                    
            except Exception as user_e:
                print(f"❌ [SAVE] Critical error ensuring user exists: {user_e}")
                return False
            
            # 실제 데이터베이스 스키마에 맞게 이벤트 데이터 변환
            db_event = {
                'user_id': event['user_id'],
                'title': event['title'],
                'description': event.get('description', ''),
                'start_datetime': event['start_datetime'],
                'end_datetime': event['end_datetime'],
                'is_all_day': event.get('all_day', False),
                'category': 'notion',
                'priority': 'medium',  # TEXT 필드이므로 문자열 사용
                'status': 'confirmed',
                'source_platform': 'notion',  # NOT NULL 필드
                'external_id': event['external_id']
                # created_at, updated_at는 DEFAULT NOW()로 자동 설정
                # last_synced_at, sync_status 필드는 스키마에 없으므로 제거
            }
            
            # calendar_id 설정 (항상 설정되어야 함)
            if 'calendar_id' in event and event['calendar_id']:
                db_event['calendar_id'] = event['calendar_id']
                print(f"📋 [SAVE] Using calendar_id: {event['calendar_id']}")
            else:
                # calendar_id가 없으면 에러 로그 및 기본값 사용
                print(f"⚠️ [SAVE] Missing calendar_id in event: {event}")
                # source_calendar_id도 설정하여 백업
                if 'calendar_id' in event:
                    db_event['source_calendar_id'] = event['calendar_id']
                    db_event['source_calendar_name'] = 'Notion Calendar'
            
            # 최종 datetime 검증 및 수정
            from datetime import datetime, timedelta
            try:
                start_dt = datetime.fromisoformat(db_event['start_datetime'].replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(db_event['end_datetime'].replace('Z', '+00:00'))
                
                if end_dt <= start_dt:
                    print(f"🚨 [SAVE] Final validation failed: end_datetime ({end_dt}) <= start_datetime ({start_dt})")
                    end_dt = start_dt + timedelta(minutes=1)
                    db_event['end_datetime'] = end_dt.isoformat()
                    print(f"🔧 [SAVE] Fixed: new end_datetime = {db_event['end_datetime']}")
                    
            except Exception as e:
                print(f"⚠️ [SAVE] Datetime validation error: {e}")
            
            print(f"💾 [SAVE] Saving event: {db_event['title']}")
            print(f"📅 [SAVE] Dates: {db_event['start_datetime']} → {db_event['end_datetime']}")
            print(f"📋 [SAVE] Event data keys: {list(db_event.keys())}")
            print(f"📋 [SAVE] source_platform value: '{db_event.get('source_platform')}'")
            print(f"📋 [SAVE] Event data: {db_event}")
            
            # 중복 체크 (실제 스키마의 unique constraint에 맞춤: user_id, external_id, source_platform)
            try:
                existing = supabase.table('calendar_events').select('id').eq(
                    'user_id', event['user_id']
                ).eq('external_id', event['external_id']).eq(
                    'source_platform', 'notion'
                ).execute()
                
                if existing.data:
                    # 기존 이벤트 업데이트
                    print(f"🔄 [SAVE] Updating existing event: {db_event['title']}")
                    result = supabase.table('calendar_events').update({
                        'title': db_event['title'],
                        'description': db_event['description'],
                        'start_datetime': db_event['start_datetime'],
                        'end_datetime': db_event['end_datetime'],
                        'is_all_day': db_event['is_all_day'],
                        'updated_at': datetime.now().isoformat()  # 동적으로 현재 시간 설정
                    }).eq('id', existing.data[0]['id']).execute()
                    print(f"✅ Updated existing event: {db_event['title']}")
                else:
                    # 새 이벤트 생성
                    print(f"🆕 [SAVE] Creating new event: {db_event['title']}")
                    result = supabase.table('calendar_events').insert(db_event).execute()
                    print(f"✅ Created new event: {db_event['title']}")
                
                return bool(result.data)
            except Exception as save_error:
                print(f"❌ [SAVE] Error saving event '{db_event['title']}': {save_error}")
                return False
            
        except Exception as e:
            print(f"❌ Error saving event: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _schedule_background_sync(self, user_id: str, calendar_id: str, access_token: str):
        """백그라운드에서 나머지 데이터 동기화 예약"""
        try:
            import threading
            import time
            
            def background_sync():
                # 5초 후 백그라운드에서 나머지 동기화 시작
                time.sleep(5)
                print(f"🔄 Starting background sync for user {user_id}")
                
                try:
                    # 전체 동기화 실행 (제한 없이)
                    self._full_background_sync(user_id, calendar_id, access_token)
                except Exception as bg_error:
                    print(f"❌ Background sync failed: {bg_error}")
            
            # 백그라운드 스레드로 실행
            bg_thread = threading.Thread(target=background_sync, daemon=True)
            bg_thread.start()
            
            print(f"📅 Background sync scheduled for user {user_id}")
            
        except Exception as e:
            print(f"❌ Failed to schedule background sync: {e}")

    def _full_background_sync(self, user_id: str, calendar_id: str, access_token: str):
        """백그라운드에서 전체 데이터 동기화 (제한 없이)"""
        try:
            print(f"🔄 Starting full background sync for user {user_id}")
            
            # Notion API 초기화
            notion_api = NotionAPI(access_token)
            
            # 모든 캘린더 데이터베이스 조회
            calendar_dbs = notion_api.search_calendar_databases()
            
            if not calendar_dbs:
                print("📭 No calendar databases found in background sync")
                return
            
            total_synced = 0
            
            for db in calendar_dbs:
                db_id = db['id']
                db_title = self._get_db_title(db)
                
                print(f"📋 Background processing database: {db_title}")
                
                # 이미 동기화된 이벤트 확인 (중복 방지)
                start_cursor = None
                
                while True:
                    result = notion_api.query_database(db_id, page_size=50, start_cursor=start_cursor)
                    pages = result.get('results', [])
                    
                    if not pages:
                        break
                    
                    for page in pages:
                        # 중복 확인
                        if not self._is_event_already_synced(page, calendar_id, user_id):
                            event = self._convert_page_to_event(page, calendar_id, user_id)
                            
                            if event and self._save_event_to_calendar(event):
                                total_synced += 1
                                if total_synced % 10 == 0:  # 10개마다 로그
                                    print(f"🔄 Background synced {total_synced} additional events...")
                    
                    if not result.get('has_more', False):
                        break
                    
                    start_cursor = result.get('next_cursor')
                    
                    # 백그라운드 처리 시 더 긴 대기 (서버 부하 방지)
                    time.sleep(0.5)
            
            print(f"✅ Background sync completed: {total_synced} additional events synced")
            
        except Exception as e:
            print(f"❌ Full background sync failed: {e}")

    def _is_event_already_synced(self, notion_page: Dict, calendar_id: str, user_id: str) -> bool:
        """이벤트가 이미 동기화되었는지 확인"""
        try:
            from utils.config import config
            supabase = config.get_client_for_user(user_id)
            
            notion_page_id = notion_page.get('id', '')
            
            # 이미 동기화된 이벤트인지 확인 (실제 스키마 필드명 사용)
            existing = supabase.table('calendar_events').select('id').eq(
                'user_id', user_id
            ).eq('external_id', notion_page_id).eq('source_platform', 'notion').execute()
            
            return len(existing.data) > 0
            
        except Exception as e:
            print(f"❌ Error checking if event already synced: {e}")
            return False


# 싱글톤 인스턴스
notion_sync = NotionCalendarSync()