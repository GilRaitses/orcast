# Enhanced ORCAST Map System

## Overview

The Enhanced ORCAST Map addresses the key issues with the previous map implementation:

**❌ Previous Issues:**
- Showed only one frame of sightings with unclear time periods
- Sliders only filtered probabilities, didn't change time periods
- No clear indication of what data was being displayed
- Mixed data types without proper separation

**✅ Enhanced Solution:**
- **Multiple toggleable layers** for different time periods
- **Independent controls** for each layer (real-time, future, historical)
- **Clear time period indicators** showing exactly what data is displayed
- **Dynamic time navigation** for historical data (day/week/month/year)
- **Real-time data updates** with configurable refresh rates

## Architecture

### Core Components

```
Enhanced Map System
├── EnhancedORCASTMap (main class)
├── Data Providers
│   ├── RealtimeDataProvider
│   ├── ForecastDataProvider
│   └── HistoricalDataProvider
├── Layer Management
│   ├── Real-time Layer (live data)
│   ├── Future Layer (forecasts)
│   └── Historical Layer (past data)
└── UI Controls
    ├── Layer toggles
    ├── Time period selectors
    ├── Independent sliders per layer
    └── Status indicators
```

### File Structure

```
orcast/
├── js/enhanced-map-component.js    # Main map component
├── css/enhanced-map.css            # Styling
├── enhanced-map-demo.html          # Demo page
└── ENHANCED_MAP_README.md          # This documentation
```

## Layer System

### 1. Real-time Layer 🔴

**Purpose:** Live orca sighting data with high confidence

**Features:**
- Auto-refresh every 30 seconds (configurable)
- Live data points with timestamps
- Probability threshold slider (0-100%)
- Opacity control
- Refresh rate control (10-300 seconds)

**Data Structure:**
```javascript
{
    lat: 48.515,
    lng: -123.152,
    probability: 85,
    timestamp: new Date(),
    confidence: 0.9
}
```

### 2. Future/Forecast Layer 🔮

**Purpose:** Predicted orca probabilities for upcoming periods

**Features:**
- Forecast periods: 24h, 48h, 7 days
- Confidence indicators
- Independent probability threshold
- Reduced opacity for uncertainty visualization

**Data Structure:**
```javascript
{
    lat: 48.515,
    lng: -123.152,
    probability: 65,
    confidence: 0.7,
    forecastTime: "24h"
}
```

### 3. Historical Layer 📈

**Purpose:** Past orca sighting data for pattern analysis

**Features:**
- Time periods: daily, weekly, monthly, yearly
- Navigation: previous/next period controls
- Historical data aggregation
- Verified sighting indicators

**Data Structure:**
```javascript
{
    lat: 48.515,
    lng: -123.152,
    probability: 78,
    confidence: 0.8,
    date: new Date("2024-07-15"),
    verified: true
}
```

## Getting Started

### 1. Setup

```bash
# Clone the feature branch
git checkout feature/enhanced-maps

# Add Google Maps API key
# Edit enhanced-map-demo.html line 11:
# Replace YOUR_GOOGLE_MAPS_API_KEY with your actual key
```

### 2. Basic Usage

```html
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="css/enhanced-map.css">
    <script src="https://maps.googleapis.com/maps/api/js?key=YOUR_KEY&libraries=visualization"></script>
</head>
<body>
    <div id="map-container"></div>
    <script src="js/enhanced-map-component.js"></script>
    <script>
        const map = new EnhancedORCASTMap('map-container', {
            center: { lat: 48.5465, lng: -123.0307 },
            zoom: 11,
            updateInterval: 30000
        });
    </script>
</body>
</html>
```

### 3. Demo

```bash
# Start local server
python3 -m http.server 8000

# Open demo
open http://localhost:8000/enhanced-map-demo.html
```

## Configuration Options

### Map Configuration

```javascript
const config = {
    center: { lat: 48.5465, lng: -123.0307 },  // Map center
    zoom: 11,                                   // Initial zoom level
    updateInterval: 30000,                      // Auto-refresh interval (ms)
    bounds: {                                   // Map boundaries
        north: 48.8,
        south: 48.3,
        east: -122.7,
        west: -123.4
    }
};
```

### Layer Configuration

```javascript
// Default layer settings
layers: {
    realtime: {
        enabled: true,
        opacity: 0.8,
        threshold: 30,
        refreshRate: 30000
    },
    future: {
        enabled: true,
        opacity: 0.6,
        threshold: 40,
        forecast: '24h'
    },
    historical: {
        enabled: true,
        opacity: 0.5,
        threshold: 50,
        period: 'week',
        offset: 0
    }
}
```

## API Reference

### Main Class: EnhancedORCASTMap

#### Constructor
```javascript
new EnhancedORCASTMap(containerId, config)
```

#### Key Methods

