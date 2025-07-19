#!/bin/bash

# OrCast Cloudflare Deployment Script
# This script automates the deployment of OrCast to Cloudflare Workers

set -e

echo "🌊 OrCast Cloudflare Deployment Script"
echo "======================================"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required tools are installed
check_dependencies() {
    log_info "Checking dependencies..."
    
    if ! command -v node &> /dev/null; then
        log_error "Node.js is not installed. Please install Node.js 18 or higher."
        exit 1
    fi
    
    if ! command -v npm &> /dev/null; then
        log_error "npm is not installed. Please install npm."
        exit 1
    fi
    
    if ! command -v wrangler &> /dev/null; then
        log_warning "Wrangler CLI not found. Installing..."
        npm install -g wrangler
    fi
    
    log_success "All dependencies are installed"
}

# Install project dependencies
install_dependencies() {
    log_info "Installing project dependencies..."
    npm install
    log_success "Project dependencies installed"
}

# Check Cloudflare authentication
check_auth() {
    log_info "Checking Cloudflare authentication..."
    
    if ! wrangler whoami &> /dev/null; then
        log_warning "Not authenticated with Cloudflare. Please login:"
        wrangler login
    fi
    
    log_success "Authenticated with Cloudflare"
}

# Create KV namespaces
create_kv_namespaces() {
    log_info "Creating KV namespaces..."
    
    echo "Creating production KV namespace..."
    PROD_KV_ID=$(wrangler kv:namespace create CACHE --preview false | grep -o 'id = "[^"]*"' | cut -d '"' -f 2)
    
    echo "Creating preview KV namespace..."
    PREVIEW_KV_ID=$(wrangler kv:namespace create CACHE --preview true | grep -o 'id = "[^"]*"' | cut -d '"' -f 2)
    
    log_success "KV namespaces created"
    log_info "Production KV ID: $PROD_KV_ID"
    log_info "Preview KV ID: $PREVIEW_KV_ID"
    
    # Update wrangler.toml with KV IDs
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/YOUR_KV_NAMESPACE_ID/$PROD_KV_ID/g" wrangler.toml
        sed -i '' "s/YOUR_KV_PREVIEW_ID/$PREVIEW_KV_ID/g" wrangler.toml
    else
        # Linux
        sed -i "s/YOUR_KV_NAMESPACE_ID/$PROD_KV_ID/g" wrangler.toml
        sed -i "s/YOUR_KV_PREVIEW_ID/$PREVIEW_KV_ID/g" wrangler.toml
    fi
    
    log_success "wrangler.toml updated with KV namespace IDs"
}

# Get Zone ID
get_zone_id() {
    log_info "Getting Zone ID for orcast.org..."
    
    echo "Please enter your Cloudflare Zone ID for orcast.org:"
    echo "(You can find this in your Cloudflare dashboard -> orcast.org -> Right sidebar)"
    read -p "Zone ID: " ZONE_ID
    
    if [ -z "$ZONE_ID" ]; then
        log_error "Zone ID is required"
        exit 1
    fi
    
    # Update wrangler.toml with Zone ID
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/YOUR_ZONE_ID/$ZONE_ID/g" wrangler.toml
    else
        # Linux
        sed -i "s/YOUR_ZONE_ID/$ZONE_ID/g" wrangler.toml
    fi
    
    log_success "Zone ID updated in wrangler.toml"
}

# Set environment variables
set_environment_variables() {
    log_info "Setting environment variables..."
    
    echo "Setting up environment variables (press Enter to skip if not available):"
    
    read -p "Google Maps API Key: " GOOGLE_MAPS_API_KEY
    if [ ! -z "$GOOGLE_MAPS_API_KEY" ]; then
        echo "$GOOGLE_MAPS_API_KEY" | wrangler secret put GOOGLE_MAPS_API_KEY
    fi
    
    read -p "OpenWeather API Key: " OPENWEATHER_API_KEY
    if [ ! -z "$OPENWEATHER_API_KEY" ]; then
        echo "$OPENWEATHER_API_KEY" | wrangler secret put OPENWEATHER_API_KEY
    fi
    
    read -p "BigQuery Project ID: " BIGQUERY_PROJECT_ID
    if [ ! -z "$BIGQUERY_PROJECT_ID" ]; then
        echo "$BIGQUERY_PROJECT_ID" | wrangler secret put BIGQUERY_PROJECT_ID
    fi
    
    log_success "Environment variables set"
}

# Deploy to Cloudflare
deploy_app() {
    log_info "Deploying OrCast to Cloudflare..."
    
    # Ask for deployment environment
    echo "Select deployment environment:"
    echo "1) Production (orcast.org)"
    echo "2) Staging (staging.orcast.org)"
    read -p "Enter choice (1-2): " DEPLOY_ENV
    
    case $DEPLOY_ENV in
        1)
            log_info "Deploying to production..."
            npm run deploy:production
            DEPLOY_URL="https://orcast.org"
            ;;
        2)
            log_info "Deploying to staging..."
            npm run deploy:staging
            DEPLOY_URL="https://staging.orcast.org"
            ;;
        *)
            log_error "Invalid choice. Defaulting to production."
            npm run deploy:production
            DEPLOY_URL="https://orcast.org"
            ;;
    esac
    
    log_success "Deployment completed!"
    log_info "App deployed to: $DEPLOY_URL"
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."
    
    DEPLOY_URL=${DEPLOY_URL:-"https://orcast.org"}
    
    # Check health endpoint
    if curl -s "$DEPLOY_URL/health" | grep -q "OK"; then
        log_success "Health check passed"
    else
        log_warning "Health check failed - the app might still be starting up"
    fi
    
    # Check API endpoint
    if curl -s "$DEPLOY_URL/api/predictions" | grep -q "location"; then
        log_success "API endpoint working"
    else
        log_warning "API endpoint check failed - the app might still be starting up"
    fi
    
    log_info "Deployment verification completed"
    log_info "Visit $DEPLOY_URL to see your app!"
}

# Main deployment flow
main() {
    log_info "Starting OrCast Cloudflare deployment..."
    
    check_dependencies
    install_dependencies
    check_auth
    
    # Check if wrangler.toml needs configuration
    if grep -q "YOUR_ZONE_ID" wrangler.toml; then
        get_zone_id
    fi
    
    if grep -q "YOUR_KV_NAMESPACE_ID" wrangler.toml; then
        create_kv_namespaces
    fi
    
    set_environment_variables
    deploy_app
    verify_deployment
    
    echo ""
    log_success "🎉 OrCast deployment completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Visit $DEPLOY_URL to see your app"
    echo "2. Check the Cloudflare dashboard for analytics"
    echo "3. Set up custom domain routing if needed"
    echo "4. Configure SSL/TLS settings in Cloudflare"
    echo ""
    echo "For monitoring and maintenance, see CLOUDFLARE_DEPLOYMENT.md"
}

# Run main function
main "$@" 