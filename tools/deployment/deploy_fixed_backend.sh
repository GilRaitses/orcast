#!/bin/bash

# Deploy Fixed ORCAST Backend with Redis Integration
set -e

echo "🔧 Deploying FIXED ORCAST Backend with Redis..."

# Configuration
PROJECT_ID="orca-466204"
SERVICE_NAME="orcast-production-backend"
REGION="us-west1"
IMAGE_NAME="orcast-backend-fixed"

echo "📋 Configuration:"
echo "   Project: $PROJECT_ID"
echo "   Service: $SERVICE_NAME"
echo "   Region: $REGION"
echo "   Image: $IMAGE_NAME"
echo ""

# Set project
gcloud config set project $PROJECT_ID

# Build the fixed version
echo "🔨 Building fixed Docker image..."
gcloud builds submit --config cloudbuild.fixed.yaml .

echo "📦 Deploying fixed backend to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$IMAGE_NAME \
    --region=$REGION \
    --platform=managed \
    --allow-unauthenticated \
    --memory=1Gi \
    --cpu=1 \
    --timeout=120 \
    --concurrency=50 \
    --max-instances=5 \
    --min-instances=1

echo "✅ Fixed backend deployment complete!"

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

echo ""
echo "🌐 Service URL: $SERVICE_URL"
echo "🔗 Health Check: $SERVICE_URL/health"
echo ""
echo "🔧 FIXES APPLIED:"
echo "   ✅ Simplified Redis cache implementation"
echo "   ✅ Fixed cache key format issues"
echo "   ✅ Reduced memory usage (1GB vs 2GB)"
echo "   ✅ Single worker process"
echo "   ✅ Better error handling"
echo "   ✅ Faster startup time"
echo ""
echo "Testing fixed backend..."
curl -s "$SERVICE_URL/" | head -3 