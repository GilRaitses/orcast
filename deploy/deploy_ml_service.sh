#!/bin/bash

# OrCast Behavioral ML Service Deployment Script
# Deploys the ML service to Google Cloud Run

set -e

# Configuration
PROJECT_ID="orca-904de"
REGION="us-central1"
SERVICE_NAME="orcast-behavioral-ml"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "Deploying OrCast Behavioral ML Service to Cloud Run..."

# Set project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable bigquery.googleapis.com
gcloud services enable aiplatform.googleapis.com

# Create BigQuery dataset and tables
echo "Setting up BigQuery dataset..."
bq mk --dataset --location=US ${PROJECT_ID}:orca_data 2>/dev/null || echo "Dataset already exists, continuing..."

# Create tables from schema (skip if tables already exist)
echo "Creating BigQuery tables..."
if bq ls ${PROJECT_ID}:orca_data | grep -q "sightings"; then
    echo "Tables already exist, skipping table creation..."
else
    bq query --use_legacy_sql=false < bigquery_schema.sql
fi

# Deploy directly from source (no Docker required)
echo "Deploying to Cloud Run from source..."
gcloud run deploy $SERVICE_NAME \
    --source . \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 3600 \
    --max-instances 10 \
    --set-env-vars PROJECT_ID=$PROJECT_ID \
    --set-env-vars REGION=$REGION

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)")

echo "Deployment complete!"
echo "Service URL: $SERVICE_URL"
echo "Health check: $SERVICE_URL/"
echo "Model status: $SERVICE_URL/model/status"
echo "Prediction endpoint: $SERVICE_URL/predict"

# Test the service
echo "Testing service..."
curl -s "$SERVICE_URL/" | jq .

# Create service account for BigQuery access
echo "Setting up service account..."
gcloud iam service-accounts create $SERVICE_NAME \
    --display-name "OrCast Behavioral ML Service" \
    --description "Service account for OrCast behavioral ML predictions"

# Grant BigQuery permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/bigquery.jobUser"

# Grant AI Platform permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

echo "OrCast Behavioral ML Service deployed successfully!"
echo ""
echo "Next steps:"
echo "1. Train the model: curl -X POST $SERVICE_URL/train"
echo "2. Check model status: curl $SERVICE_URL/model/status"
echo "3. Make predictions: curl -X POST $SERVICE_URL/predict -d '{...}'"
echo "4. Update frontend with service URL: $SERVICE_URL" 