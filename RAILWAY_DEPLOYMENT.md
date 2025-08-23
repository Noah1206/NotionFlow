# 🚂 Railway 배포 가이드

## 📋 배포 준비 완료

모든 Railway 배포 설정이 완료되었습니다!

## 🚀 Railway 대시보드에서 설정하기

### 1. Railway 프로젝트 접속
```bash
railway open
```
또는 https://railway.app 에서 로그인

### 2. 환경 변수 설정 (Variables 탭)

다음 환경 변수를 Railway 대시보드에 추가하세요:

```env
# 필수 환경 변수
SUPABASE_URL=https://pzyyfhxftgkftqlxqxjd.supabase.co
SUPABASE_ANON_KEY=[Supabase에서 복사]
SUPABASE_SERVICE_KEY=[Supabase에서 복사]

# 보안 키 (32바이트 키 생성 필요)
API_KEY_ENCRYPTION_KEY=[32바이트 암호화 키]
FLASK_SECRET_KEY=[Flask 시크릿 키]

# Notion OAuth (Notion 연동에 필수)
NOTION_CLIENT_ID=[Notion 개발자 포털에서 복사]
NOTION_CLIENT_SECRET=[Notion 개발자 포털에서 복사]

# Google OAuth (선택사항)
GOOGLE_CLIENT_ID=[Google Cloud Console에서 복사]
GOOGLE_CLIENT_SECRET=[Google Cloud Console에서 복사]
```

### 3. 배포 트리거

#### 자동 배포 (권장)
GitHub 저장소가 연결되어 있으면 자동으로 배포가 시작됩니다.

#### 수동 배포
```bash
railway up
```

### 4. 배포 상태 확인

Railway 대시보드에서:
- **View Logs**: 실시간 로그 확인
- **Deployments**: 배포 히스토리 확인
- **Metrics**: 리소스 사용량 모니터링

## 📁 배포 파일 구조

```
NotionFlow/
├── Procfile              # Railway 시작 명령
├── runtime.txt           # Python 버전 (3.11.9)
├── requirements.txt      # Python 패키지
├── railway.json          # Railway 설정
├── nixpacks.toml        # 빌드 설정
├── .env.railway         # 환경 변수 가이드
└── frontend/
    └── app.py           # Flask 애플리케이션
```

## ⚙️ 배포 설정 상세

### Procfile
```
web: gunicorn frontend.app:app --bind 0.0.0.0:$PORT --timeout 120 --workers 1 --threads 2 --log-level info
```

### railway.json
- Nixpacks 빌더 사용
- 헬스체크: `/health`
- 재시작 정책: ON_FAILURE (최대 10회)
- 레플리카: 1개

### nixpacks.toml
- Python 3.11 사용
- 자동 의존성 설치
- Gunicorn으로 서버 실행

## 🔍 트러블슈팅

### PORT 에러
- Railway가 자동으로 PORT 환경 변수를 제공합니다
- Procfile의 `$PORT`를 수정하지 마세요

### 빌드 실패
- requirements.txt 확인
- Python 버전 호환성 확인 (3.11.9)

### 500 에러
- 환경 변수 설정 확인
- Supabase 연결 확인
- 로그에서 자세한 에러 확인

## 📞 지원

문제가 있으면:
1. Railway 대시보드의 로그 확인
2. GitHub Issues에 문제 보고
3. Railway Discord 커뮤니티 참고

## ✅ 체크리스트

- [x] Procfile 생성
- [x] runtime.txt 설정
- [x] requirements.txt 확인
- [x] railway.json 구성
- [x] nixpacks.toml 생성
- [x] GitHub 저장소 연결
- [ ] 환경 변수 설정 (Railway 대시보드에서)
- [ ] 배포 확인

---

**배포 준비 완료!** 🎉

Railway 대시보드에서 환경 변수만 설정하면 자동으로 배포가 시작됩니다.