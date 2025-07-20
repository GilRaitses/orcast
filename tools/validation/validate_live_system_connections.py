#!/usr/bin/env python3
"""
ORCAST Live System Validation Test
Comprehensive validation of all inputs and connections for live monitoring dashboard
"""

import asyncio
import aiohttp
import json
import time
import os
import sys
from datetime import datetime
from typing import Dict, List, Tuple, Any
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ORCASTSystemValidator:
    """Validates all ORCAST system connections and inputs"""
    
    def __init__(self):
        self.validation_results = {}
        self.failed_validations = []
        self.passed_validations = []
        
        # Service endpoints to validate
        self.services = {
            'http_server': 'http://localhost:8000',
            'ml_service': 'http://localhost:8081', 
            'firestore_ml': 'http://localhost:8080'
        }
        
        # All endpoint categories from the dashboard
        self.endpoint_categories = {
            'ml_services': [
                {'url': '/api/ml/predict', 'method': 'POST', 'service': 'ml_service'},
                {'url': '/api/ml/predict/physics', 'method': 'POST', 'service': 'ml_service'},
                {'url': '/api/ml/model/status', 'method': 'GET', 'service': 'ml_service'},
                {'url': '/api/ml/features/importance', 'method': 'GET', 'service': 'ml_service'}
            ],
            'firestore_integration': [
                {'url': '/forecast/spatial', 'method': 'POST', 'service': 'firestore_ml'},
                {'url': '/forecast/quick', 'method': 'POST', 'service': 'firestore_ml'},
                {'url': '/forecast/current', 'method': 'GET', 'service': 'firestore_ml'},
                {'url': '/forecast/status', 'method': 'GET', 'service': 'firestore_ml'},
                {'url': '/predict/store', 'method': 'POST', 'service': 'firestore_ml'}
            ],
            'realtime_streaming': [
                {'url': '/api/realtime/events', 'method': 'GET', 'service': 'http_server'},
                {'url': '/api/realtime/status', 'method': 'GET', 'service': 'http_server'},
                {'url': '/api/realtime/health', 'method': 'GET', 'service': 'http_server'}
            ],
            'orcahello_integration': [
                {'url': '/api/orcahello/detections', 'method': 'GET', 'service': 'http_server'},
                {'url': '/api/orcahello/status', 'method': 'GET', 'service': 'http_server'},
                {'url': '/api/orcahello/hydrophones', 'method': 'GET', 'service': 'http_server'}
            ],
            'bigquery_analytics': [
                {'url': '/api/bigquery/recent_detections', 'method': 'GET', 'service': 'http_server'},
                {'url': '/api/bigquery/active_hotspots', 'method': 'GET', 'service': 'http_server'},
                {'url': '/api/bigquery/top_routes', 'method': 'GET', 'service': 'http_server'}
            ],
            'environmental_data': [
                {'url': '/api/environmental', 'method': 'GET', 'service': 'http_server'},
                {'url': '/api/environmental/noaa/weather', 'method': 'GET', 'service': 'http_server'},
                {'url': '/api/environmental/noaa/tides', 'method': 'GET', 'service': 'http_server'}
            ],
            'route_optimization': [
                {'url': '/api/routes/recommendations', 'method': 'GET', 'service': 'http_server'},
                {'url': '/api/routes/google', 'method': 'POST', 'service': 'http_server'}
            ],
            'system_health': [
                {'url': '/api/status', 'method': 'GET', 'service': 'http_server'},
                {'url': '/health', 'method': 'GET', 'service': 'firestore_ml'},
                {'url': '/api/firebase/status', 'method': 'GET', 'service': 'http_server'}
            ]
        }
        
        # Sample payloads for POST endpoints
        self.sample_payloads = {
            '/api/ml/predict': {
                'latitude': 48.5465,
                'longitude': -123.0307,
                'pod_size': 5,
                'water_depth': 45.0,
                'tidal_flow': 0.3,
                'temperature': 15.8,
                'salinity': 30.2,
                'visibility': 25.0,
                'current_speed': 0.4,
                'noise_level': 115.0,
                'prey_density': 0.7,
                'hour_of_day': 14,
                'day_of_year': 200
            },
            '/forecast/spatial': {
                'lat': 48.5465,
                'lng': -123.0307,
                'radius_km': 10
            },
            '/forecast/quick': {
                'lat': 48.5465,
                'lng': -123.0307
            },
            '/api/routes/google': {
                'origin': {'lat': 48.5465, 'lng': -123.0307},
                'destination': {'lat': 48.6, 'lng': -123.1}
            }
        }
        
        # Required files and directories
        self.required_files = [
            'js/live_backend_monitoring_dashboard.js',
            'index.html',
            'config.js',
            'bigquery_config.json',
            'requirements.txt',
            'models/',  # directory
            'venv/',    # directory
        ]
        
        # Environment variables to check
        self.required_env_vars = [
            'GOOGLE_CLOUD_PROJECT',
            'GOOGLE_APPLICATION_CREDENTIALS'
        ]

    async def run_full_validation(self) -> Dict[str, Any]:
        """Run comprehensive validation of all system components"""
        
        print("🔍 ORCAST Live System Validation Starting...")
        print("=" * 60)
        
        start_time = time.time()
        
        # 1. Validate required files and directories
        await self.validate_file_structure()
        
        # 2. Validate environment setup
        await self.validate_environment()
        
        # 3. Validate service connectivity
        await self.validate_services()
        
        # 4. Validate all endpoint categories
        await self.validate_all_endpoints()
        
        # 5. Validate dashboard dependencies
        await self.validate_dashboard_dependencies()
        
        # 6. Validate data flows
        await self.validate_data_flows()
        
        # Generate final report
        end_time = time.time()
        self.generate_validation_report(end_time - start_time)
        
        return self.validation_results

    async def validate_file_structure(self):
        """Validate required files and directories exist"""
        print("\n📁 Validating File Structure...")
        
        file_results = {}
        
        for file_path in self.required_files:
            path = Path(file_path)
            exists = path.exists()
            
            if file_path.endswith('/'):
                # Directory check
                is_valid = exists and path.is_dir()
                file_count = len(list(path.iterdir())) if is_valid else 0
                file_results[file_path] = {
                    'exists': exists,
                    'is_directory': is_valid,
                    'file_count': file_count,
                    'status': 'PASS' if is_valid else 'FAIL'
                }
            else:
                # File check
                size = path.stat().st_size if exists else 0
                file_results[file_path] = {
                    'exists': exists,
                    'size_bytes': size,
                    'status': 'PASS' if exists else 'FAIL'
                }
            
            status = "✅" if file_results[file_path]['status'] == 'PASS' else "❌"
            print(f"  {status} {file_path}")
        
        self.validation_results['file_structure'] = file_results
        
        passed = sum(1 for r in file_results.values() if r['status'] == 'PASS')
        total = len(file_results)
        print(f"📁 File Structure: {passed}/{total} checks passed")

    async def validate_environment(self):
        """Validate environment variables and configuration"""
        print("\n🌍 Validating Environment...")
        
        env_results = {}
        
        # Check environment variables
        for var in self.required_env_vars:
            value = os.getenv(var)
            env_results[var] = {
                'exists': value is not None,
                'value_length': len(value) if value else 0,
                'status': 'PASS' if value else 'FAIL'
            }
            
            status = "✅" if env_results[var]['status'] == 'PASS' else "❌"
            print(f"  {status} {var}")
        
        # Check Python environment
        try:
            import google.cloud.firestore
            import google.cloud.bigquery
            firestore_available = True
        except ImportError:
            firestore_available = False
        
        env_results['google_cloud_libs'] = {
            'available': firestore_available,
            'status': 'PASS' if firestore_available else 'FAIL'
        }
        
        status = "✅" if firestore_available else "❌"
        print(f"  {status} Google Cloud Libraries")
        
        # Check BigQuery config
        bigquery_config_exists = Path('bigquery_config.json').exists()
        env_results['bigquery_config'] = {
            'exists': bigquery_config_exists,
            'status': 'PASS' if bigquery_config_exists else 'FAIL'
        }
        
        status = "✅" if bigquery_config_exists else "❌"
        print(f"  {status} BigQuery Configuration")
        
        self.validation_results['environment'] = env_results
        
        passed = sum(1 for r in env_results.values() if r['status'] == 'PASS')
        total = len(env_results)
        print(f"🌍 Environment: {passed}/{total} checks passed")

    async def validate_services(self):
        """Validate core services are running"""
        print("\n🚀 Validating Services...")
        
        service_results = {}
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            for service_name, base_url in self.services.items():
                try:
                    # Try health check endpoint first
                    health_endpoints = ['/health', '/', '/api/status']
                    
                    service_up = False
                    response_data = None
                    response_time = None
                    
                    for endpoint in health_endpoints:
                        try:
                            start_time = time.time()
                            async with session.get(f"{base_url}{endpoint}") as response:
                                end_time = time.time()
                                response_time = (end_time - start_time) * 1000  # ms
                                
                                if response.status == 200:
                                    try:
                                        response_data = await response.json()
                                    except:
                                        response_data = await response.text()
                                    service_up = True
                                    break
                        except Exception as e:
                            continue
                    
                    service_results[service_name] = {
                        'url': base_url,
                        'reachable': service_up,
                        'response_time_ms': response_time,
                        'response_data': str(response_data)[:200] if response_data else None,
                        'status': 'PASS' if service_up else 'FAIL'
                    }
                    
                except Exception as e:
                    service_results[service_name] = {
                        'url': base_url,
                        'reachable': False,
                        'error': str(e),
                        'status': 'FAIL'
                    }
                
                status = "✅" if service_results[service_name]['status'] == 'PASS' else "❌"
                response_time = service_results[service_name].get('response_time_ms', 0)
                print(f"  {status} {service_name} ({base_url}) - {response_time:.0f}ms")
        
        self.validation_results['services'] = service_results
        
        passed = sum(1 for r in service_results.values() if r['status'] == 'PASS')
        total = len(service_results)
        print(f"🚀 Services: {passed}/{total} services running")

    async def validate_all_endpoints(self):
        """Validate all dashboard endpoints"""
        print("\n🔗 Validating All Dashboard Endpoints...")
        
        endpoint_results = {}
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            total_endpoints = 0
            passed_endpoints = 0
            
            for category, endpoints in self.endpoint_categories.items():
                print(f"\n  📂 {category.upper()}:")
                category_results = {}
                
                for endpoint_config in endpoints:
                    total_endpoints += 1
                    url = endpoint_config['url']
                    method = endpoint_config['method']
                    service = endpoint_config['service']
                    
                    if service not in self.services:
                        continue
                    
                    base_url = self.services[service]
                    full_url = f"{base_url}{url}"
                    
                    try:
                        start_time = time.time()
                        
                        # Prepare request
                        kwargs = {'url': full_url}
                        if method == 'POST' and url in self.sample_payloads:
                            kwargs['json'] = self.sample_payloads[url]
                            kwargs['headers'] = {'Content-Type': 'application/json'}
                        
                        # Make request
                        async with session.request(method, **kwargs) as response:
                            end_time = time.time()
                            response_time = (end_time - start_time) * 1000
                            
                            # Get response data
                            try:
                                if response.content_type and 'json' in response.content_type:
                                    response_data = await response.json()
                                else:
                                    response_data = await response.text()
                            except:
                                response_data = "Unable to parse response"
                            
                            is_success = 200 <= response.status < 400
                            
                            category_results[url] = {
                                'method': method,
                                'full_url': full_url,
                                'status_code': response.status,
                                'response_time_ms': response_time,
                                'response_size': len(str(response_data)),
                                'success': is_success,
                                'status': 'PASS' if is_success else 'FAIL'
                            }
                            
                            if is_success:
                                passed_endpoints += 1
                    
                    except Exception as e:
                        category_results[url] = {
                            'method': method,
                            'full_url': full_url,
                            'error': str(e),
                            'success': False,
                            'status': 'FAIL'
                        }
                    
                    # Print result
                    result = category_results[url]
                    status = "✅" if result['status'] == 'PASS' else "❌"
                    response_time = result.get('response_time_ms', 0)
                    status_code = result.get('status_code', 'ERR')
                    print(f"    {status} {method} {url} ({status_code}) - {response_time:.0f}ms")
                
                endpoint_results[category] = category_results
        
        self.validation_results['endpoints'] = endpoint_results
        print(f"\n🔗 Endpoints: {passed_endpoints}/{total_endpoints} endpoints responding")

    async def validate_dashboard_dependencies(self):
        """Validate dashboard-specific dependencies"""
        print("\n📊 Validating Dashboard Dependencies...")
        
        dashboard_results = {}
        
        # Check JavaScript files
        js_files = [
            'js/live_backend_monitoring_dashboard.js',
            'js/data-loader.js',
            'js/map-component.js',
            'js/api-tester.js',
            'js/ui-manager.js'
        ]
        
        js_results = {}
        for js_file in js_files:
            path = Path(js_file)
            exists = path.exists()
            
            if exists:
                content = path.read_text()
                # Check for key dashboard classes/functions
                has_dashboard_class = 'ORCASTLiveBackendDashboard' in content
                has_init_function = 'initialize' in content
                
                js_results[js_file] = {
                    'exists': True,
                    'size': len(content),
                    'has_dashboard_class': has_dashboard_class,
                    'has_init_function': has_init_function,
                    'status': 'PASS' if has_dashboard_class or has_init_function else 'WARN'
                }
            else:
                js_results[js_file] = {
                    'exists': False,
                    'status': 'FAIL'
                }
            
            status = "✅" if js_results[js_file]['status'] == 'PASS' else ("⚠️" if js_results[js_file]['status'] == 'WARN' else "❌")
            print(f"  {status} {js_file}")
        
        dashboard_results['javascript_files'] = js_results
        
        # Check CSS files
        css_files = ['css/base.css', 'css/sidebar.css', 'css/tabs.css', 'css/inspection.css']
        css_results = {}
        
        for css_file in css_files:
            path = Path(css_file)
            exists = path.exists()
            css_results[css_file] = {
                'exists': exists,
                'status': 'PASS' if exists else 'FAIL'
            }
            
            status = "✅" if exists else "❌"
            print(f"  {status} {css_file}")
        
        dashboard_results['css_files'] = css_results
        
        self.validation_results['dashboard_dependencies'] = dashboard_results
        
        total_deps = len(js_results) + len(css_results)
        passed_deps = sum(1 for r in {**js_results, **css_results}.values() if r['status'] == 'PASS')
        print(f"📊 Dashboard Dependencies: {passed_deps}/{total_deps} files ready")

    async def validate_data_flows(self):
        """Validate end-to-end data flows"""
        print("\n🔄 Validating Data Flows...")
        
        flow_results = {}
        
        # Test ML prediction flow
        try:
            async with aiohttp.ClientSession() as session:
                # Test Firestore ML service prediction
                ml_url = f"{self.services['firestore_ml']}/forecast/quick"
                payload = {'lat': 48.5465, 'lng': -123.0307}
                
                async with session.post(ml_url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        flow_results['ml_prediction_flow'] = {
                            'success': True,
                            'response_size': len(str(data)),
                            'has_prediction': 'probability' in str(data).lower(),
                            'status': 'PASS'
                        }
                    else:
                        flow_results['ml_prediction_flow'] = {
                            'success': False,
                            'status_code': response.status,
                            'status': 'FAIL'
                        }
        except Exception as e:
            flow_results['ml_prediction_flow'] = {
                'success': False,
                'error': str(e),
                'status': 'FAIL'
            }
        
        # Test dashboard initialization flow
        dashboard_js_path = Path('js/live_backend_monitoring_dashboard.js')
        if dashboard_js_path.exists():
            content = dashboard_js_path.read_text()
            has_endpoints = 'endpoints' in content and 'url' in content
            has_cost_tracking = 'CostTracker' in content
            has_initialization = 'initialize' in content
            
            flow_results['dashboard_initialization'] = {
                'js_file_exists': True,
                'has_endpoints': has_endpoints,
                'has_cost_tracking': has_cost_tracking,
                'has_initialization': has_initialization,
                'status': 'PASS' if all([has_endpoints, has_cost_tracking, has_initialization]) else 'WARN'
            }
        else:
            flow_results['dashboard_initialization'] = {
                'js_file_exists': False,
                'status': 'FAIL'
            }
        
        self.validation_results['data_flows'] = flow_results
        
        for flow_name, result in flow_results.items():
            status = "✅" if result['status'] == 'PASS' else ("⚠️" if result['status'] == 'WARN' else "❌")
            print(f"  {status} {flow_name}")
        
        passed_flows = sum(1 for r in flow_results.values() if r['status'] == 'PASS')
        total_flows = len(flow_results)
        print(f"🔄 Data Flows: {passed_flows}/{total_flows} flows validated")

    def generate_validation_report(self, duration: float):
        """Generate comprehensive validation report"""
        print("\n" + "=" * 60)
        print("📋 ORCAST LIVE SYSTEM VALIDATION REPORT")
        print("=" * 60)
        
        # Summary statistics
        total_checks = 0
        passed_checks = 0
        
        for category, results in self.validation_results.items():
            if isinstance(results, dict):
                for item, result in results.items():
                    total_checks += 1
                    if isinstance(result, dict) and result.get('status') == 'PASS':
                        passed_checks += 1
        
        success_rate = (passed_checks / total_checks * 100) if total_checks > 0 else 0
        
        print(f"⏱️  Duration: {duration:.2f} seconds")
        print(f"📊 Total Checks: {total_checks}")
        print(f"✅ Passed: {passed_checks}")
        print(f"❌ Failed: {total_checks - passed_checks}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        # Category breakdown
        print(f"\n📂 Category Breakdown:")
        for category, results in self.validation_results.items():
            if isinstance(results, dict):
                category_total = len(results)
                category_passed = sum(1 for r in results.values() if isinstance(r, dict) and r.get('status') == 'PASS')
                category_rate = (category_passed / category_total * 100) if category_total > 0 else 0
                print(f"  {category}: {category_passed}/{category_total} ({category_rate:.0f}%)")
        
        # Overall status
        if success_rate >= 90:
            status = "🟢 EXCELLENT - System ready for live monitoring"
        elif success_rate >= 75:
            status = "🟡 GOOD - Minor issues, mostly functional"
        elif success_rate >= 50:
            status = "🟠 NEEDS ATTENTION - Several components need fixing"
        else:
            status = "🔴 CRITICAL - Major issues prevent live monitoring"
        
        print(f"\n🎯 Overall Status: {status}")
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"validation_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'duration_seconds': duration,
                'summary': {
                    'total_checks': total_checks,
                    'passed_checks': passed_checks,
                    'failed_checks': total_checks - passed_checks,
                    'success_rate': success_rate
                },
                'detailed_results': self.validation_results
            }, f, indent=2)
        
        print(f"💾 Detailed report saved: {report_file}")
        
        return success_rate >= 75  # Return True if system is mostly functional

async def main():
    """Run the validation"""
    validator = ORCASTSystemValidator()
    success = await validator.run_full_validation()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main()) 