```javascript
// Layer control
toggleLayer(layerType, enabled)
updateLayerThreshold(layerType, threshold)
updateLayerOpacity(layerType, opacity)

// Data loading
loadRealtimeLayer()
loadFutureLayer()
loadHistoricalLayer()
refreshAllLayers()

// Time navigation
updateForecastPeriod(period)        // '24h', '48h', '7d'
updateHistoricalPeriod(period)      // 'day', 'week', 'month', 'year'
navigateHistorical(direction)       // -1 (previous), 1 (next)

// Auto-update control
startAutoUpdate()
stopAutoUpdate()
updateRefreshRate(milliseconds)

// Map control
resetMapView()
```

### Data Provider Classes

#### RealtimeDataProvider
```javascript
class RealtimeDataProvider {
    async getCurrentData()              // Returns live sighting data
    generateRealtimeData()              // Simulates real-time data
}
```

#### ForecastDataProvider
```javascript
class ForecastDataProvider {
    async getForecastData(period)       // Returns forecast for period
    generateForecastData(period)        // Simulates forecast data
}
```

#### HistoricalDataProvider
```javascript
class HistoricalDataProvider {
    async getHistoricalData(period, offset)  // Returns historical data
    generateHistoricalData(period, offset)   // Simulates historical data
    getHistoricalDate(period, offset)        // Calculates date for period
}
```

## Development Tasks

### Priority 1: Data Integration

**Current:** Uses simulated data
**Goal:** Connect to real APIs

```javascript
// TODO: Replace simulation with real API calls
class RealtimeDataProvider {
    async getCurrentData() {
        // Replace with:
        // const response = await fetch('/api/realtime-sightings');
        // return response.json();
        
        return this.generateRealtimeData(); // Remove this
    }
}
```

### Priority 2: Time Period Accuracy

**Current:** Basic time period display
**Goal:** Accurate time boundaries

```javascript
// TODO: Implement precise time filtering
function filterDataByTimePeriod(data, period, offset) {
    const now = new Date();
    const boundaries = calculateTimeBoundaries(period, offset);
    
    return data.filter(point => {
        return point.timestamp >= boundaries.start && 
               point.timestamp <= boundaries.end;
    });
}
```

### Priority 3: Performance Optimization

**Current:** Redraws entire heatmaps
**Goal:** Incremental updates

```javascript
// TODO: Implement incremental heatmap updates
class LayerManager {
    updateHeatmapIncremental(newData, removedData) {
        // Only update changed points
        // Preserve existing visualization state
    }
}
```

### Priority 4: Advanced Features

#### Real-time Notifications
```javascript
// TODO: Add real-time alerts
class EnhancedORCASTMap {
    setupRealTimeNotifications() {
        // WebSocket connection for live updates
        // Browser notifications for high-probability sightings
    }
}
```

#### Export/Share
```javascript
// TODO: Add export capabilities
exportCurrentView(format) {
    // Export as PNG/PDF
    // Share current layer configuration
    // Generate shareable URLs
}
```

## Testing

### Unit Tests
```javascript
// Test layer management
describe('Layer Management', () => {
    test('toggles layer visibility', () => {
        const map = new EnhancedORCASTMap('test-container');
        map.toggleLayer('realtime', false);
        expect(map.layers.realtime.enabled).toBe(false);
    });
});
```

### Integration Tests
```javascript
// Test data provider integration
describe('Data Integration', () => {
    test('loads real-time data', async () => {
        const provider = new RealtimeDataProvider();
        const data = await provider.getCurrentData();
        expect(data).toHaveLength.greaterThan(0);
    });
});
```

## Troubleshooting

### Common Issues

#### Google Maps API Issues
```javascript
// Check API key and libraries
window.gm_authFailure = function() {
    console.error('Maps API auth failed');
    // Show error message to user
};
```

#### Performance Issues
```javascript
// Limit data points per layer
const MAX_POINTS_PER_LAYER = 1000;

function limitDataPoints(data) {
    if (data.length > MAX_POINTS_PER_LAYER) {
        // Keep highest probability points
        return data.sort((a, b) => b.probability - a.probability)
                   .slice(0, MAX_POINTS_PER_LAYER);
    }
    return data;
}
```

#### Memory Leaks
```javascript
// Clean up event listeners and intervals
class EnhancedORCASTMap {
    destroy() {
        this.stopAutoUpdate();
        // Remove all event listeners
        // Clear heatmap layers
    }
}
```

## Keyboard Shortcuts

**Development shortcuts:**
- `Ctrl/Cmd + R`: Refresh all layers
- `Ctrl/Cmd + 1`: Toggle real-time layer
- `Ctrl/Cmd + 2`: Toggle future layer
- `Ctrl/Cmd + 3`: Toggle historical layer

## Next Steps

1. **Connect Real APIs**: Replace simulated data with actual sighting APIs
2. **Add Time Accuracy**: Implement precise time period filtering
3. **Optimize Performance**: Add incremental updates and data limits
4. **Enhanced UX**: Add loading states, error handling, offline support
5. **Advanced Features**: Real-time notifications, export/share capabilities

## Support

- **Demo**: `enhanced-map-demo.html`
- **Documentation**: This file
- **Code**: `js/enhanced-map-component.js`
- **Styling**: `css/enhanced-map.css`

The enhanced map system provides a solid foundation for multi-temporal orca probability visualization with clear separation of concerns and extensible architecture. 