#!/usr/bin/env python3
"""
Test ORCAST Firestore ML Service
Demonstrates spatial forecasting for map UI and Firestore integration
"""

import requests
import json
import time
from datetime import datetime
import numpy as np

class ORCASTFirestoreMLTester:
    """Test suite for ORCAST Firestore ML Service"""
    
    def __init__(self, base_url: str = "http://localhost:8082"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_service_health(self):
        """Test service health and Firebase connection"""
        print("🏥 Testing Firestore ML service health...")
        
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                print("✅ Service is healthy")
                print(f"   • Firebase connected: {data['firebase_connected']}")
                print(f"   • Models loaded: {data['models_loaded']}")
                print(f"   • Capabilities: {', '.join(data['capabilities'])}")
                return True
            else:
                print(f"❌ Service health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Failed to connect to service: {e}")
            return False
    
    def test_quick_forecast(self):
        """Test quick spatial forecast generation"""
        print("\n🗺️ Testing quick spatial forecast generation...")
        
        try:
            response = self.session.post(f"{self.base_url}/forecast/quick")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Quick forecast generated successfully")
                print(f"   • Status: {data['status']}")
                print(f"   • Forecast ID: {data['forecast_id']}")
                print(f"   • Grid points: {data['grid_points']}")
                print(f"   • Time slices: {data['time_slices']}")
                return data
            else:
                print(f"❌ Quick forecast failed: {response.status_code}")
                print(response.text)
                return None
                
        except Exception as e:
            print(f"❌ Quick forecast error: {e}")
            return None
    
    def test_spatial_forecast_request(self):
        """Test spatial forecast with custom parameters"""
        print("\n🎯 Testing custom spatial forecast...")
        
        forecast_request = {
            "region": "san_juan_islands",
            "grid_resolution": 0.02,  # Lower resolution for faster testing
            "forecast_hours": 12,
            "time_step_hours": 6
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/forecast/spatial",
                json=forecast_request
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Spatial forecast request accepted")
                print(f"   • Status: {data['status']}")
                print(f"   • Region: {data['region']}")
                print(f"   • Estimated completion: {data['estimated_completion']}")
                return data
            else:
                print(f"❌ Spatial forecast request failed: {response.status_code}")
                print(response.text)
                return None
                
        except Exception as e:
            print(f"❌ Spatial forecast request error: {e}")
            return None
    
    def test_single_prediction_storage(self):
        """Test single prediction with Firestore storage"""
        print("\n💾 Testing prediction with Firestore storage...")
        
        prediction_data = {
            "latitude": 48.5155,  # Lime Kiln Point
            "longitude": -123.1522,
            "pod_size": 4,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/predict/store",
                json=prediction_data
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Prediction with storage successful")
                print(f"   • Behavior: {data['predicted_behavior']}")
                print(f"   • Confidence: {data['confidence']:.3f}")
                print(f"   • Stored in Firestore: {data.get('stored_in_firestore', False)}")
                
                if data.get('prediction_id'):
                    print(f"   • Prediction ID: {data['prediction_id']}")
                
                return data
            else:
                print(f"❌ Prediction storage failed: {response.status_code}")
                print(response.text)
                return None
                
        except Exception as e:
            print(f"❌ Prediction storage error: {e}")
            return None
    
    def test_forecast_status(self):
        """Test forecast status endpoint"""
        print("\n📊 Testing forecast status...")
        
        try:
            response = self.session.get(f"{self.base_url}/forecast/status")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Forecast status retrieved")
                print(f"   • Firestore connected: {data['firestore_connected']}")
                print(f"   • Models loaded: {data['models_loaded']}")
                print(f"   • Current forecast available: {data['current_forecast_available']}")
                
                if data['current_forecast_id']:
                    print(f"   • Current forecast ID: {data['current_forecast_id']}")
                    
                return data
            else:
                print(f"❌ Forecast status failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Forecast status error: {e}")
            return None
    
    def test_current_forecast_retrieval(self):
        """Test retrieving current forecast from Firestore"""
        print("\n📥 Testing current forecast retrieval...")
        
        try:
            response = self.session.get(f"{self.base_url}/forecast/current")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Current forecast retrieved from Firestore")
                print(f"   • Forecast ID: {data['forecast_id']}")
                print(f"   • Region: {data['metadata']['region']}")
                print(f"   • Grid size: {data['metadata']['grid_size']}")
                print(f"   • Time series length: {len(data['time_series'])}")
                
                # Show sample of time series data
                if data['time_series']:
                    first_slice = data['time_series'][0]
                    print(f"   • Sample time slice:")
                    print(f"     - Timestamp: {first_slice['timestamp']}")
                    print(f"     - Grid points: {len(first_slice['grid_points'])}")
                    
                    if first_slice['grid_points']:
                        sample_point = first_slice['grid_points'][0]
                        print(f"     - Sample point: lat={sample_point['lat']:.3f}, lng={sample_point['lng']:.3f}")
                        print(f"     - Feeding prob: {sample_point['feeding_prob']:.3f}")
                        print(f"     - Predicted behavior: {sample_point['predicted_behavior']}")
                
                return data
            elif response.status_code == 404:
                print("⚠️ No current forecast found in Firestore")
                return None
            else:
                print(f"❌ Current forecast retrieval failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Current forecast retrieval error: {e}")
            return None
    
    def demonstrate_map_ui_data(self, forecast_data):
        """Demonstrate how forecast data would be used in map UI"""
        print("\n🗺️ Demonstrating Map UI Integration...")
        
        if not forecast_data or 'time_series' not in forecast_data:
            print("❌ No forecast data available for demonstration")
            return
        
        time_series = forecast_data['time_series']
        
        print(f"📊 Map UI Data Structure:")
        print(f"   • Total time slices: {len(time_series)}")
        
        for i, time_slice in enumerate(time_series[:3]):  # Show first 3 time slices
            print(f"\n   🕐 Time Slice {i+1}:")
            print(f"     • Timestamp: {time_slice['timestamp']}")
            print(f"     • Hour offset: {time_slice['hour_offset']}")
            print(f"     • Grid points: {len(time_slice['grid_points'])}")
            
            # Calculate statistics for this time slice
            grid_points = time_slice['grid_points']
            
            if grid_points:
                feeding_probs = [p['feeding_prob'] for p in grid_points]
                socializing_probs = [p['socializing_prob'] for p in grid_points]
                
                print(f"     • Feeding probability: min={min(feeding_probs):.3f}, max={max(feeding_probs):.3f}, avg={np.mean(feeding_probs):.3f}")
                print(f"     • Socializing probability: min={min(socializing_probs):.3f}, max={max(socializing_probs):.3f}, avg={np.mean(socializing_probs):.3f}")
                
                # Behavior distribution
                behaviors = [p['predicted_behavior'] for p in grid_points]
                behavior_counts = {b: behaviors.count(b) for b in set(behaviors)}
                print(f"     • Behavior distribution: {behavior_counts}")
        
        print(f"\n🎛️ Map UI Slider Configuration:")
        print(f"   • Time range: {len(time_series)} time steps")
        print(f"   • Each step represents: {time_series[1]['hour_offset'] - time_series[0]['hour_offset'] if len(time_series) > 1 else 'N/A'} hours")
        print(f"   • Probability heatmaps available for: feeding, socializing, traveling")
        print(f"   • Confidence overlay available for prediction quality")
    
    def run_comprehensive_test(self):
        """Run complete test suite"""
        print("🚀 Running ORCAST Firestore ML Service Test Suite")
        print("=" * 60)
        
        # Health check
        if not self.test_service_health():
            print("❌ Service not healthy, aborting tests")
            return False
        
        # Test individual prediction with storage
        self.test_single_prediction_storage()
        
        # Test forecast status
        self.test_forecast_status()
        
        # Generate quick forecast
        quick_result = self.test_quick_forecast()
        
        # Wait a moment for the quick forecast to complete
        if quick_result:
            print("\n⏳ Waiting for quick forecast to complete...")
            time.sleep(5)
        
        # Test current forecast retrieval
        current_forecast = self.test_current_forecast_retrieval()
        
        # Demonstrate map UI integration
        if current_forecast:
            self.demonstrate_map_ui_data(current_forecast)
        
        # Test spatial forecast request (background)
        self.test_spatial_forecast_request()
        
        print("\n🎉 Firestore ML Service test suite completed!")
        print("=" * 60)
        
        return True

def main():
    """Run the test suite"""
    tester = ORCASTFirestoreMLTester()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main() 