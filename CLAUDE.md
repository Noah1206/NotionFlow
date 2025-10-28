# CLAUDE.md - NotionFlow Project Guidelines

> 이 문서는 NotionFlow 프로젝트의 코드 작성, 수정 및 개발 시 준수해야 할 모든 규칙과 가이드라인을 정의합니다.

## 📋 목차

1. [프로젝트 컨텍스트](#프로젝트-컨텍스트)
2. [코딩 표준](#코딩-표준)
3. [아키텍처 원칙](#아키텍처-원칙)
4. [개발 워크플로우](#개발-워크플로우)
5. [보안 가이드라인](#보안-가이드라인)
6. [성능 최적화](#성능-최적화)
7. [테스팅 전략](#테스팅-전략)
8. [문서화 규칙](#문서화-규칙)

---

## ⚠️ 최우선 규칙 - 반드시 준수!

### ✅ 스키마 불일치 해결됨: 실제 DB 확인 완료
**최종 확인 결과**:
- **실제 Supabase DB**: calendars 테이블은 `owner_id` 컬럼 사용 ✅
- **Python 코드**: `owner_id` 사용 중 ✅ (올바름)
- **기존 master_schema.sql**: `user_id`로 잘못 정의됨 ❌ (수정됨)

**해결 완료**:
1. ✅ 실제 DB 스키마 확인 (26개 테이블)
2. ✅ `updated_master_schema.sql` 생성 (정확한 스키마)
3. ✅ CLAUDE.md 업데이트 (올바른 컬럼명 반영)

### ✅ Google Calendar OAuth 2단계 모달 수정 완료 (2024-10-05)
**수정된 사항**:
- **Google Calendar 카드 비활성화 로직 복원**: 캘린더가 없을 때 모든 플랫폼 카드 비활성화
- **올바른 2단계 모달 플로우 구현**:
  - 1단계: 사용자의 Google 캘린더 선택 (구글 계정에 있는 캘린더들)
  - 2단계: NotionFlow 캘린더 선택 (연결할 대상 캘린더)
- **캘린더 자동 생성 로직 완전 제거**: 사용자가 직접 캘린더를 생성해야 함

**수정된 파일들**:
1. `frontend/static/js/google-calendar-manager.js`: 2단계 모달 플로우 구현
2. `frontend/templates/dashboard-api-keys.html`: 캘린더 없을 때 카드 비활성화 로직
3. `frontend/routes/oauth_routes.py`: 자동 캘린더 생성 로직 제거 (2곳)
4. `frontend/app.py`: 자동 캘린더 생성 로직 제거 (2곳)

## ⚠️ 최우선 규칙 - 반드시 준수!

### 절대 준수사항
1. **코드 수정 시 무조건 에러 처리 추가**
   - try-except 블록 필수
   - 에러 로깅 필수
   - 사용자에게 친절한 에러 메시지 반환

2. **Supabase 쿼리 시 항상 .execute() 추가**
   ```python
   # ✅ GOOD
   result = supabase.from_('users').select('*').execute()

   # ❌ BAD
   result = supabase.from_('users').select('*')
   ```

3. **환경변수는 반드시 .env 파일에서 관리**
   - 하드코딩 절대 금지
   - `os.environ.get()` 또는 `config.py` 사용

4. **세션 관리 시 user_id는 항상 문자열(TEXT) 타입**
   ```python
   # ✅ GOOD
   user_id = session.get('user_id')  # 문자열로 저장

   # ❌ BAD
   user_id = uuid.UUID(session.get('user_id'))  # UUID 변환 금지
   ```

5. **API 응답은 항상 일관된 형식**
   ```python
   # 성공 응답
   return jsonify({"success": True, "data": data}), 200

   # 에러 응답
   return jsonify({"success": False, "error": "Error message"}), 400
   ```

6. **✅ calendars 테이블 컬럼명 확인 완료**
   ```python
   # ✅ 실제 DB 확인 결과: calendars 테이블은 owner_id 사용!
   # Python 코드가 올바르게 작성되어 있었음

   # ✅ 올바른 사용법 (실제 DB 기준)
   supabase.from_('calendars').select('*').eq('owner_id', normalized_id)

   # 다른 테이블들은 user_id 사용
   supabase.from_('calendar_events').select('*').eq('user_id', user_id)
   supabase.from_('sync_status').select('*').eq('user_id', user_id)
   ```

7. **UUID 정규화 함수 사용**
   ```python
   from utils.uuid_helper import normalize_uuid

   # 항상 UUID 정규화 후 사용
   user_id = session.get('user_id')
   normalized_id = normalize_uuid(user_id)  # 하이픈 포함 형식으로 통일

   # DB 저장 시
   calendar_data = {
       'owner_id': normalized_id,  # ✅ calendars 테이블은 owner_id 사용!
       'name': 'My Calendar'
   }
   ```

8. **세션에서 user_id 가져오기**
   ```python
   from utils.auth_manager import AuthManager

   # 권장: AuthManager 사용
   user_id = AuthManager.get_current_user_id()

   # 또는 직접 세션에서
   user_id = session.get('user_id')  # 항상 문자열
   ```

9. **✅ 크로스 플랫폼 버튼 상태 격리 원칙 (2024-10-05 수정)**
   ```javascript
   // ✅ GOOD: 플랫폼별 버튼 제거 시 OAuth 상태 확인
   if (platformName === 'google' && !platform.oauth_connected) {
       const googleDisconnectBtn = platformCard.querySelector('.google-disconnect-btn');
       if (googleDisconnectBtn) {
           googleDisconnectBtn.remove();
           console.log('🗑️ [GOOGLE] OAuth 토큰이 없으므로 연결해제 버튼 제거');
       }
   }

   // ❌ BAD: 다른 플랫폼 상태 업데이트 시 무조건 제거
   if (platformName === 'google') {
       const googleDisconnectBtn = platformCard.querySelector('.google-disconnect-btn');
       if (googleDisconnectBtn) {
           googleDisconnectBtn.remove(); // OAuth 상태 확인 없이 제거
       }
   }
   ```

   **문제**: Apple Calendar OAuth 시 `updateAllPlatformStatus()` 호출 → Google Calendar 상태 검사 → `enabled: false` 확인 → Google 연결해제 버튼 제거

   **해결**: OAuth 토큰(`oauth_connected`)이 있으면 일시적 비활성화 상태여도 버튼 유지

10. **Google Calendar OAuth 2단계 모달 플로우 준수 (2024-10-05 추가)**
   ```javascript
   // ✅ 올바른 2단계 플로우
   // 1단계: Google 캘린더 선택 (사용자 계정의 구글 캘린더들)
   await this.showGoogleCalendarSelection();

   // 2단계: NotionFlow 캘린더 선택 (연결할 대상)
   await this.showNotionFlowCalendarSelection();

   // ❌ 잘못된 플로우: 바로 NotionFlow 캘린더 선택하거나 자동 캘린더 생성
   ```

10. **캘린더 자동 생성 금지 (2024-10-05 추가)**
    ```python
    # ✅ 올바른 처리: 캘린더가 없으면 에러 반환
    if not user_calendars.data:
        print(f"⚠️ No calendars found for user {user_id} - user must create one first")
        return jsonify({'error': 'No calendars found. Please create a calendar first.'}), 400

    # ❌ 금지: 자동 캘린더 생성
    # new_calendar = {...}
    # supabase.table('calendars').insert(new_calendar).execute()
    ```

11. **플랫폼 카드 활성화 조건 (2024-10-05 추가)**
    ```javascript
    // ✅ 캘린더가 없으면 모든 플랫폼 카드 비활성화
    if (totalCalendars === 0) {
        disableAllPlatformCards();
        showNoCalendarNotice();
        return;
    }

    // ❌ 금지: 캘린더 없이 플랫폼 카드 활성화
    ```

12. **플랫폼별 버튼 상태 격리 (2024-10-05 추가)**
    ```javascript
    // ✅ 플랫폼별 버튼 제거는 해당 플랫폼일 때만
    if (platformName === 'google') {
        const googleDisconnectBtn = platformCard.querySelector('.google-disconnect-btn');
        if (googleDisconnectBtn) {
            googleDisconnectBtn.remove();
        }
    }

    // ❌ 금지: 모든 플랫폼 업데이트 시 특정 플랫폼 버튼 무차별 제거
    const googleDisconnectBtn = platformCard.querySelector('.google-disconnect-btn');
    if (googleDisconnectBtn) {
        googleDisconnectBtn.remove(); // 다른 플랫폼에도 영향
    }
    ```

---

## 🎯 프로젝트 컨텍스트

### 프로젝트 개요
- **이름**: NotionFlow
- **목적**: Notion과 다양한 캘린더 플랫폼 간의 원활한 동기화
- **주요 기술**: Flask, Supabase, PostgreSQL, OAuth 2.0
- **배포 환경**: Railway, Google Cloud Run, Docker

### 핵심 기능
1. **플랫폼 통합**: Google Calendar, Apple Calendar, Outlook, Notion, Slack
2. **실시간 동기화**: 양방향 자동 동기화
3. **보안 인증**: OAuth 2.0 기반 안전한 인증
4. **사용자 경험**: 직관적이고 반응형 UI

---

## 💻 코딩 표준

### Python (Backend)
```python
# ✅ GOOD: 명확한 함수명과 타입 힌트
def sync_calendar_events(
    user_id: str,
    calendar_id: str,
    start_date: datetime,
    end_date: datetime
) -> Dict[str, Any]:
    """
    캘린더 이벤트를 동기화합니다.

    Args:
        user_id: 사용자 고유 ID
        calendar_id: 캘린더 고유 ID
        start_date: 동기화 시작 날짜
        end_date: 동기화 종료 날짜

    Returns:
        동기화 결과를 담은 딕셔너리
    """
    pass

# ❌ BAD: 불명확한 이름과 타입 힌트 없음
def sync(u, c, s, e):
    pass
```

### JavaScript (Frontend)
```javascript
// ✅ GOOD: ES6+ 문법, async/await 사용
class CalendarManager {
    constructor(apiKey) {
        this.apiKey = apiKey;
        this.baseUrl = '/api/v1';
    }

    async syncEvents(calendarId) {
        try {
            const response = await fetch(`${this.baseUrl}/sync/${calendarId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.apiKey}`
                }
            });

            if (!response.ok) {
                throw new Error(`Sync failed: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Sync error:', error);
            throw error;
        }
    }
}

// ❌ BAD: 콜백 지옥, var 사용
function sync(id) {
    var self = this;
    $.ajax({
        url: '/sync',
        success: function(data) {
            // ...
        }
    });
}
```

### 명명 규칙
- **Python**: snake_case (함수, 변수), PascalCase (클래스)
- **JavaScript**: camelCase (함수, 변수), PascalCase (클래스)
- **SQL**: snake_case (테이블, 컬럼)
- **API 엔드포인트**: kebab-case (`/api/calendar-events`)
- **환경 변수**: UPPER_SNAKE_CASE (`SUPABASE_URL`)

---

## 🏗️ 아키텍처 원칙

### 1. 레이어드 아키텍처
```
┌─────────────────────────────────┐
│     Frontend (Templates/JS)     │
├─────────────────────────────────┤
│      API Routes (Flask)         │
├─────────────────────────────────┤
│     Services (Business Logic)   │
├─────────────────────────────────┤
│     Database (Supabase)         │
└─────────────────────────────────┘
```

### 2. 서비스 분리 원칙
- **각 플랫폼별 독립 서비스**: `google_calendar_service.py`, `notion_service.py`
- **공통 기능 추상화**: `base_calendar_service.py`
- **유틸리티 분리**: `utils/` 디렉토리에 공통 기능

### 3. 에러 처리 패턴
```python
# 모든 서비스는 일관된 에러 처리
class CalendarSyncError(Exception):
    """캘린더 동기화 관련 에러"""
    pass

def sync_with_retry(func, max_retries=3):
    """재시도 로직을 포함한 동기화"""
    for attempt in range(max_retries):
        try:
            return func()
        except CalendarSyncError as e:
            if attempt == max_retries - 1:
                logger.error(f"Sync failed after {max_retries} attempts: {e}")
                raise
            time.sleep(2 ** attempt)  # 지수 백오프
```

---

## 🔄 개발 워크플로우

### 1. 기능 추가 시
1. **요구사항 분석**: PROJECT_OVERVIEW.md 참조
2. **DB 스키마 확인**: `database/master_schema.sql` 검토
3. **서비스 레이어 구현**: `backend/services/`
4. **API 라우트 추가**: `frontend/routes/`
5. **프론트엔드 통합**: `frontend/static/js/`
6. **테스트 작성**: 단위 테스트 및 통합 테스트
7. **문서 업데이트**: API 문서 및 README

### 2. 버그 수정 시
1. **이슈 재현**: 로컬 환경에서 버그 재현
2. **로그 분석**: `logs/` 디렉토리 확인
3. **근본 원인 파악**: 디버거 사용
4. **수정 및 테스트**: 회귀 테스트 포함
5. **배포 전 검증**: 스테이징 환경 테스트

### 3. 코드 리뷰 체크리스트
- [ ] 타입 힌트 추가 (Python)
- [ ] 에러 처리 구현
- [ ] 로깅 추가
- [ ] 보안 검증 (SQL 인젝션, XSS)
- [ ] 성능 영향 검토
- [ ] 테스트 커버리지 80% 이상
- [ ] 문서 업데이트

---

## 🔐 보안 가이드라인

### 1. 인증 및 인가
```python
# 모든 API 엔드포인트는 인증 필요
from functools import wraps
from flask import request, jsonify

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or not verify_token(token):
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/sync')
@require_auth
def sync_endpoint():
    pass
```

### 2. 민감 정보 관리
- **환경 변수 사용**: 하드코딩 금지
- **시크릿 로테이션**: 정기적인 API 키 갱신
- **.env 파일**: `.gitignore`에 포함
- **암호화**: 민감 데이터 저장 시 암호화

### 3. SQL 인젝션 방지
```python
# ✅ GOOD: 파라미터화된 쿼리
cursor.execute(
    "SELECT * FROM users WHERE id = %s",
    (user_id,)
)

# ❌ BAD: 문자열 연결
cursor.execute(
    f"SELECT * FROM users WHERE id = {user_id}"
)
```

---

## ⚡ 성능 최적화

### 1. 데이터베이스 최적화
- **인덱스 활용**: 자주 조회하는 컬럼에 인덱스
- **N+1 문제 방지**: JOIN 활용
- **커넥션 풀링**: 데이터베이스 연결 재사용
- **배치 처리**: 대량 데이터 처리 시 배치 사용

### 2. 캐싱 전략
```python
from functools import lru_cache
import redis

# 메모리 캐싱
@lru_cache(maxsize=100)
def get_user_calendars(user_id: str):
    return fetch_from_db(user_id)

# Redis 캐싱 (선택적)
def get_cached_events(calendar_id: str):
    cache_key = f"events:{calendar_id}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    events = fetch_events_from_api(calendar_id)
    redis_client.setex(cache_key, 3600, json.dumps(events))
    return events
```

### 3. 비동기 처리
```python
# 긴 작업은 백그라운드로
from celery import Celery

celery_app = Celery('notionflow')

@celery_app.task
def sync_all_calendars(user_id: str):
    """백그라운드에서 모든 캘린더 동기화"""
    calendars = get_user_calendars(user_id)
    for calendar in calendars:
        sync_calendar.delay(calendar.id)
```

---

## 🧪 테스팅 전략

### 1. 단위 테스트
```python
import pytest
from unittest.mock import Mock, patch

def test_calendar_sync():
    """캘린더 동기화 테스트"""
    with patch('services.google_calendar_service.fetch_events') as mock_fetch:
        mock_fetch.return_value = [
            {'id': '1', 'title': 'Meeting'},
            {'id': '2', 'title': 'Lunch'}
        ]

        result = sync_calendar_events('user123', 'cal456')
        assert len(result['synced']) == 2
        assert result['status'] == 'success'
```

### 2. 통합 테스트
```python
def test_api_endpoint_integration():
    """API 엔드포인트 통합 테스트"""
    client = app.test_client()

    response = client.post('/api/sync',
        headers={'Authorization': 'Bearer test-token'},
        json={'calendar_id': 'test-cal'})

    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
```

### 3. E2E 테스트
```javascript
// Playwright 또는 Selenium 사용
describe('Calendar Sync Flow', () => {
    it('should sync Google Calendar successfully', async () => {
        await page.goto('/dashboard');
        await page.click('#connect-google');
        await page.waitForSelector('.sync-success');

        const status = await page.textContent('.sync-status');
        expect(status).toBe('Synced successfully');
    });
});
```

---

## 📝 문서화 규칙

### 1. 코드 문서화
```python
class CalendarService:
    """
    캘린더 서비스 기본 클래스

    모든 캘린더 서비스가 상속받아야 하는 추상 클래스입니다.
    각 플랫폼별 구현체는 이 클래스의 메서드를 구현해야 합니다.

    Attributes:
        api_key (str): API 인증 키
        base_url (str): API 기본 URL

    Example:
        >>> service = GoogleCalendarService(api_key='xxx')
        >>> events = service.fetch_events('2024-01-01', '2024-01-31')
    """
```

### 2. API 문서화
```python
@app.route('/api/calendars/<calendar_id>/sync', methods=['POST'])
def sync_calendar(calendar_id):
    """
    캘린더 동기화 API

    ---
    parameters:
      - name: calendar_id
        in: path
        type: string
        required: true
        description: 캘린더 고유 ID
      - name: start_date
        in: body
        type: string
        format: date
        description: 동기화 시작 날짜 (ISO 8601)
      - name: end_date
        in: body
        type: string
        format: date
        description: 동기화 종료 날짜 (ISO 8601)

    responses:
      200:
        description: 동기화 성공
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            synced_count:
              type: integer
              example: 15
      400:
        description: 잘못된 요청
      401:
        description: 인증 실패
    """
```

### 3. 변경 로그
```markdown
## [1.2.0] - 2024-10-04
### Added
- Slack 통합 기능 추가
- 다중 캘린더 선택 UI

### Fixed
- Google Calendar CORS 오류 수정
- 동기화 중복 이벤트 처리

### Changed
- OAuth 플로우 개선
- 성능 최적화: 캐싱 도입
```

---

## 🚀 배포 체크리스트

### 배포 전 확인사항
- [ ] 모든 테스트 통과
- [ ] 환경 변수 설정 확인
- [ ] 데이터베이스 마이그레이션 준비
- [ ] 보안 스캔 완료
- [ ] 성능 테스트 완료
- [ ] 롤백 계획 수립
- [ ] 모니터링 설정
- [ ] 문서 업데이트

### 배포 명령어
```bash
# Railway 배포
railway up

# Docker 빌드 및 배포
docker build -t notionflow:latest .
docker push gcr.io/project-id/notionflow:latest

# 상태 확인
curl https://notionflow.app/health
```

---

## 🗄️ Supabase 데이터베이스 스키마 (최신 확인됨)

### 핵심 테이블 구조 (26개 테이블)

#### 1. users 테이블
```sql
CREATE TABLE public.users (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  email character varying NOT NULL UNIQUE,
  name character varying DEFAULT 'User'::character varying,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  is_active boolean DEFAULT true,
  subscription_plan character varying DEFAULT 'free'::character varying,
  subscription_expires_at timestamp with time zone,
  last_login_at timestamp with time zone,
  email_verified boolean DEFAULT false,
  avatar_url text,
  timezone character varying DEFAULT 'UTC'::character varying,
  CONSTRAINT users_pkey PRIMARY KEY (id)
);
```

#### 2. calendars 테이블 ✅ (owner_id 사용 확인됨!)
```sql
CREATE TABLE public.calendars (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  owner_id text NOT NULL,  -- ✅ 실제 DB는 owner_id 사용!
  type character varying NOT NULL CHECK (type::text = ANY (ARRAY['personal'::character varying, 'shared'::character varying]::text[])),
  name character varying DEFAULT 'My Calendar'::character varying,
  description text,
  color character varying DEFAULT '#3B82F6'::character varying,
  share_link text,
  is_active boolean DEFAULT true,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  public_access boolean DEFAULT false,
  allow_editing boolean DEFAULT false,
  media_filename text,
  media_file_path text,
  media_file_type text,
  CONSTRAINT calendars_pkey PRIMARY KEY (id)
);
```

#### 3. calendar_events 테이블
```sql
CREATE TABLE public.calendar_events (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid,  -- 이벤트는 user_id 사용
  calendar_id uuid,  -- 외래키: calendars.id 참조
  title character varying NOT NULL,
  description text,
  start_datetime timestamp with time zone NOT NULL,
  end_datetime timestamp with time zone NOT NULL,
  is_all_day boolean DEFAULT false,
  source_platform character varying NOT NULL,  -- google, notion, apple, outlook, manual
  sync_status character varying DEFAULT 'synced'::character varying,
  location text,
  attendees jsonb,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT calendar_events_pkey PRIMARY KEY (id),
  CONSTRAINT calendar_events_calendar_id_fkey FOREIGN KEY (calendar_id) REFERENCES public.calendars(id),
  CONSTRAINT calendar_events_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
```

#### 4. user_profiles 테이블
```sql
CREATE TABLE public.user_profiles (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  user_id uuid,
  username character varying NOT NULL UNIQUE,
  display_name character varying,
  bio text,
  website_url text,
  is_public boolean DEFAULT false,
  avatar_url text,
  email character varying,
  birthdate date DEFAULT '1990-01-01'::date,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT user_profiles_pkey PRIMARY KEY (id)
);
```

#### 5. sync_status 테이블
```sql
CREATE TABLE public.sync_status (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  user_id uuid NOT NULL,  -- user_id 사용
  platform text NOT NULL,  -- notion, google_calendar, apple_calendar, slack, outlook
  is_synced boolean DEFAULT false,
  is_connected boolean DEFAULT false,
  last_sync_at timestamp with time zone,
  sync_frequency integer DEFAULT 15,
  error_message text,
  items_synced integer DEFAULT 0,
  items_failed integer DEFAULT 0,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT sync_status_pkey PRIMARY KEY (id),
  CONSTRAINT sync_status_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id)
);
```

#### 6. oauth_tokens 테이블
```sql
CREATE TABLE public.oauth_tokens (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  platform character varying NOT NULL,
  access_token text NOT NULL,
  refresh_token text,
  token_type character varying DEFAULT 'Bearer'::character varying,
  expires_at timestamp with time zone,
  scope text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT oauth_tokens_pkey PRIMARY KEY (id)
);
```

### 전체 테이블 목록 (26개)
**핵심 테이블**:
- `users`, `user_profiles`, `calendars`, `calendar_events`

**캘린더 관련**:
- `calendar_shares`, `calendar_members`, `calendar_share_tokens`, `calendar_tags`, `event_tags`, `event_attendees`

**동기화 시스템**:
- `calendar_sync_configs`, `calendar_sync`, `sync_status`, `sync_events`, `sync_logs`, `sync_analytics`

**이벤트 처리**:
- `event_validation_history`, `event_sync_queue`, `event_sync_mapping`, `event_content_fingerprints`

**인증 & OAuth**:
- `oauth_tokens`, `oauth_states`, `platform_connections`, `platform_coverage`

**사용자 기능**:
- `friendships`, `user_subscriptions`, `notification_preferences`

**분석 & 로깅**:
- `user_activity`, `user_visits`


### Supabase 쿼리 패턴

#### SELECT 쿼리
```python
# 단일 레코드 조회
result = supabase.from_('users') \
    .select('*') \
    .eq('id', user_id) \
    .single() \
    .execute()

# ✅ calendars 테이블은 owner_id 사용!
result = supabase.from_('calendars') \
    .select('*') \
    .eq('owner_id', user_id) \
    .execute()

# JOIN 쿼리
result = supabase.from_('calendars') \
    .select('*, users(email, display_name)') \
    .eq('user_id', user_id) \
    .execute()
```

#### INSERT 쿼리
```python
# ✅ calendars 테이블은 owner_id 사용!
result = supabase.from_('calendars') \
    .insert({
        'owner_id': normalized_user_id,
        'name': 'My Calendar',
        'platform': 'google'
    }) \
    .execute()

# 다중 삽입
result = supabase.from_('calendars') \
    .insert([
        {'owner_id': normalized_user_id, 'name': 'Calendar 1'},
        {'owner_id': normalized_user_id, 'name': 'Calendar 2'}
    ]) \
    .execute()
```

#### UPDATE 쿼리
```python
result = supabase.from_('calendars') \
    .update({
        'sync_status': 'syncing',
        'last_sync_display': 'Syncing...'
    }) \
    .eq('id', calendar_id) \
    .execute()
```

#### DELETE 쿼리
```python
result = supabase.from_('calendars') \
    .delete() \
    .eq('id', calendar_id) \
    .execute()
```

#### UPSERT (INSERT or UPDATE)
```python
result = supabase.from_('api_keys') \
    .upsert({
        'user_id': user_id,
        'platform': 'google',
        'key_name': 'Google Calendar API',
        'encrypted_key': encrypted_key
    }) \
    .execute()
```

#### RPC (Remote Procedure Call)
```python
# 저장 프로시저 호출
result = supabase.rpc('create_user_with_profile', {
    'p_user_id': user_id,
    'p_email': email,
    'p_username': username
}).execute()
```

### 에러 처리 패턴
```python
from supabase.exceptions import PostgrestException

try:
    result = supabase.from_('calendars') \
        .select('*') \
        .eq('user_id', user_id) \
        .execute()

    if result.data:
        return result.data
    else:
        return []

except PostgrestException as e:
    logger.error(f"Database error: {str(e)}")
    return None
except Exception as e:
    logger.error(f"Unexpected error: {str(e)}")
    return None
```

### Row Level Security (RLS) 정책
```sql
-- ✅ calendars 테이블은 owner_id 사용!
CREATE POLICY "Users can view own calendars" ON calendars
    FOR SELECT USING (owner_id = auth.uid()::text);

-- 사용자는 자신의 데이터만 수정 가능
CREATE POLICY "Users can update own calendars" ON calendars
    FOR UPDATE USING (owner_id = auth.uid()::text);

-- 서비스 역할은 모든 접근 가능
CREATE POLICY "Service role full access" ON calendars
    FOR ALL TO service_role USING (true) WITH CHECK (true);
```

### 인덱스 최적화
```sql
-- ✅ calendars 테이블은 owner_id 인덱스!
CREATE INDEX idx_calendars_owner_id ON calendars(owner_id);
CREATE INDEX idx_calendars_platform ON calendars(platform);
CREATE INDEX idx_calendars_sync_status ON calendars(sync_status);
CREATE INDEX idx_api_keys_user_platform ON api_keys(user_id, platform);
```

### UUID 변환 규칙 정리

#### UUID 정규화 프로세스
```python
"""
UUID 형식 통일 규칙:
1. 모든 UUID는 하이픈 포함 형식으로 저장 (예: 12345678-1234-1234-1234-123456789012)
2. 세션의 user_id는 항상 TEXT 타입
3. calendars 테이블만 owner_id 사용, 나머지는 user_id
"""

from utils.uuid_helper import normalize_uuid

# 1. 세션에서 user_id 가져오기
user_id = session.get('user_id')  # 문자열

# 2. UUID 정규화 (하이픈 포함 형식)
normalized_id = normalize_uuid(user_id)

# 3. DB 쿼리 시 사용
# ✅ calendars 테이블은 owner_id 사용!
supabase.from_('calendars').select('*').eq('owner_id', normalized_id).execute()

# 다른 테이블들
supabase.from_('api_keys').select('*').eq('user_id', normalized_id).execute()
```

#### 특수 케이스 처리
```python
# 잘못된 UUID 형식 자동 수정
# 예: 87875eda-6797-f839-f8c7-0aa90efb1352 (중간 부분 잘못됨)
# normalize_uuid가 자동으로 수정

# 이메일을 UUID로 변환
from utils.auth_manager import AuthManager
uuid_from_email = AuthManager._email_to_uuid('user@example.com')

# Mock 모드 처리
if MOCK_MODE:
    user_id = 'mock_user_123'
```

### 테이블별 user_id 필드명 정리

| 테이블 | 필드명 | 타입 | 비고 |
|--------|--------|------|------|
| users | id | UUID | Primary Key |
| calendars | **owner_id** | TEXT | ✅ owner_id 사용 (코드가 올바름) |
| api_keys | user_id | TEXT | |
| user_profiles | user_id | UUID | users.id 참조 |
| payment_subscriptions | user_id | TEXT | |
| user_visits | user_id | TEXT | |
| enhanced_features | user_id | TEXT | |

### 실제 코드 예제
```python
@app.route('/api/calendars')
def get_calendars():
    # 1. 사용자 ID 가져오기
    user_id = AuthManager.get_current_user_id()
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    # 2. UUID 정규화
    from utils.uuid_helper import normalize_uuid
    normalized_id = normalize_uuid(user_id)

    try:
        # 3. calendars 테이블 쿼리 (owner_id 사용!)
        result = supabase.from_('calendars') \
            .select('*') \
            .eq('owner_id', normalized_id) \
            .execute()

        return jsonify({
            'success': True,
            'calendars': result.data
        })
    except Exception as e:
        logger.error(f"Error fetching calendars: {str(e)}")
        return jsonify({
            'success': False,
            'error': '캘린더 조회 중 오류가 발생했습니다.'
        }), 500
```

---

## 🔧 개발 도구 설정

### VS Code 설정
```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true
  }
}
```

### Pre-commit 훅
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.9.1
    hooks:
      - id: black
  - repo: https://github.com/PyCQA/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
```

---

## 🚦 추가 개발 규칙

### 파일 구조 및 네이밍
```
frontend/
├── routes/           # API 라우트 (xxx_routes.py)
├── static/
│   ├── css/         # 스타일시트
│   ├── js/          # JavaScript 파일
│   └── images/      # 이미지 파일
├── templates/       # HTML 템플릿
└── app.py          # Flask 메인 앱

backend/
└── services/        # 비즈니스 로직 (xxx_service.py)

utils/              # 공통 유틸리티
database/           # DB 스키마 및 마이그레이션
```

### 로깅 규칙
```python
import logging

logger = logging.getLogger(__name__)

# 로그 레벨별 사용
logger.debug("상세 디버깅 정보")
logger.info("일반 정보성 메시지")
logger.warning("경고 메시지")
logger.error("에러 발생: {str(e)}")
logger.critical("치명적 오류")

# 모든 API 엔드포인트 시작 시 로깅
@app.route('/api/endpoint')
def endpoint():
    logger.info(f"Endpoint called by user: {session.get('user_id')}")
```

### 세션 관리 규칙
```python
from flask import session

# 세션에 저장할 키 목록 (다른 키 사용 금지)
SESSION_KEYS = [
    'user_id',        # 사용자 ID (TEXT 타입)
    'email',          # 이메일
    'display_name',   # 표시 이름
    'platform_tokens' # 플랫폼별 토큰 (딕셔너리)
]

# 세션 설정
def set_user_session(user_data):
    session['user_id'] = str(user_data.get('id'))  # 항상 문자열로
    session['email'] = user_data.get('email')
    session['display_name'] = user_data.get('display_name')
    session.permanent = True  # 세션 유지

# 세션 제거
def clear_user_session():
    session.clear()
```

### OAuth 토큰 관리
```python
# 플랫폼별 OAuth 토큰 저장 구조
OAUTH_TOKENS = {
    'google': {
        'access_token': 'xxx',
        'refresh_token': 'xxx',
        'expires_at': 'timestamp'
    },
    'notion': {
        'access_token': 'xxx',
        'workspace_id': 'xxx'
    },
    'slack': {
        'access_token': 'xxx',
        'team_id': 'xxx'
    }
}

# 토큰 암호화 저장
from cryptography.fernet import Fernet

def encrypt_token(token):
    key = os.environ.get('ENCRYPTION_KEY')
    f = Fernet(key)
    return f.encrypt(token.encode()).decode()

def decrypt_token(encrypted_token):
    key = os.environ.get('ENCRYPTION_KEY')
    f = Fernet(key)
    return f.decrypt(encrypted_token.encode()).decode()
```

### CORS 설정 (필수)
```python
from flask_cors import CORS

# 개발 환경
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:*"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

# 프로덕션 환경
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://notionflow.app"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})
```

### 날짜/시간 처리
```python
from datetime import datetime, timezone
import pytz

# 항상 UTC로 저장
now_utc = datetime.now(timezone.utc)

# 사용자 타임존으로 변환
def convert_to_user_timezone(utc_time, user_timezone='Asia/Seoul'):
    tz = pytz.timezone(user_timezone)
    return utc_time.replace(tzinfo=pytz.UTC).astimezone(tz)

# ISO 8601 형식 사용
date_string = datetime.now(timezone.utc).isoformat()
```

### 환경변수 필수 목록
```bash
# Supabase
SUPABASE_URL=
SUPABASE_KEY=
SUPABASE_SERVICE_KEY=

# Flask
FLASK_SECRET_KEY=
FLASK_ENV=production

# OAuth - Google
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=

# OAuth - Notion
NOTION_CLIENT_ID=
NOTION_CLIENT_SECRET=
NOTION_REDIRECT_URI=

# OAuth - Slack
SLACK_CLIENT_ID=
SLACK_CLIENT_SECRET=
SLACK_REDIRECT_URI=

# OAuth - Outlook
OUTLOOK_CLIENT_ID=
OUTLOOK_CLIENT_SECRET=

# Stripe (Optional)
STRIPE_API_KEY=
STRIPE_WEBHOOK_SECRET=

# Encryption
ENCRYPTION_KEY=

# Application
APP_URL=https://notionflow.app
PORT=8080
```

### 프론트엔드 JavaScript 규칙
```javascript
// 항상 DOMContentLoaded 이벤트 사용
document.addEventListener('DOMContentLoaded', function() {
    // 초기화 코드
});

// API 호출 패턴
async function apiCall(endpoint, method = 'GET', data = null) {
    try {
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include'  // 세션 쿠키 포함
        };

        if (data) {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(endpoint, options);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        showErrorMessage('작업 중 오류가 발생했습니다.');
        return null;
    }
}

// 에러 메시지 표시
function showErrorMessage(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger';
    alertDiv.textContent = message;
    document.body.insertBefore(alertDiv, document.body.firstChild);

    setTimeout(() => alertDiv.remove(), 5000);
}

// 성공 메시지 표시
function showSuccessMessage(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-success';
    alertDiv.textContent = message;
    document.body.insertBefore(alertDiv, document.body.firstChild);

    setTimeout(() => alertDiv.remove(), 3000);
}
```

### HTML 템플릿 규칙
```html
<!-- 기본 레이아웃 상속 -->
{% extends "base.html" %}

<!-- 타이틀 블록 -->
{% block title %}페이지 제목{% endblock %}

<!-- 컨텐츠 블록 -->
{% block content %}
<div class="container mx-auto px-4 py-8">
    <!-- 페이지 내용 -->
</div>
{% endblock %}

<!-- JavaScript 블록 -->
{% block scripts %}
<script src="{{ url_for('static', filename='js/page-specific.js') }}"></script>
{% endblock %}

<!-- Jinja2 변수는 항상 한 줄로 -->
<script>
    const userId = "{{ session.get('user_id', '') }}";
    const apiUrl = "{{ url_for('api.endpoint') }}";
</script>
```

### 보안 체크리스트
- [ ] SQL 인젝션 방지 (파라미터화된 쿼리 사용)
- [ ] XSS 방지 (입력값 검증 및 이스케이프)
- [ ] CSRF 방지 (Flask-WTF 사용)
- [ ] 민감정보 암호화 저장
- [ ] HTTPS 강제 적용
- [ ] Rate Limiting 구현
- [ ] 입력값 검증 (서버 사이드)
- [ ] 에러 메시지에 민감정보 노출 금지

## 📞 문제 해결 및 지원

### 일반적인 문제
1. **OAuth 인증 실패**: 리다이렉트 URI 확인
2. **동기화 실패**: API 할당량 확인
3. **성능 저하**: 캐시 및 인덱스 확인
4. **CORS 에러**: CORS 설정 확인
5. **세션 유지 실패**: 쿠키 설정 확인

### 디버깅 팁
```python
# 상세 로깅 활성화
import logging
logging.basicConfig(level=logging.DEBUG)

# Supabase 쿼리 디버깅
print(f"Query: {supabase.from_('table').select('*').build()}")

# 세션 디버깅
print(f"Session data: {dict(session)}")

# 프로파일링
from flask_profiler import Profiler
profiler = Profiler(app)
```

---

*이 문서는 NotionFlow 프로젝트의 모든 개발 활동에 대한 절대 지침입니다.*
*모든 코드 수정 시 이 문서의 규칙을 반드시 준수해야 합니다.*

*마지막 업데이트: 2024년 10월 5일*

## 📝 최근 변경사항 (2024-10-05)

### Google Calendar OAuth 2단계 모달 수정
- **문제**: OAuth 성공 후 2단계 모달이 나타나지 않고, Google Calendar enabled 상태가 false로 표시됨
- **해결**:
  1. GoogleCalendarManager 2단계 플로우 구현 (Google 캘린더 선택 → NotionFlow 캘린더 선택)
  2. 캘린더가 없을 때 플랫폼 카드 비활성화 로직 복원
  3. 모든 자동 캘린더 생성 로직 제거 (사용자가 직접 생성해야 함)

### 핵심 변경 파일
- `frontend/static/js/google-calendar-manager.js`: 2단계 모달 플로우
- `frontend/templates/dashboard-api-keys.html`: 카드 비활성화 로직
- `frontend/routes/oauth_routes.py`: 자동 생성 로직 제거
- `frontend/app.py`: 자동 생성 로직 제거

### ✅ 애플 캘린더 OAuth 시 구글 캘린더 연결해제 버튼 사라지는 문제 해결 (2024-10-05)
**문제**: 애플 캘린더 OAuth 인증 시 구글 캘린더의 연결해제 버튼이 사라지는 현상
**원인**: `updateAllPlatformStatus()` 함수에서 모든 플랫폼 업데이트 시 무차별적으로 구글 연결해제 버튼 제거
**해결**:
- 구글 연결해제 버튼 제거 로직을 해당 플랫폼(google)일 때만 실행되도록 수정
- 다른 플랫폼 OAuth 시 구글 캘린더 상태에 영향주지 않도록 개선

**수정된 파일**: `frontend/templates/dashboard-api-keys.html` (2045-2051라인)