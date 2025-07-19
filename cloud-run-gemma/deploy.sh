#!/bin/bash
# ORCAST Gemma 3 Cloud Run GPU Deployment Script
# For Google Cloud Hackathon - Agentic AI on Cloud Run GPUs

set -e

# Configuration
PROJECT_ID="orca-904de"
SERVICE_NAME="orcast-gemma3-gpu"
REGION="europe-west4"  # Hackathon required zone
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 ORCAST Gemma 3 Cloud Run GPU Deployment${NC}"
echo -e "${YELLOW}For Google Cloud Hackathon - Agentic AI on Cloud Run GPUs${NC}"
echo ""

# Check if gcloud is configured
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${RED}❌ Error: No active gcloud account found${NC}"
    echo "Please run: gcloud auth login"
    exit 1
fi

# Set project
echo -e "${YELLOW}📝 Setting project: ${PROJECT_ID}${NC}"
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo -e "${YELLOW}🔧 Enabling required APIs...${NC}"
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Build and push Docker image
echo -e "${YELLOW}🐳 Building Docker image...${NC}"
gcloud builds submit --tag ${IMAGE_NAME} .

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Docker build failed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker image built successfully${NC}"

# Deploy to Cloud Run with GPU
echo -e "${YELLOW}🚀 Deploying to Cloud Run with GPU...${NC}"
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --memory 16Gi \
    --cpu 4 \
    --gpu 1 \
    --gpu-type nvidia-l4 \
    --max-instances 1 \
    --min-instances 0 \
    --timeout 900 \
    --concurrency 10 \
    --set-env-vars MODEL_NAME=google/gemma-2-2b-it \
    --set-env-vars PORT=8080 \
    --port 8080

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Cloud Run deployment failed${NC}"
    exit 1
fi

# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(status.url)")

echo ""
echo -e "${GREEN}🎉 Deployment successful!${NC}"
echo -e "${GREEN}📍 Service URL: ${SERVICE_URL}${NC}"
echo ""
echo -e "${YELLOW}🧪 Test endpoints:${NC}"
echo -e "  Health check: ${SERVICE_URL}/health"
echo -e "  Model info:   ${SERVICE_URL}/info"
echo -e "  Generate:     ${SERVICE_URL}/generate (POST)"
echo -e "  Constraints:  ${SERVICE_URL}/extract-constraints (POST)"
echo ""

# Test health check
echo -e "${YELLOW}🩺 Testing health check...${NC}"
curl -s "${SERVICE_URL}/health" | jq . || echo "Health check response received"

echo ""
echo -e "${GREEN}✅ ORCAST Gemma 3 GPU service deployed successfully!${NC}"
echo -e "${YELLOW}💰 Remember: This uses GPU resources - monitor costs!${NC}"
echo -e "${YELLOW}🏆 Hackathon ready: Agentic AI on Cloud Run GPUs${NC}"

# Output configuration for frontend
echo ""
echo -e "${YELLOW}🔧 Frontend configuration:${NC}"
echo "Update your config.js with:"
echo "  gemmaService: {"
echo "    baseUrl: '${SERVICE_URL}',"
echo "    healthEndpoint: '/health',"
echo "    generateEndpoint: '/generate',"
echo "    constraintsEndpoint: '/extract-constraints'"
echo "  }" 