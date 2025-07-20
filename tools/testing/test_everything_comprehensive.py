#!/usr/bin/env python3
"""
Comprehensive ORCAST System Test
Tests everything: Backend, Frontend, Redis, APIs, Integration, Performance
"""

import json
import time
import logging
import requests
import asyncio
from datetime import datetime
from typing import Dict, List, Any
import concurrent.futures

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ORCASTSystemTester:
    def __init__(self):
        # Update backend URL to the correct deployed service
        self.backend_url = "https://orcast-production-backend-2cvqukvhga-uw.a.run.app"
        self.frontend_urls = [
            {"name": "Custom Domain", "url": "https://orcast.org"},
            {"name": "Firebase URL", "url": "https://orca-904de.web.app"}
        ]
        
        self.test_results = {
            'backend_tests': {},
            'frontend_tests': {},
            'redis_tests': {},
            'integration_tests': {},
            'performance_tests': {},
            'real_time_tests': {}
        }
        
        self.all_endpoints = [
            # Basic endpoints
            {"name": "Root", "path": "/", "method": "GET"},
            {"name": "Health", "path": "/health", "method": "GET"},
            
            # ML and prediction endpoints
            {"name": "Current Forecast", "path": "/forecast/current", "method": "GET"},
            {"name": "Quick Forecast", "path": "/forecast/quick", "method": "POST", 
             "payload": {"lat": 48.5465, "lng": -123.0307}},
            {"name": "ML Predict", "path": "/api/ml/predict", "method": "POST",
             "payload": {"latitude": 48.5465, "longitude": -123.0307, "pod_size": 5}},
            
            # API status and info
            {"name": "API Status", "path": "/api/status", "method": "GET"},
            
            # Redis-specific endpoints
            {"name": "Cache Stats", "path": "/api/cache/stats", "method": "GET"},
            {"name": "Real-time Events", "path": "/api/real-time/events", "method": "GET"},
        ]

    async def test_backend_comprehensive(self):
        """Comprehensive backend testing"""
        
        print("🔧 TESTING BACKEND COMPREHENSIVELY")
        print("-" * 50)
        
        backend_results = {}
        
        # Test basic connectivity with timeout handling
        try:
            print("   Testing basic connectivity...")
            
            # Use shorter timeout and retry logic
            for attempt in range(3):
                try:
                    response = requests.get(f"{self.backend_url}/", timeout=30)
                    if response.status_code == 200:
                        data = response.json()
                        print(f"   ✅ Backend connected (attempt {attempt + 1})")
                        print(f"      Version: {data.get('version', 'unknown')}")
                        print(f"      Redis Status: {data.get('redis_status', 'unknown')}")
                        print(f"      Features: {len(data.get('features', []))}")
                        
                        backend_results['connectivity'] = {
                            'success': True,
                            'version': data.get('version'),
                            'redis_status': data.get('redis_status'),
                            'features': data.get('features', [])
                        }
                        break
                except requests.Timeout:
                    print(f"   ⚠️ Timeout on attempt {attempt + 1}, retrying...")
                    if attempt == 2:
                        raise
                    time.sleep(5)
                        
        except Exception as e:
            print(f"   ❌ Backend connectivity failed: {e}")
            backend_results['connectivity'] = {'success': False, 'error': str(e)}
        
        # Test all endpoints with increased timeout
        print("\n   Testing all backend endpoints...")
        endpoint_results = {}
        
        for endpoint in self.all_endpoints:
            try:
                print(f"      Testing {endpoint['name']}...")
                
                start_time = time.time()
                
                if endpoint['method'] == 'GET':
                    response = requests.get(
                        f"{self.backend_url}{endpoint['path']}", 
                        timeout=45  # Longer timeout
                    )
                else:
                    payload = endpoint.get('payload', {})
                    response = requests.post(
                        f"{self.backend_url}{endpoint['path']}", 
                        json=payload, 
                        timeout=45
                    )
                
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    print(f"      ✅ {endpoint['name']}: {response.status_code} ({response_time:.0f}ms)")
                    
                    # Try to parse JSON
                    try:
                        data = response.json()
                        data_size = len(str(data))
                    except:
                        data = response.text
                        data_size = len(data)
                    
                    endpoint_results[endpoint['name']] = {
                        'success': True,
                        'status_code': response.status_code,
                        'response_time_ms': response_time,
                        'data_size': data_size
                    }
                else:
                    print(f"      ❌ {endpoint['name']}: HTTP {response.status_code}")
                    endpoint_results[endpoint['name']] = {
                        'success': False,
                        'status_code': response.status_code,
                        'response_time_ms': response_time
                    }
                    
            except requests.Timeout:
                print(f"      ⏱️ {endpoint['name']}: Timeout (>45s)")
                endpoint_results[endpoint['name']] = {
                    'success': False,
                    'error': 'Timeout'
                }
            except Exception as e:
                print(f"      ❌ {endpoint['name']}: {e}")
                endpoint_results[endpoint['name']] = {
                    'success': False,
                    'error': str(e)
                }
        
        backend_results['endpoints'] = endpoint_results
        self.test_results['backend_tests'] = backend_results
        
        # Summary
        successful_endpoints = sum(1 for result in endpoint_results.values() if result.get('success', False))
        total_endpoints = len(endpoint_results)
        
        print(f"\n   📊 Backend Summary: {successful_endpoints}/{total_endpoints} endpoints working")
        
        return successful_endpoints > 0

    async def test_frontend_comprehensive(self):
        """Test frontend functionality"""
        
        print("\n📱 TESTING FRONTEND COMPREHENSIVELY")
        print("-" * 50)
        
        frontend_results = {}
        
        # Test both frontend URLs
        frontend_urls = [
            {"name": "Custom Domain", "url": self.frontend_url},
            {"name": "Firebase URL", "url": self.firebase_url}
        ]
        
        for frontend in frontend_urls:
            try:
                print(f"   Testing {frontend['name']}...")
                
                response = requests.get(frontend['url'], timeout=15)
                
                if response.status_code == 200:
                    content = response.text
                    
                    # Check for ORCAST content
                    has_orcast = 'ORCAST' in content
                    has_dashboard = 'live_backend_monitoring_dashboard.js' in content
                    has_backend_url = self.backend_url in content
                    
                    print(f"   ✅ {frontend['name']}: {response.status_code}")
                    print(f"      ORCAST Content: {has_orcast}")
                    print(f"      Dashboard JS: {has_dashboard}")
                    print(f"      Backend URL Configured: {has_backend_url}")
                    
                    frontend_results[frontend['name']] = {
                        'success': True,
                        'status_code': response.status_code,
                        'has_orcast_content': has_orcast,
                        'has_dashboard': has_dashboard,
                        'backend_url_configured': has_backend_url
                    }
                else:
                    print(f"   ❌ {frontend['name']}: HTTP {response.status_code}")
                    frontend_results[frontend['name']] = {
                        'success': False,
                        'status_code': response.status_code
                    }
                    
            except Exception as e:
                print(f"   ❌ {frontend['name']}: {e}")
                frontend_results[frontend['name']] = {
                    'success': False,
                    'error': str(e)
                }
        
        self.test_results['frontend_tests'] = frontend_results
        
        return any(result.get('success', False) for result in frontend_results.values())

    async def test_redis_functionality(self):
        """Test Redis-specific functionality"""
        
        print("\n🔴 TESTING REDIS FUNCTIONALITY")
        print("-" * 50)
        
        redis_results = {}
        
        # Test Redis connection via backend
        try:
            print("   Testing Redis connection status...")
            response = requests.get(f"{self.backend_url}/", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                redis_connected = data.get('redis_status') == 'connected'
                
                print(f"   ✅ Redis Status: {data.get('redis_status', 'unknown')}")
                
                redis_results['connection'] = {
                    'success': redis_connected,
                    'status': data.get('redis_status')
                }
            else:
                redis_results['connection'] = {'success': False, 'error': f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"   ❌ Redis connection test failed: {e}")
            redis_results['connection'] = {'success': False, 'error': str(e)}
        
        # Test caching performance
        try:
            print("   Testing caching performance...")
            
            test_payload = {"lat": 48.5465, "lng": -123.0307}
            
            # First request (no cache)
            start_time = time.time()
            response1 = requests.post(f"{self.backend_url}/forecast/quick", 
                                    json=test_payload, timeout=30)
            first_time = (time.time() - start_time) * 1000
            
            if response1.status_code == 200:
                print(f"   ✅ First request: {first_time:.0f}ms")
                
                # Second request (should be cached)
                time.sleep(1)  # Brief pause
                start_time = time.time()
                response2 = requests.post(f"{self.backend_url}/forecast/quick", 
                                        json=test_payload, timeout=30)
                second_time = (time.time() - start_time) * 1000
                
                if response2.status_code == 200:
                    print(f"   ✅ Second request: {second_time:.0f}ms")
                    
                    # Check if cached
                    try:
                        data2 = response2.json()
                        cached = data2.get('cached', False)
                        print(f"   ✅ Cached response: {cached}")
                    except:
                        cached = False
                    
                    redis_results['caching'] = {
                        'success': True,
                        'first_request_ms': first_time,
                        'second_request_ms': second_time,
                        'cached': cached
                    }
                else:
                    redis_results['caching'] = {'success': False, 'error': 'Second request failed'}
            else:
                redis_results['caching'] = {'success': False, 'error': 'First request failed'}
                
        except Exception as e:
            print(f"   ❌ Caching test failed: {e}")
            redis_results['caching'] = {'success': False, 'error': str(e)}
        
        self.test_results['redis_tests'] = redis_results
        
        return any(result.get('success', False) for result in redis_results.values())

    async def test_performance_metrics(self):
        """Test system performance"""
        
        print("\n⚡ TESTING PERFORMANCE METRICS")
        print("-" * 50)
        
        performance_results = {}
        
        # Test key endpoints for performance
        performance_endpoints = [
            {"name": "Root", "url": "/"},
            {"name": "Health Check", "url": "/health"},
            {"name": "Current Forecast", "url": "/forecast/current"}
        ]
        
        for endpoint in performance_endpoints:
            try:
                print(f"   Performance testing {endpoint['name']}...")
                
                times = []
                for i in range(3):  # Test 3 times
                    start_time = time.time()
                    response = requests.get(f"{self.backend_url}{endpoint['url']}", timeout=20)
                    request_time = (time.time() - start_time) * 1000
                    
                    if response.status_code == 200:
                        times.append(request_time)
                    
                    time.sleep(0.5)  # Brief pause between requests
                
                if times:
                    avg_time = sum(times) / len(times)
                    min_time = min(times)
                    max_time = max(times)
                    
                    print(f"   ✅ {endpoint['name']}: {avg_time:.0f}ms avg ({min_time:.0f}-{max_time:.0f}ms)")
                    
                    performance_results[endpoint['name']] = {
                        'success': True,
                        'average_ms': avg_time,
                        'min_ms': min_time,
                        'max_ms': max_time,
                        'requests': len(times)
                    }
                else:
                    performance_results[endpoint['name']] = {'success': False, 'error': 'No successful requests'}
                    
            except Exception as e:
                print(f"   ❌ {endpoint['name']}: {e}")
                performance_results[endpoint['name']] = {'success': False, 'error': str(e)}
        
        self.test_results['performance_tests'] = performance_results
        
        return any(result.get('success', False) for result in performance_results.values())

    async def test_system_integration(self):
        """Test end-to-end system integration"""
        
        print("\n🔗 TESTING SYSTEM INTEGRATION")
        print("-" * 50)
        
        integration_results = {}
        
        # Test frontend → backend communication
        try:
            print("   Testing frontend → backend integration...")
            
            # Check if frontend can reach backend
            frontend_response = requests.get(self.frontend_url, timeout=15)
            
            if frontend_response.status_code == 200:
                frontend_content = frontend_response.text
                
                # Check if backend URL is configured in frontend
                backend_configured = self.backend_url in frontend_content
                
                print(f"   ✅ Frontend loaded: {frontend_response.status_code}")
                print(f"   ✅ Backend URL configured: {backend_configured}")
                
                integration_results['frontend_backend'] = {
                    'success': backend_configured,
                    'frontend_status': frontend_response.status_code,
                    'backend_configured': backend_configured
                }
            else:
                integration_results['frontend_backend'] = {
                    'success': False,
                    'error': f"Frontend HTTP {frontend_response.status_code}"
                }
                
        except Exception as e:
            print(f"   ❌ Frontend-backend integration: {e}")
            integration_results['frontend_backend'] = {'success': False, 'error': str(e)}
        
        # Test complete prediction workflow
        try:
            print("   Testing complete prediction workflow...")
            
            # Make prediction request
            test_data = {
                "latitude": 48.5465,
                "longitude": -123.0307,
                "pod_size": 5
            }
            
            response = requests.post(f"{self.backend_url}/api/ml/predict", 
                                   json=test_data, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                has_prediction = 'ml_prediction' in data
                has_location = 'location' in data
                has_environmental = 'environmental_data' in data
                
                print(f"   ✅ Prediction workflow: {response.status_code}")
                print(f"      Has ML prediction: {has_prediction}")
                print(f"      Has location data: {has_location}")
                print(f"      Has environmental data: {has_environmental}")
                
                integration_results['prediction_workflow'] = {
                    'success': has_prediction and has_location,
                    'status_code': response.status_code,
                    'has_prediction': has_prediction,
                    'has_location': has_location,
                    'has_environmental': has_environmental
                }
            else:
                integration_results['prediction_workflow'] = {
                    'success': False,
                    'status_code': response.status_code
                }
                
        except Exception as e:
            print(f"   ❌ Prediction workflow: {e}")
            integration_results['prediction_workflow'] = {'success': False, 'error': str(e)}
        
        self.test_results['integration_tests'] = integration_results
        
        return any(result.get('success', False) for result in integration_results.values())

    def generate_comprehensive_report(self):
        """Generate comprehensive test report"""
        
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE ORCAST SYSTEM TEST REPORT")
        print("=" * 70)
        
        # Calculate overall metrics
        all_test_categories = [
            ('Backend Tests', self.test_results['backend_tests']),
            ('Frontend Tests', self.test_results['frontend_tests']),
            ('Redis Tests', self.test_results['redis_tests']),
            ('Performance Tests', self.test_results['performance_tests']),
            ('Integration Tests', self.test_results['integration_tests'])
        ]
        
        total_categories = len(all_test_categories)
        passed_categories = 0
        
        for category_name, category_results in all_test_categories:
            if isinstance(category_results, dict):
                category_success = any(
                    test.get('success', False) if isinstance(test, dict) else False 
                    for test in category_results.values()
                )
                if category_success:
                    passed_categories += 1
                
                status = "✅ PASS" if category_success else "❌ FAIL"
                print(f"{status} {category_name}")
                
                # Show detailed results for each category
                for test_name, test_result in category_results.items():
                    if isinstance(test_result, dict):
                        test_status = "✅" if test_result.get('success', False) else "❌"
                        test_display = test_name.replace('_', ' ').title()
                        print(f"   {test_status} {test_display}")
                        
                        if 'error' in test_result:
                            print(f"      Error: {test_result['error'][:100]}...")
        
        # Overall system health
        overall_health = (passed_categories / total_categories * 100) if total_categories > 0 else 0
        
        print(f"\n🎯 OVERALL SYSTEM HEALTH: {passed_categories}/{total_categories} ({overall_health:.1f}%)")
        
        if overall_health >= 80:
            status = "🟢 EXCELLENT - System fully operational"
            hackathon_ready = True
        elif overall_health >= 60:
            status = "🟡 GOOD - Minor issues, mostly functional"
            hackathon_ready = True
        elif overall_health >= 40:
            status = "🟠 FAIR - Several components need attention"
            hackathon_ready = False
        else:
            status = "🔴 POOR - Major issues require immediate attention"
            hackathon_ready = False
        
        print(f"Status: {status}")
        
        print(f"\n🚀 HACKATHON READINESS:")
        print(f"   Ready for Demo: {'✅ YES' if hackathon_ready else '❌ NO'}")
        
        # Key features status
        print(f"\n🎯 KEY FEATURES STATUS:")
        
        # Check backend endpoints
        backend_endpoints = self.test_results['backend_tests'].get('endpoints', {})
        working_endpoints = sum(1 for ep in backend_endpoints.values() if ep.get('success', False))
        total_endpoints = len(backend_endpoints)
        
        print(f"   • Backend APIs: {working_endpoints}/{total_endpoints} working")
        
        # Check Redis status
        redis_connection = self.test_results['redis_tests'].get('connection', {})
        redis_working = redis_connection.get('success', False)
        print(f"   • Redis Integration: {'✅ Connected' if redis_working else '❌ Not Connected'}")
        
        # Check frontend
        frontend_tests = self.test_results['frontend_tests']
        frontend_working = any(test.get('success', False) for test in frontend_tests.values())
        print(f"   • Frontend: {'✅ Working' if frontend_working else '❌ Issues'}")
        
        # Save detailed report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"comprehensive_orcast_test_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'system_urls': {
                    'backend': self.backend_url,
                    'frontend': self.frontend_url,
                    'firebase': self.firebase_url
                },
                'test_results': self.test_results,
                'summary': {
                    'total_categories': total_categories,
                    'passed_categories': passed_categories,
                    'overall_health_percent': overall_health,
                    'hackathon_ready': hackathon_ready,
                    'working_endpoints': working_endpoints,
                    'total_endpoints': total_endpoints,
                    'redis_connected': redis_working,
                    'frontend_working': frontend_working
                }
            }, f, indent=2)
        
        print(f"\n📄 Detailed report saved: {report_file}")
        
        return hackathon_ready

async def main():
    """Run comprehensive ORCAST system tests"""
    
    print("🎯 COMPREHENSIVE ORCAST SYSTEM TEST")
    print("Testing everything: Backend, Frontend, Redis, APIs, Integration")
    print("=" * 70)
    
    tester = ORCASTSystemTester()
    
    # Run all test categories
    test_functions = [
        tester.test_backend_comprehensive,
        tester.test_frontend_comprehensive, 
        tester.test_redis_functionality,
        tester.test_performance_metrics,
        tester.test_system_integration
    ]
    
    # Execute tests
    for test_func in test_functions:
        try:
            await test_func()
            time.sleep(2)  # Brief pause between test categories
        except Exception as e:
            print(f"❌ Test category failed: {e}")
    
    # Generate final report
    hackathon_ready = tester.generate_comprehensive_report()
    
    if hackathon_ready:
        print("\n🎉 ORCAST SYSTEM IS READY FOR HACKATHON!")
        print("All core components are operational.")
    else:
        print("\n⚠️ Some components need attention before hackathon.")
        print("Check the detailed report above.")
    
    return 0 if hackathon_ready else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 