"""
Test OrcaHello Live API Integration
Connects to actual OrcaHello production API to fetch live whale detection data
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_live_orcahello_api():
    """Test connection to live OrcaHello API"""
    
    base_url = "https://aifororcas.azurewebsites.net/api"
    
    async with aiohttp.ClientSession() as session:
        
        print("🐋 Testing Live OrcaHello API Connection...")
        print(f"API Base URL: {base_url}")
        
        # Test 1: Get hydrophone locations
        print("\n📍 Testing hydrophone locations endpoint...")
        try:
            async with session.get(f"{base_url}/hydrophones") as response:
                print(f"Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Successfully retrieved hydrophone data")
                    print(f"Response structure: {list(data.keys()) if isinstance(data, dict) else 'List/Other'}")
                    if isinstance(data, dict) and 'hydrophones' in data:
                        hydrophones = data['hydrophones']
                        print(f"Found {len(hydrophones)} hydrophones:")
                        for hydro in hydrophones[:3]:  # Show first 3
                            print(f"  - {hydro.get('name', 'Unknown')}: {hydro.get('latitude', 'N/A')}, {hydro.get('longitude', 'N/A')}")
                    else:
                        print(f"Raw response: {data}")
                else:
                    error_text = await response.text()
                    print(f"❌ Error: {response.status} - {error_text}")
        except Exception as e:
            print(f"❌ Exception in hydrophones test: {e}")
        
        # Test 2: Get recent detections by tag
        print("\n🎵 Testing detections endpoint...")
        
        # Calculate date range (last 3 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=3)
        
        # Try different tags that might exist
        test_tags = ["whale", "orca", "click", "call"]
        
        for tag in test_tags:
            print(f"\n  Testing tag: '{tag}'")
            try:
                params = {
                    'fromDate': start_date.strftime('%m/%d/%Y'),
                    'toDate': end_date.strftime('%m/%d/%Y'),
                    'page': 1,
                    'pageSize': 10
                }
                
                url = f"{base_url}/detections/bytag/{tag}"
                print(f"  Request URL: {url}")
                print(f"  Params: {params}")
                
                async with session.get(url, params=params) as response:
                    print(f"  Status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        print(f"  ✅ Success! Response keys: {list(data.keys()) if isinstance(data, dict) else 'List/Other'}")
                        
                        if isinstance(data, dict):
                            if 'detections' in data and data['detections']:
                                detections = data['detections']
                                print(f"  Found {len(detections)} detections for tag '{tag}':")
                                
                                for i, det in enumerate(detections[:2]):  # Show first 2
                                    print(f"    {i+1}. Detection ID: {det.get('id', 'N/A')}")
                                    print(f"       Location: {det.get('locationName', 'N/A')}")
                                    print(f"       Confidence: {det.get('whaleFoundConfidence', 'N/A')}")
                                    print(f"       Timestamp: {det.get('timestamp', 'N/A')}")
                                    if 'location' in det:
                                        loc = det['location']
                                        print(f"       Coordinates: {loc.get('latitude', 'N/A')}, {loc.get('longitude', 'N/A')}")
                                
                                return detections  # Return actual detections found
                            elif 'totalCount' in data:
                                print(f"  Total count: {data['totalCount']}")
                                if data['totalCount'] == 0:
                                    print(f"  No detections found for tag '{tag}' in date range")
                            else:
                                print(f"  Response structure: {data}")
                        else:
                            print(f"  Unexpected response type: {type(data)}")
                    
                    elif response.status == 400:
                        error_text = await response.text()
                        print(f"  ❌ Bad request (400): {error_text}")
                    elif response.status == 404:
                        print(f"  ❌ Not found (404) - tag '{tag}' may not exist")
                    else:
                        error_text = await response.text()
                        print(f"  ❌ Error {response.status}: {error_text}")
                        
            except Exception as e:
                print(f"  ❌ Exception testing tag '{tag}': {e}")
        
        # Test 3: Try getting a specific detection if we have an ID
        print("\n🔍 Testing specific detection endpoint...")
        
        # Try a few potential detection IDs (these might not exist)
        test_detection_ids = [
            "000000000-000000000-00000000-00000000000",  # From their schema example
        ]
        
        for det_id in test_detection_ids:
            try:
                url = f"{base_url}/detections/{det_id}"
                async with session.get(url) as response:
                    print(f"Detection ID {det_id}: Status {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Found detection: {data.get('locationName', 'N/A')}")
                        return data
                    elif response.status == 404:
                        print(f"Detection {det_id} not found (expected)")
                    else:
                        error_text = await response.text()
                        print(f"Error: {error_text}")
            except Exception as e:
                print(f"Exception testing detection ID: {e}")
        
        # Test 4: Try different date ranges
        print("\n📅 Testing different date ranges...")
        
        date_ranges = [
            ("last 24 hours", 1),
            ("last week", 7),
            ("last month", 30)
        ]
        
        for range_name, days_back in date_ranges:
            print(f"\n  Testing {range_name}:")
            start_date = datetime.now() - timedelta(days=days_back)
            end_date = datetime.now()
            
            params = {
                'fromDate': start_date.strftime('%m/%d/%Y'),
                'toDate': end_date.strftime('%m/%d/%Y'),
                'page': 1,
                'pageSize': 5
            }
            
            try:
                # Try with whale tag
                url = f"{base_url}/detections/bytag/whale"
                async with session.get(url, params=params) as response:
                    print(f"    Status: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        if isinstance(data, dict) and 'detections' in data:
                            count = len(data['detections'])
                            print(f"    ✅ Found {count} detections in {range_name}")
                            if count > 0:
                                latest = data['detections'][0]
                                print(f"    Latest: {latest.get('locationName', 'N/A')} at {latest.get('timestamp', 'N/A')}")
                        else:
                            print(f"    Response: {data}")
                    else:
                        error_text = await response.text()
                        print(f"    Error: {error_text}")
            except Exception as e:
                print(f"    Exception: {e}")

async def get_live_whale_detections():
    """Get actual live whale detections from OrcaHello API"""
    
    base_url = "https://aifororcas.azurewebsites.net/api"
    
    async with aiohttp.ClientSession() as session:
        
        print("🐋 Fetching Live Whale Detections...")
        
        # Try to get detections from last 7 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        params = {
            'fromDate': start_date.strftime('%m/%d/%Y'),
            'toDate': end_date.strftime('%m/%d/%Y'),
            'page': 1,
            'pageSize': 20
        }
        
        # Try different search strategies
        search_strategies = [
            ("whale", "Direct whale tag search"),
            ("orca", "Orca tag search"),
            ("click", "Click call search"),
            ("call", "General call search")
        ]
        
        all_detections = []
        
        for tag, description in search_strategies:
            print(f"\n📡 {description}...")
            
            try:
                url = f"{base_url}/detections/bytag/{tag}"
                async with session.get(url, params=params) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        if isinstance(data, dict) and 'detections' in data:
                            detections = data['detections']
                            print(f"✅ Found {len(detections)} detections")
                            
                            for detection in detections:
                                # Extract location info
                                location = detection.get('location', {})
                                
                                detection_info = {
                                    'id': detection.get('id'),
                                    'timestamp': detection.get('timestamp'),
                                    'location_name': detection.get('locationName'),
                                    'confidence': detection.get('whaleFoundConfidence'),
                                    'state': detection.get('state'),
                                    'latitude': location.get('latitude'),
                                    'longitude': location.get('longitude'),
                                    'audio_uri': detection.get('audioUri'),
                                    'image_uri': detection.get('imageUri'),
                                    'predictions': detection.get('predictions', [])
                                }
                                
                                all_detections.append(detection_info)
                                
                                # Print detection details
                                timestamp = detection_info['timestamp']
                                if timestamp:
                                    try:
                                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                                        age = datetime.now(dt.tzinfo) - dt
                                        age_str = f"{age.days}d {age.seconds//3600}h ago"
                                    except:
                                        age_str = "unknown age"
                                else:
                                    age_str = "no timestamp"
                                
                                print(f"  🎵 {detection_info['location_name']}")
                                print(f"     Confidence: {detection_info['confidence']}%")
                                print(f"     Coordinates: {detection_info['latitude']}, {detection_info['longitude']}")
                                print(f"     Age: {age_str}")
                                print(f"     State: {detection_info['state']}")
                        
                        elif isinstance(data, dict) and 'totalCount' in data:
                            print(f"Total available: {data['totalCount']}")
                            if data['totalCount'] == 0:
                                print("No detections found for this tag/timeframe")
                        
                        else:
                            print(f"Unexpected response format: {type(data)}")
                    
                    else:
                        error_text = await response.text()
                        print(f"❌ Error {response.status}: {error_text}")
            
            except Exception as e:
                print(f"❌ Exception in {description}: {e}")
        
        # Remove duplicates and sort by timestamp
        unique_detections = {d['id']: d for d in all_detections if d['id']}.values()
        sorted_detections = sorted(
            unique_detections, 
            key=lambda x: x['timestamp'] or '', 
            reverse=True
        )
        
        print(f"\n📊 Summary:")
        print(f"Total unique detections found: {len(sorted_detections)}")
        
        if sorted_detections:
            print(f"\n🏆 Most Recent Detections:")
            for i, detection in enumerate(sorted_detections[:5]):
                print(f"{i+1}. {detection['location_name']} - {detection['confidence']}% confidence")
                print(f"   Coordinates: {detection['latitude']}, {detection['longitude']}")
        
        return sorted_detections

async def main():
    """Main test function"""
    print("🚀 Starting OrcaHello Live API Tests...\n")
    
    # Test API connectivity
    await test_live_orcahello_api()
    
    print("\n" + "="*60 + "\n")
    
    # Get live detections
    detections = await get_live_whale_detections()
    
    if detections:
        print(f"\n✅ Successfully retrieved {len(detections)} live whale detections!")
        
        # Save to file for analysis
        with open('live_orcahello_detections.json', 'w') as f:
            json.dump(detections, f, indent=2, default=str)
        print("💾 Saved detections to live_orcahello_detections.json")
        
    else:
        print("\n⚠️ No detections retrieved - API might be down or no recent activity")

if __name__ == "__main__":
    asyncio.run(main()) 