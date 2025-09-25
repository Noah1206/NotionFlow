# 🚨 긴급 배포 가이드

Python 3.11 패키지 오류를 해결하기 위한 즉시 사용 가능한 Dockerfile들:

## ✅ 1순위: Debian 기반 (현재 메인)
```bash
# 현재 Dockerfile 사용 (Python 3.9 사용)
docker build -t notionflow .
```

## ✅ 2순위: Alpine Linux (가장 가벼움)
```bash
docker build -f Dockerfile.alpine -t notionflow .
```

## ✅ 3순위: Google App Engine Runtime
```bash
docker build -f Dockerfile.gae -t notionflow .
```

## ✅ 4순위: Google Cloud Buildpack
```bash
docker build -f Dockerfile.gcp -t notionflow .
```

## 🎯 추천 순서

1. **Alpine 먼저 시도** (가장 안전):
   ```bash
   docker build -f Dockerfile.alpine -t notionflow .
   ```

2. **실패하면 메인 Dockerfile**:
   ```bash
   docker build -t notionflow .
   ```

3. **그래도 실패하면 Google 런타임**:
   ```bash
   docker build -f Dockerfile.gae -t notionflow .
   ```

## 🚀 즉시 배포

```bash
# 1. Alpine으로 빌드 시도
docker build -f Dockerfile.alpine -t notionflow .

# 2. 성공하면 배포
gcloud builds submit --tag gcr.io/[PROJECT-ID]/notionflow
gcloud run deploy --image gcr.io/[PROJECT-ID]/notionflow --region asia-southeast1

# 또는 Railway에 커밋
git add .
git commit -m "Fix Python package installation"
git push
```

## 💡 핵심 변경사항

- Python 3.11 → Python 3.9/3.10 (패키지 호환성)
- Node.js 베이스 제거
- 간단한 시스템 이미지 사용
- 의존성 최소화