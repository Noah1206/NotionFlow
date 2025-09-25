#!/bin/bash

echo "🚀 NotionFlow 배포 (로컬 Docker 불필요)"

# Check if we're in git repo
if ! git status &>/dev/null; then
    echo "❌ Git 저장소가 아닙니다. Git 초기화 필요:"
    echo "git init"
    echo "git add ."
    echo "git commit -m 'Initial commit'"
    exit 1
fi

echo "📋 배포 옵션을 선택하세요:"
echo "1) Railway (추천 - 가장 간단)"
echo "2) Google Cloud Run"
echo "3) Heroku"

read -p "옵션 번호를 입력하세요 (1-3): " choice

case $choice in
    1)
        echo "🚀 Railway로 배포 중..."
        echo "1. Railway 사이트에서 GitHub 연결"
        echo "2. 이 저장소 선택"
        echo "3. 자동 배포 시작"
        
        # Git에 변경사항 커밋
        git add .
        git commit -m "Deploy to Railway - $(date)"
        
        echo "✅ Git 커밋 완료. Railway에 푸시하세요:"
        echo "git push origin main"
        ;;
        
    2)
        echo "☁️ Google Cloud Run으로 배포 중..."
        
        # PROJECT_ID 확인
        PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
        if [ -z "$PROJECT_ID" ]; then
            echo "❌ Google Cloud 프로젝트가 설정되지 않았습니다."
            echo "gcloud auth login"
            echo "gcloud config set project [YOUR-PROJECT-ID]"
            exit 1
        fi
        
        echo "📦 프로젝트 ID: $PROJECT_ID"
        echo "🏗️ Cloud Build로 빌드 시작..."
        
        gcloud builds submit --tag gcr.io/$PROJECT_ID/notionflow .
        
        if [ $? -eq 0 ]; then
            echo "🌐 Cloud Run에 배포 중..."
            gcloud run deploy notionflow \
                --image gcr.io/$PROJECT_ID/notionflow \
                --region asia-southeast1 \
                --platform managed \
                --allow-unauthenticated \
                --port 8080 \
                --memory 512Mi
        else
            echo "❌ 빌드 실패. Dockerfile을 확인하세요."
        fi
        ;;
        
    3)
        echo "🎯 Heroku로 배포 중..."
        
        # Heroku CLI 확인
        if ! command -v heroku &> /dev/null; then
            echo "❌ Heroku CLI가 설치되지 않았습니다."
            echo "https://devcenter.heroku.com/articles/heroku-cli에서 설치하세요."
            exit 1
        fi
        
        # Heroku 앱 생성 (이미 있으면 무시)
        APP_NAME="notionflow-$(date +%s)"
        heroku create $APP_NAME
        heroku stack:set container -a $APP_NAME
        
        # Git remote 추가
        heroku git:remote -a $APP_NAME
        
        # 배포
        git push heroku main
        ;;
        
    *)
        echo "❌ 잘못된 선택입니다."
        exit 1
        ;;
esac

echo "✅ 배포 완료!"