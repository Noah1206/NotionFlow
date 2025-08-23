# Python 3.11 slim image 사용
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 의존성 파일 복사
COPY requirements.txt .

# Python 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# Docker 캐시 무효화 - 강제 재빌드
ARG CACHE_BUST=20250823-1930-forcebuild
RUN echo "Cache bust: ${CACHE_BUST}"

# 애플리케이션 코드 복사
COPY . .

# 포트 노출
EXPOSE 8080

# 환경 변수 설정
ENV FLASK_APP=frontend/app.py
ENV PYTHONPATH=/app

# 애플리케이션 시작
CMD ["gunicorn", "frontend.app:app", "--bind", "0.0.0.0:8080", "--timeout", "120", "--workers", "2", "--threads", "4"]