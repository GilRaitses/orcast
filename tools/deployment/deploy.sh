#!/bin/bash
set -e

echo "🚀 Deploying ORCAST to Google Cloud..."

# Set project
gcloud config set project orca-466204

# Build and push container
echo "📦 Building container..."
gcloud builds submit --tag gcr.io/orca-466204/orcast-backend

# Deploy to Cloud Run
echo "🌐 Deploying to Cloud Run..."
gcloud run deploy orcast-backend \
  --image gcr.io/orca-466204/orcast-backend \
  --region us-west1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 1 \
  --max-instances 10 \
  --set-env-vars GOOGLE_CLOUD_PROJECT=orca-466204,ENVIRONMENT=production

# Deploy frontend to Cloud Storage
echo "📂 Deploying frontend..."
gsutil -m cp production_index.html gs://orca-466204-frontend/index.html
gsutil -m cp -r css/ gs://orca-466204-frontend/css/
gsutil -m cp -r js/ gs://orca-466204-frontend/js/
gsutil -m cp -r images/ gs://orca-466204-frontend/images/

# Make bucket publicly readable
gsutil iam ch allUsers:objectViewer gs://orca-466204-frontend

echo "✅ Deployment complete!"
echo "🌐 Frontend: https://storage.googleapis.com/orca-466204-frontend/index.html"
echo "🔧 Backend: Check Cloud Run console for service URL"
