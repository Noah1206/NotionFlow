# 🚂 Railway 배포 가이드 - NotionFlow

## 🎯 Railway 추천 이유
- ✅ **$5 무료 크레딧** (매월 제공)
- ✅ **카드 등록 불필요**
- ✅ 슬립 모드 없음 (항상 켜짐)
- ✅ 빠른 배포 (3분 이내)
- ✅ GitHub 자동 연동

## 📋 배포 단계

### 방법 1: Railway CLI (빠른 방법)

```bash
# 1. Railway CLI 설치
npm install -g @railway/cli

# 2. Railway 로그인
railway login

# 3. 프로젝트 초기화
cd /Users/johyeon-ung/Desktop/NotionFlow
railway init

# 4. 환경변수 설정
railway variables set SUPABASE_URL="https://pzyyfhxftgkftqlxqxjd.supabase.co"
railway variables set SUPABASE_API_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB6eXlmaHhmdGdrZnRxbHhxeGpkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE4MTc5NDgsImV4cCI6MjA2NzM5Mzk0OH0.JfdGpYt537J98m9Ar2vjj86Clce9Iygm4NKlR5ujM3s"
railway variables set FLASK_SECRET_KEY="250bc12b57bf3eec1b550fec1d1fb5f483d3fff06b1b66aeb8bb5ba623d3411d"

# 5. 배포
railway up
```

### 방법 2: GitHub 연동 (웹 UI)

1. **https://railway.app** 방문
2. **Start a New Project** 클릭
3. **Deploy from GitHub repo** 선택
4. GitHub 저장소 선택
5. 환경변수 추가 (Settings → Variables)
6. 자동 배포 시작!

## 🔧 Railway 전용 설정 파일

`railway.json` 생성 (선택사항):
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "gunicorn frontend.app:app --bind 0.0.0.0:$PORT --timeout 120",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

## 📊 무료 크레딧 사용량
- $5 = 약 500시간 실행 가능
- 한 달 내내 켜둬도 충분
- 매월 자동 리셋

---

# 🎮 Replit 배포 가이드 (대안)

## 🎯 Replit 장점
- ✅ **100% 무료**
- ✅ 온라인 IDE (코드 수정 가능)
- ✅ 즉시 실행
- ✅ 카드 불필요

## 📋 Replit 배포

1. **https://replit.com** 방문
2. **Create Repl** → **Import from GitHub**
3. GitHub URL 입력
4. **Secrets** 탭에서 환경변수 추가
5. **Run** 버튼 클릭!

### Replit 전용 설정
`.replit` 파일:
```toml
run = "python frontend/app.py"
language = "python3"

[env]
FLASK_ENV = "production"
PYTHONPATH = "/home/runner/NotionFlow"

[packager]
language = "python3"

[packager.features]
packageSearch = true
guessImports = true
```

---

# 🐍 PythonAnywhere 배포 가이드

## 🎯 PythonAnywhere 특징
- ✅ **완전 무료**
- ✅ Python 전문 호스팅
- ✅ 웹 UI 배포
- ⚠️ 일일 CPU 제한 (초보자용 충분)

## 📋 배포 단계

1. **https://www.pythonanywhere.com** 가입
2. **Web** 탭 → **Add a new web app**
3. **Flask** 선택
4. **Python 3.11** 선택
5. 코드 업로드:
   ```bash
   # Bash console에서
   git clone https://github.com/YOUR_USERNAME/notionflow.git
   ```
6. WSGI 설정 수정
7. 환경변수 설정
8. **Reload** 클릭

---

# 🚀 Koyeb 배포 가이드 (Docker 지원)

## 🎯 Koyeb 장점
- ✅ 무료 티어 제공
- ✅ Docker 네이티브
- ✅ 글로벌 배포

## 📋 배포 단계

1. **https://www.koyeb.com** 가입
2. **Create App** → **GitHub**
3. Repository 선택
4. **Dockerfile** 자동 감지
5. 환경변수 설정
6. **Deploy** 클릭

---

# 💡 추천 순위

## 1위: Railway 🚂
- 가장 빠르고 안정적
- $5 크레딧으로 충분
- 슬립 모드 없음

## 2위: Replit 🎮
- 완전 무료
- 온라인 IDE 제공
- 초보자 친화적

## 3위: PythonAnywhere 🐍
- Python 특화
- 안정적
- 무료 도메인

어떤 플랫폼으로 진행하시겠어요? Railway가 가장 추천입니다!