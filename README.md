# NodeFlow 📅

> Seamless calendar synchronization between Notion and your favorite calendar apps

## ✨ Quick Overview

**NodeFlow**는 여러 캘린더 플랫폼 간의 원활한 동기화를 제공하는 웹 애플리케이션입니다.

### 주요 기능
- 🗓️ **다중 플랫폼 지원**: Google Calendar, Apple Calendar, Outlook, Notion
- 🔄 **실시간 동기화**: 양방향 자동 이벤트 동기화
- 🔐 **안전한 OAuth**: 모든 플랫폼에 대한 보안 인증
- 💻 **직관적 대시보드**: 동기화 관리를 위한 깔끔한 인터페이스
- 🛡️ **API 키 관리**: 암호화된 인증 정보 저장

## 🚀 빠른 시작

```bash
# 1. 저장소 클론
git clone https://github.com/yourusername/notionflow.git
cd notionflow

# 2. 가상환경 설정
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. 환경변수 설정
cp .env.template .env
# .env 파일 편집하여 API 키 입력

# 4. 애플리케이션 실행
python app.py
# http://localhost:8082 접속
```

## 📚 상세 문서

**모든 상세 정보는 통합 문서에서 확인하세요:**

### 📖 [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)
- 완전한 설치 가이드
- 배포 방법 (Railway, Docker, Google Cloud)
- OAuth 설정 방법
- 데이터베이스 마이그레이션
- 문제 해결 가이드
- 프로젝트 구조 설명

## 🛠 기술 스택

- **Backend**: Flask + Supabase + PostgreSQL
- **Frontend**: HTML5/CSS3 + JavaScript + Tailwind CSS
- **배포**: Docker + Railway + Google Cloud Run
- **인증**: OAuth 2.0 + JWT

## 🤝 기여하기

1. 이 저장소를 포크하세요
2. 새 브랜치를 생성하세요 (`git checkout -b feature/amazing-feature`)
3. 변경사항을 커밋하세요 (`git commit -m 'Add amazing feature'`)
4. 브랜치에 푸시하세요 (`git push origin feature/amazing-feature`)
5. 풀 리퀘스트를 생성하세요

## 📞 지원

- 🐛 **버그 리포트**: [GitHub Issues](https://github.com/yourusername/notionflow/issues)
- 💡 **기능 요청**: [GitHub Discussions](https://github.com/yourusername/notionflow/discussions)
- 📖 **문서**: [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)

---

*Made with ❤️ for seamless productivity workflows*
