#!/usr/bin/env python3
"""
ORCAST Production Deployment Script
Moves the system from localhost to Google Cloud production infrastructure
"""

import subprocess
import json
import os
import sys
from pathlib import Path
from datetime import datetime

class ORCASTProductionDeployer:
    """Deploys ORCAST system to Google Cloud production environment"""
    
    def __init__(self):
        self.project_id = "orca-466204"
        self.region = "us-west1"
        self.domain = "orcast.live"  # Your custom domain
        
        # Production URLs (will replace localhost)
        self.production_urls = {
            'frontend': f'https://{self.domain}',
            'ml_service': f'https://orcast-ml-service-{self.region}-{self.project_id}.cloudfunctions.net',
            'api_gateway': f'https://api.{self.domain}',
            'firestore_service': f'https://orcast-firestore-{self.region}.run.app'
        }
        
        self.services_to_deploy = [
            'frontend',
            'ml_service', 
            'firestore_service',
            'real_time_api',
            'orcahello_processor'
        ]

    def check_prerequisites(self):
        """Check if all prerequisites for deployment are met"""
        print("🔍 Checking deployment prerequisites...")
        
        issues = []
        
        # Check Google Cloud SDK
        try:
            result = subprocess.run(['gcloud', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                issues.append("Google Cloud SDK not installed")
            else:
                print("   ✅ Google Cloud SDK available")
        except:
            issues.append("Google Cloud SDK not found in PATH")
        
        # Check authentication
        try:
            result = subprocess.run(['gcloud', 'auth', 'list'], capture_output=True, text=True)
            if 'ACTIVE' not in result.stdout:
                issues.append("Not authenticated with Google Cloud (run: gcloud auth login)")
            else:
                print("   ✅ Google Cloud authentication active")
        except:
            issues.append("Cannot verify Google Cloud authentication")
        
        # Check project access
        try:
            result = subprocess.run(['gcloud', 'config', 'get-value', 'project'], 
                                  capture_output=True, text=True)
            current_project = result.stdout.strip()
            if current_project != self.project_id:
                print(f"   ⚠️  Current project: {current_project}, will switch to {self.project_id}")
        except:
            issues.append(f"Cannot access project {self.project_id}")
        
        # Check required files
        required_files = [
            'src/backend/orcast_firestore_ml_service.py',
            'js/live_backend_monitoring_dashboard.js',
            'index.html',
            'requirements.txt',
            'bigquery_config.json'
        ]
        
        for file_path in required_files:
            if not Path(file_path).exists():
                issues.append(f"Required file missing: {file_path}")
            else:
                print(f"   ✅ {file_path} ready for deployment")
        
        return issues

    def prepare_production_configs(self):
        """Prepare configuration files for production deployment"""
        print("\n🔧 Preparing production configurations...")
        
        # Create production config
        production_config = {
            "project_id": self.project_id,
            "region": self.region,
            "environment": "production",
            "frontend_url": self.production_urls['frontend'],
            "api_base_url": self.production_urls['api_gateway'],
            "ml_service_url": self.production_urls['ml_service'],
            "firestore_service_url": self.production_urls['firestore_service'],
            "monitoring_enabled": True,
            "cost_alerts_enabled": True,
            "auto_scaling": {
                "min_instances": 1,
                "max_instances": 10,
                "target_cpu_utilization": 60
            },
            "security": {
                "cors_origins": [self.production_urls['frontend']],
                "api_key_required": True,
                "https_only": True
            }
        }
        
        with open('production_config.json', 'w') as f:
            json.dump(production_config, f, indent=2)
        
        print("   ✅ Production config created: production_config.json")
        
        # Update JavaScript dashboard with production URLs
        self.update_dashboard_urls()
        
        # Create Cloud Run service configs
        self.create_cloud_run_configs()
        
        # Create domain configuration
        self.create_domain_config()

    def update_dashboard_urls(self):
        """Update dashboard JavaScript to use production URLs instead of localhost"""
        print("   🔄 Updating dashboard URLs for production...")
        
        dashboard_file = Path('js/live_backend_monitoring_dashboard.js')
        if not dashboard_file.exists():
            print("   ❌ Dashboard file not found")
            return
        
        content = dashboard_file.read_text()
        
        # Replace localhost URLs with production URLs
        replacements = {
            'http://localhost:8000': self.production_urls['frontend'],
            'http://localhost:8081': self.production_urls['ml_service'],
            'http://localhost:8080': self.production_urls['firestore_service'],
            'localhost:8000': self.domain,
            'localhost:8081': f'orcast-ml-service-{self.region}.run.app',
            'localhost:8080': f'orcast-firestore-{self.region}.run.app'
        }
        
        for localhost_url, production_url in replacements.items():
            content = content.replace(localhost_url, production_url)
            
        # Save production version
        production_dashboard = Path('js/live_backend_monitoring_dashboard_production.js')
        production_dashboard.write_text(content)
        
        print(f"   ✅ Production dashboard: {production_dashboard}")

    def create_cloud_run_configs(self):
        """Create Cloud Run service configuration files"""
        print("   📦 Creating Cloud Run configurations...")
        
        # ML Service Dockerfile
        ml_dockerfile = """FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/backend/orcast_firestore_ml_service.py .
COPY models/ ./models/
COPY bigquery_config.json .

EXPOSE 8080

CMD ["uvicorn", "orcast_firestore_ml_service:app", "--host", "0.0.0.0", "--port", "8080"]
"""
        
        with open('Dockerfile.ml_service', 'w') as f:
            f.write(ml_dockerfile)
        
        # Cloud Run service definition
        cloud_run_config = {
            "apiVersion": "serving.knative.dev/v1",
            "kind": "Service",
            "metadata": {
                "name": "orcast-ml-service",
                "labels": {
                    "run.googleapis.com/ingress": "all"
                }
            },
            "spec": {
                "template": {
                    "metadata": {
                        "labels": {
                            "run.googleapis.com/execution-environment": "gen2"
                        },
                        "annotations": {
                            "autoscaling.knative.dev/maxScale": "10",
                            "run.googleapis.com/memory": "2Gi",
                            "run.googleapis.com/cpu": "1000m"
                        }
                    },
                    "spec": {
                        "containerConcurrency": 80,
                        "containers": [{
                            "image": f"gcr.io/{self.project_id}/orcast-ml-service",
                            "ports": [{"containerPort": 8080}],
                            "env": [
                                {"name": "GOOGLE_CLOUD_PROJECT", "value": self.project_id},
                                {"name": "ENVIRONMENT", "value": "production"}
                            ],
                            "resources": {
                                "limits": {
                                    "cpu": "1000m",
                                    "memory": "2Gi"
                                }
                            }
                        }]
                    }
                }
            }
        }
        
        with open('cloud_run_ml_service.yaml', 'w') as f:
            json.dump(cloud_run_config, f, indent=2)
        
        print("   ✅ Cloud Run configs created")

    def create_domain_config(self):
        """Create domain and SSL configuration"""
        print("   🌐 Creating domain configuration...")
        
        domain_config = {
            "domain": self.domain,
            "ssl_certificate": "managed",
            "services": {
                "frontend": {
                    "type": "cloud_storage",
                    "bucket": f"{self.project_id}-frontend"
                },
                "api": {
                    "type": "cloud_run",
                    "service": "orcast-ml-service"
                }
            },
            "cdn": {
                "enabled": True,
                "cache_mode": "CACHE_ALL_STATIC"
            }
        }
        
        with open('domain_config.json', 'w') as f:
            json.dump(domain_config, f, indent=2)
        
        print(f"   ✅ Domain config: {self.domain}")

    def deploy_to_cloud_run(self):
        """Deploy services to Google Cloud Run"""
        print("\n🚀 Deploying to Google Cloud Run...")
        
        # Set project
        subprocess.run(['gcloud', 'config', 'set', 'project', self.project_id])
        
        # Build and deploy ML service
        print("   📦 Building ML service container...")
        build_cmd = [
            'gcloud', 'builds', 'submit',
            '--tag', f'gcr.io/{self.project_id}/orcast-ml-service',
            '--file', 'Dockerfile.ml_service'
        ]
        
        result = subprocess.run(build_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"   ❌ Build failed: {result.stderr}")
            return False
        
        print("   ✅ Container built successfully")
        
        # Deploy to Cloud Run
        print("   🌐 Deploying to Cloud Run...")
        deploy_cmd = [
            'gcloud', 'run', 'deploy', 'orcast-ml-service',
            '--image', f'gcr.io/{self.project_id}/orcast-ml-service',
            '--region', self.region,
            '--allow-unauthenticated',
            '--memory', '2Gi',
            '--cpu', '1',
            '--max-instances', '10',
            '--set-env-vars', f'GOOGLE_CLOUD_PROJECT={self.project_id},ENVIRONMENT=production'
        ]
        
        result = subprocess.run(deploy_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"   ❌ Deployment failed: {result.stderr}")
            return False
        
        # Extract service URL
        service_url = None
        for line in result.stdout.split('\n'):
            if 'Service URL:' in line:
                service_url = line.split('Service URL:')[1].strip()
                break
        
        if service_url:
            print(f"   ✅ ML Service deployed: {service_url}")
            self.production_urls['ml_service'] = service_url
        
        return True

    def deploy_frontend(self):
        """Deploy frontend to Cloud Storage with CDN"""
        print("\n🌐 Deploying frontend...")
        
        bucket_name = f"{self.project_id}-frontend"
        
        # Create storage bucket
        print(f"   📦 Creating storage bucket: {bucket_name}")
        subprocess.run([
            'gsutil', 'mb', '-p', self.project_id, 
            '-c', 'STANDARD', '-l', self.region.replace('-', ''),
            f'gs://{bucket_name}'
        ])
        
        # Enable web hosting
        subprocess.run([
            'gsutil', 'web', 'set', '-m', 'index.html', '-e', '404.html',
            f'gs://{bucket_name}'
        ])
        
        # Copy files
        print("   📂 Uploading frontend files...")
        subprocess.run([
            'gsutil', '-m', 'cp', '-r',
            'index.html', 'css/', 'js/', 'images/',
            f'gs://{bucket_name}/'
        ])
        
        # Make bucket public
        subprocess.run([
            'gsutil', 'iam', 'ch', 'allUsers:objectViewer',
            f'gs://{bucket_name}'
        ])
        
        frontend_url = f"https://storage.googleapis.com/{bucket_name}/index.html"
        print(f"   ✅ Frontend deployed: {frontend_url}")
        
        return frontend_url

    def setup_monitoring(self):
        """Setup production monitoring and alerting"""
        print("\n📊 Setting up production monitoring...")
        
        # Create monitoring dashboard
        monitoring_config = {
            "displayName": "ORCAST Production Dashboard",
            "mosaicLayout": {
                "tiles": [
                    {
                        "width": 6, "height": 4,
                        "widget": {
                            "title": "Cloud Run Request Count",
                            "xyChart": {
                                "dataSets": [{
                                    "timeSeriesQuery": {
                                        "timeSeriesFilter": {
                                            "filter": f'resource.type="cloud_run_revision" AND resource.labels.project_id="{self.project_id}"',
                                            "aggregation": {
                                                "alignmentPeriod": "60s",
                                                "perSeriesAligner": "ALIGN_RATE"
                                            }
                                        }
                                    }
                                }]
                            }
                        }
                    }
                ]
            }
        }
        
        with open('monitoring_dashboard.json', 'w') as f:
            json.dump(monitoring_config, f, indent=2)
        
        print("   ✅ Monitoring dashboard configuration created")

    def run_deployment(self):
        """Run the complete deployment process"""
        print("🚀 ORCAST Production Deployment")
        print("=" * 50)
        
        # Check prerequisites
        issues = self.check_prerequisites()
        if issues:
            print("\n❌ Prerequisites not met:")
            for issue in issues:
                print(f"   • {issue}")
            return False
        
        # Prepare configs
        self.prepare_production_configs()
        
        # Deploy services
        if not self.deploy_to_cloud_run():
            print("❌ Cloud Run deployment failed")
            return False
        
        # Deploy frontend
        frontend_url = self.deploy_frontend()
        
        # Setup monitoring
        self.setup_monitoring()
        
        # Generate deployment summary
        self.generate_deployment_summary(frontend_url)
        
        return True

    def generate_deployment_summary(self, frontend_url):
        """Generate deployment summary"""
        print("\n" + "=" * 50)
        print("🎉 ORCAST PRODUCTION DEPLOYMENT COMPLETE!")
        print("=" * 50)
        
        print(f"\n🌐 Production URLs:")
        print(f"   Frontend: {frontend_url}")
        print(f"   ML Service: {self.production_urls['ml_service']}")
        print(f"   Monitoring: https://console.cloud.google.com/monitoring/dashboards")
        
        print(f"\n💰 Cost Monitoring:")
        print(f"   Billing: https://console.cloud.google.com/billing/projects/{self.project_id}")
        print(f"   Usage: https://console.cloud.google.com/apis/dashboard?project={self.project_id}")
        
        print(f"\n🔧 Management:")
        print(f"   Cloud Run: https://console.cloud.google.com/run?project={self.project_id}")
        print(f"   Logs: https://console.cloud.google.com/logs/query?project={self.project_id}")
        
        print(f"\n📊 Next Steps:")
        print(f"   1. Update DNS records to point {self.domain} to the frontend")
        print(f"   2. Test all endpoints using the production dashboard")
        print(f"   3. Configure monitoring alerts and budget limits")
        print(f"   4. Update any external systems to use production URLs")
        
        # Save deployment info
        deployment_info = {
            "timestamp": datetime.now().isoformat(),
            "project_id": self.project_id,
            "region": self.region,
            "production_urls": self.production_urls,
            "frontend_url": frontend_url,
            "status": "deployed"
        }
        
        with open('deployment_info.json', 'w') as f:
            json.dump(deployment_info, f, indent=2)
        
        print(f"\n📄 Deployment details saved: deployment_info.json")

def main():
    """Main deployment function"""
    deployer = ORCASTProductionDeployer()
    
    print("⚠️  This will deploy ORCAST to production. Continue? (y/N): ", end="")
    if input().lower() != 'y':
        print("Deployment cancelled.")
        return
    
    success = deployer.run_deployment()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 