# 📋 NotionFlow - 프로젝트 통합 문서

> 모든 문서를 하나로 통합한 프로젝트 개요 및 가이드

## 📖 목차

1. [프로젝트 개요](#프로젝트-개요)
2. [주요 기능](#주요-기능)
3. [기술 스택](#기술-스택)
4. [프로젝트 구조](#프로젝트-구조)
5. [설치 및 실행](#설치-및-실행)
6. [배포 가이드](#배포-가이드)
7. [OAuth 설정](#oauth-설정)
8. [데이터베이스 마이그레이션](#데이터베이스-마이그레이션)
9. [문제 해결](#문제-해결)

---

## 🎯 프로젝트 개요

**NotionFlow**는 Notion과 다양한 캘린더 앱 간의 원활한 동기화를 제공하는 웹 애플리케이션입니다.

### 핵심 목표
- 여러 플랫폼 간 캘린더 동기화
- 안전한 OAuth 인증
- 직관적인 사용자 인터페이스
- 실시간 양방향 동기화

---

## ✨ 주요 기능

### 플랫폼 지원
- **Google Calendar** - OAuth 2.0 인증
- **Apple Calendar** - 스마트 설정 마법사
- **Outlook** - Microsoft OAuth
- **Notion** - Notion API 연동
- **Slack** - 워크스페이스 연동

### 핵심 기능
- ✅ **원클릭 연동**: 간편한 플랫폼 연결
- ✅ **실시간 동기화**: 자동 이벤트 동기화
- ✅ **캘린더 관리**: 다중 캘린더 지원
- ✅ **API 키 관리**: 안전한 인증 정보 저장
- ✅ **동기화 상태 모니터링**: 실시간 상태 확인

---

## 🛠 기술 스택

### Backend
- **Flask** - 웹 프레임워크
- **Supabase** - 데이터베이스 및 인증
- **PostgreSQL** - 관계형 데이터베이스
- **OAuth 2.0** - 보안 인증

### Frontend
- **HTML5/CSS3** - 마크업 및 스타일링
- **JavaScript (ES6+)** - 동적 인터랙션
- **Tailwind CSS** - 유틸리티 기반 스타일링
- **Responsive Design** - 모바일 친화적 UI

### 배포 및 인프라
- **Docker** - 컨테이너화
- **Railway** - 클라우드 배포
- **Google Cloud Run** - 서버리스 배포
- **Heroku** - 대안 배포 플랫폼

---

## 📁 프로젝트 구조

```
NotionFlow/
├── frontend/                   # 웹 애플리케이션
│   ├── app.py                 # Flask 메인 애플리케이션
│   ├── routes/                # API 엔드포인트
│   │   ├── auth_routes.py     # 인증 라우트
│   │   ├── calendar_routes.py # 캘린더 API
│   │   ├── oauth_routes.py    # OAuth 처리
│   │   └── dashboard_routes.py # 대시보드 API
│   ├── static/                # 정적 파일
│   │   ├── css/              # 스타일시트
│   │   ├── js/               # JavaScript 파일
│   │   └── images/           # 이미지 자산
│   ├── templates/            # HTML 템플릿
│   │   ├── base.html         # 기본 레이아웃
│   │   ├── dashboard.html    # 대시보드
│   │   └── calendar.html     # 캘린더 뷰
│   └── utils/                # 유틸리티 함수
├── backend/                   # 백엔드 서비스
│   └── services/             # 통합 서비스
│       ├── google_calendar_sync.py
│       └── notion_sync.py
├── database/                 # 데이터베이스 관련
│   ├── master_schema.sql     # 통합 스키마
│   └── migrations/           # 마이그레이션 스크립트
├── utils/                    # 공통 유틸리티
│   ├── config.py            # 설정 관리
│   ├── auth_utils.py        # 인증 유틸리티
│   └── calendar_db.py       # 캘린더 DB 처리
├── docker/                   # Docker 설정
│   ├── Dockerfile           # 메인 Docker 이미지
│   ├── Dockerfile.simple    # 간단한 배포용
│   └── docker-compose.yml   # 로컬 개발용
└── docs/                    # 문서
    └── PROJECT_OVERVIEW.md  # 이 파일
```

---

## 🚀 설치 및 실행

### 1. 저장소 클론
```bash
git clone https://github.com/yourusername/notionflow.git
cd notionflow
```

### 2. 가상환경 설정
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 환경변수 설정
```bash
cp .env.template .env
# .env 파일을 편집하여 필요한 API 키와 설정을 입력
```

### 4. 애플리케이션 실행
```bash
# 개발 모드
python app.py

# 또는 포트 지정
PORT=8082 python app.py
```

### 5. 브라우저에서 접속
```
http://localhost:8082
```

---

## 🌐 배포 가이드

### Railway 배포 (권장)
```bash
# 1. Railway CLI 설치
npm install -g @railway/cli

# 2. Railway 프로젝트 생성
railway login
railway init
railway link

# 3. 환경변수 설정
railway variables set PORT=8080
railway variables set FLASK_ENV=production

# 4. 배포
railway up
```

### Docker 로컬 빌드
```bash
# 간단한 Dockerfile 사용
docker build -f docker/Dockerfile.simple -t notionflow .
docker run -p 8080:8080 notionflow
```

### Google Cloud Run
```bash
# 프로젝트 빌드 및 배포
gcloud builds submit --tag gcr.io/[PROJECT_ID]/notionflow
gcloud run deploy notionflow \
  --image gcr.io/[PROJECT_ID]/notionflow \
  --region asia-southeast1 \
  --port 8080
```

---

## 🔐 OAuth 설정

### Google Calendar OAuth
1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. APIs & Services > Credentials
4. OAuth 2.0 Client ID 생성
5. 승인된 리디렉션 URI 추가:
   ```
   http://localhost:8082/auth/google/callback
   https://yourdomain.com/auth/google/callback
   ```

### 환경변수 설정
```bash
# .env 파일에 추가
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8082/auth/google/callback

# Supabase 설정
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_key
```

---

## 🗄️ 데이터베이스 마이그레이션

### 데이터베이스 스키마
주요 테이블들:
- `users` - 사용자 정보
- `calendars` - 캘린더 정보
- `oauth_tokens` - OAuth 토큰 저장
- `api_keys` - API 키 관리
- `user_visits` - 사용자 활동 추적

### 마이그레이션 실행
```bash
# 데이터베이스 설정
python database/setup_database.py

# 스키마 적용
psql -f database/master_schema.sql

# 캘린더 마이그레이션 (필요시)
python database/migrate_calendars_to_db.py
```

---

## 🔧 문제 해결

### 일반적인 문제들

#### 1. Google Calendar 연결 오류
**증상**: CORS 오류 또는 OAuth 실패
**해결책**:
```javascript
// GoogleCalendarManager 사용 (새로운 구현)
window.googleManager.connect()
```

#### 2. JavaScript 문법 오류
**증상**: `Uncaught SyntaxError`
**해결책**: Jinja2 템플릿 구문을 한 줄로 작성

#### 3. 포트 충돌
**증상**: `Address already in use`
**해결책**:
```bash
# 다른 포트 사용
PORT=8082 python app.py
```

#### 4. 데이터베이스 연결 실패
**증상**: Supabase 연결 오류
**해결책**:
1. `.env` 파일의 Supabase 설정 확인
2. 네트워크 연결 상태 확인
3. API 키 유효성 검증

### 디버깅 팁

#### 로그 확인
```bash
# Flask 애플리케이션 로그
tail -f logs/app.log

# 개발 모드에서 상세 로그
FLASK_ENV=development python app.py
```

#### 브라우저 개발자 도구
1. F12로 개발자 도구 열기
2. Console 탭에서 JavaScript 오류 확인
3. Network 탭에서 API 요청 상태 확인

---

## 📝 개발 노트

### 최근 주요 변경사항
1. **Google Calendar Manager 분리**: 별도 JavaScript 클래스로 구현
2. **블러 효과 제거**: UI 문제를 야기하는 코드 제거
3. **CORS 오류 해결**: OAuth 팝업 방식 개선
4. **Jinja2 템플릿 수정**: 다중 줄 템플릿 구문 정리

### 코딩 컨벤션
- **Python**: PEP 8 스타일 가이드 준수
- **JavaScript**: ES6+ 문법 사용
- **HTML/CSS**: 시맨틱 마크업, BEM 방법론
- **Git**: Conventional Commits 스타일

---

## 🤝 기여 가이드

### 개발 환경 설정
1. 이 저장소를 포크
2. 로컬에 클론 및 설정
3. 새 브랜치 생성
4. 변경사항 커밋
5. 풀 리퀘스트 생성

### 코드 리뷰 체크리스트
- [ ] 테스트 파일 추가/수정
- [ ] 문서 업데이트
- [ ] 코딩 스타일 준수
- [ ] 성능 영향 검토
- [ ] 보안 취약점 확인

---

## 📞 지원 및 문의

- **이슈 리포트**: GitHub Issues 활용
- **기능 요청**: Discussion 탭 활용
- **보안 문제**: 직접 연락

---

*마지막 업데이트: 2025년 10월 2일*
*생성자: Claude Code SuperClaude*