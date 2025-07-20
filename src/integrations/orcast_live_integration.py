"""
ORCAST Live Integration with Orcasound
Integrates real live hydrophone data into ORCAST system
"""

import json
import asyncio
import aiohttp
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ORCASTLiveIntegration:
    """Integration of live Orcasound data with ORCAST system"""
    
    def __init__(self):
        self.orcasound_feed_url = "https://live.orcasound.net/api/json/feeds"
        self.hydrophones = []
        self.live_streams = {}
        self.last_update = None
    
    async def fetch_live_hydrophone_data(self):
        """Fetch current hydrophone data from Orcasound API"""
        
        logger.info("🐋 Fetching live hydrophone data from Orcasound...")
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.orcasound_feed_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if 'data' in data:
                            self.hydrophones = []
                            
                            for feed in data['data']:
                                attributes = feed.get('attributes', {})
                                
                                # Extract hydrophone info
                                hydrophone = {
                                    'id': attributes.get('node_name', ''),
                                    'name': attributes.get('name', ''),
                                    'slug': attributes.get('slug', ''),
                                    'active': attributes.get('visible', False),
                                    'bucket': attributes.get('bucket', ''),
                                    'description': self._clean_html(attributes.get('intro_html', '')),
                                    'image_url': attributes.get('image_url'),
                                    'latitude': None,
                                    'longitude': None,
                                    'last_status_check': datetime.now().isoformat(),
                                    'streams': {}
                                }
                                
                                # Extract coordinates
                                if 'location_point' in attributes:
                                    coords = attributes['location_point'].get('coordinates', [])
                                    if len(coords) >= 2:
                                        hydrophone['longitude'] = coords[0]
                                        hydrophone['latitude'] = coords[1]
                                
                                self.hydrophones.append(hydrophone)
                            
                            self.last_update = datetime.now()
                            logger.info(f"✅ Fetched {len(self.hydrophones)} hydrophones")
                            return True
                    
                    else:
                        logger.error(f"Failed to fetch data: {response.status}")
                        return False
            
            except Exception as e:
                logger.error(f"Error fetching hydrophone data: {e}")
                return False
    
    def _clean_html(self, html_text):
        """Remove HTML tags from description"""
        if not html_text:
            return ""
        
        # Simple HTML tag removal (not comprehensive, but good enough)
        import re
        clean_text = re.sub('<.*?>', '', html_text)
        clean_text = clean_text.replace('\n', ' ').strip()
        return clean_text[:200] + "..." if len(clean_text) > 200 else clean_text
    
    def get_active_hydrophones(self):
        """Get only active/visible hydrophones"""
        return [h for h in self.hydrophones if h['active']]
    
    def get_hydrophone_by_id(self, hydrophone_id):
        """Get specific hydrophone by ID"""
        for h in self.hydrophones:
            if h['id'] == hydrophone_id:
                return h
        return None
    
    def generate_orcast_frontend_data(self):
        """Generate data for ORCAST frontend integration"""
        
        active_hydrophones = self.get_active_hydrophones()
        
        frontend_data = {
            'timestamp': datetime.now().isoformat(),
            'source': 'live.orcasound.net',
            'hydrophone_count': len(active_hydrophones),
            'coverage_area': self._calculate_coverage_area(active_hydrophones),
            'hydrophones': []
        }
        
        for hydro in active_hydrophones:
            frontend_hydro = {
                'id': hydro['id'],
                'name': hydro['name'],
                'coordinates': {
                    'lat': hydro['latitude'],
                    'lng': hydro['longitude']
                },
                'status': 'active',
                'description': hydro['description'],
                'region': self._classify_region(hydro['latitude'], hydro['longitude']),
                'marker_type': 'live_hydrophone',
                'info_window': self._generate_info_window(hydro)
            }
            
            frontend_data['hydrophones'].append(frontend_hydro)
        
        return frontend_data
    
    def _calculate_coverage_area(self, hydrophones):
        """Calculate approximate coverage area of hydrophone network"""
        if len(hydrophones) < 2:
            return {"area_km2": 0, "bounds": None}
        
        lats = [h['latitude'] for h in hydrophones if h['latitude']]
        lngs = [h['longitude'] for h in hydrophones if h['longitude']]
        
        if not lats or not lngs:
            return {"area_km2": 0, "bounds": None}
        
        bounds = {
            'north': max(lats),
            'south': min(lats),
            'east': max(lngs),
            'west': min(lngs)
        }
        
        # Rough area calculation
        lat_km = (bounds['north'] - bounds['south']) * 111
        lng_km = (bounds['east'] - bounds['west']) * 111 * abs((bounds['north'] + bounds['south']) / 2 * 3.14159 / 180)
        area_km2 = lat_km * lng_km
        
        return {
            "area_km2": round(area_km2, 0),
            "bounds": bounds,
            "dimensions_km": {"lat": round(lat_km, 1), "lng": round(lng_km, 1)}
        }
    
    def _classify_region(self, lat, lng):
        """Classify hydrophone location into geographic regions"""
        if lat > 48.4:
            if lng < -123.0:
                return "San Juan Islands"
            else:
                return "Northern Puget Sound"
        elif 47.8 <= lat <= 48.4:
            return "Central Puget Sound"
        else:
            return "South Puget Sound"
    
    def _generate_info_window(self, hydrophone):
        """Generate info window content for map marker"""
        status_icon = "🟢" if hydrophone['active'] else "🔴"
        
        return f"""
        <div class="hydrophone-info">
            <h4>{status_icon} {hydrophone['name']}</h4>
            <p><strong>Status:</strong> {"Live" if hydrophone['active'] else "Offline"}</p>
            <p><strong>Location:</strong> {hydrophone['latitude']:.4f}, {hydrophone['longitude']:.4f}</p>
            <p><strong>Region:</strong> {self._classify_region(hydrophone['latitude'], hydrophone['longitude'])}</p>
            <p><strong>Description:</strong> {hydrophone['description'][:100]}...</p>
            <div class="hydrophone-actions">
                <button onclick="focusHydrophone('{hydrophone['id']}')" class="btn-small">
                    Focus Location
                </button>
                <button onclick="checkHydrophoneActivity('{hydrophone['id']}')" class="btn-small">
                    Check Activity
                </button>
            </div>
        </div>
        """
    
    async def save_integration_files(self):
        """Save integration files for ORCAST"""
        
        # Generate frontend data
        frontend_data = self.generate_orcast_frontend_data()
        
        # Save JSON data for backend
        with open('orcast_live_hydrophones.json', 'w') as f:
            json.dump(frontend_data, f, indent=2)
        
        # Generate JavaScript for frontend
        js_content = f"""
/**
 * ORCAST Live Hydrophone Integration
 * Real-time data from Orcasound network
 * Last updated: {datetime.now().isoformat()}
 */

// Live hydrophone locations from Orcasound
const LIVE_HYDROPHONES = {json.dumps(frontend_data['hydrophones'], indent=2)};

// Network coverage information
const NETWORK_COVERAGE = {json.dumps(frontend_data['coverage_area'], indent=2)};

// Integration functions
class ORCASTLiveHydrophones {{
    constructor(map) {{
        this.map = map;
        this.markers = new Map();
        this.infoWindows = new Map();
        this.lastUpdate = '{frontend_data['timestamp']}';
    }}
    
    displayHydrophones() {{
        console.log('📍 Displaying {{}} live hydrophones...', LIVE_HYDROPHONES.length);
        
        LIVE_HYDROPHONES.forEach(hydrophone => {{
            const marker = new google.maps.Marker({{
                position: hydrophone.coordinates,
                map: this.map,
                title: hydrophone.name,
                icon: {{
                    url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <circle cx="12" cy="12" r="10" fill="#2196F3" stroke="#1976D2" stroke-width="2"/>
                            <text x="12" y="16" text-anchor="middle" fill="white" font-size="12">🎙️</text>
                        </svg>
                    `),
                    scaledSize: new google.maps.Size(24, 24)
                }}
            }});
            
            const infoWindow = new google.maps.InfoWindow({{
                content: hydrophone.info_window
            }});
            
            marker.addListener('click', () => {{
                // Close other info windows
                this.infoWindows.forEach(window => window.close());
                infoWindow.open(this.map, marker);
            }});
            
            this.markers.set(hydrophone.id, marker);
            this.infoWindows.set(hydrophone.id, infoWindow);
        }});
        
        console.log('✅ Displayed {{}} live hydrophone markers', this.markers.size);
    }}
    
    focusHydrophone(hydrophoneId) {{
        const hydrophone = LIVE_HYDROPHONES.find(h => h.id === hydrophoneId);
        if (hydrophone) {{
            this.map.setCenter(hydrophone.coordinates);
            this.map.setZoom(12);
            
            const marker = this.markers.get(hydrophoneId);
            const infoWindow = this.infoWindows.get(hydrophoneId);
            
            if (marker && infoWindow) {{
                infoWindow.open(this.map, marker);
            }}
        }}
    }}
    
    getNetworkBounds() {{
        if (NETWORK_COVERAGE.bounds) {{
            return new google.maps.LatLngBounds(
                new google.maps.LatLng(NETWORK_COVERAGE.bounds.south, NETWORK_COVERAGE.bounds.west),
                new google.maps.LatLng(NETWORK_COVERAGE.bounds.north, NETWORK_COVERAGE.bounds.east)
            );
        }}
        return null;
    }}
    
    fitMapToNetwork() {{
        const bounds = this.getNetworkBounds();
        if (bounds) {{
            this.map.fitBounds(bounds);
        }}
    }}
    
    showNetworkInfo() {{
        console.log('🌊 Orcasound Network Coverage:', NETWORK_COVERAGE);
        return NETWORK_COVERAGE;
    }}
}}

// Global functions for info window buttons
function focusHydrophone(hydrophoneId) {{
    if (window.liveHydrophones) {{
        window.liveHydrophones.focusHydrophone(hydrophoneId);
    }}
}}

function checkHydrophoneActivity(hydrophoneId) {{
    // This would check for recent whale activity at this hydrophone
    console.log('Checking activity for hydrophone:', hydrophoneId);
    alert('Feature coming soon: Real-time whale activity detection at ' + hydrophoneId);
}}

// Auto-initialize when map is ready
if (typeof google !== 'undefined' && window.map) {{
    window.liveHydrophones = new ORCASTLiveHydrophones(window.map);
    window.liveHydrophones.displayHydrophones();
}} else {{
    // Wait for map to be ready
    document.addEventListener('DOMContentLoaded', () => {{
        if (window.map) {{
            window.liveHydrophones = new ORCASTLiveHydrophones(window.map);
            window.liveHydrophones.displayHydrophones();
        }}
    }});
}}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {{
    module.exports = {{ LIVE_HYDROPHONES, NETWORK_COVERAGE, ORCASTLiveHydrophones }};
}}
"""
        
        with open('js/orcast_live_hydrophones.js', 'w') as f:
            f.write(js_content)
        
        # Update index.html to include the live hydrophone integration
        html_integration = f"""
<!-- ORCAST Live Hydrophone Integration -->
<script src="js/orcast_live_hydrophones.js"></script>
<div id="live-hydrophones-status" class="status-panel">
    <h4>🎙️ Live Hydrophones ({len(frontend_data['hydrophones'])})</h4>
    <p>Coverage: {frontend_data['coverage_area']['area_km2']:.0f} km² | Last update: {datetime.now().strftime('%H:%M')}</p>
    <ul>
"""
        
        for hydro in frontend_data['hydrophones']:
            html_integration += f"""        <li>🟢 {hydro['name']} ({hydro['region']})</li>\n"""
        
        html_integration += """    </ul>
</div>
"""
        
        with open('live_hydrophones_integration.html', 'w') as f:
            f.write(html_integration)
        
        logger.info("💾 Saved integration files:")
        logger.info("   - orcast_live_hydrophones.json (backend data)")
        logger.info("   - js/orcast_live_hydrophones.js (frontend script)")
        logger.info("   - live_hydrophones_integration.html (HTML snippet)")
    
    async def update_orcast_system(self):
        """Update ORCAST system with latest live data"""
        
        logger.info("🔄 Updating ORCAST with live Orcasound data...")
        
        # Fetch latest data
        success = await self.fetch_live_hydrophone_data()
        
        if success:
            # Save integration files
            await self.save_integration_files()
            
            # Show summary
            active_count = len(self.get_active_hydrophones())
            total_count = len(self.hydrophones)
            
            logger.info(f"✅ ORCAST integration updated!")
            logger.info(f"   Active hydrophones: {active_count}/{total_count}")
            logger.info(f"   Coverage area: {self.generate_orcast_frontend_data()['coverage_area']['area_km2']:.0f} km²")
            
            # List active hydrophones
            for hydro in self.get_active_hydrophones():
                region = self._classify_region(hydro['latitude'], hydro['longitude'])
                logger.info(f"   🟢 {hydro['name']} ({region}): {hydro['latitude']:.4f}, {hydro['longitude']:.4f}")
            
            return True
        
        else:
            logger.error("❌ Failed to fetch live data")
            return False

async def main():
    """Main integration function"""
    print("🚀 ORCAST Live Integration with Orcasound")
    
    integration = ORCASTLiveIntegration()
    
    # Update ORCAST with live data
    success = await integration.update_orcast_system()
    
    if success:
        print("\n🎯 Integration Complete!")
        print("Real live hydrophone data is now integrated into ORCAST")
        print("Frontend files generated for immediate use")
        
        # Show network coverage
        coverage = integration.generate_orcast_frontend_data()['coverage_area']
        print(f"\n📊 Network Statistics:")
        print(f"   Coverage area: {coverage['area_km2']} km²")
        print(f"   Dimensions: {coverage['dimensions_km']['lat']} x {coverage['dimensions_km']['lng']} km")
        print(f"   Active hydrophones: {len(integration.get_active_hydrophones())}")
    
    else:
        print("❌ Integration failed")

if __name__ == "__main__":
    asyncio.run(main()) 