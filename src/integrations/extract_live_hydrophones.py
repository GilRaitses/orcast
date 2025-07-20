"""
Extract Live Hydrophone Data from Orcasound API
Parses the real JSON API format data to get coordinates and status
"""

import json
from datetime import datetime

def extract_hydrophone_data():
    """Extract hydrophone data from the live Orcasound feeds JSON"""
    
    try:
        # Load the actual data we just fetched
        with open('live_orcasound_feeds.json', 'r') as f:
            data = json.load(f)
        
        print("🐋 Extracting Live Hydrophone Data from Orcasound...")
        
        # Parse JSON API format
        if 'data' in data and isinstance(data['data'], list):
            feeds = data['data']
            print(f"Found {len(feeds)} total feeds")
            
            hydrophones = []
            
            for feed in feeds:
                attributes = feed.get('attributes', {})
                
                # Extract basic info
                hydrophone = {
                    'id': attributes.get('node_name', ''),
                    'name': attributes.get('name', ''),
                    'slug': attributes.get('slug', ''),
                    'visible': attributes.get('visible', False),
                    'bucket': attributes.get('bucket', ''),
                    'description': attributes.get('intro_html', ''),
                    'image_url': attributes.get('image_url'),
                    'coordinates': None,
                    'latitude': None,
                    'longitude': None
                }
                
                # Extract coordinates from location_point (GeoJSON format)
                if 'location_point' in attributes:
                    location_point = attributes['location_point']
                    if 'coordinates' in location_point:
                        coords = location_point['coordinates']
                        # GeoJSON format: [longitude, latitude]
                        hydrophone['longitude'] = coords[0]
                        hydrophone['latitude'] = coords[1]
                        hydrophone['coordinates'] = coords
                
                # Also get from lat_lng (backup)
                if 'lat_lng' in attributes:
                    lat_lng = attributes['lat_lng']
                    if not hydrophone['latitude']:
                        hydrophone['latitude'] = lat_lng.get('lat')
                    if not hydrophone['longitude']:
                        hydrophone['longitude'] = lat_lng.get('lng')
                
                hydrophones.append(hydrophone)
                
                # Print hydrophone info
                status = "🟢 LIVE" if hydrophone['visible'] else "🔴 Offline"
                print(f"\n🎙️ {hydrophone['name']} ({hydrophone['id']})")
                print(f"   Status: {status}")
                if hydrophone['latitude'] and hydrophone['longitude']:
                    print(f"   Coordinates: {hydrophone['latitude']:.6f}, {hydrophone['longitude']:.6f}")
                else:
                    print("   Coordinates: Not available")
                print(f"   Bucket: {hydrophone['bucket']}")
            
            # Filter to active/visible hydrophones
            active_hydrophones = [h for h in hydrophones if h['visible']]
            print(f"\n📊 Summary:")
            print(f"Total hydrophones: {len(hydrophones)}")
            print(f"Active/visible hydrophones: {len(active_hydrophones)}")
            
            # Save for ORCAST integration
            orcast_data = {
                'timestamp': datetime.now().isoformat(),
                'source': 'live.orcasound.net',
                'total_hydrophones': len(hydrophones),
                'active_hydrophones': len(active_hydrophones),
                'all_hydrophones': hydrophones,
                'active_only': active_hydrophones
            }
            
            with open('orcasound_hydrophones_for_orcast.json', 'w') as f:
                json.dump(orcast_data, f, indent=2)
            
            print(f"\n💾 Saved ORCAST-ready data to orcasound_hydrophones_for_orcast.json")
            
            # Show active hydrophone coordinates for ORCAST
            if active_hydrophones:
                print(f"\n🎯 Active Hydrophones for ORCAST Integration:")
                for hydro in active_hydrophones:
                    print(f"   • {hydro['name']}: {hydro['latitude']:.6f}, {hydro['longitude']:.6f}")
                    
                # Generate JavaScript array for frontend
                js_coords = []
                for hydro in active_hydrophones:
                    js_coords.append(f"  {{id: '{hydro['id']}', name: '{hydro['name']}', lat: {hydro['latitude']}, lng: {hydro['longitude']}}}")
                
                js_array = "const liveHydrophones = [\n" + ",\n".join(js_coords) + "\n];"
                
                with open('live_hydrophones_for_frontend.js', 'w') as f:
                    f.write(js_array)
                print(f"📱 Saved frontend JavaScript to live_hydrophones_for_frontend.js")
            
            return orcast_data
        
        else:
            print("❌ Unexpected data format")
            return None
            
    except FileNotFoundError:
        print("❌ live_orcasound_feeds.json not found. Run test_live_orcasound_feeds.py first.")
        return None
    except Exception as e:
        print(f"❌ Error parsing data: {e}")
        return None

def show_geographic_coverage(hydrophones_data):
    """Show geographic coverage of the hydrophone network"""
    
    if not hydrophones_data or 'active_only' not in hydrophones_data:
        return
    
    active_hydrophones = hydrophones_data['active_only']
    
    if not active_hydrophones:
        print("No active hydrophones to analyze")
        return
    
    print(f"\n🗺️ Geographic Coverage Analysis:")
    
    # Calculate bounds
    lats = [h['latitude'] for h in active_hydrophones if h['latitude']]
    lngs = [h['longitude'] for h in active_hydrophones if h['longitude']]
    
    if lats and lngs:
        min_lat, max_lat = min(lats), max(lats)
        min_lng, max_lng = min(lngs), max(lngs)
        
        print(f"   Latitude range: {min_lat:.4f} to {max_lat:.4f} ({max_lat - min_lat:.4f}°)")
        print(f"   Longitude range: {min_lng:.4f} to {max_lng:.4f} ({max_lng - min_lng:.4f}°)")
        
        # Calculate center point
        center_lat = (min_lat + max_lat) / 2
        center_lng = (min_lng + max_lng) / 2
        print(f"   Network center: {center_lat:.4f}, {center_lng:.4f}")
        
        # Estimate coverage area (rough)
        lat_km = (max_lat - min_lat) * 111  # ~111 km per degree latitude
        lng_km = (max_lng - min_lng) * 111 * abs(center_lat * 3.14159 / 180)  # longitude varies by latitude
        area_km2 = lat_km * lng_km
        
        print(f"   Approximate coverage: {lat_km:.1f} km x {lng_km:.1f} km = {area_km2:.0f} km²")
        
        # Identify regions
        print(f"\n📍 Geographic Regions:")
        for hydro in active_hydrophones:
            region = "Unknown"
            lat, lng = hydro['latitude'], hydro['longitude']
            
            # Rough regional classification for Puget Sound area
            if lat > 48.4:  # Northern region
                if lng < -123.0:
                    region = "San Juan Islands / Haro Strait"
                else:
                    region = "Northern Puget Sound"
            elif 47.8 <= lat <= 48.4:  # Central region
                region = "Central Puget Sound"
            else:  # Southern region
                region = "South Puget Sound"
            
            print(f"   • {hydro['name']}: {region}")

if __name__ == "__main__":
    print("🚀 Extracting Live Hydrophone Data...")
    
    data = extract_hydrophone_data()
    
    if data:
        show_geographic_coverage(data)
        print(f"\n✅ Successfully extracted {data['active_hydrophones']} active hydrophone locations!")
        print("🎯 Ready for ORCAST integration with real live whale detection network!")
    else:
        print("❌ Failed to extract hydrophone data") 