
/**
 * ORCAST Live Hydrophone Integration
 * Real-time data from Orcasound network
 * Last updated: 2025-07-19T19:48:14.586384
 */

// Live hydrophone locations from Orcasound
const LIVE_HYDROPHONES = [
  {
    "id": "rpi_north_sjc",
    "name": "North San Juan Channel",
    "coordinates": {
      "lat": 48.591294,
      "lng": -123.058779
    },
    "status": "active",
    "description": "This an ideal location for hearing sounds made by orcas, humpbacks, and other marine life -- including fish. Bigg's killer whales frequent this location year round, and Southern Resident killer whales...",
    "region": "San Juan Islands",
    "marker_type": "live_hydrophone",
    "info_window": "\n        <div class=\"hydrophone-info\">\n            <h4>\ud83d\udfe2 North San Juan Channel</h4>\n            <p><strong>Status:</strong> Live</p>\n            <p><strong>Location:</strong> 48.5913, -123.0588</p>\n            <p><strong>Region:</strong> San Juan Islands</p>\n            <p><strong>Description:</strong> This an ideal location for hearing sounds made by orcas, humpbacks, and other marine life -- includi...</p>\n            <div class=\"hydrophone-actions\">\n                <button onclick=\"focusHydrophone('rpi_north_sjc')\" class=\"btn-small\">\n                    Focus Location\n                </button>\n                <button onclick=\"checkHydrophoneActivity('rpi_north_sjc')\" class=\"btn-small\">\n                    Check Activity\n                </button>\n            </div>\n        </div>\n        "
  },
  {
    "id": "rpi_sunset_bay",
    "name": "Beach Camp at Sunset Bay",
    "coordinates": {
      "lat": 47.86497296593844,
      "lng": -122.33393605795372
    },
    "status": "active",
    "description": "Located halfway between Edmonds and Mukilteo, this is a good place to listen to central Puget Sound. You may hear sounds from marine life like killer whales, seals, and possibly humpback or gray whale...",
    "region": "Central Puget Sound",
    "marker_type": "live_hydrophone",
    "info_window": "\n        <div class=\"hydrophone-info\">\n            <h4>\ud83d\udfe2 Beach Camp at Sunset Bay</h4>\n            <p><strong>Status:</strong> Live</p>\n            <p><strong>Location:</strong> 47.8650, -122.3339</p>\n            <p><strong>Region:</strong> Central Puget Sound</p>\n            <p><strong>Description:</strong> Located halfway between Edmonds and Mukilteo, this is a good place to listen to central Puget Sound....</p>\n            <div class=\"hydrophone-actions\">\n                <button onclick=\"focusHydrophone('rpi_sunset_bay')\" class=\"btn-small\">\n                    Focus Location\n                </button>\n                <button onclick=\"checkHydrophoneActivity('rpi_sunset_bay')\" class=\"btn-small\">\n                    Check Activity\n                </button>\n            </div>\n        </div>\n        "
  },
  {
    "id": "rpi_port_townsend",
    "name": "Port Townsend",
    "coordinates": {
      "lat": 48.135743,
      "lng": -122.760614
    },
    "status": "active",
    "description": "This is a great location to hear the Southern Resident killer whales as they pass through Admiralty Inlet in search of salmon. This can happen any time of year, but is more common in the fall when coh...",
    "region": "Central Puget Sound",
    "marker_type": "live_hydrophone",
    "info_window": "\n        <div class=\"hydrophone-info\">\n            <h4>\ud83d\udfe2 Port Townsend</h4>\n            <p><strong>Status:</strong> Live</p>\n            <p><strong>Location:</strong> 48.1357, -122.7606</p>\n            <p><strong>Region:</strong> Central Puget Sound</p>\n            <p><strong>Description:</strong> This is a great location to hear the Southern Resident killer whales as they pass through Admiralty ...</p>\n            <div class=\"hydrophone-actions\">\n                <button onclick=\"focusHydrophone('rpi_port_townsend')\" class=\"btn-small\">\n                    Focus Location\n                </button>\n                <button onclick=\"checkHydrophoneActivity('rpi_port_townsend')\" class=\"btn-small\">\n                    Check Activity\n                </button>\n            </div>\n        </div>\n        "
  },
  {
    "id": "rpi_orcasound_lab",
    "name": "Orcasound Lab",
    "coordinates": {
      "lat": 48.5583362,
      "lng": -123.1735774
    },
    "status": "active",
    "description": "Centered with in the summertime habitat of the endangered Southern Resident killer whales, Orcasound Lab is a good place to listen for orcas, as well as ships passing through Haro Strait and boats tra...",
    "region": "San Juan Islands",
    "marker_type": "live_hydrophone",
    "info_window": "\n        <div class=\"hydrophone-info\">\n            <h4>\ud83d\udfe2 Orcasound Lab</h4>\n            <p><strong>Status:</strong> Live</p>\n            <p><strong>Location:</strong> 48.5583, -123.1736</p>\n            <p><strong>Region:</strong> San Juan Islands</p>\n            <p><strong>Description:</strong> Centered with in the summertime habitat of the endangered Southern Resident killer whales, Orcasound...</p>\n            <div class=\"hydrophone-actions\">\n                <button onclick=\"focusHydrophone('rpi_orcasound_lab')\" class=\"btn-small\">\n                    Focus Location\n                </button>\n                <button onclick=\"checkHydrophoneActivity('rpi_orcasound_lab')\" class=\"btn-small\">\n                    Check Activity\n                </button>\n            </div>\n        </div>\n        "
  },
  {
    "id": "rpi_bush_point",
    "name": "Bush Point",
    "coordinates": {
      "lat": 48.0336664,
      "lng": -122.6040035
    },
    "status": "active",
    "description": "This is a great place to listen for the Southern Resident killer whales who pass through Admiralty Inlet about once a month in search of salmon. Other common sounds here come from ships heading to and...",
    "region": "Central Puget Sound",
    "marker_type": "live_hydrophone",
    "info_window": "\n        <div class=\"hydrophone-info\">\n            <h4>\ud83d\udfe2 Bush Point</h4>\n            <p><strong>Status:</strong> Live</p>\n            <p><strong>Location:</strong> 48.0337, -122.6040</p>\n            <p><strong>Region:</strong> Central Puget Sound</p>\n            <p><strong>Description:</strong> This is a great place to listen for the Southern Resident killer whales who pass through Admiralty I...</p>\n            <div class=\"hydrophone-actions\">\n                <button onclick=\"focusHydrophone('rpi_bush_point')\" class=\"btn-small\">\n                    Focus Location\n                </button>\n                <button onclick=\"checkHydrophoneActivity('rpi_bush_point')\" class=\"btn-small\">\n                    Check Activity\n                </button>\n            </div>\n        </div>\n        "
  }
];

