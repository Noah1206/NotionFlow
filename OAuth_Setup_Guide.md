# NotionFlow OAuth 설정 가이드

각 플랫폼별로 OAuth 앱을 생성하고 설정하는 방법입니다.

## 📝 1. Notion OAuth 설정

### Notion Integration 생성
1. https://www.notion.so/my-integrations 접속
2. "New integration" 클릭
3. 다음 정보 입력:
   - Name: `NotionFlow`
   - Associated workspace: 사용할 워크스페이스 선택
4. "Capabilities" 탭에서:
   - Read content: ✅
   - Update content: ✅ (선택사항)
   - Read comments: ✅ (선택사항)

### OAuth 설정
1. "OAuth Domain & URIs" 섹션:
   - Redirect URI 추가: `https://notionflow.onrender.com/oauth/notion/callback`
   - 로컬 테스트용: `http://localhost:5003/oauth/notion/callback`
2. OAuth 정보 복사:
   - OAuth client ID
   - OAuth client secret (한 번만 표시됨!)

### .env 업데이트
```bash
NOTION_CLIENT_ID=your_oauth_client_id_here
NOTION_CLIENT_SECRET=your_oauth_client_secret_here
```

---

## 📅 2. Google Calendar OAuth 설정

### Google Cloud Console 설정
1. https://console.cloud.google.com/ 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. "API 및 서비스" → "사용 설정된 API"
4. "API 및 서비스 사용 설정" 클릭
5. "Google Calendar API" 검색 및 사용 설정

### OAuth 2.0 클라이언트 생성
1. "API 및 서비스" → "사용자 인증 정보"
2. "사용자 인증 정보 만들기" → "OAuth 클라이언트 ID"
3. 애플리케이션 유형: "웹 애플리케이션"
4. 설정:
   - 이름: `NotionFlow`
   - 승인된 JavaScript 원본: `https://notionflow.onrender.com`
   - 승인된 리디렉션 URI: 
     - `https://notionflow.onrender.com/oauth/google/callback`
     - `http://localhost:5003/oauth/google/callback` (로컬 테스트)

### .env 업데이트
```bash
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret_here
```

---

## 📧 3. Microsoft/Outlook OAuth 설정

### Azure Portal 앱 등록
1. https://portal.azure.com/ 접속
2. "Azure Active Directory" → "앱 등록"
3. "새 등록" 클릭
4. 설정:
   - 이름: `NotionFlow`
   - 지원되는 계정 유형: "모든 조직 디렉터리의 계정 및 개인 Microsoft 계정"
   - 리디렉션 URI: Web → `https://notionflow.onrender.com/oauth/outlook/callback`

### API 권한 설정
1. "API 권한" → "권한 추가"
2. "Microsoft Graph" 선택
3. "위임된 권한" 선택
4. 다음 권한 추가:
   - Calendars.ReadWrite
   - User.Read
   - offline_access

### 클라이언트 시크릿 생성
1. "인증서 및 비밀" → "새 클라이언트 암호"
2. 설명 입력 및 만료 기간 선택
3. 생성된 값 복사 (한 번만 표시됨!)

### .env 업데이트
```bash
MICROSOFT_CLIENT_ID=your_application_id_here
MICROSOFT_CLIENT_SECRET=your_client_secret_here
MICROSOFT_TENANT_ID=common  # 또는 특정 테넌트 ID
```

---

## 💬 4. Slack OAuth 설정

### Slack App 생성
1. https://api.slack.com/apps 접속
2. "Create New App" → "From scratch"
3. App Name: `NotionFlow`
4. Workspace 선택

### OAuth & Permissions 설정
1. "OAuth & Permissions" 메뉴
2. Redirect URLs 추가:
   - `https://notionflow.onrender.com/oauth/slack/callback`
   - `http://localhost:5003/oauth/slack/callback` (로컬)
3. Scopes 추가 (Bot Token Scopes):
   - `chat:write`
   - `channels:read`
   - `users:read`

### .env 업데이트
```bash
SLACK_CLIENT_ID=your_client_id_here
SLACK_CLIENT_SECRET=your_client_secret_here
```

---

## 🍎 5. Apple (Sign in with Apple) 설정

### Apple Developer 계정 필요
1. https://developer.apple.com/ 접속
2. "Certificates, Identifiers & Profiles"
3. "Identifiers" → "App IDs" 생성
4. "Sign in with Apple" 기능 활성화

### Service ID 생성
1. "Identifiers" → "Services IDs"
2. 새 Service ID 생성
3. "Sign in with Apple" 설정:
   - Primary App ID 선택
   - Return URLs: `https://notionflow.onrender.com/oauth/apple/callback`

### Private Key 생성
1. "Keys" → 새 키 생성
2. "Sign in with Apple" 선택
3. .p8 파일 다운로드 (한 번만 다운로드 가능!)

### .env 업데이트
```bash
APPLE_CLIENT_ID=your_service_id_here
APPLE_TEAM_ID=your_team_id_here
APPLE_KEY_ID=your_key_id_here
APPLE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----
your_private_key_content_here
-----END PRIVATE KEY-----"
```

---

## 🚀 설정 완료 후

1. `.env` 파일 저장
2. 서버 재시작:
   ```bash
   # 로컬 개발
   python frontend/app.py
   
   # 프로덕션 (Render)
   git add . && git commit -m "Add OAuth credentials" && git push
   ```

3. 테스트:
   - 각 플랫폼의 "원클릭" 버튼 클릭
   - OAuth 팝업이 열리고 로그인 페이지가 표시되는지 확인
   - 인증 완료 후 자동으로 연결되는지 확인

## ⚠️ 보안 주의사항

- **절대로** OAuth 자격 증명을 Git에 커밋하지 마세요
- `.env` 파일은 `.gitignore`에 포함되어 있어야 합니다
- 프로덕션 환경에서는 환경 변수로 관리하세요 (Render Dashboard에서 설정)