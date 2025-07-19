#!/usr/bin/env python3
"""
Real-Time Environmental Data Collector for Orca Behavior Tracking
Fetches live data from actual APIs and uploads to Firebase
"""

import requests
import json
from datetime import datetime, timedelta
import os
import time

class RealTimeDataCollector:
    def __init__(self):
        self.firebase_url = "https://orca-904de-default-rtdb.firebaseio.com/"
    
    def get_noaa_tidal_data(self):
        """Get real-time tidal data from NOAA CO-OPS API"""
        try:
            # Friday Harbor, WA - Station 9449880
            url = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
            
                                      # Get latest water level data
             now = datetime.now()
             params = {
                 "station": "9449880",
                 "product": "water_level",
                 "datum": "MLLW",
                 "format": "json",
                 "units": "english",
                 "time_zone": "lst_ldt",
                 "application": "orca_tracker",
                 "begin_date": (now - timedelta(minutes=30)).strftime("%Y%m%d %H:%M"),
                 "end_date": now.strftime("%Y%m%d %H:%M")
             }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if 'data' in data and len(data['data']) > 0:
                latest = data['data'][-1]  # Most recent measurement
                return {
                    "height": float(latest['v']),
                    "timestamp": latest['t'],
                    "quality": "excellent",
                    "source": "NOAA CO-OPS Station 9449880"
                }
            else:
                print("No tidal data available")
                return None
                
        except Exception as e:
            print(f"Error fetching NOAA tidal data: {e}")
            return None
    
    def get_marine_weather_data(self):
        """Get marine weather data from Open-Meteo"""
        try:
            # San Juan Islands coordinates
            url = "https://marine-api.open-meteo.com/v1/marine"
            params = {
                "latitude": 48.5,
                "longitude": -123.0,
                "current": ["wave_height", "wave_direction", "current_speed", "current_direction"],
                "hourly": ["sea_surface_temperature"],
                "timezone": "America/Los_Angeles",
                "forecast_days": 1
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            current = data.get('current', {})
            hourly = data.get('hourly', {})
            
            # Get current sea surface temperature from hourly data
            sst = None
            if 'sea_surface_temperature' in hourly and len(hourly['sea_surface_temperature']) > 0:
                sst = hourly['sea_surface_temperature'][0]  # Current hour
            
            return {
                "seaTemperature": sst,
                "waveHeight": current.get('wave_height'),
                "currentSpeed": current.get('current_speed'),
                "timestamp": current.get('time'),
                "quality": "good",
                "source": "Open-Meteo Marine API"
            }
            
        except Exception as e:
            print(f"Error fetching marine weather data: {e}")
            return None
    
    def get_salmon_data(self):
        """Get salmon passage data from DART Columbia River"""
        try:
            # Bonneville Dam - most relevant for Puget Sound orcas
            # Note: DART data is typically daily, not real-time
            url = "https://www.cbr.washington.edu/dart/cs/php/rpt/adult_daily.php"
            params = {
                "outputFormat": "json",
                "proj": "BON",  # Bonneville Dam
                "span": "no",
                "startdate": (datetime.now() - timedelta(days=7)).strftime("%m/%d/%Y"),
                "enddate": datetime.now().strftime("%m/%d/%Y")
            }
            
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            # DART returns HTML, not JSON despite the parameter
            # For now, we'll use a representative value based on seasonal patterns
            current_month = datetime.now().month
            
            # Seasonal salmon abundance estimates (based on typical Columbia River patterns)
            seasonal_estimates = {
                1: 50, 2: 75, 3: 150, 4: 300, 5: 500, 6: 800,
                7: 600, 8: 400, 9: 350, 10: 200, 11: 100, 12: 75
            }
            
            estimated_count = seasonal_estimates.get(current_month, 200)
            
                         return {
                 "salmonCount": estimated_count,
                 "timestamp": datetime.utcnow().isoformat() + "Z",
                 "quality": "estimated",
                 "source": "DART Columbia River (seasonal estimate)",
                 "note": "Based on typical monthly patterns"
             }
            
        except Exception as e:
            print(f"Error fetching salmon data: {e}")
            return None
    
    def estimate_vessel_noise(self):
        """Estimate vessel noise based on time of day and day of week"""
        try:
            now = datetime.now()
            hour = now.hour
            is_weekend = now.weekday() >= 5  # Saturday = 5, Sunday = 6
            
            # Base noise level (ambient ocean)
            base_noise = 90
            
            # Time of day effects
            if 6 <= hour <= 18:  # Daytime
                time_factor = 25
            elif 19 <= hour <= 22:  # Evening
                time_factor = 15
            else:  # Night
                time_factor = 5
            
            # Weekend/weekday effects
            weekend_factor = 20 if is_weekend else 10
            
            # Seasonal effects (summer = more boat traffic)
            month = now.month
            if 6 <= month <= 8:  # Summer
                seasonal_factor = 20
            elif month in [5, 9]:  # Shoulder season
                seasonal_factor = 10
            else:  # Winter
                seasonal_factor = 0
            
            estimated_noise = base_noise + time_factor + weekend_factor + seasonal_factor
            
            # Add some realistic variation
            import random
            variation = random.randint(-5, 5)
            final_noise = max(85, min(160, estimated_noise + variation))
            
            return {
                "vesselNoise": final_noise,
                "timestamp": now.isoformat(),
                "quality": "estimated",
                "source": "Time-based vessel traffic model",
                "components": {
                    "base": base_noise,
                    "time_of_day": time_factor,
                    "weekend": weekend_factor,
                    "seasonal": seasonal_factor
                }
            }
            
        except Exception as e:
            print(f"Error estimating vessel noise: {e}")
            return None
    
    def collect_all_data(self):
        """Collect data from all sources"""
        print(f"🌊 Collecting real-time environmental data at {datetime.now()}")
        
        # Collect from all sources
        tidal_data = self.get_noaa_tidal_data()
        marine_data = self.get_marine_weather_data()
        salmon_data = self.get_salmon_data()
        noise_data = self.estimate_vessel_noise()
        
        # Combine into single environmental data object
        environmental_data = {
            "lastUpdated": datetime.now().isoformat(),
            "tidalHeight": tidal_data['height'] if tidal_data else None,
            "seaTemperature": marine_data['seaTemperature'] if marine_data else None,
            "salmonCount": salmon_data['salmonCount'] if salmon_data else None,
            "vesselNoise": noise_data['vesselNoise'] if noise_data else None,
            "waveHeight": marine_data['waveHeight'] if marine_data else None,
            "currentSpeed": marine_data['currentSpeed'] if marine_data else None,
            "dataQuality": {
                "tidal": tidal_data['quality'] if tidal_data else "unavailable",
                "marine": marine_data['quality'] if marine_data else "unavailable",
                "salmon": salmon_data['quality'] if salmon_data else "unavailable",
                "noise": noise_data['quality'] if noise_data else "unavailable"
            },
            "sources": {
                "tidal": tidal_data['source'] if tidal_data else None,
                "marine": marine_data['source'] if marine_data else None,
                "salmon": salmon_data['source'] if salmon_data else None,
                "noise": noise_data['source'] if noise_data else None
            }
        }
        
        return environmental_data
    
    def upload_to_firebase_direct(self, data):
        """Upload data to Firebase using direct HTTP API"""
        try:
            # Firebase REST API endpoint
            url = f"{self.firebase_url}environmentalData.json"
            
            response = requests.put(url, json=data, timeout=10)
            response.raise_for_status()
            
            print(f"✅ Data uploaded to Firebase successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error uploading to Firebase: {e}")
            return False
    
    def save_to_local_file(self, data):
        """Save data to local file as backup"""
        try:
            filename = f"environmental_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"💾 Data saved to {filename}")
        except Exception as e:
            print(f"Error saving to file: {e}")

def main():
    """Main function to collect and upload real-time data"""
    collector = RealTimeDataCollector()
    
    print("🐋 Starting real-time environmental data collection...")
    
    try:
        # Collect all environmental data
        data = collector.collect_all_data()
        
        # Print summary
        print("\n📊 Collected Data Summary:")
        print(f"   🌊 Tidal Height: {data.get('tidalHeight', 'N/A')} ft")
        print(f"   🌡️  Sea Temperature: {data.get('seaTemperature', 'N/A')}°C")
        print(f"   🐟 Salmon Count: {data.get('salmonCount', 'N/A')}")
        print(f"   🚢 Vessel Noise: {data.get('vesselNoise', 'N/A')} dB")
        print(f"   🌊 Wave Height: {data.get('waveHeight', 'N/A')} m")
        
        # Save locally
        collector.save_to_local_file(data)
        
        # Upload to Firebase
        success = collector.upload_to_firebase_direct(data)
        
        if success:
            print("\n🎉 Real-time data collection completed successfully!")
            print("🔗 View data at: https://console.firebase.google.com/project/orca-904de/database")
        else:
            print("\n⚠️  Upload failed, but data saved locally")
            
    except Exception as e:
        print(f"❌ Error in main collection process: {e}")

if __name__ == "__main__":
    main() 