# 🚂 Railway 배포 가이드 (Docker 불필요)

## 🎯 5분 안에 배포 완료!

### 1단계: Git 저장소 준비
```bash
# 현재 변경사항 저장
git add .
git commit -m "Ready for Railway deployment"

# GitHub에 푸시 (저장소가 있다면)
git push origin main
```

### 2단계: Railway 연결
1. https://railway.app 방문
2. "Start a New Project" 클릭
3. "Deploy from GitHub repo" 선택
4. NotionFlow 저장소 선택

### 3단계: 환경변수 설정
Railway 대시보드에서:
- `PORT` = `8080` (자동 설정됨)
- 기타 필요한 환경변수들 추가

### 4단계: 배포 확인
- Railway가 자동으로 Dockerfile 감지
- 빌드 로그 확인
- 배포 완료 후 URL 제공

## 🔧 설정 파일들

이미 준비된 파일들:
- ✅ `railway.json` - Railway 설정
- ✅ `Dockerfile` - Debian + Python 3.9
- ✅ `Dockerfile.alpine` - Alpine Linux (백업용)
- ✅ `.dockerignore` - 빌드 최적화

## 🚨 문제 해결

### 빌드 실패 시:
1. Railway 대시보드에서 "Settings" → "Build Command" 확인
2. 다른 Dockerfile 사용: `Dockerfile.alpine` 또는 `Dockerfile.gae`

### 앱 시작 실패 시:
1. PORT 환경변수 확인
2. Start Command: `python app.py`

## 💡 꿀팁

- Railway는 Git push할 때마다 자동 재배포
- 무료 플랜으로도 충분히 사용 가능
- 커스텀 도메인 연결 가능

## 🎉 완료!

Railway 배포는 로컬 Docker 없이도 클라우드에서 자동으로 빌드됩니다!