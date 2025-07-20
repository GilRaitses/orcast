#!/usr/bin/env python3
"""
ORCAST Live Dashboard Validation Test
Comprehensive validation of ALL endpoints and connections for live monitoring
Tests REAL connectivity - no mock data
"""

import asyncio
import aiohttp
import json
import sys
import time
from datetime import datetime
from typing import Dict, List, Tuple, Any
import logging
from pathlib import Path
import subprocess
import socket
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ORCASTDashboardValidator:
    """Validates all ORCAST dashboard endpoints and dependencies"""
    
    def __init__(self):
        self.test_results = {}
        self.failed_tests = []
        self.passed_tests = []
        self.warnings = []
        
        # All real endpoints from the dashboard
        self.endpoints = {
            # Local Services
            'HTTP Server': 'http://localhost:8000',
            'ML Service Health': 'http://localhost:8081/health',
            'ML Service Root': 'http://localhost:8081/',
            'ML Spatial Forecast': 'http://localhost:8081/forecast/spatial',
            'ML Quick Forecast': 'http://localhost:8081/forecast/quick',
            'ML Current Forecast': 'http://localhost:8081/forecast/current',
            'ML Forecast Status': 'http://localhost:8081/forecast/status',
            'ML Store Prediction': 'http://localhost:8081/predict/store',
            
            # BigQuery Project Endpoints (orca-466204)
            'BigQuery Project': 'orca-466204',
            
            # Firebase Configuration
            'Firebase Config': 'config/firebase',
            
            # External APIs
            'Google Maps API': 'https://maps.googleapis.com/maps/api/js',
            'NOAA Tides API': 'https://api.tidesandcurrents.noaa.gov/api/prod/datagetter',
            'Orcasound Live Feeds': 'https://live.orcasound.net/api/json/feeds',
            
            # Files and Dependencies
            'Dashboard JS': 'js/live_backend_monitoring_dashboard.js',
            'BigQuery Config': 'bigquery_config.json',
            'Main Index': 'index.html',
            'Test Page': 'live_backend_test.html'
        }
        
        # Test payloads for POST endpoints
        self.test_payloads = {
            'spatial_forecast': {
                "lat": 48.5465,
                "lng": -123.0307,
                "radius_km": 10
            },
            'quick_forecast': {
                "lat": 48.5465,
                "lng": -123.0307
            },
            'store_prediction': {
                "latitude": 48.5465,
                "longitude": -123.0307,
                "pod_size": 5,
                "water_depth": 45.0,
                "tidal_flow": 0.3,
                "temperature": 15.8,
                "salinity": 30.2,
                "visibility": 25.0,
                "current_speed": 0.4,
                "noise_level": 115.0,
                "prey_density": 0.7,
                "hour_of_day": 14,
                "day_of_year": 200
            }
        }
        
    async def run_comprehensive_validation(self):
        """Run all validation tests"""
        
        print("🔧 ORCAST Live Dashboard Validation Test")
        print("=" * 60)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Test categories
        test_categories = [
            ("🌐 Network & Port Validation", self.test_network_connectivity),
            ("📁 File & Configuration Validation", self.test_file_dependencies),
            ("🎯 Local Service Endpoints", self.test_local_endpoints),
            ("☁️ External API Connectivity", self.test_external_apis),
            ("🔥 Firebase Integration", self.test_firebase_integration),
            ("📊 BigQuery Connectivity", self.test_bigquery_integration),
            ("🐋 OrcaHello Integration", self.test_orcahello_integration),
            ("📈 Dashboard Functionality", self.test_dashboard_functionality),
            ("💰 Cost Tracking Validation", self.test_cost_tracking),
            ("🔄 Real-time Features", self.test_realtime_features)
        ]
        
        total_tests = 0
        for category_name, test_func in test_categories:
            print(f"\n{category_name}")
            print("-" * 40)
            
            try:
                results = await test_func()
                total_tests += len(results)
                
                for test_name, status, details in results:
                    status_symbol = "✅" if status else "❌"
                    print(f"{status_symbol} {test_name}")
                    
                    if details:
                        print(f"   └─ {details}")
                    
                    if status:
                        self.passed_tests.append(test_name)
                    else:
                        self.failed_tests.append((test_name, details))
                        
            except Exception as e:
                print(f"❌ Category test failed: {e}")
                self.failed_tests.append((category_name, str(e)))
        
        # Generate comprehensive summary
        await self.generate_validation_summary(total_tests)
        
        return len(self.failed_tests) == 0
    
    async def test_network_connectivity(self) -> List[Tuple[str, bool, str]]:
        """Test network ports and basic connectivity"""
        results = []
        
        # Test required ports
        ports_to_test = [
            (8000, "HTTP Server"),
            (8081, "ML Service"),
            (443, "HTTPS External APIs"),
            (80, "HTTP External APIs")
        ]
        
        for port, description in ports_to_test:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(3)
                    if port in [8000, 8081]:
                        result = sock.connect_ex(('localhost', port))
                        is_open = result == 0
                        details = f"Port {port} {'open' if is_open else 'closed'} on localhost"
                    else:
                        # Test external connectivity
                        result = sock.connect_ex(('google.com', port))
                        is_open = result == 0
                        details = f"External {description} connectivity {'available' if is_open else 'unavailable'}"
                    
                results.append((f"{description} Port {port}", is_open, details))
                
            except Exception as e:
                results.append((f"{description} Port {port}", False, f"Error: {e}"))
        
        # Test internet connectivity
        try:
            response = requests.get('https://www.google.com', timeout=5)
            internet_ok = response.status_code == 200
            results.append(("Internet Connectivity", internet_ok, "Google reachable" if internet_ok else "No internet"))
        except Exception as e:
            results.append(("Internet Connectivity", False, f"Error: {e}"))
        
        return results
    
    async def test_file_dependencies(self) -> List[Tuple[str, bool, str]]:
        """Test all required files and configurations exist"""
        results = []
        
        required_files = [
            'js/live_backend_monitoring_dashboard.js',
            'bigquery_config.json',
            'index.html',
            'live_backend_test.html',
            'config.js',
            'requirements.txt'
        ]
        
        for file_path in required_files:
            path = Path(file_path)
            exists = path.exists()
            
            if exists:
                size = path.stat().st_size
                details = f"File exists ({size:,} bytes)"
                
                # Additional checks for specific files
                if file_path.endswith('.js'):
                    content = path.read_text()
                    if 'ORCASTLiveBackendDashboard' in content:
                        details += " - Dashboard class found"
                    else:
                        details += " - WARNING: Dashboard class not found"
                        
                elif file_path.endswith('.json'):
                    try:
                        with open(path) as f:
                            data = json.load(f)
                        details += f" - Valid JSON ({len(data)} keys)"
                    except:
                        details += " - ERROR: Invalid JSON"
                        exists = False
                        
            else:
                details = "File missing"
            
            results.append((f"File: {file_path}", exists, details))
        
        return results
    
    async def test_local_endpoints(self) -> List[Tuple[str, bool, str]]:
        """Test all local service endpoints"""
        results = []
        
        # Test GET endpoints
        get_endpoints = [
            ('http://localhost:8081/health', 'ML Service Health'),
            ('http://localhost:8081/', 'ML Service Root'),
            ('http://localhost:8081/forecast/current', 'Current Forecast'),
            ('http://localhost:8081/forecast/status', 'Forecast Status')
        ]
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            for url, name in get_endpoints:
                try:
                    async with session.get(url) as response:
                        success = response.status == 200
                        if success:
                            data = await response.json()
                            details = f"Status {response.status} - Response has {len(data)} fields"
                        else:
                            details = f"Status {response.status}"
                    
                    results.append((name, success, details))
                    
                except Exception as e:
                    results.append((name, False, f"Connection failed: {e}"))
        
        # Test POST endpoints
        post_endpoints = [
            ('http://localhost:8081/forecast/spatial', 'Spatial Forecast', self.test_payloads['spatial_forecast']),
            ('http://localhost:8081/forecast/quick', 'Quick Forecast', self.test_payloads['quick_forecast']),
            ('http://localhost:8081/predict/store', 'Store Prediction', self.test_payloads['store_prediction'])
        ]
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
            for url, name, payload in post_endpoints:
                try:
                    async with session.post(url, json=payload) as response:
                        success = response.status in [200, 201, 202]
                        if success:
                            try:
                                data = await response.json()
                                details = f"Status {response.status} - ML prediction successful"
                            except:
                                details = f"Status {response.status} - Non-JSON response"
                        else:
                            details = f"Status {response.status}"
                    
                    results.append((name, success, details))
                    
                except Exception as e:
                    results.append((name, False, f"Request failed: {e}"))
        
        return results
    
    async def test_external_apis(self) -> List[Tuple[str, bool, str]]:
        """Test external API connectivity"""
        results = []
        
        external_apis = [
            ('https://live.orcasound.net/api/json/feeds', 'Orcasound Live Feeds'),
            ('https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?station=9449880&product=water_level&datum=MLLW&format=json&units=english&time_zone=lst_ldt&application=orcast&begin_date=20250101&end_date=20250102', 'NOAA Tides API'),
            ('https://maps.googleapis.com/maps/api/js?key=AIzaSyD9aM6oj1wpVG-VungMtIpyNWeHp3Q7XjU&libraries=visualization', 'Google Maps API')
        ]
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            for url, name in external_apis:
                try:
                    async with session.get(url) as response:
                        success = response.status == 200
                        if success:
                            content_type = response.headers.get('content-type', '')
                            content_length = len(await response.text())
                            details = f"Status {response.status} - {content_type} ({content_length:,} chars)"
                        else:
                            details = f"Status {response.status}"
                    
                    results.append((name, success, details))
                    
                except Exception as e:
                    results.append((name, False, f"Connection failed: {e}"))
        
        return results
    
    async def test_firebase_integration(self) -> List[Tuple[str, bool, str]]:
        """Test Firebase configuration and connectivity"""
        results = []
        
        # Check Firebase config file
        try:
            with open('config.js', 'r') as f:
                config_content = f.read()
            
            firebase_present = 'firebase' in config_content.lower()
            api_key_present = 'apikey' in config_content.lower()
            project_id_present = 'projectid' in config_content.lower()
            
            results.append(("Firebase Config Present", firebase_present, "Found in config.js"))
            results.append(("Firebase API Key", api_key_present, "API key configured"))
            results.append(("Firebase Project ID", project_id_present, "Project ID configured"))
            
        except Exception as e:
            results.append(("Firebase Config", False, f"Config file error: {e}"))
        
        # Test if Firebase SDK is accessible
        try:
            response = requests.get('https://www.gstatic.com/firebasejs/9.22.2/firebase-app-compat.js', timeout=5)
            sdk_available = response.status_code == 200
            results.append(("Firebase SDK", sdk_available, f"SDK accessible (Status {response.status_code})"))
        except Exception as e:
            results.append(("Firebase SDK", False, f"SDK not accessible: {e}"))
        
        return results
    
    async def test_bigquery_integration(self) -> List[Tuple[str, bool, str]]:
        """Test BigQuery configuration and setup"""
        results = []
        
        # Check BigQuery config
        try:
            with open('bigquery_config.json', 'r') as f:
                bq_config = json.load(f)
            
            project_id = bq_config.get('project_id')
            datasets = bq_config.get('datasets', {})
            tables = bq_config.get('tables', {})
            setup_completed = bq_config.get('setup_completed', False)
            
            results.append(("BigQuery Project ID", project_id == "orca-466204", f"Project: {project_id}"))
            results.append(("BigQuery Datasets", len(datasets) >= 3, f"{len(datasets)} datasets configured"))
            results.append(("BigQuery Tables", len(tables) >= 3, f"{len(tables)} tables configured"))
            results.append(("BigQuery Setup Complete", setup_completed, "Setup flag true"))
            
        except Exception as e:
            results.append(("BigQuery Config", False, f"Config error: {e}"))
        
        # Test if Google Cloud SDK is available
        try:
            result = subprocess.run(['gcloud', '--version'], capture_output=True, text=True, timeout=5)
            gcloud_available = result.returncode == 0
            if gcloud_available:
                version_info = result.stdout.split('\n')[0]
                details = f"Available: {version_info}"
            else:
                details = "gcloud command not found"
            results.append(("Google Cloud SDK", gcloud_available, details))
        except Exception as e:
            results.append(("Google Cloud SDK", False, f"Not available: {e}"))
        
        return results
    
    async def test_orcahello_integration(self) -> List[Tuple[str, bool, str]]:
        """Test OrcaHello AI integration"""
        results = []
        
        # Check if OrcaHello repository is cloned
        orcahello_path = Path('/Users/gilraitses/orcasound/aifororcas-livesystem')
        orcahello_exists = orcahello_path.exists()
        results.append(("OrcaHello Repository", orcahello_exists, str(orcahello_path)))
        
        if orcahello_exists:
            # Check for required files
            inference_system = orcahello_path / 'InferenceSystem'
            inference_exists = inference_system.exists()
            results.append(("OrcaHello Inference System", inference_exists, str(inference_system)))
            
            if inference_exists:
                # Check for model files
                model_path = inference_system / 'src' / 'model'
                model_exists = model_path.exists()
                results.append(("OrcaHello Models", model_exists, str(model_path)))
        
        # Test live Orcasound feeds
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get('https://live.orcasound.net/api/json/feeds') as response:
                    if response.status == 200:
                        feeds = await response.json()
                        feed_count = len(feeds) if isinstance(feeds, list) else len(feeds.get('feeds', []))
                        results.append(("Live Orcasound Feeds", True, f"{feed_count} active feeds"))
                    else:
                        results.append(("Live Orcasound Feeds", False, f"Status {response.status}"))
        except Exception as e:
            results.append(("Live Orcasound Feeds", False, f"Connection failed: {e}"))
        
        return results
    
    async def test_dashboard_functionality(self) -> List[Tuple[str, bool, str]]:
        """Test dashboard JavaScript functionality"""
        results = []
        
        # Check if dashboard JS file has required classes and functions
        try:
            with open('js/live_backend_monitoring_dashboard.js', 'r') as f:
                js_content = f.read()
            
            required_classes = ['ORCASTLiveBackendDashboard', 'CostTracker']
            required_methods = ['initialize', 'testEndpoint', 'updateEndpointMetrics', 'addActivityEntry']
            
            for class_name in required_classes:
                present = class_name in js_content
                results.append((f"JS Class: {class_name}", present, "Class definition found" if present else "Class missing"))
            
            for method_name in required_methods:
                present = method_name in js_content
                results.append((f"JS Method: {method_name}", present, "Method found" if present else "Method missing"))
            
            # Check if all endpoint categories are defined
            endpoint_categories = ['ml', 'firestore', 'realtime', 'orcahello', 'bigquery', 'environmental', 'routes', 'system']
            for category in endpoint_categories:
                present = f"'{category}'" in js_content
                results.append((f"Endpoint Category: {category}", present, "Category defined" if present else "Category missing"))
            
        except Exception as e:
            results.append(("Dashboard JavaScript", False, f"File error: {e}"))
        
        # Test if HTML pages have proper structure
        html_files = ['index.html', 'live_backend_test.html']
        for html_file in html_files:
            try:
                with open(html_file, 'r') as f:
                    html_content = f.read()
                
                has_dashboard_script = 'live_backend_monitoring_dashboard.js' in html_content
                has_inspection_tab = 'inspection-tab' in html_content
                has_init_function = 'initializeBackendDashboard' in html_content or 'initializeDashboard' in html_content
                
                results.append((f"HTML: {html_file} Dashboard Script", has_dashboard_script, "Script reference found"))
                results.append((f"HTML: {html_file} Inspection Tab", has_inspection_tab, "Tab container found"))
                results.append((f"HTML: {html_file} Init Function", has_init_function, "Initialization found"))
                
            except Exception as e:
                results.append((f"HTML: {html_file}", False, f"File error: {e}"))
        
        return results
    
    async def test_cost_tracking(self) -> List[Tuple[str, bool, str]]:
        """Test cost tracking functionality"""
        results = []
        
        # Test cost tracking logic in JavaScript
        try:
            with open('js/live_backend_monitoring_dashboard.js', 'r') as f:
                js_content = f.read()
            
            cost_features = [
                ('cost_per_request', 'Cost per request defined'),
                ('CostTracker', 'Cost tracking class exists'),
                ('addRequest', 'Cost tracking method exists'),
                ('getTotalCost', 'Total cost calculation exists'),
                ('getCostByCategory', 'Category cost breakdown exists')
            ]
            
            for feature, description in cost_features:
                present = feature in js_content
                results.append((f"Cost Feature: {feature}", present, description if present else f"{feature} missing"))
            
        except Exception as e:
            results.append(("Cost Tracking Code", False, f"Code error: {e}"))
        
        return results
    
    async def test_realtime_features(self) -> List[Tuple[str, bool, str]]:
        """Test real-time monitoring features"""
        results = []
        
        # Check for real-time functionality in code
        try:
            with open('js/live_backend_monitoring_dashboard.js', 'r') as f:
                js_content = f.read()
            
            realtime_features = [
                ('setInterval', 'Periodic updates configured'),
                ('EventSource', 'Server-sent events support'),
                ('updateInterval', 'Update interval defined'),
                ('activity-feed', 'Activity feed functionality'),
                ('runPeriodicChecks', 'Periodic endpoint checks')
            ]
            
            for feature, description in realtime_features:
                present = feature in js_content
                results.append((f"Real-time: {feature}", present, description if present else f"{feature} missing"))
            
        except Exception as e:
            results.append(("Real-time Features", False, f"Code error: {e}"))
        
        return results
    
    async def generate_validation_summary(self, total_tests: int):
        """Generate comprehensive validation summary"""
        
        print("\n" + "=" * 60)
        print("🎯 VALIDATION SUMMARY")
        print("=" * 60)
        
        passed_count = len(self.passed_tests)
        failed_count = len(self.failed_tests)
        success_rate = (passed_count / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_count}")
        print(f"❌ Failed: {failed_count}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print()
        
        if self.failed_tests:
            print("❌ FAILED TESTS:")
            print("-" * 30)
            for test_name, details in self.failed_tests:
                print(f"   • {test_name}")
                if details:
                    print(f"     └─ {details}")
            print()
        
        # Dashboard readiness assessment
        critical_systems = [
            "ML Service Health",
            "Dashboard JavaScript",
            "Firebase Config Present", 
            "BigQuery Project ID",
            "Live Orcasound Feeds"
        ]
        
        critical_passed = sum(1 for test in self.passed_tests if any(critical in test for critical in critical_systems))
        critical_total = len(critical_systems)
        
        print("🔧 DASHBOARD READINESS:")
        print("-" * 30)
        print(f"Critical Systems: {critical_passed}/{critical_total} operational")
        
        if success_rate >= 80:
            status = "🟢 READY"
            message = "Live monitoring dashboard is ready for deployment"
        elif success_rate >= 60:
            status = "🟡 PARTIAL"
            message = "Dashboard has some issues but may function with limitations"
        else:
            status = "🔴 NOT READY"
            message = "Critical issues prevent dashboard from functioning properly"
        
        print(f"Status: {status}")
        print(f"Assessment: {message}")
        print()
        
        # Next steps
        print("🚀 NEXT STEPS:")
        print("-" * 30)
        if failed_count == 0:
            print("   1. ✅ All systems operational - dashboard ready for use")
            print("   2. 🌐 Access: http://localhost:8000 → Backend Inspection tab")
            print("   3. 🔄 Start live monitoring: Click 'Initialize Live Backend Monitoring'")
        else:
            print("   1. 🔧 Fix failed tests listed above")
            print("   2. 🔄 Re-run validation: python validate_live_dashboard_connections.py")
            print("   3. 📋 Check individual service logs for detailed error information")
        
        print()
        print("💡 HELPFUL COMMANDS:")
        print("-" * 30)
        print("   • Start HTTP server: python3 -m http.server 8000")
        print("   • Start ML service: source venv/bin/activate && python src/backend/orcast_firestore_ml_service.py")
        print("   • Check port usage: lsof -i :8000,8081")
        print("   • Test single endpoint: curl http://localhost:8081/health")
        
        # Save results to file
        results_file = 'dashboard_validation_results.json'
        validation_results = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': total_tests,
            'passed_count': passed_count,
            'failed_count': failed_count,
            'success_rate': success_rate,
            'passed_tests': self.passed_tests,
            'failed_tests': [{'test': test, 'details': details} for test, details in self.failed_tests],
            'dashboard_ready': success_rate >= 80
        }
        
        with open(results_file, 'w') as f:
            json.dump(validation_results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: {results_file}")

async def main():
    """Run the comprehensive validation test"""
    validator = ORCASTDashboardValidator()
    
    try:
        success = await validator.run_comprehensive_validation()
        exit_code = 0 if success else 1
        
        print(f"\n🏁 Validation completed with exit code: {exit_code}")
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n⏹️ Validation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Validation failed with error: {e}")
        logging.exception("Validation error")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 