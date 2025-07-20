#!/bin/bash

# Deploy Redis on Google Cloud Memorystore for ORCAST
# This provides high-performance caching and real-time pub/sub

set -e

echo "🔴 Deploying Redis for ORCAST on Google Cloud Memorystore..."

# Configuration
PROJECT_ID="orca-466204"
REGION="us-west1"
REDIS_INSTANCE_NAME="orcast-redis"
SIZE_GB="1"  # Start with 1GB, can scale up
TIER="standard"  # Standard tier
NETWORK="default"

echo "📋 Configuration:"
echo "   Project: $PROJECT_ID"
echo "   Region: $REGION"
echo "   Instance: $REDIS_INSTANCE_NAME"
echo "   Size: ${SIZE_GB}GB"
echo "   Tier: $TIER"
echo ""

# Set project
echo "🔧 Setting project..."
gcloud config set project $PROJECT_ID

# Enable Redis API
echo "🔌 Enabling Redis API..."
gcloud services enable redis.googleapis.com

# Create Redis instance
echo "🚀 Creating Redis instance..."
gcloud redis instances create $REDIS_INSTANCE_NAME \
    --region=$REGION \
    --size=$SIZE_GB \
    --tier=$TIER \
    --network=$NETWORK \
    --redis-version=redis_7_0

echo "⏳ Waiting for Redis instance to be ready..."

# Wait for instance to be ready
while true; do
    STATUS=$(gcloud redis instances describe $REDIS_INSTANCE_NAME --region=$REGION --format="value(state)")
    echo "   Current status: $STATUS"
    
    if [ "$STATUS" = "READY" ]; then
        break
    fi
    
    echo "   Waiting 30 seconds..."
    sleep 30
done

echo "✅ Redis instance is ready!"

# Get connection details
echo "📡 Getting Redis connection details..."
REDIS_HOST=$(gcloud redis instances describe $REDIS_INSTANCE_NAME --region=$REGION --format="value(host)")
REDIS_PORT=$(gcloud redis instances describe $REDIS_INSTANCE_NAME --region=$REGION --format="value(port)")

echo ""
echo "🎯 Redis Connection Details:"
echo "   Host: $REDIS_HOST"
echo "   Port: $REDIS_PORT"
echo "   Connection String: redis://$REDIS_HOST:$REDIS_PORT"

# Save connection details to file
cat > redis_connection.env << EOF
REDIS_HOST=$REDIS_HOST
REDIS_PORT=$REDIS_PORT
REDIS_URL=redis://$REDIS_HOST:$REDIS_PORT
EOF

echo ""
echo "💾 Connection details saved to: redis_connection.env"

# Create environment variable for Cloud Run
echo ""
echo "🔧 Setting up Cloud Run environment variables..."

# Update Cloud Run service with Redis connection
gcloud run services update orcast-production-backend \
    --region=us-west1 \
    --set-env-vars="REDIS_HOST=$REDIS_HOST,REDIS_PORT=$REDIS_PORT,REDIS_URL=redis://$REDIS_HOST:$REDIS_PORT" \
    --project=$PROJECT_ID

echo ""
echo "✅ Redis deployment complete!"
echo ""
echo "🎉 Next steps:"
echo "   1. Update backend code to use Redis"
echo "   2. Deploy updated backend with Redis integration"
echo "   3. Test caching and real-time features"
echo ""
echo "💰 Estimated cost: ~$30-50/month for 1GB Standard Redis" 