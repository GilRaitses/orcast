"""
Test Live Orcasound Feeds API
Connects to the actual live.orcasound.net API to get real hydrophone data
"""

import asyncio
import aiohttp
import json
from datetime import datetime

async def test_live_orcasound_feeds():
    """Test the actual Orcasound live feeds API"""
    
    feed_url = "https://live.orcasound.net/api/json/feeds"
    
    async with aiohttp.ClientSession() as session:
        
        print("🐋 Testing Live Orcasound Feeds API...")
        print(f"Feed URL: {feed_url}")
        
        try:
            async with session.get(feed_url) as response:
                print(f"\nStatus: {response.status}")
                print(f"Content-Type: {response.headers.get('content-type')}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Successfully retrieved feeds data!")
                    
                    # Parse the feeds structure
                    if isinstance(data, dict):
                        print(f"\nResponse structure keys: {list(data.keys())}")
                        
                        # Look for feeds information
                        if 'feeds' in data:
                            feeds = data['feeds']
                            print(f"\nFound {len(feeds)} active feeds:")
                            
                            for feed_id, feed_info in feeds.items():
                                print(f"\n📡 Feed ID: {feed_id}")
                                
                                # Extract location information
                                if 'name' in feed_info:
                                    print(f"   Name: {feed_info['name']}")
                                
                                if 'location' in feed_info:
                                    location = feed_info['location']
                                    if isinstance(location, dict):
                                        print(f"   Location: {location}")
                                        if 'coordinates' in location:
                                            coords = location['coordinates']
                                            print(f"   Coordinates: {coords}")
                                
                                # Look for audio streams
                                if 'streams' in feed_info:
                                    streams = feed_info['streams']
                                    print(f"   Available streams: {len(streams)}")
                                    for stream_type, stream_url in streams.items():
                                        print(f"     {stream_type}: {stream_url}")
                                
                                # Look for description
                                if 'description' in feed_info:
                                    print(f"   Description: {feed_info['description']}")
                                
                                # Look for any recent activity indicators
                                if 'activity' in feed_info:
                                    print(f"   Activity: {feed_info['activity']}")
                        
                        # Look for any other relevant data
                        for key, value in data.items():
                            if key != 'feeds':
                                print(f"\nAdditional data - {key}: {value}")
                    
                    else:
                        print(f"Unexpected data type: {type(data)}")
                        print(f"Data: {data}")
                    
                    # Save the feeds data
                    with open('live_orcasound_feeds.json', 'w') as f:
                        json.dump(data, f, indent=2)
                    print(f"\n💾 Saved feeds data to live_orcasound_feeds.json")
                    
                    return data
                
                else:
                    error_text = await response.text()
                    print(f"❌ Error {response.status}: {error_text}")
                    return None
        
        except Exception as e:
            print(f"❌ Exception: {e}")
            return None

async def test_individual_feed_streams(feeds_data):
    """Test individual feed streams for activity"""
    
    if not feeds_data or 'feeds' not in feeds_data:
        print("No feeds data available")
        return
    
    print("\n🎵 Testing Individual Feed Streams...")
    
    async with aiohttp.ClientSession() as session:
        
        for feed_id, feed_info in feeds_data['feeds'].items():
            print(f"\n📡 Testing feed: {feed_info.get('name', feed_id)}")
            
            # Try to get the HLS manifest or stream info
            if 'streams' in feed_info:
                streams = feed_info['streams']
                
                for stream_type, stream_url in streams.items():
                    if stream_url:
                        print(f"   Testing {stream_type} stream...")
                        try:
                            # Just test if the stream endpoint is accessible
                            async with session.head(stream_url, timeout=10) as response:
                                print(f"     Status: {response.status}")
                                if response.status == 200:
                                    print(f"     ✅ Stream is live!")
                                    # Get content type to understand stream format
                                    content_type = response.headers.get('content-type', 'unknown')
                                    print(f"     Content-Type: {content_type}")
                                else:
                                    print(f"     ❌ Stream not accessible")
                        
                        except asyncio.TimeoutError:
                            print(f"     ⏰ Stream timeout (might be live but slow)")
                        except Exception as e:
                            print(f"     ❌ Stream error: {e}")

async def get_hydrophone_coordinates(feeds_data):
    """Extract hydrophone coordinates for ORCAST integration"""
    
    if not feeds_data or 'feeds' not in feeds_data:
        return []
    
    hydrophones = []
    
    print("\n📍 Extracting Hydrophone Coordinates for ORCAST...")
    
    for feed_id, feed_info in feeds_data['feeds'].items():
        hydrophone = {
            'id': feed_id,
            'name': feed_info.get('name', 'Unknown'),
            'description': feed_info.get('description', ''),
            'streams': feed_info.get('streams', {}),
            'coordinates': None,
            'latitude': None,
            'longitude': None
        }
        
        # Extract coordinates
        if 'location' in feed_info and isinstance(feed_info['location'], dict):
            location = feed_info['location']
            
            # Try different coordinate formats
            if 'coordinates' in location:
                coords = location['coordinates']
                if isinstance(coords, list) and len(coords) >= 2:
                    # GeoJSON format [longitude, latitude]
                    hydrophone['longitude'] = coords[0]
                    hydrophone['latitude'] = coords[1]
                    hydrophone['coordinates'] = coords
                elif isinstance(coords, dict):
                    # Object format
                    hydrophone['latitude'] = coords.get('lat') or coords.get('latitude')
                    hydrophone['longitude'] = coords.get('lng') or coords.get('longitude')
            
            # Try direct lat/lng fields
            if not hydrophone['latitude']:
                hydrophone['latitude'] = location.get('lat') or location.get('latitude')
            if not hydrophone['longitude']:
                hydrophone['longitude'] = location.get('lng') or location.get('longitude')
        
        hydrophones.append(hydrophone)
        
        # Print hydrophone info
        print(f"   🎙️ {hydrophone['name']}")
        if hydrophone['latitude'] and hydrophone['longitude']:
            print(f"      Coordinates: {hydrophone['latitude']:.6f}, {hydrophone['longitude']:.6f}")
        else:
            print(f"      Coordinates: Not available")
        print(f"      Streams: {list(hydrophone['streams'].keys())}")
    
    # Save hydrophone data for ORCAST
    with open('orcasound_hydrophones.json', 'w') as f:
        json.dump(hydrophones, f, indent=2)
    print(f"\n💾 Saved hydrophone data to orcasound_hydrophones.json")
    
    return hydrophones

async def main():
    """Main test function"""
    print("🚀 Testing Live Orcasound Feeds API...")
    
    # Get feeds data
    feeds_data = await test_live_orcasound_feeds()
    
    if feeds_data:
        # Test individual streams
        await test_individual_feed_streams(feeds_data)
        
        # Extract coordinates for ORCAST
        hydrophones = await get_hydrophone_coordinates(feeds_data)
        
        print(f"\n✅ Successfully processed {len(hydrophones)} hydrophone locations!")
        
        # Show summary
        active_hydrophones = [h for h in hydrophones if h['latitude'] and h['longitude']]
        print(f"📍 {len(active_hydrophones)} hydrophones have coordinates")
        
        if active_hydrophones:
            print("\n🎯 Ready for ORCAST integration:")
            for hydro in active_hydrophones:
                print(f"   • {hydro['name']}: {hydro['latitude']:.4f}, {hydro['longitude']:.4f}")
    
    else:
        print("❌ Failed to retrieve feeds data")

if __name__ == "__main__":
    asyncio.run(main()) 