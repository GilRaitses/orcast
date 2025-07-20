#!/usr/bin/env python3
"""
Update ORCAST URLs from localhost to production
Prepares the system for cloud deployment
"""

import json
import re
from pathlib import Path

def update_dashboard_urls():
    """Update dashboard JavaScript to use production URLs"""
    
    # Production URL mappings
    url_mappings = {
        'http://localhost:8000': 'https://orcast.live',
        'http://localhost:8081': 'https://orcast-ml-service-us-west1.run.app', 
        'http://localhost:8080': 'https://orcast-firestore-us-west1.run.app',
        'localhost:8000': 'orcast.live',
        'localhost:8081': 'orcast-ml-service-us-west1.run.app',
        'localhost:8080': 'orcast-firestore-us-west1.run.app'
    }
    
    print("🔄 Updating dashboard URLs for production deployment...")
    
    # Update main dashboard file
    dashboard_file = Path('js/live_backend_monitoring_dashboard.js')
    if dashboard_file.exists():
        content = dashboard_file.read_text()
        
        for localhost_url, production_url in url_mappings.items():
            content = content.replace(localhost_url, production_url)
        
        # Save production version
        production_file = Path('js/live_backend_monitoring_dashboard_production.js')
        production_file.write_text(content)
        print(f"   ✅ Production dashboard: {production_file}")
    
    # Update HTML files
    html_files = ['index.html', 'live_backend_test.html']
    for html_file in html_files:
        path = Path(html_file)
        if path.exists():
            content = path.read_text()
            
            for localhost_url, production_url in url_mappings.items():
                content = content.replace(localhost_url, production_url)
            
            # Save production version
            production_path = Path(f"production_{html_file}")
            production_path.write_text(content)
            print(f"   ✅ Production HTML: {production_path}")
    
    # Update config.js
    config_file = Path('config.js')
    if config_file.exists():
        content = config_file.read_text()
        
        for localhost_url, production_url in url_mappings.items():
            content = content.replace(localhost_url, production_url)
        
        production_config = Path('production_config.js')
        production_config.write_text(content)
        print(f"   ✅ Production config: {production_config}")

def create_cloud_run_dockerfile():
    """Create Dockerfile for Cloud Run deployment"""
    
    dockerfile_content = """FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY src/backend/orcast_firestore_ml_service.py .
COPY models/ ./models/
COPY bigquery_config.json .
COPY production_config.js ./config.js

# Expose port 8080 (Cloud Run requirement)
EXPOSE 8080

# Set environment variables
ENV PORT=8080
ENV ENVIRONMENT=production
ENV GOOGLE_CLOUD_PROJECT=orca-466204

# Run the application
CMD ["uvicorn", "orcast_firestore_ml_service:app", "--host", "0.0.0.0", "--port", "8080"]
"""
    
    with open('Dockerfile', 'w') as f:
        f.write(dockerfile_content)
    
    print("   ✅ Dockerfile created for Cloud Run")

def create_deployment_configs():
    """Create deployment configuration files"""
    
    # Cloud Run service configuration
    cloud_run_config = {
        "apiVersion": "serving.knative.dev/v1",
        "kind": "Service", 
        "metadata": {
            "name": "orcast-backend",
            "annotations": {
                "run.googleapis.com/ingress": "all"
            }
        },
        "spec": {
            "template": {
                "metadata": {
                    "annotations": {
                        "autoscaling.knative.dev/maxScale": "10",
                        "run.googleapis.com/memory": "2Gi",
                        "run.googleapis.com/cpu": "1000m"
                    }
                },
                "spec": {
                    "containers": [{
                        "image": "gcr.io/orca-466204/orcast-backend",
                        "ports": [{"containerPort": 8080}],
                        "env": [
                            {"name": "GOOGLE_CLOUD_PROJECT", "value": "orca-466204"},
                            {"name": "ENVIRONMENT", "value": "production"}
                        ]
                    }]
                }
            }
        }
    }
    
    with open('cloud-run-service.yaml', 'w') as f:
        json.dump(cloud_run_config, f, indent=2)
    
    print("   ✅ Cloud Run service config created")

def create_deployment_scripts():
    """Create deployment bash scripts"""
    
    deploy_script = """#!/bin/bash
set -e

echo "🚀 Deploying ORCAST to Google Cloud..."

# Set project
gcloud config set project orca-466204

# Build and push container
echo "📦 Building container..."
gcloud builds submit --tag gcr.io/orca-466204/orcast-backend

# Deploy to Cloud Run
echo "🌐 Deploying to Cloud Run..."
gcloud run deploy orcast-backend \\
  --image gcr.io/orca-466204/orcast-backend \\
  --region us-west1 \\
  --allow-unauthenticated \\
  --memory 2Gi \\
  --cpu 1 \\
  --max-instances 10 \\
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
"""
    
    with open('deploy.sh', 'w') as f:
        f.write(deploy_script)
    
    # Make executable
    Path('deploy.sh').chmod(0o755)
    
    print("   ✅ Deployment script: deploy.sh")

def main():
    """Main function to prepare for production"""
    
    print("🔧 ORCAST Production Preparation")
    print("=" * 40)
    
    # Update URLs
    update_dashboard_urls()
    
    # Create Docker configuration
    create_cloud_run_dockerfile()
    
    # Create deployment configs
    create_deployment_configs()
    
    # Create deployment scripts
    create_deployment_scripts()
    
    print("\n✅ Production files created:")
    print("   • js/live_backend_monitoring_dashboard_production.js")
    print("   • production_index.html")
    print("   • production_config.js")
    print("   • Dockerfile")
    print("   • cloud-run-service.yaml")
    print("   • deploy.sh")
    
    print("\n🚀 To deploy to production:")
    print("   1. Authenticate: gcloud auth login")
    print("   2. Set project: gcloud config set project orca-466204")
    print("   3. Run deployment: ./deploy.sh")
    
    print("\n🌐 Production URLs will be:")
    print("   • Frontend: https://storage.googleapis.com/orca-466204-frontend/index.html")
    print("   • Backend: https://orcast-backend-us-west1.run.app")
    print("   • Domain: https://orcast.live (after DNS setup)")

if __name__ == "__main__":
    main() 