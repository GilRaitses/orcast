#!/usr/bin/env python3
"""
ORCAST ML Service Test Suite
Comprehensive testing of the behavioral prediction API
"""

import requests
import json
import time
from typing import Dict, List

class ORCASTMLTester:
    """Test suite for ORCAST ML Service"""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_health_check(self):
        """Test service health and model status"""
        print("🏥 Testing service health...")
        
        response = self.session.get(f"{self.base_url}/health")
        if response.status_code == 200:
            data = response.json()
            print("✅ Service is healthy")
            print(f"   • Models loaded: {data['models']}")
            print(f"   • Available classes: {data['classes']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    
    def test_single_prediction(self):
        """Test single prediction endpoint"""
        print("\n🔮 Testing single prediction...")
        
        # Test case 1: Typical San Juan Islands conditions
        test_data = {
            "latitude": 48.5,
            "longitude": -123.0,
            "pod_size": 3,
            "water_depth": 50.0,
            "tidal_flow": 0.2,
            "temperature": 15.5,
            "salinity": 30.1,
            "visibility": 20.0,
            "current_speed": 0.5,
            "noise_level": 120.0,
            "prey_density": 0.6,
            "hour_of_day": 14,
            "day_of_year": 200
        }
        
        response = self.session.post(
            f"{self.base_url}/predict",
            json=test_data
        )
        
        if response.status_code == 200:
            prediction = response.json()
            print("✅ Prediction successful")
            print(f"   • Behavior: {prediction['predicted_behavior']}")
            print(f"   • Confidence: {prediction['confidence']:.3f}")
            print(f"   • Top probabilities:")
            
            # Sort probabilities by value
            sorted_probs = sorted(
                prediction['probabilities'].items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            
            for behavior, prob in sorted_probs[:3]:
                print(f"     - {behavior}: {prob:.3f}")
            
            if prediction['feeding_success_probability']:
                print(f"   • Feeding success: {prediction['feeding_success_probability']:.3f}")
            
            return prediction
        else:
            print(f"❌ Prediction failed: {response.status_code}")
            print(response.text)
            return None
    
    def test_feeding_conditions(self):
        """Test conditions optimized for feeding behavior"""
        print("\n🐟 Testing feeding-optimized conditions...")
        
        # Optimal feeding conditions
        feeding_data = {
            "latitude": 48.5155,  # Lime Kiln Point
            "longitude": -123.1522,
            "pod_size": 6,  # Larger pod
            "water_depth": 60.0,  # Good depth for salmon
            "tidal_flow": 0.8,  # Strong tidal flow
            "temperature": 16.0,  # Optimal temperature
            "salinity": 30.0,
            "visibility": 25.0,  # Good visibility
            "current_speed": 0.7,
            "noise_level": 105.0,  # Low noise
            "prey_density": 0.9,  # High prey density
            "hour_of_day": 6,  # Dawn feeding time
            "day_of_year": 180  # Summer
        }
        
        response = self.session.post(
            f"{self.base_url}/predict",
            json=feeding_data
        )
        
        if response.status_code == 200:
            prediction = response.json()
            print("✅ Feeding conditions prediction successful")
            print(f"   • Behavior: {prediction['predicted_behavior']}")
            print(f"   • Feeding probability: {prediction['probabilities']['feeding']:.3f}")
            
            if prediction['feeding_success_probability']:
                print(f"   • Success probability: {prediction['feeding_success_probability']:.3f}")
            
            return prediction
        else:
            print(f"❌ Feeding prediction failed: {response.status_code}")
            return None
    
    def test_batch_prediction(self):
        """Test batch prediction capability"""
        print("\n📊 Testing batch predictions...")
        
        # Multiple scenarios
        batch_data = {
            "features": [
                {  # Scenario 1: Early morning, high prey
                    "latitude": 48.5,
                    "longitude": -123.0,
                    "pod_size": 4,
                    "water_depth": 45.0,
                    "tidal_flow": 0.3,
                    "temperature": 15.8,
                    "salinity": 30.2,
                    "visibility": 22.0,
                    "current_speed": 0.6,
                    "noise_level": 115.0,
                    "prey_density": 0.8,
                    "hour_of_day": 6,
                    "day_of_year": 190
                },
                {  # Scenario 2: Midday, social conditions
                    "latitude": 48.6,
                    "longitude": -123.1,
                    "pod_size": 8,
                    "water_depth": 30.0,
                    "tidal_flow": 0.1,
                    "temperature": 16.5,
                    "salinity": 29.8,
                    "visibility": 18.0,
                    "current_speed": 0.3,
                    "noise_level": 125.0,
                    "prey_density": 0.4,
                    "hour_of_day": 12,
                    "day_of_year": 200
                },
                {  # Scenario 3: Evening, travel conditions
                    "latitude": 48.7,
                    "longitude": -123.2,
                    "pod_size": 2,
                    "water_depth": 80.0,
                    "tidal_flow": -0.4,
                    "temperature": 15.2,
                    "salinity": 30.5,
                    "visibility": 15.0,
                    "current_speed": 1.2,
                    "noise_level": 130.0,
                    "prey_density": 0.3,
                    "hour_of_day": 18,
                    "day_of_year": 210
                }
            ]
        }
        
        response = self.session.post(
            f"{self.base_url}/predict/batch",
            json=batch_data
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Batch prediction successful")
            print(f"   • Predictions: {result['total_predictions']}")
            print(f"   • Processing time: {result['processing_time_ms']:.1f}ms")
            
            for i, prediction in enumerate(result['predictions']):
                print(f"   • Scenario {i+1}: {prediction['predicted_behavior']} "
                      f"(confidence: {prediction['confidence']:.3f})")
            
            return result
        else:
            print(f"❌ Batch prediction failed: {response.status_code}")
            return None
    
    def test_performance(self, num_requests: int = 10):
        """Test prediction performance"""
        print(f"\n⚡ Testing performance with {num_requests} requests...")
        
        test_data = {
            "latitude": 48.5,
            "longitude": -123.0,
            "pod_size": 3,
            "water_depth": 50.0,
            "tidal_flow": 0.2,
            "temperature": 15.5,
            "salinity": 30.1,
            "visibility": 20.0,
            "current_speed": 0.5,
            "noise_level": 120.0,
            "prey_density": 0.6,
            "hour_of_day": 14,
            "day_of_year": 200
        }
        
        times = []
        successful = 0
        
        for i in range(num_requests):
            start_time = time.time()
            response = self.session.post(f"{self.base_url}/predict", json=test_data)
            end_time = time.time()
            
            if response.status_code == 200:
                successful += 1
                times.append((end_time - start_time) * 1000)  # Convert to ms
        
        if times:
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            
            print("✅ Performance test completed")
            print(f"   • Successful requests: {successful}/{num_requests}")
            print(f"   • Average response time: {avg_time:.1f}ms")
            print(f"   • Min response time: {min_time:.1f}ms")
            print(f"   • Max response time: {max_time:.1f}ms")
            
            return {
                'successful': successful,
                'total': num_requests,
                'avg_time_ms': avg_time,
                'min_time_ms': min_time,
                'max_time_ms': max_time
            }
        else:
            print("❌ All performance tests failed")
            return None
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("🚀 Running ORCAST ML Service Test Suite")
        print("=" * 50)
        
        # Health check
        if not self.test_health_check():
            print("❌ Service not healthy, aborting tests")
            return False
        
        # Single prediction
        self.test_single_prediction()
        
        # Feeding conditions
        self.test_feeding_conditions()
        
        # Batch prediction
        self.test_batch_prediction()
        
        # Performance test
        self.test_performance()
        
        print("\n🎉 Test suite completed!")
        print("=" * 50)
        
        return True

def main():
    """Run the test suite"""
    tester = ORCASTMLTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main() 