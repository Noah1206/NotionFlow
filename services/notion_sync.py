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
        # 문제 있는 데이터베이스 블랙리스트 (메모리 저장)
        self.blacklisted_databases = set()
    
    def search_databases(self) -> List[Dict]:
        """모든 데이터베이스 검색"""
        try:
            import requests
            
            # Searching Notion databases
            
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
            
            # 먼저 데이터베이스 스키마 확인 (방어 로직)
            try:
                schema_response = requests.get(
                    f"{self.base_url}/databases/{database_id}",
                    headers=self.headers,
                    timeout=10
                )
                if schema_response.status_code != 200:
                    print(f"⚠️ Database schema check failed for {database_id}: {schema_response.status_code}")
                    print(f"Response: {schema_response.text}")
                    return {'results': [], 'has_more': False, 'next_cursor': None, 'total_count': 0}
                    
                schema = schema_response.json()
                properties = schema.get('properties', {})
                print(f"✅ Database {database_id} has {len(properties)} properties")
                
            except Exception as schema_error:
                print(f"⚠️ Could not check database schema for {database_id}: {schema_error}")
                # Continue with query anyway
            
            # 최근 3개월 데이터만 가져오기 (성능 최적화)
            three_months_ago = (datetime.now() - timedelta(days=90)).isoformat()
            
            # 안전한 쿼리 - 스키마 확인 후 정렬 설정
            query_payload = {
                "page_size": page_size
            }
            
            # 스키마에서 날짜 프로퍼티가 있는지 확인하고 있으면 정렬에 사용
            try:
                if 'schema' in locals() and 'properties' in locals():
                    # 날짜 타입 프로퍼티 찾기
                    date_property_name = None
                    for prop_name, prop_data in properties.items():
                        if prop_data.get('type') == 'date':
                            date_property_name = prop_name
                            break
                    
                    if date_property_name:
                        # 날짜 프로퍼티로 정렬
                        query_payload["sorts"] = [
                            {
                                "property": date_property_name,
                                "direction": "descending"
                            }
                        ]
                        print(f"✅ Using date property '{date_property_name}' for sorting")
                    else:
                        # 날짜 프로퍼티가 없으면 timestamp로 정렬
                        query_payload["sorts"] = [
                            {
                                "timestamp": "last_edited_time",
                                "direction": "descending"
                            }
                        ]
                        # Using last_edited_time for sorting
                else:
                    # 스키마 확인 실패시 안전한 기본값
                    query_payload["sorts"] = [
                        {
                            "timestamp": "last_edited_time",
                            "direction": "descending"
                        }
                    ]
                    print("⚠️ Schema not available, using last_edited_time for sorting")
            except Exception as sort_error:
                print(f"⚠️ Error setting up sort: {sort_error}")
                # 정렬 없이 진행
                pass
            
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
                print(f"❌ Database query failed for {database_id}: {response.status_code}")
                print(f"Response: {response.text}")
                
                # 400 에러인 경우 더 자세한 분석
                if response.status_code == 400:
                    try:
                        error_data = response.json()
                        error_code = error_data.get('code')
                        error_message = error_data.get('message', '')
                        
                        if 'property' in error_message.lower() and 'date' in error_message.lower():
                            # Date property error detected
                            print(f"Error: {error_message}")
                            # 이 데이터베이스는 날짜 속성이 없거나 잘못된 구조
                        
                    except Exception as parse_error:
                        print(f"Could not parse error response: {parse_error}")
                
                return {'results': [], 'has_more': False, 'next_cursor': None, 'total_count': 0}
                
        except Exception as e:
            print(f"❌ Error querying database {database_id}: {e}")
            
            # 특정 에러 패턴 감지
            error_str = str(e).lower()
            if 'property' in error_str and ('date' in error_str or 'name' in error_str or 'id' in error_str):
                # Property access error
                print("This database may have an incompatible schema or may be inaccessible")
                # 문제 있는 데이터베이스는 블랙리스트에 추가
                self._add_to_blacklist(database_id, "property_access_error")
                
            elif 'not found' in error_str or '404' in error_str:
                print(f"🗑️ Database {database_id} not found - may have been deleted")
                self._add_to_blacklist(database_id, "not_found")
                
            elif 'unauthorized' in error_str or '403' in error_str:
                print(f"🔒 Database {database_id} access denied")
                self._add_to_blacklist(database_id, "access_denied")
                
            return {'results': [], 'has_more': False, 'next_cursor': None, 'total_count': 0}
    
    def _add_to_blacklist(self, database_id: str, reason: str):
        """문제 있는 데이터베이스를 블랙리스트에 추가"""
        self.blacklisted_databases.add(database_id)
        print(f"🚫 Database {database_id} added to blacklist (reason: {reason})")
    
    def _is_blacklisted(self, database_id: str) -> bool:
        """데이터베이스가 블랙리스트에 있는지 확인"""
        return database_id in self.blacklisted_databases
    
    def query_database_safe(self, database_id: str, page_size: int = 50, start_cursor: str = None) -> Dict:
        """안전한 데이터베이스 쿼리 - 블랙리스트 확인"""
        if self._is_blacklisted(database_id):
            print(f"⏭️ Skipping blacklisted database {database_id}")
            return {'results': [], 'has_more': False, 'next_cursor': None, 'total_count': 0}
        
        return self.query_database(database_id, page_size, start_cursor)


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
            # Searching for user token
            
            # 통일된 형식 사용 - 더 이상 여러 형식을 시도하지 않음
            # Using unified user format
            
            supabase = config.get_client_for_user(user_id)
            
            if not supabase:
                print("❌ Supabase client not available")
                return None
            
            # 1. calendar_sync_configs 테이블에서 검색 (새로운 주요 저장소)
            # Checking sync configs for user
            config_result = supabase.table('calendar_sync_configs').select('*').eq(
                'user_id', normalized_user_id
            ).eq('platform', 'notion').execute()
            
            if config_result.data:
                # Found sync config data
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
                    # Using session token
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
                    # Using token fallback
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
                # Found calendar database
            
            # 날짜 속성이 있는지 체크
            elif self._has_date_property(db):
                calendar_dbs.append(db)
                # Found database with date property
        
        return calendar_dbs
    
    def get_user_calendar_id(self, user_id: str) -> Optional[str]:
        """Get the correct calendar_id for a user from selected_calendars table"""
        try:
            from utils.config import config
            from utils.uuid_helper import normalize_uuid
            
            # Normalize user_id for consistency
            normalized_user_id = normalize_uuid(user_id)
            
            # Use admin client to bypass RLS
            supabase = config.supabase_admin if hasattr(config, 'supabase_admin') and config.supabase_admin else config.get_client_for_user(user_id)
            
            if not supabase:
                print(f"❌ [CALENDAR_ID] No Supabase client for user {user_id}")
                return None
            
            # Fallback: Use first available calendar for the user
            try:
                calendars_result = supabase.table('calendars').select('id, name').eq('owner_id', user_id).eq('is_active', True).limit(1).execute()
                if calendars_result.data:
                    calendar_id = calendars_result.data[0]['id']
                    calendar_name = calendars_result.data[0]['name']
                    print(f"✅ [CALENDAR_ID] Using first available calendar for user {user_id}: {calendar_name} ({calendar_id})")
                    return calendar_id
                else:
                    print(f"⚠️ [CALENDAR_ID] No active calendars found for user {user_id}")
                    return None
            except Exception as calendar_error:
                print(f"❌ [CALENDAR_ID] Error querying user_calendars: {calendar_error}")
                return None
                
        except Exception as e:
            print(f"❌ [CALENDAR_ID] Error getting calendar_id for user {user_id}: {e}")
            return None
    
    def _create_default_calendar(self, user_id: str, supabase) -> Optional[Dict]:
        """Create a default calendar for user if none exists"""
        try:
            import uuid
            from utils.uuid_helper import normalize_uuid
            
            normalized_user_id = normalize_uuid(user_id)
            
            default_calendar_data = {
                'id': str(uuid.uuid4()),
                'owner_id': normalized_user_id,
                'name': 'My Notion Calendar',
                'type': 'notion',
                'color': '#3B82F6',
                'description': 'Auto-created calendar for Notion sync',
                'is_active': True,
                'public_access': False,
                'allow_editing': True,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            result = supabase.table('calendars').insert(default_calendar_data).execute()
            
            if result.data:
                print(f"✅ [CALENDAR_ID] Created default calendar: {result.data[0]['id']}")
                return result.data[0]
            else:
                print(f"❌ [CALENDAR_ID] Failed to create default calendar")
                return None
                
        except Exception as e:
            print(f"❌ [CALENDAR_ID] Error creating default calendar: {e}")
            return None

    def sync_to_calendar(self, user_id: str, calendar_id: str = None) -> Dict[str, Any]:
        """Notion 데이터를 NotionFlow 캘린더로 동기화 - 배치 처리 최적화"""
        try:
            # If no calendar_id provided, get it from database
            if not calendar_id:
                calendar_id = self.get_user_calendar_id(user_id)
                if not calendar_id:
                    return {
                        'success': False,
                        'error': '동기화할 캘린더가 선택되지 않았습니다. API 키 연결 페이지에서 캘린더를 선택해주세요.',
                        'synced_events': 0
                    }

            print(f"🚀 [BATCH SYNC] Starting optimized Notion sync for user {user_id}, calendar {calendar_id}")

            # 1. Notion 토큰 확인
            token = self.get_user_notion_token(user_id)
            # Token validation complete

            if not token:
                print(f"❌ [NOTION] No token found for user {user_id}")
                return {
                    'success': False,
                    'error': 'No Notion token found',
                    'synced_events': 0
                }

            # 2. Notion API 초기화
            # Initializing Notion API
            notion_api = NotionAPI(token)

            # 3. 캘린더 데이터베이스 찾기
            # Searching calendar databases
            calendar_dbs = self.find_calendar_databases(notion_api)
            print(f"📚 [NOTION] Found {len(calendar_dbs)} calendar databases")

            if not calendar_dbs:
                print(f"⚠️ [NOTION] No calendar databases found in Notion workspace")
                return {
                    'success': True,
                    'message': 'No calendar databases found in Notion',
                    'synced_events': 0
                }

            # 4. 배치 처리로 이벤트 추출 및 동기화
            total_synced = 0
            max_initial_load = 50  # 배치 처리로 처리량 증가
            batch_size = 10  # 배치 크기
            batch_events = []  # 배치 저장용 임시 리스트

            for db in calendar_dbs:
                db_id = db['id']
                db_title = self._get_db_title(db)

                # Processing database in batches

                # 페이지네이션으로 페이지들 조회
                start_cursor = None
                db_synced = 0

                while True:
                    # 한 번에 25개씩 처리 (배치 처리로 효율성 증가)
                    result = notion_api.query_database_safe(db_id, page_size=25, start_cursor=start_cursor)
                    pages = result.get('results', [])

                    if not pages:
                        break

                    print(f"📄 Processing {len(pages)} pages from {db_title}")

                    # 배치 처리 방식으로 메모리 효율성 및 DB 연결 최적화
                    for page in pages:
                        # Notion 페이지를 캘린더 이벤트로 변환
                        event = self._convert_page_to_event(page, calendar_id, user_id)
                        if event:
                            batch_events.append(event)

                        # 배치가 찼거나 마지막 페이지면 저장
                        if len(batch_events) >= batch_size:
                            saved_count = self._save_events_batch(batch_events)
                            total_synced += saved_count
                            db_synced += saved_count
                            print(f"💾 [BATCH] Saved {saved_count}/{len(batch_events)} events")
                            batch_events.clear()  # 배치 초기화

                        # 초기 로드 제한 확인
                        if total_synced >= max_initial_load:
                            print(f"⚡ Initial load limit reached ({max_initial_load} events). Breaking early.")
                            break

                    # 초기 로드 제한 확인
                    if total_synced >= max_initial_load:
                        print(f"⚡ Initial load limit reached ({max_initial_load} events). Remaining data will be synced in background.")
                        break

                    # 다음 페이지가 있는지 확인
                    if not result.get('has_more', False):
                        break

                    start_cursor = result.get('next_cursor')

                # 남은 배치 이벤트들 저장
                if batch_events:
                    saved_count = self._save_events_batch(batch_events)
                    total_synced += saved_count
                    db_synced += saved_count
                    print(f"💾 [BATCH FINAL] Saved final {saved_count}/{len(batch_events)} events")
                    batch_events.clear()

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
                    self._schedule_background_sync(user_id, calendar_id, token)
                    result['background_sync_scheduled'] = True
                except Exception as bg_error:
                    print(f"⚠️ Failed to schedule background sync: {bg_error}")
                    result['background_sync_scheduled'] = False

            # PERFORMANCE OPTIMIZATION: 연동 직후 캐시 워밍업을 위한 백그라운드 프리로딩
            try:
                self._schedule_cache_warmup(user_id, calendar_id)
            except Exception as cache_error:
                print(f"⚠️ Cache warmup scheduling failed: {cache_error}")

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
        """페이지에서 날짜 정보 추출 - 안전한 방식으로 모든 날짜 타입 속성 확인"""
        try:
            # 먼저 일반적인 날짜 속성명들을 확인
            common_date_keys = ['Date', 'Due', 'When', '날짜', '일정', 'Start', 'End', '시작', '종료', 'Deadline', 'Created', 'Updated']
            
            for key in common_date_keys:
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
            
            # 일반적인 이름으로 찾지 못한 경우, 모든 속성을 순회하여 날짜 타입 찾기
            for prop_name, prop_data in properties.items():
                if prop_data.get('type') == 'date' and prop_data.get('date'):
                    date_prop = prop_data.get('date')
                    start = date_prop.get('start')
                    end = date_prop.get('end') or start
                    
                    if start:
                        all_day = 'T' not in start
                        print(f"✅ Found date property '{prop_name}': {start} → {end}")
                        
                        return {
                            'start': start,
                            'end': end,
                            'all_day': all_day
                        }
        
        except Exception as e:
            print(f"⚠️ Error extracting date from properties: {e}")
        
        return None
    
    def _normalize_datetime(self, date_info: Dict) -> tuple:
        """날짜/시간을 정규화하고 검증"""
        try:
            start_str = date_info['start']
            end_str = date_info['end']
            
            # ISO 형식 파싱
            from datetime import datetime, timedelta
            import re
            
            # 시간 정보가 있는지 확인
            has_time = 'T' in start_str
            
            if has_time:
                # 시간 정보가 있는 경우
                try:
                    # Handle various timezone formats
                    if start_str.endswith('Z'):
                        start_dt = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                        end_dt = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
                    elif '+' in start_str and start_str.count('+') == 1:
                        # Handle +09:00 format
                        start_dt = datetime.fromisoformat(start_str)
                        end_dt = datetime.fromisoformat(end_str)
                    elif '.' in start_str and start_str.endswith('+09:00'):
                        # Handle .000+09:00 format specifically
                        start_dt = datetime.fromisoformat(start_str)
                        end_dt = datetime.fromisoformat(end_str)
                    else:
                        # No timezone, assume UTC
                        start_dt = datetime.fromisoformat(start_str + '+00:00')
                        end_dt = datetime.fromisoformat(end_str + '+00:00')
                except ValueError as parse_error:
                    print(f"⚠️ [NORMALIZE] Datetime parsing error: {parse_error}")
                    # Fallback: try to parse without timezone and add UTC
                    base_start = start_str.split('+')[0].split('Z')[0]
                    base_end = end_str.split('+')[0].split('Z')[0]
                    start_dt = datetime.fromisoformat(base_start + '+00:00')
                    end_dt = datetime.fromisoformat(base_end + '+00:00')
            else:
                # 날짜만 있는 경우 (종일 이벤트)
                start_dt = datetime.fromisoformat(start_str + 'T00:00:00+00:00')
                end_dt = datetime.fromisoformat(end_str + 'T23:59:59+00:00')
            
            # Date validation
            
            # CRITICAL: Prevent constraint violations with multiple validation layers
            # Validate date order
            
            # Convert to UTC for reliable comparison if needed
            if start_dt.tzinfo and end_dt.tzinfo:
                start_utc = start_dt.astimezone(timezone.utc)
                end_utc = end_dt.astimezone(timezone.utc)
                # UTC conversion for comparison
            else:
                start_utc, end_utc = start_dt, end_dt
            
            # Primary fix: end must be after start
            if end_utc <= start_utc:
                # Fix constraint violation: end <= start
                if not has_time:
                    # All-day events: ensure 24-hour span
                    start_dt = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
                    end_dt = start_dt + timedelta(days=1)
                    # Fixed all-day event duration
                else:
                    # Timed events: minimum 1-hour duration
                    end_dt = start_dt + timedelta(hours=1)
                    # Fixed timed event duration
            
            # Secondary safety check: after fixing, verify again
            end_final_utc = end_dt.astimezone(timezone.utc) if end_dt.tzinfo else end_dt
            start_final_utc = start_dt.astimezone(timezone.utc) if start_dt.tzinfo else start_dt
            
            if end_final_utc <= start_final_utc:
                # Secondary fix: 2-hour duration
                end_dt = start_dt + timedelta(hours=2)
            
            # Final absolute guarantee: never allow equality
            if end_dt == start_dt:
                # Emergency fix: add 10 minutes
                end_dt = start_dt + timedelta(minutes=10)
            
            # ISO 형식으로 반환
            result_start = start_dt.isoformat()
            result_end = end_dt.isoformat()
            
            # Date normalization complete
            return result_start, result_end
            
        except Exception as e:
            print(f"❌ Error normalizing datetime: {e}")
            print(f"📊 Error details: start={date_info.get('start')}, end={date_info.get('end')}")
            
            # 안전한 기본값 반환 (1시간 duration)
            now = datetime.now(timezone.utc)
            start_default = now.isoformat()
            end_default = (now + timedelta(hours=1)).isoformat()
            
            # Using safe default dates
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
            # Generated UUID from email
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
            # UUID normalized
            pass
            
        return formatted_uuid

    def _get_user_primary_calendar_id(self, user_id: str) -> Optional[str]:
        """Get user's primary calendar ID (first calendar or default)"""
        try:
            from utils.config import config
            from utils.uuid_helper import normalize_uuid
            
            # Normalize user_id for consistency
            normalized_user_id = normalize_uuid(user_id)
            
            # Use admin client to bypass RLS
            supabase = config.supabase_admin if hasattr(config, 'supabase_admin') and config.supabase_admin else config.get_client_for_user(user_id)
            
            if not supabase:
                print(f"❌ [PRIMARY_CAL] No Supabase client for user {user_id}")
                return None
            
            # Get user's first calendar (using owner_id field)
            result = supabase.table('calendars').select('id').eq('owner_id', normalized_user_id).order('created_at').limit(1).execute()
            
            if result.data:
                calendar_id = result.data[0]['id']
                print(f"✅ [PRIMARY_CAL] Found primary calendar: {calendar_id}")
                return calendar_id
            else:
                print(f"⚠️ [PRIMARY_CAL] No calendar found for user {normalized_user_id}")
                return None
                
        except Exception as e:
            print(f"❌ [PRIMARY_CAL] Error getting primary calendar ID: {e}")
            return None

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
                    # Creating user record
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
                        # User record created/verified
                        pass
                    else:
                        print("Error: Failed to create user record")
                        return False
                else:
                    # User record verified
                    pass
            except Exception as user_e:
                print(f"Error: Critical user error - {user_e}")
                return False
            
            # 실제 데이터베이스 스키마에 맞게 이벤트 데이터 변환
            db_event = {
                'user_id': event['user_id'],
                'title': event['title'],
                'description': event.get('description', ''),
                'start_datetime': event['start_datetime'],
                'end_datetime': event['end_datetime'],
                'is_all_day': event.get('all_day', False),
                'category': 'notion',  # 실제 스키마 필드명
                'priority': 1,  # integer 타입 (0=low, 1=medium, 2=high)
                'status': 'confirmed',
                'source_platform': 'notion',  # 실제 스키마 필드명
                'external_id': event['external_id']  # 실제 스키마 필드명
                # created_at, updated_at는 DEFAULT NOW()로 자동 설정
            }
            
            # CRITICAL FIX: calendar_id 설정 (항상 설정되어야 함)
            if 'calendar_id' in event and event['calendar_id']:
                db_event['calendar_id'] = event['calendar_id']
                # Using event calendar_id
            else:
                # calendar_id가 없으면 사용자의 첫 번째 캘린더로 설정
                # Getting primary calendar for event
                
                # Get user's primary calendar
                primary_calendar_id = self._get_user_primary_calendar_id(user_id)
                if primary_calendar_id:
                    db_event['calendar_id'] = primary_calendar_id
                    # Using primary calendar
                else:
                    print(f"Warning: No calendar found for user {user_id}")
                    # Don't save orphaned events
                    return False
            
            # ULTRA-CRITICAL: Final datetime validation with timezone awareness
            from datetime import datetime, timedelta, timezone
            try:
                # Parse with proper timezone handling
                start_str = db_event['start_datetime']
                end_str = db_event['end_datetime']
                
                # Final date validation
                
                # Handle various timezone formats in the final check
                if start_str.endswith('Z'):
                    start_dt = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                    end_dt = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
                elif '+' in start_str or '-' in start_str[-6:]:
                    start_dt = datetime.fromisoformat(start_str)
                    end_dt = datetime.fromisoformat(end_str)
                else:
                    start_dt = datetime.fromisoformat(start_str + '+00:00')
                    end_dt = datetime.fromisoformat(end_str + '+00:00')
                
                # Date parsing validation
                
                # Convert to UTC for reliable comparison
                start_utc = start_dt.astimezone(timezone.utc) if start_dt.tzinfo else start_dt
                end_utc = end_dt.astimezone(timezone.utc) if end_dt.tzinfo else end_dt
                
                # UTC time comparison validation
                
                # ABSOLUTE CONSTRAINT VIOLATION CHECK
                if end_utc <= start_utc:
                    # Critical: fixing constraint violation
                    
                    # Force minimum duration based on event type
                    if db_event.get('is_all_day', False):
                        # All-day: 24 hours minimum
                        end_dt = start_dt + timedelta(days=1)
                        # Fixed all-day event duration
                    else:
                        # Timed: 2 hours minimum (extra safe)
                        end_dt = start_dt + timedelta(hours=2)
                        # Fixed timed event duration
                    
                    db_event['end_datetime'] = end_dt.isoformat()
                    # Constraint violation fixed
                
                # Triple-check: verify the fix worked
                final_start = datetime.fromisoformat(db_event['start_datetime'].replace('Z', '+00:00') if 'Z' in db_event['start_datetime'] else db_event['start_datetime'])
                final_end = datetime.fromisoformat(db_event['end_datetime'].replace('Z', '+00:00') if 'Z' in db_event['end_datetime'] else db_event['end_datetime'])
                
                if final_start.tzinfo:
                    final_start_utc = final_start.astimezone(timezone.utc)
                    final_end_utc = final_end.astimezone(timezone.utc)
                else:
                    final_start_utc, final_end_utc = final_start, final_end
                
                if final_end_utc <= final_start_utc:
                    # Using emergency time fallback
                    now = datetime.now(timezone.utc)
                    db_event['start_datetime'] = now.isoformat()
                    db_event['end_datetime'] = (now + timedelta(hours=3)).isoformat()
                
                # Event times validated
                    
            except Exception as e:
                print(f"Error: Date validation failed - {e}")
                # Emergency fallback: guaranteed safe times
                now = datetime.now(timezone.utc)
                db_event['start_datetime'] = now.isoformat()
                db_event['end_datetime'] = (now + timedelta(hours=3)).isoformat()
                # Emergency fallback applied
            
            # Saving event to database
            
            # 중복 체크 (실제 스키마의 unique constraint에 맞춤: user_id, external_id, source_platform)
            try:
                existing = supabase.table('calendar_events').select('id').eq(
                    'user_id', event['user_id']
                ).eq('external_id', event['external_id']).eq(
                    'source_platform', 'notion'
                ).execute()
                
                if existing.data:
                    # 기존 이벤트 업데이트
                    # Updating existing event
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
                    # Creating new event
                    result = supabase.table('calendar_events').insert(db_event).execute()
                    print(f"✅ Created new event: {db_event['title']}")
                
                return bool(result.data)
            except Exception as save_error:
                print(f"Error saving event '{db_event['title']}': {save_error}")
                return False
            
        except Exception as e:
            print(f"❌ Error saving event: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _save_events_batch(self, events: List[Dict]) -> int:
        """배치로 이벤트들을 NotionFlow 캘린더에 저장 - DB 연결 최적화"""
        if not events:
            return 0

        try:
            from utils.config import config
            from datetime import datetime, timezone

            # Use admin client to bypass RLS policies
            supabase = config.supabase_admin if hasattr(config, 'supabase_admin') and config.supabase_admin else config.get_client_for_user(events[0]['user_id'])

            if not supabase:
                print("❌ [BATCH] Supabase client not available")
                return 0

            saved_count = 0
            batch_data = []
            update_data = []

            print(f"💾 [BATCH] Processing {len(events)} events")

            # 1. 중복 체크를 위한 기존 이벤트 조회 (한 번의 쿼리로)
            user_id = self._normalize_uuid(events[0]['user_id'])
            external_ids = [event['external_id'] for event in events]

            existing_result = supabase.table('calendar_events').select('id, external_id').eq(
                'user_id', user_id
            ).eq('source_platform', 'notion').in_('external_id', external_ids).execute()

            existing_external_ids = {item['external_id']: item['id'] for item in existing_result.data} if existing_result.data else {}

            print(f"🔍 [BATCH] Found {len(existing_external_ids)} existing events to update")

            # 2. 이벤트별로 처리 (새로 생성할 것과 업데이트할 것 분리)
            for event in events:
                try:
                    # UUID 정규화
                    user_id = self._normalize_uuid(event['user_id'])
                    event['user_id'] = user_id

                    # CRITICAL FIX: calendar_id 반드시 설정
                    if not event.get('calendar_id'):
                        primary_calendar_id = self._get_user_primary_calendar_id(user_id)
                        if primary_calendar_id:
                            event['calendar_id'] = primary_calendar_id
                            print(f"🎯 [BATCH] Auto-assigned calendar_id: {primary_calendar_id}")
                        else:
                            print(f"⚠️ [BATCH] No calendar found for user {user_id}, skipping event")
                            continue

                    # 실제 데이터베이스 스키마에 맞게 이벤트 데이터 변환
                    db_event = {
                        'user_id': event['user_id'],
                        'calendar_id': event['calendar_id'],  # CRITICAL: 항상 설정
                        'title': event['title'],
                        'description': event.get('description', ''),
                        'start_datetime': event['start_datetime'],
                        'end_datetime': event['end_datetime'],
                        'is_all_day': event.get('all_day', False),
                        'category': 'notion',
                        'priority': 1,
                        'status': 'confirmed',
                        'source_platform': 'notion',
                        'external_id': event['external_id']
                    }

                    # 기존 이벤트인지 확인
                    if event['external_id'] in existing_external_ids:
                        # 업데이트용 데이터 준비
                        db_event['updated_at'] = datetime.now().isoformat()
                        update_data.append({
                            'id': existing_external_ids[event['external_id']],
                            'data': db_event
                        })
                    else:
                        # 새 이벤트용 데이터 준비
                        batch_data.append(db_event)

                except Exception as event_error:
                    print(f"❌ [BATCH] Error processing event {event.get('title', 'Unknown')}: {event_error}")
                    continue

            # 3. 배치 삽입 (새 이벤트들)
            if batch_data:
                try:
                    insert_result = supabase.table('calendar_events').insert(batch_data).execute()
                    inserted_count = len(insert_result.data) if insert_result.data else 0
                    saved_count += inserted_count
                    print(f"✅ [BATCH INSERT] Created {inserted_count} new events")
                except Exception as insert_error:
                    print(f"❌ [BATCH INSERT] Failed: {insert_error}")

            # 4. 배치 업데이트 (기존 이벤트들) - 개별적으로 처리
            updated_count = 0
            for update_item in update_data:
                try:
                    # Remove id and updated_at from data for update
                    update_data_clean = {k: v for k, v in update_item['data'].items() if k not in ['id', 'created_at']}
                    update_result = supabase.table('calendar_events').update(update_data_clean).eq('id', update_item['id']).execute()
                    if update_result.data:
                        updated_count += 1
                except Exception as update_error:
                    print(f"❌ [BATCH UPDATE] Failed for event {update_item['id']}: {update_error}")

            saved_count += updated_count
            print(f"✅ [BATCH UPDATE] Updated {updated_count} existing events")

            print(f"💾 [BATCH COMPLETE] Total saved: {saved_count}/{len(events)} events")
            return saved_count

        except Exception as e:
            print(f"❌ [BATCH] Error saving batch: {e}")
            import traceback
            traceback.print_exc()
            return 0

    def _schedule_cache_warmup(self, user_id: str, calendar_id: str):
        """PERFORMANCE: 캐시 워밍업을 위한 백그라운드 프리로딩 예약"""
        try:
            import threading
            import time

            def cache_warmup_worker():
                try:
                    # 3초 후 캐시 워밍업 실행 (UI 응답성 확보)
                    time.sleep(3)
                    print(f"🚀 [CACHE WARMUP] Starting for user {user_id}")

                    # 캐시용 이벤트 조회 및 저장
                    from utils.config import config
                    supabase = config.supabase_admin if hasattr(config, 'supabase_admin') and config.supabase_admin else config.get_client_for_user(user_id)

                    if supabase:
                        # 향후 30일간의 이벤트를 미리 캐시
                        from datetime import datetime, timedelta, timezone
                        start_date = datetime.now(timezone.utc)
                        end_date = start_date + timedelta(days=30)

                        # 캐시 테이블에 이벤트 정보 저장 (미래 확장용)
                        cache_result = supabase.table('calendar_events').select('id, title, start_datetime, end_datetime').eq(
                            'user_id', user_id
                        ).eq('calendar_id', calendar_id).gte(
                            'start_datetime', start_date.isoformat()
                        ).lte(
                            'start_datetime', end_date.isoformat()
                        ).execute()

                        cached_count = len(cache_result.data) if cache_result.data else 0
                        print(f"✅ [CACHE WARMUP] Cached {cached_count} events for faster access")

                except Exception as warmup_error:
                    print(f"⚠️ [CACHE WARMUP] Error: {warmup_error}")

            # 백그라운드 스레드로 실행
            cache_thread = threading.Thread(target=cache_warmup_worker, daemon=True)
            cache_thread.start()
            print(f"🎯 [CACHE WARMUP] Scheduled for user {user_id}")

        except Exception as e:
            print(f"❌ [CACHE WARMUP] Scheduling failed: {e}")

    def _schedule_background_sync(self, user_id: str, calendar_id: str, access_token: str):
        """백그라운드에서 나머지 데이터 동기화 예약"""
        try:
            import threading
            import time
            
            def background_sync():
                # 5초 후 백그라운드에서 나머지 동기화 시작
                time.sleep(5)
                # Starting background sync
                
                try:
                    # 전체 동기화 실행 (제한 없이)
                    self._full_background_sync(user_id, calendar_id, access_token)
                except Exception as bg_error:
                    print(f"❌ Background sync failed: {bg_error}")
            
            # 백그라운드 스레드로 실행
            bg_thread = threading.Thread(target=background_sync, daemon=True)
            bg_thread.start()
            
            # Background sync scheduled
            
        except Exception as e:
            print(f"❌ Failed to schedule background sync: {e}")

    def _full_background_sync(self, user_id: str, calendar_id: str, access_token: str):
        """백그라운드에서 전체 데이터 동기화 (제한 없이)"""
        try:
            # Starting full background sync
            
            # Notion API 초기화
            notion_api = NotionAPI(access_token)
            
            # 모든 캘린더 데이터베이스 조회
            calendar_dbs = self.find_calendar_databases(notion_api)
            
            if not calendar_dbs:
                print("📭 No calendar databases found in background sync")
                return
            
            total_synced = 0
            
            for db in calendar_dbs:
                db_id = db['id']
                db_title = self._get_db_title(db)
                
                # Background processing database
                
                # 이미 동기화된 이벤트 확인 (중복 방지)
                start_cursor = None
                
                while True:
                    result = notion_api.query_database_safe(db_id, page_size=50, start_cursor=start_cursor)
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
                                    pass  # Background sync progress
                    
                    if not result.get('has_more', False):
                        break
                    
                    start_cursor = result.get('next_cursor')
                    
                    # 백그라운드 처리 시 메모리 정리 및 부하 방지
                    import gc
                    gc.collect()
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