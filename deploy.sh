#!/bin/bash

# Deploy to Google Cloud Run

echo "🚀 Starting deployment to Google Cloud Run..."

# Set your project ID
PROJECT_ID="your-project-id"
REGION="asia-southeast1"
SERVICE_NAME="notionflow"

echo "📦 Building Docker image locally..."
# Try different Dockerfile if the main one fails
if ! docker build -t gcr.io/$PROJECT_ID/$SERVICE_NAME:latest .; then
    echo "⚠️ Main Dockerfile failed, trying alternative..."
    if [ -f "Dockerfile.gcr" ]; then
        docker build -f Dockerfile.gcr -t gcr.io/$PROJECT_ID/$SERVICE_NAME:latest .
    elif [ -f "Dockerfile.simple" ]; then
        docker build -f Dockerfile.simple -t gcr.io/$PROJECT_ID/$SERVICE_NAME:latest .
    else
        echo "❌ Build failed"
        exit 1
    fi
fi

echo "📤 Pushing image to Google Container Registry..."
docker push gcr.io/$PROJECT_ID/$SERVICE_NAME:latest

echo "🌐 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME:latest \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --memory 512Mi \
    --timeout 300 \
    --max-instances 10

echo "✅ Deployment complete!"