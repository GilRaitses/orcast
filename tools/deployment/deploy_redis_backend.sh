#!/bin/bash

# Deploy ORCAST Backend with Redis Integration
set -e

echo "🚀 Deploying ORCAST Backend with Redis Integration..."

# Configuration
PROJECT_ID="orca-466204"
SERVICE_NAME="orcast-production-backend"
REGION="us-west1"
IMAGE_NAME="orcast-backend-redis"

echo "📋 Configuration:"
echo "   Project: $PROJECT_ID"
echo "   Service: $SERVICE_NAME"
echo "   Region: $REGION"
echo "   Image: $IMAGE_NAME"
echo ""

# Set project
gcloud config set project $PROJECT_ID

# Build and deploy with Cloud Build
echo "🔨 Building Docker image with Redis support..."
gcloud builds submit --config cloudbuild.redis.yaml .

echo "📦 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$IMAGE_NAME \
    --region=$REGION \
    --platform=managed \
    --allow-unauthenticated \
    --memory=2Gi \
    --cpu=2 \
    --timeout=300 \
    --concurrency=100 \
    --max-instances=10

echo "✅ Redis-enabled backend deployment complete!"

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

echo ""
echo "🌐 Service URL: $SERVICE_URL"
echo "🔗 Health Check: $SERVICE_URL/health"
echo "📊 Cache Stats: $SERVICE_URL/api/cache/stats"
echo "📡 Real-time Events: $SERVICE_URL/api/real-time/events"
echo ""
echo "🎯 Redis Features Now Available:"
echo "   ✅ ML prediction caching (30min TTL)"
echo "   ✅ Environmental data caching (5min TTL)"
echo "   ✅ Real-time pub/sub messaging"
echo "   ✅ Rate limiting protection"
echo "   ✅ Performance optimization" 