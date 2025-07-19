#!/usr/bin/env python3
"""
Test script to check OpenWeather API key activation
"""

import os
import requests
import time
from datetime import datetime

def test_openweather_api():
    """Test OpenWeather API key activation"""
    api_key = os.getenv('OPENWEATHER_API_KEY')
    
    if not api_key:
        print("❌ OPENWEATHER_API_KEY environment variable not set")
        return False
    
    print(f"🔑 Testing OpenWeather API key: {api_key}")
    
    # Test with Seattle coordinates (perfect for orca research)
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        'lat': 47.6062,  # Seattle latitude
        'lon': -122.3321,  # Seattle longitude
        'appid': api_key,
        'units': 'metric'
    }
    
    try:
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ OpenWeather API is working!")
            print(f"   Location: {data['name']}")
            print(f"   Temperature: {data['main']['temp']}°C")
            print(f"   Weather: {data['weather'][0]['description']}")
            print(f"   Wind Speed: {data['wind']['speed']} m/s")
            return True
        elif response.status_code == 401:
            print("⏳ API key not yet activated (can take up to 2 hours)")
            print("   Try again in a few minutes...")
            return False
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return False

if __name__ == "__main__":
    print(f"🕐 Testing at {datetime.now().strftime('%H:%M:%S')}")
    success = test_openweather_api()
    
    if not success:
        print("\n💡 OpenWeather API keys typically activate within 2 hours of registration")
        print("   Check your email for a welcome message when it's ready!")
    else:
        print("\n🎉 Your OpenWeather API key is ready to use!")
        print("   You can now run the production pipeline to get enhanced weather data") 