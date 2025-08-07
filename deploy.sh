#!/bin/bash

# 🚀 NotionFlow 자동 배포 스크립트
echo "🚀 NotionFlow Auto Deploy Script"
echo "=================================="

# 현재 브랜치 확인
CURRENT_BRANCH=$(git branch --show-current)
echo "📍 Current branch: $CURRENT_BRANCH"

if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "⚠️  Warning: You're not on the main branch!"
    echo "   Current branch: $CURRENT_BRANCH"
    echo "   Auto-deploy only works on 'main' branch"
    read -p "   Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Deploy cancelled"
        exit 1
    fi
fi

# Git 상태 확인
echo ""
echo "📊 Git Status:"
git status --short

# 미커밋된 변경사항 확인
if ! git diff-index --quiet HEAD --; then
    echo ""
    echo "⚠️  You have uncommitted changes!"
    echo "   Please commit your changes first:"
    echo "   git add . && git commit -m 'your message'"
    exit 1
fi

# Push 실행
echo ""
echo "📤 Pushing to GitHub..."
git push origin $CURRENT_BRANCH

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Push successful!"
    echo ""
    echo "🔄 Render Auto Deploy Status:"
    echo "   • Main branch push detected"
    echo "   • Render will start deployment automatically"
    echo "   • Deployment usually takes 2-3 minutes"
    echo ""
    echo "🌐 Monitor deployment:"
    echo "   • Render Dashboard: https://dashboard.render.com"
    echo "   • Health Check: https://notionflow.onrender.com/health"
    echo "   • Live Site: https://notionflow.onrender.com"
    echo ""
    echo "🎉 Deployment initiated successfully!"
else
    echo "❌ Push failed!"
    exit 1
fi