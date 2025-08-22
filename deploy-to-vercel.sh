#!/bin/bash

echo "🚀 NotionFlow Vercel 배포 스크립트"
echo "=================================="

# Vercel CLI 설치 확인
if ! command -v vercel &> /dev/null; then
    echo "📦 Vercel CLI 설치 중..."
    npm i -g vercel
fi

echo ""
echo "📝 배포 시작..."
echo "GitHub 저장소와 연결하여 자동 배포를 설정합니다."
echo ""

# Vercel 배포 실행
vercel --prod

echo ""
echo "✅ 배포가 완료되었습니다!"
echo "대시보드에서 환경변수를 설정하세요: https://vercel.com/dashboard"