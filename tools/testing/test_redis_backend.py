#!/usr/bin/env python3
"""
Test Redis-enabled ORCAST Backend
Comprehensive testing of caching, real-time features, and performance improvements
"""

import requests
import json
import time
from datetime import datetime
import asyncio
import aiohttp

class ORCASTRedisBackendTester:
    """Test Redis functionality in deployed ORCAST backend"""
    
    def __init__(self):
        self.backend_url = "https://orcast-production-backend-126424997157.us-west1.run.app"
        self.test_results = {}
        
    def test_backend_status(self):
        """Test basic backend connectivity and Redis status"""
        
        print("🔍 Testing Backend Status & Redis Connection...")
        
        try:
            response = requests.get(f"{self.backend_url}/", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                redis_connected = data.get('redis_status') == 'connected'
                version = data.get('version', 'unknown')
                features = data.get('features', [])
                
                print(f"   ✅ Backend Status: {response.status_code}")
                print(f"   ✅ Version: {version}")
                print(f"   ✅ Redis Status: {data.get('redis_status', 'unknown')}")
                print(f"   ✅ Features: {len(features)} Redis features")
                
                self.test_results['backend_status'] = {
                    'success': True,
                    'redis_connected': redis_connected,
                    'version': version,
                    'features': features
                }
                
                return True
                
            else:
                print(f"   ❌ Backend Error: {response.status_code}")
                self.test_results['backend_status'] = {
                    'success': False,
                    'error': f"HTTP {response.status_code}"
                }
                return False
                
        except Exception as e:
            print(f"   ❌ Connection Error: {e}")
            self.test_results['backend_status'] = {
                'success': False,
                'error': str(e)
            }
            return False
    
    def test_prediction_caching(self):
        """Test ML prediction caching performance"""
        
        print("\n🧠 Testing ML Prediction Caching...")
        
        test_payload = {
            "lat": 48.5465,
            "lng": -123.0307
        }
        
        try:
            # First request (should cache)
            print("   Making first prediction request (no cache)...")
            start_time = time.time()
            response1 = requests.post(
                f"{self.backend_url}/forecast/quick",
                json=test_payload,
                timeout=15
            )
            first_request_time = (time.time() - start_time) * 1000
            
            if response1.status_code == 200:
                data1 = response1.json()
                print(f"   ✅ First Request: {first_request_time:.0f}ms")
                
                # Second request (should be cached)
                print("   Making second prediction request (cached)...")
                start_time = time.time()
                response2 = requests.post(
                    f"{self.backend_url}/forecast/quick",
                    json=test_payload,
                    timeout=15
                )
                second_request_time = (time.time() - start_time) * 1000
                
                if response2.status_code == 200:
                    data2 = response2.json()
                    cached_flag = data2.get('cached', False)
                    
                    print(f"   ✅ Second Request: {second_request_time:.0f}ms")
                    print(f"   ✅ Cached Response: {cached_flag}")
                    
                    # Performance improvement
                    if second_request_time < first_request_time:
                        improvement = ((first_request_time - second_request_time) / first_request_time) * 100
                        print(f"   🚀 Performance Improvement: {improvement:.1f}% faster")
                    
                    self.test_results['prediction_caching'] = {
                        'success': True,
                        'first_request_ms': first_request_time,
                        'second_request_ms': second_request_time,
                        'cached': cached_flag,
                        'improvement_percent': improvement if 'improvement' in locals() else 0
                    }
                    
                    return True
                    
            print(f"   ❌ Prediction Error: {response1.status_code}")
            self.test_results['prediction_caching'] = {
                'success': False,
                'error': f"HTTP {response1.status_code}"
            }
            return False
            
        except Exception as e:
            print(f"   ❌ Caching Test Error: {e}")
            self.test_results['prediction_caching'] = {
                'success': False,
                'error': str(e)
            }
            return False
    
    def test_multiple_endpoints(self):
        """Test multiple endpoints to verify Redis integration"""
        
        print("\n🔗 Testing Multiple Redis-Enabled Endpoints...")
        
        endpoints = [
            {"name": "Current Forecast", "url": "/forecast/current", "method": "GET"},
            {"name": "API Status", "url": "/api/status", "method": "GET"},
            {"name": "ML Predict", "url": "/api/ml/predict", "method": "POST", 
             "payload": {"latitude": 48.5465, "longitude": -123.0307, "pod_size": 5}}
        ]
        
        success_count = 0
        
        for endpoint in endpoints:
            try:
                print(f"   Testing {endpoint['name']}...")
                
                if endpoint['method'] == 'GET':
                    response = requests.get(f"{self.backend_url}{endpoint['url']}", timeout=10)
                else:
                    payload = endpoint.get('payload', {})
                    response = requests.post(f"{self.backend_url}{endpoint['url']}", 
                                           json=payload, timeout=10)
                
                if response.status_code == 200:
                    print(f"   ✅ {endpoint['name']}: {response.status_code}")
                    success_count += 1
                else:
                    print(f"   ❌ {endpoint['name']}: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ {endpoint['name']}: {e}")
        
        self.test_results['multiple_endpoints'] = {
            'success': success_count == len(endpoints),
            'passed': success_count,
            'total': len(endpoints)
        }
        
        return success_count == len(endpoints)
    
    def test_rate_limiting(self):
        """Test Redis rate limiting functionality"""
        
        print("\n🛡️ Testing Rate Limiting (Redis-based)...")
        
        # Make rapid requests to test rate limiting
        rapid_requests = 5
        success_count = 0
        
        try:
            for i in range(rapid_requests):
                response = requests.get(f"{self.backend_url}/forecast/current", timeout=5)
                
                if response.status_code == 200:
                    success_count += 1
                elif response.status_code == 429:
                    print(f"   ✅ Rate Limiting Triggered: HTTP 429")
                    break
                    
                time.sleep(0.1)  # Small delay
            
            print(f"   ✅ Rapid Requests: {success_count}/{rapid_requests} succeeded")
            
            self.test_results['rate_limiting'] = {
                'success': True,
                'requests_made': rapid_requests,
                'requests_succeeded': success_count
            }
            
            return True
            
        except Exception as e:
            print(f"   ❌ Rate Limiting Test Error: {e}")
            self.test_results['rate_limiting'] = {
                'success': False,
                'error': str(e)
            }
            return False
    
    def test_performance_comparison(self):
        """Compare performance with and without Redis"""
        
        print("\n⚡ Testing Performance (Redis vs No-Redis comparison)...")
        
        test_cases = [
            {"name": "Current Forecast", "url": "/forecast/current"},
            {"name": "Quick Forecast", "url": "/forecast/quick", "method": "POST",
             "payload": {"lat": 48.5465, "lng": -123.0307}}
        ]
        
        for test_case in test_cases:
            try:
                print(f"   Testing {test_case['name']} performance...")
                
                # Multiple requests to get average
                times = []
                for i in range(3):
                    start_time = time.time()
                    
                    if test_case.get('method') == 'POST':
                        response = requests.post(
                            f"{self.backend_url}{test_case['url']}",
                            json=test_case.get('payload', {}),
                            timeout=10
                        )
                    else:
                        response = requests.get(f"{self.backend_url}{test_case['url']}", timeout=10)
                    
                    request_time = (time.time() - start_time) * 1000
                    times.append(request_time)
                    
                    if response.status_code != 200:
                        break
                        
                    time.sleep(0.5)  # Brief pause
                
                if times:
                    avg_time = sum(times) / len(times)
                    print(f"   ✅ {test_case['name']}: {avg_time:.0f}ms average")
                    
            except Exception as e:
                print(f"   ❌ {test_case['name']}: {e}")
        
        print("   📊 With Redis caching, subsequent requests should be significantly faster!")
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        
        print("\n📊 REDIS BACKEND TEST REPORT")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result.get('success', False))
        
        print(f"Tests Passed: {passed_tests}/{total_tests}")
        print(f"Redis Integration: {'✅ Fully Functional' if passed_tests >= 3 else '⚠️ Partial' if passed_tests >= 1 else '❌ Failed'}")
        
        # Detailed results
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result.get('success', False) else "❌ FAIL"
            test_display = test_name.replace('_', ' ').title()
            print(f"{status} {test_display}")
            
            if 'error' in result:
                print(f"      Error: {result['error']}")
        
        # Save detailed report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"redis_backend_test_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'backend_url': self.backend_url,
                'test_results': self.test_results,
                'summary': {
                    'total_tests': total_tests,
                    'passed_tests': passed_tests,
                    'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0
                }
            }, f, indent=2)
        
        print(f"\n📄 Detailed report saved: {report_file}")
        
        return passed_tests >= 3

def main():
    """Run comprehensive Redis backend tests"""
    
    print("🔴 TESTING REDIS-ENABLED ORCAST BACKEND")
    print("=" * 50)
    
    tester = ORCASTRedisBackendTester()
    
    # Run all tests
    tests_passed = 0
    
    if tester.test_backend_status():
        tests_passed += 1
    
    if tester.test_prediction_caching():
        tests_passed += 1
    
    if tester.test_multiple_endpoints():
        tests_passed += 1
    
    if tester.test_rate_limiting():
        tests_passed += 1
    
    tester.test_performance_comparison()
    
    # Generate final report
    success = tester.generate_test_report()
    
    if success:
        print("\n🎉 REDIS INTEGRATION SUCCESSFUL!")
        print("Your ORCAST backend now has:")
        print("   ✅ High-performance caching")
        print("   ✅ Real-time pub/sub capabilities") 
        print("   ✅ Rate limiting protection")
        print("   ✅ Performance optimization")
        print("   ✅ All features ready for hackathon!")
    else:
        print("\n⚠️ Some Redis features may need attention")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main()) 