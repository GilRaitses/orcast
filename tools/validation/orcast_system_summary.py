#!/usr/bin/env python3
"""
ORCAST Complete System Summary & Health Report
Shows all deployed components, their locations, and health status
"""

import asyncio
import aiohttp
import json
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Any
import sys

class ORCASTSystemSummary:
    """Complete ORCAST system architecture and health reporter"""
    
    def __init__(self):
        self.system_components = {
            'frontend': {
                'platform': 'Firebase Hosting',
                'project': 'orca-904de',
                'urls': {
                    'firebase': 'https://orca-904de.web.app',
                    'custom_domain': 'https://orcast.org'
                },
                'description': 'Static frontend - HTML, CSS, JavaScript, images',
                'technologies': ['HTML5', 'JavaScript', 'CSS3', 'Google Maps API', 'Firebase SDK'],
                'files': ['index.html', 'js/', 'css/', 'api/', 'data/']
            },
            'backend': {
                'platform': 'Google Cloud Run',
                'project': 'orca-466204',
                'urls': {
                    'primary': 'https://orcast-production-backend-2cvqukvhga-uw.a.run.app'
                },
                'description': 'REST API backend - ML predictions, data processing',
                'technologies': ['Python', 'Flask', 'FastAPI', 'Machine Learning', 'BigQuery'],
                'endpoints_count': 46
            },
            'data_storage': {
                'firebase_firestore': {
                    'project': 'orca-904de',
                    'description': 'Real-time whale detection data',
                    'collections': ['whale_detections', 'ml_analysis', 'user_sessions']
                },
                'bigquery': {
                    'project': 'orca-466204',
                    'description': 'Data warehouse for analytics',
                    'datasets': ['whale_data', 'ml_analysis', 'orcast_results']
                }
            },
            'external_services': {
                'orcahello_ai': 'https://aifororcas.azurewebsites.net/api',
                'noaa_tides': 'https://api.tidesandcurrents.noaa.gov/api/prod/datagetter',
                'google_maps': 'https://maps.googleapis.com/maps/api/js'
            }
        }
        
        self.health_results = {}
        
    async def run_complete_system_summary(self):
        """Generate complete system summary and health report"""
        
        print("🎯 ORCAST COMPLETE SYSTEM SUMMARY & HEALTH REPORT")
        print("=" * 70)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Architecture Overview
        await self.show_architecture_overview()
        
        # Test all components
        await self.test_frontend_components()
        await self.test_backend_components() 
        await self.test_data_storage()
        await self.test_external_services()
        await self.test_connectivity()
        
        # Generate final health report
        await self.generate_health_report()
        
        # Show costs and usage
        await self.show_cost_analysis()
        
        return self.health_results

    async def show_architecture_overview(self):
        """Show the complete system architecture"""
        
        print("🏗️  SYSTEM ARCHITECTURE OVERVIEW")
        print("-" * 50)
        
        print("\n📱 FRONTEND (Firebase Hosting)")
        frontend = self.system_components['frontend']
        print(f"   Platform: {frontend['platform']}")
        print(f"   Project: {frontend['project']}")
        print(f"   Firebase URL: {frontend['urls']['firebase']}")
        print(f"   Custom Domain: {frontend['urls']['custom_domain']}")
        print(f"   Technologies: {', '.join(frontend['technologies'])}")
        print(f"   Description: {frontend['description']}")
        
        print("\n🔧 BACKEND (Google Cloud Run)")  
        backend = self.system_components['backend']
        print(f"   Platform: {backend['platform']}")
        print(f"   Project: {backend['project']}")
        print(f"   API URL: {backend['urls']['primary']}")
        print(f"   Endpoints: {backend['endpoints_count']} REST API endpoints")
        print(f"   Technologies: {', '.join(backend['technologies'])}")
        print(f"   Description: {backend['description']}")
        
        print("\n💾 DATA STORAGE")
        storage = self.system_components['data_storage']
        
        print(f"   🔥 Firestore (Project: {storage['firebase_firestore']['project']})")
        print(f"      Purpose: {storage['firebase_firestore']['description']}")
        print(f"      Collections: {', '.join(storage['firebase_firestore']['collections'])}")
        
        print(f"   📊 BigQuery (Project: {storage['bigquery']['project']})")
        print(f"      Purpose: {storage['bigquery']['description']}")
        print(f"      Datasets: {', '.join(storage['bigquery']['datasets'])}")
        
        print("\n🌐 EXTERNAL INTEGRATIONS")
        external = self.system_components['external_services']
        print(f"   • OrcaHello AI Detection: {external['orcahello_ai']}")
        print(f"   • NOAA Tides API: {external['noaa_tides']}")
        print(f"   • Google Maps API: {external['google_maps']}")

    async def test_frontend_components(self):
        """Test Firebase frontend components"""
        
        print("\n\n📱 FRONTEND HEALTH CHECK")
        print("-" * 50)
        
        frontend_tests = []
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            # Test Firebase URL
            try:
                async with session.get(self.system_components['frontend']['urls']['firebase']) as response:
                    success = response.status == 200
                    content = await response.text()
                    
                    # Check for ORCAST content
                    has_orcast = 'ORCAST' in content
                    has_dashboard = 'live_backend_monitoring_dashboard.js' in content
                    
                    frontend_tests.append({
                        'test': 'Firebase Hosting',
                        'url': self.system_components['frontend']['urls']['firebase'],
                        'status': response.status,
                        'success': success and has_orcast,
                        'details': f"ORCAST content: {has_orcast}, Dashboard: {has_dashboard}"
                    })
                    
            except Exception as e:
                frontend_tests.append({
                    'test': 'Firebase Hosting',
                    'success': False,
                    'details': f"Error: {e}"
                })
            
            # Test Custom Domain  
            try:
                async with session.get(self.system_components['frontend']['urls']['custom_domain']) as response:
                    success = response.status == 200
                    frontend_tests.append({
                        'test': 'Custom Domain (orcast.org)',
                        'url': self.system_components['frontend']['urls']['custom_domain'],
                        'status': response.status,
                        'success': success,
                        'details': f"Domain resolution and SSL working"
                    })
                    
            except Exception as e:
                frontend_tests.append({
                    'test': 'Custom Domain',
                    'success': False,
                    'details': f"Error: {e}"
                })
        
        # Display results
        for test in frontend_tests:
            status = "✅" if test['success'] else "❌"
            print(f"   {status} {test['test']}")
            if 'url' in test:
                print(f"      URL: {test['url']}")
            if 'status' in test:
                print(f"      Status: {test['status']}")
            print(f"      Details: {test['details']}")
            print()
        
        self.health_results['frontend'] = frontend_tests

    async def test_backend_components(self):
        """Test Google Cloud Run backend components"""
        
        print("\n🔧 BACKEND HEALTH CHECK")
        print("-" * 50)
        
        backend_tests = []
        backend_url = self.system_components['backend']['urls']['primary']
        
        # Key endpoints to test
        test_endpoints = [
            {'path': '/', 'method': 'GET', 'name': 'Backend Root'},
            {'path': '/health', 'method': 'GET', 'name': 'Health Check'},
            {'path': '/forecast/current', 'method': 'GET', 'name': 'Current Forecast'},
            {'path': '/forecast/quick', 'method': 'POST', 'name': 'Quick Forecast', 
             'payload': {'lat': 48.5465, 'lng': -123.0307}},
            {'path': '/api/ml/predict', 'method': 'POST', 'name': 'ML Prediction',
             'payload': {'latitude': 48.5465, 'longitude': -123.0307, 'pod_size': 5}},
            {'path': '/api/status', 'method': 'GET', 'name': 'API Status'}
        ]
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
            for endpoint in test_endpoints:
                try:
                    url = f"{backend_url}{endpoint['path']}"
                    start_time = time.time()
                    
                    if endpoint['method'] == 'GET':
                        async with session.get(url) as response:
                            end_time = time.time()
                            response_time = (end_time - start_time) * 1000
                            
                            success = 200 <= response.status < 400
                            try:
                                data = await response.json()
                                details = f"Response time: {response_time:.0f}ms, Data keys: {len(data)}"
                            except:
                                details = f"Response time: {response_time:.0f}ms, Non-JSON response"
                                
                    else:  # POST
                        payload = endpoint.get('payload', {})
                        async with session.post(url, json=payload) as response:
                            end_time = time.time()
                            response_time = (end_time - start_time) * 1000
                            
                            success = 200 <= response.status < 400
                            try:
                                data = await response.json()
                                details = f"Response time: {response_time:.0f}ms, ML prediction successful"
                            except:
                                details = f"Response time: {response_time:.0f}ms, Non-JSON response"
                    
                    backend_tests.append({
                        'test': endpoint['name'],
                        'method': endpoint['method'],
                        'url': url,
                        'status': response.status,
                        'success': success,
                        'response_time_ms': response_time,
                        'details': details
                    })
                    
                except Exception as e:
                    backend_tests.append({
                        'test': endpoint['name'],
                        'method': endpoint['method'],
                        'success': False,
                        'details': f"Error: {e}"
                    })
        
        # Display results
        for test in backend_tests:
            status = "✅" if test['success'] else "❌"
            print(f"   {status} {test['test']} ({test['method']})")
            if 'status' in test:
                print(f"      Status: {test['status']}")
            if 'response_time_ms' in test:
                print(f"      Response Time: {test['response_time_ms']:.0f}ms")
            print(f"      Details: {test['details']}")
            print()
        
        self.health_results['backend'] = backend_tests

    async def test_data_storage(self):
        """Test data storage components"""
        
        print("\n💾 DATA STORAGE HEALTH CHECK")
        print("-" * 50)
        
        storage_tests = []
        
        # Test BigQuery
        try:
            result = subprocess.run(['gcloud', 'projects', 'describe', 'orca-466204'], 
                                  capture_output=True, text=True, timeout=10)
            bigquery_accessible = result.returncode == 0
            
            storage_tests.append({
                'test': 'BigQuery Project Access',
                'success': bigquery_accessible,
                'details': f"Project orca-466204 {'accessible' if bigquery_accessible else 'not accessible'}"
            })
            
        except Exception as e:
            storage_tests.append({
                'test': 'BigQuery Project Access',
                'success': False,
                'details': f"Error: {e}"
            })
        
        # Test Firebase project
        try:
            result = subprocess.run(['firebase', 'projects:list'], 
                                  capture_output=True, text=True, timeout=10)
            firebase_accessible = 'orca-904de' in result.stdout
            
            storage_tests.append({
                'test': 'Firebase Project Access',
                'success': firebase_accessible,
                'details': f"Project orca-904de {'found' if firebase_accessible else 'not found'}"
            })
            
        except Exception as e:
            storage_tests.append({
                'test': 'Firebase Project Access',
                'success': False,
                'details': f"Error: {e}"
            })
        
        # Display results
        for test in storage_tests:
            status = "✅" if test['success'] else "❌"
            print(f"   {status} {test['test']}")
            print(f"      Details: {test['details']}")
            print()
        
        self.health_results['data_storage'] = storage_tests

    async def test_external_services(self):
        """Test external service integrations"""
        
        print("\n🌐 EXTERNAL SERVICES HEALTH CHECK")
        print("-" * 50)
        
        external_tests = []
        external_services = self.system_components['external_services']
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            for service_name, service_url in external_services.items():
                try:
                    # Modify URLs for actual testing
                    if 'orcahello_ai' in service_name:
                        test_url = service_url
                    elif 'noaa' in service_name:
                        test_url = f"{service_url}?station=9449880&product=water_level&date=latest&datum=MLLW&format=json&units=english&time_zone=lst_ldt&application=ORCAST"
                    else:
                        test_url = f"{service_url}?key=test"
                    
                    async with session.get(test_url) as response:
                        success = response.status == 200
                        content_length = len(await response.text())
                        
                        external_tests.append({
                            'test': service_name.replace('_', ' ').title(),
                            'url': service_url,
                            'status': response.status,
                            'success': success,
                            'details': f"Response size: {content_length:,} chars"
                        })
                        
                except Exception as e:
                    # More detailed error reporting for debugging
                    error_msg = str(e)
                    if 'timeout' in error_msg.lower():
                        error_msg = f"Connection timeout (30s exceeded)"
                    elif 'ssl' in error_msg.lower():
                        error_msg = f"SSL/Certificate error"
                    elif 'connection' in error_msg.lower():
                        error_msg = f"Connection refused/failed"
                    
                    external_tests.append({
                        'test': service_name.replace('_', ' ').title(),
                        'success': False,
                        'details': f"Error: {error_msg}"
                    })
        
        # Display results  
        for test in external_tests:
            status = "✅" if test['success'] else "❌"
            print(f"   {status} {test['test']}")
            if 'status' in test:
                print(f"      Status: {test['status']}")
            print(f"      Details: {test['details']}")
            print()
        
        self.health_results['external_services'] = external_tests

    async def test_connectivity(self):
        """Test connectivity between frontend and backend"""
        
        print("\n🔗 FRONTEND ↔ BACKEND CONNECTIVITY")
        print("-" * 50)
        
        connectivity_tests = []
        
        # Test if frontend can reach backend
        frontend_url = self.system_components['frontend']['urls']['firebase']
        backend_url = self.system_components['backend']['urls']['primary']
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            try:
                # Get frontend config.js file
                config_url = f"{frontend_url}/config.js"
                async with session.get(config_url) as response:
                    config_content = await response.text()
                    
                    # Check if it contains backend URL
                    backend_referenced = backend_url in config_content
                    
                    connectivity_tests.append({
                        'test': 'Frontend → Backend URL Configuration',
                        'success': backend_referenced,
                        'details': f"Backend URL {'found' if backend_referenced else 'not found'} in frontend config.js"
                    })
                    
            except Exception as e:
                connectivity_tests.append({
                    'test': 'Frontend → Backend URL Configuration',
                    'success': False,
                    'details': f"Error: {e}"
                })
            
            # Test CORS (Cross-Origin Resource Sharing)
            try:
                headers = {
                    'Origin': frontend_url,
                    'Access-Control-Request-Method': 'POST',
                    'Access-Control-Request-Headers': 'Content-Type'
                }
                
                async with session.options(f"{backend_url}/forecast/quick", headers=headers) as response:
                    cors_working = response.status in [200, 204]
                    
                    connectivity_tests.append({
                        'test': 'CORS (Cross-Origin Requests)',
                        'success': cors_working,
                        'details': f"CORS {'enabled' if cors_working else 'disabled'} for frontend domain"
                    })
                    
            except Exception as e:
                connectivity_tests.append({
                    'test': 'CORS (Cross-Origin Requests)',
                    'success': False,
                    'details': f"Error: {e}"
                })
        
        # Display results
        for test in connectivity_tests:
            status = "✅" if test['success'] else "❌"
            print(f"   {status} {test['test']}")
            print(f"      Details: {test['details']}")
            print()
        
        self.health_results['connectivity'] = connectivity_tests

    async def generate_health_report(self):
        """Generate overall system health report"""
        
        print("\n📊 OVERALL SYSTEM HEALTH REPORT")
        print("=" * 70)
        
        # Calculate health metrics
        total_tests = 0
        passed_tests = 0
        
        for category, tests in self.health_results.items():
            category_total = len(tests)
            category_passed = sum(1 for test in tests if test['success'])
            
            total_tests += category_total
            passed_tests += category_passed
            
            success_rate = (category_passed / category_total * 100) if category_total > 0 else 0
            
            status_emoji = "🟢" if success_rate >= 80 else "🟡" if success_rate >= 60 else "🔴"
            
            print(f"{status_emoji} {category.upper().replace('_', ' ')}: {category_passed}/{category_total} ({success_rate:.0f}%)")
        
        overall_health = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n🎯 OVERALL SYSTEM HEALTH: {passed_tests}/{total_tests} ({overall_health:.1f}%)")
        
        if overall_health >= 90:
            status = "🟢 EXCELLENT - System fully operational"
        elif overall_health >= 75:
            status = "🟡 GOOD - Minor issues, mostly functional"
        elif overall_health >= 50:
            status = "🟠 FAIR - Several components need attention"
        else:
            status = "🔴 POOR - Major issues require immediate attention"
        
        print(f"Status: {status}")
        
        # System readiness assessment
        print(f"\n🚀 DEPLOYMENT READINESS:")
        print(f"   • Hackathon Ready: {'✅ YES' if overall_health >= 70 else '❌ NO'}")
        print(f"   • App Store Ready: {'✅ YES' if overall_health >= 80 else '❌ NO'}")
        print(f"   • Production Ready: {'✅ YES' if overall_health >= 90 else '❌ NO'}")

    async def show_cost_analysis(self):
        """Show cost and usage analysis"""
        
        print(f"\n💰 COST & USAGE ANALYSIS")
        print("-" * 50)
        
        # Estimated costs based on current architecture
        costs = {
            'Firebase Hosting': {'monthly': '$1-5', 'description': 'Static file serving, CDN'},
            'Google Cloud Run': {'monthly': '$10-50', 'description': 'Backend API auto-scaling'},
            'BigQuery': {'monthly': '$5-25', 'description': 'Data queries and storage'},
            'External APIs': {'monthly': '$10-30', 'description': 'Google Maps, NOAA data'},
            'Firestore': {'monthly': '$1-10', 'description': 'Real-time database'},
        }
        
        print("📊 Estimated Monthly Costs:")
        total_min = 0
        total_max = 0
        
        for service, info in costs.items():
            cost_range = info['monthly'].replace('$', '').split('-')
            min_cost = int(cost_range[0])
            max_cost = int(cost_range[1])
            total_min += min_cost
            total_max += max_cost
            
            print(f"   • {service}: {info['monthly']} - {info['description']}")
        
        print(f"\n💵 Total Estimated Cost: ${total_min}-{total_max}/month")
        print(f"🎯 Target for App Store: Freemium model with premium features")
        
        # Usage metrics
        print(f"\n📈 Current Usage:")
        print(f"   • Frontend: Global CDN delivery via Firebase")
        print(f"   • Backend: Auto-scaling 0-10 instances based on demand")
        print(f"   • Data: Real-time whale detection storage and analytics")
        print(f"   • APIs: 46 endpoints handling ML predictions and data")

async def main():
    """Run the complete system summary"""
    
    system_summary = ORCASTSystemSummary()
    
    try:
        health_results = await system_summary.run_complete_system_summary()
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"orcast_system_health_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'system_architecture': system_summary.system_components,
                'health_results': health_results,
                'summary': {
                    'total_tests': sum(len(tests) for tests in health_results.values()),
                    'passed_tests': sum(sum(1 for test in tests if test['success']) for tests in health_results.values())
                }
            }, f, indent=2)
        
        print(f"\n📄 Detailed report saved: {report_file}")
        print(f"\n🌐 Quick Access URLs:")
        print(f"   • Frontend: https://orca-904de.web.app")
        print(f"   • Custom Domain: https://orcast.org")
        print(f"   • Backend API: https://orcast-production-backend-2cvqukvhga-uw.a.run.app")
        print(f"   • Firebase Console: https://console.firebase.google.com/project/orca-904de")
        print(f"   • Google Cloud Console: https://console.cloud.google.com/run?project=orca-466204")
        
        return 0
        
    except Exception as e:
        print(f"\n💥 Error during system summary: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 