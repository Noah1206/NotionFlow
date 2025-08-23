# Railway 환경변수 설정 가이드

Railway 대시보드에서 다음 환경변수들을 설정해주세요:

## 필수 환경변수

```bash
# Supabase 설정
SUPABASE_URL=your_supabase_url_here
SUPABASE_ANON_KEY=your_supabase_anon_key_here

# 보안 키
API_KEY_ENCRYPTION_KEY=your_encryption_key_here
FLASK_SECRET_KEY=your_flask_secret_key_here

# 환경 설정
ENVIRONMENT=production
PORT=8080

# OAuth 설정 (선택사항)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

## Railway 자동 배포 설정

1. Railway 대시보드 접속: https://railway.app/dashboard
2. "New Project" → "Deploy from GitHub repo"
3. "Noah1206/NotionFlow" 선택
4. Variables 탭에서 위 환경변수들 추가
5. Settings에서 Start Command 확인: `gunicorn frontend.app:app --bind 0.0.0.0:$PORT`

## 자동 배포 완료!

- GitHub main 브랜치에 push하면 자동으로 Railway에서 감지
- 빌드 및 배포 진행 (보통 2-5분 소요)
- `https://notionflow-production.up.railway.app` 형태의 URL로 접속 가능

현재 코드가 GitHub에 이미 push되어 있으므로, Railway에서 자동으로 최신 버전을 배포합니다!