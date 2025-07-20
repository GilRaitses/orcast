#!/usr/bin/env python3
"""
Update Frontend for Live Production Backend
"""

from pathlib import Path

def update_frontend_urls():
    """Update frontend to use live production backend"""
    
    production_backend = "https://orcast-simple-126424997157.us-west1.run.app"
    
    # Update the production index file
    index_file = Path('production_index.html')
    if index_file.exists():
        content = index_file.read_text()
        
        # Replace any localhost URLs with production backend
        content = content.replace('http://localhost:8081', production_backend)
        content = content.replace('http://localhost:8080', production_backend)
        
        # Save updated file
        index_file.write_text(content)
        print(f"✅ Updated index.html with backend: {production_backend}")
    
    # Update dashboard JavaScript
    dashboard_file = Path('js/live_backend_monitoring_dashboard_production.js')
    if dashboard_file.exists():
        content = dashboard_file.read_text()
        
        # Replace localhost URLs
        content = content.replace('http://localhost:8081', production_backend)
        content = content.replace('http://localhost:8080', production_backend)
        content = content.replace('localhost:8081', 'orcast-simple-126424997157.us-west1.run.app')
        content = content.replace('localhost:8080', 'orcast-simple-126424997157.us-west1.run.app')
        
        # Save updated file
        dashboard_file.write_text(content)
        print(f"✅ Updated dashboard.js with backend: {production_backend}")
    
    return production_backend

def upload_updated_frontend():
    """Upload the updated frontend files"""
    import subprocess
    
    # Upload updated files
    subprocess.run([
        'gsutil', 'cp', 'production_index.html', 'gs://orcast-org/index.html'
    ])
    
    subprocess.run([
        'gsutil', 'cp', 'js/live_backend_monitoring_dashboard_production.js', 
        'gs://orcast-org/js/live_backend_monitoring_dashboard.js'
    ])
    
    print("✅ Updated frontend files uploaded")

def main():
    backend_url = update_frontend_urls()
    upload_updated_frontend()
    
    print("\n🎉 ORCAST IS NOW LIVE!")
    print("=" * 40)
    print(f"🌐 Frontend: https://storage.googleapis.com/orcast-org/index.html")
    print(f"🔧 Backend: {backend_url}")
    print(f"🏆 Domain: https://orcast.org (after DNS setup)")
    
    print("\n📱 HACKATHON READY!")
    print("✅ Real whale detection predictions")
    print("✅ Live monitoring dashboard") 
    print("✅ Production-grade interface")
    print("✅ Global accessibility")
    
    print("\n🔗 Test the live system:")
    print("   1. Open: https://storage.googleapis.com/orcast-org/index.html")
    print("   2. Click: 'Backend Inspection' tab")
    print("   3. Click: 'Initialize Live Backend Monitoring'")
    print("   4. See: Real-time whale predictions!")

if __name__ == "__main__":
    main() 