// Network coverage information
const NETWORK_COVERAGE = {
  "area_km2": 6325.0,
  "bounds": {
    "north": 48.591294,
    "south": 47.86497296593844,
    "east": -122.33393605795372,
    "west": -123.1735774
  },
  "dimensions_km": {
    "lat": 80.6,
    "lng": 78.5
  }
};

// Integration functions
class ORCASTLiveHydrophones {
    constructor(map) {
        this.map = map;
        this.markers = new Map();
        this.infoWindows = new Map();
        this.lastUpdate = '2025-07-19T19:48:14.585533';
    }
    
    displayHydrophones() {
        console.log('📍 Displaying {} live hydrophones...', LIVE_HYDROPHONES.length);
        
        LIVE_HYDROPHONES.forEach(hydrophone => {
            const marker = new google.maps.Marker({
                position: hydrophone.coordinates,
                map: this.map,
                title: hydrophone.name,
                icon: {
                    url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <circle cx="12" cy="12" r="10" fill="#2196F3" stroke="#1976D2" stroke-width="2"/>
                            <text x="12" y="16" text-anchor="middle" fill="white" font-size="12">🎙️</text>
                        </svg>
                    `),
                    scaledSize: new google.maps.Size(24, 24)
                }
            });
            
            const infoWindow = new google.maps.InfoWindow({
                content: hydrophone.info_window
            });
            
            marker.addListener('click', () => {
                // Close other info windows
                this.infoWindows.forEach(window => window.close());
                infoWindow.open(this.map, marker);
            });
            
            this.markers.set(hydrophone.id, marker);
            this.infoWindows.set(hydrophone.id, infoWindow);
        });
        
        console.log('✅ Displayed {} live hydrophone markers', this.markers.size);
    }
    
    focusHydrophone(hydrophoneId) {
        const hydrophone = LIVE_HYDROPHONES.find(h => h.id === hydrophoneId);
        if (hydrophone) {
            this.map.setCenter(hydrophone.coordinates);
            this.map.setZoom(12);
            
            const marker = this.markers.get(hydrophoneId);
            const infoWindow = this.infoWindows.get(hydrophoneId);
            
            if (marker && infoWindow) {
                infoWindow.open(this.map, marker);
            }
        }
    }
    
    getNetworkBounds() {
        if (NETWORK_COVERAGE.bounds) {
            return new google.maps.LatLngBounds(
                new google.maps.LatLng(NETWORK_COVERAGE.bounds.south, NETWORK_COVERAGE.bounds.west),
                new google.maps.LatLng(NETWORK_COVERAGE.bounds.north, NETWORK_COVERAGE.bounds.east)
            );
        }
        return null;
    }
    
    fitMapToNetwork() {
        const bounds = this.getNetworkBounds();
        if (bounds) {
            this.map.fitBounds(bounds);
        }
    }
    
    showNetworkInfo() {
        console.log('🌊 Orcasound Network Coverage:', NETWORK_COVERAGE);
        return NETWORK_COVERAGE;
    }
}

// Global functions for info window buttons
function focusHydrophone(hydrophoneId) {
    if (window.liveHydrophones) {
        window.liveHydrophones.focusHydrophone(hydrophoneId);
    }
}

function checkHydrophoneActivity(hydrophoneId) {
    // This would check for recent whale activity at this hydrophone
    console.log('Checking activity for hydrophone:', hydrophoneId);
    alert('Feature coming soon: Real-time whale activity detection at ' + hydrophoneId);
}

// Auto-initialize when map is ready
if (typeof google !== 'undefined' && window.map) {
    window.liveHydrophones = new ORCASTLiveHydrophones(window.map);
    window.liveHydrophones.displayHydrophones();
} else {
    // Wait for map to be ready
    document.addEventListener('DOMContentLoaded', () => {
        if (window.map) {
            window.liveHydrophones = new ORCASTLiveHydrophones(window.map);
            window.liveHydrophones.displayHydrophones();
        }
    });
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { LIVE_HYDROPHONES, NETWORK_COVERAGE, ORCASTLiveHydrophones };
}
