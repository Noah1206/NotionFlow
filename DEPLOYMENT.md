# 🚀 NotionFlow 배포 가이드

Docker Hub 인증 오류로 인해 여러 배포 옵션을 준비했습니다.

## 🔧 Docker Hub 401 오류 해결 방법

### 옵션 1: 메인 Dockerfile (Node.js 베이스)
```bash
# 현재 Dockerfile 사용 (Node.js + Python)
docker build -t notionflow .
```

### 옵션 2: Google Cloud 전용 Dockerfile
```bash
# Google Cloud Buildpacks 사용
docker build -f Dockerfile.gcp -t notionflow .
```

### 옵션 3: Heroku 스타일 Dockerfile  
```bash
# Heroku Python buildpack 사용
docker build -f Dockerfile.heroku -t notionflow .
```

### 옵션 4: 간단한 Dockerfile
```bash
# 최소한의 설정
docker build -f Dockerfile.simple -t notionflow .
```

## 🌐 배포 플랫폼

### Google Cloud Run
```bash
# 자동 배포 스크립트 사용
chmod +x deploy.sh
./deploy.sh

# 또는 수동으로
gcloud builds submit --tag gcr.io/[PROJECT_ID]/notionflow
gcloud run deploy notionflow --image gcr.io/[PROJECT_ID]/notionflow --region asia-southeast1
```

### Railway
1. GitHub 저장소를 Railway에 연결
2. `railway.json` 설정이 자동으로 적용됨
3. 환경변수 설정: `PORT=8080`

### Heroku
```bash
# Heroku CLI 사용
heroku create notionflow-app
heroku container:push web -a notionflow-app
heroku container:release web -a notionflow-app
```

### Vercel (Serverless)
```bash
# vercel.json 필요 (별도 생성)
npm i -g vercel
vercel --prod
```

## 🔍 문제 해결

### Docker Hub 401 오류가 계속 발생하는 경우:
1. Docker 캐시 클리어: `docker system prune -a`
2. 다른 Dockerfile 시도: `docker build -f Dockerfile.gcp .`
3. 로컬에서 먼저 빌드 테스트: `docker build --no-cache .`

### 빌드 실패 시:
1. requirements.txt 확인
2. Python 버전 호환성 확인  
3. 의존성 충돌 해결

## 📋 체크리스트

- [ ] PORT 환경변수 설정 (8080)
- [ ] requirements.txt 최신화
- [ ] 환경변수 설정 (.env 파일 제외)
- [ ] 정적 파일 경로 확인
- [ ] 데이터베이스 연결 설정

## 🆘 긴급 배포

가장 간단한 방법:
```bash
# 1. 간단한 Dockerfile 사용
docker build -f Dockerfile.simple -t notionflow .

# 2. 로컬에서 테스트
docker run -p 8080:8080 notionflow

# 3. 성공하면 배포 진행
```