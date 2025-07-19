# ORCAST Hackathon Team Developer Guide

## Overview

ORCAST is a **real-time orca behavioral analysis platform** using machine learning and biologging data from the San Juan Islands. The codebase has been architected for **parallel development** - multiple team members can work simultaneously without conflicts.

**Live Demo:** [orcast.org](https://orcast.org)  
**Architecture:** Modular components with clean separation of concerns  
**Data:** 1,354 real orca sightings + 427KB probability grid data  

---

## 🏗️ Architecture Overview

```
ORCAST Platform
├── Frontend UI (HTML + CSS modules)
├── Map Visualization (Google Maps + real data)  
├── API Backend Integration (JSON endpoints)
└── Data Processing (Real research datasets)
```

**Core Philosophy:** Each developer owns specific modules and can work independently.

---

## 👥 Parallel Developer Tracks

### Track 1: Frontend UI/UX Developer
**Owner:** Frontend design, user experience, visual components  
**Files:** CSS modules, HTML structure  
**Independence Level:** ⭐⭐⭐⭐⭐ (Fully independent)

#### Responsibilities:
- Visual design and styling
- Responsive layout improvements 
- Tab navigation enhancements
- Control panel design
- Loading animations and transitions

#### Your Files:
```
css/
├── base.css        - Global layout, typography, foundations
├── sidebar.css     - Left control panel, sliders, buttons
├── tabs.css        - Tab navigation, map container, legends  
└── inspection.css  - Backend panels, API response styling
```

#### Quick Start:
1. **Test changes live:** Modify any CSS file and refresh browser
2. **No conflicts:** CSS changes don't affect JavaScript functionality
3. **Focus areas:** 
   - Improve color schemes and animations
   - Add mobile responsiveness 
   - Enhance visual feedback for controls
   - Design better loading states

#### Example Tasks:
- Add smooth transitions to tab switching
- Improve slider visual design
- Create animated loading indicators
- Design dark/light theme toggle
- Enhance probability legend styling

---

### Track 2: Map Visualization Specialist  
**Owner:** Google Maps integration, geospatial rendering, data visualization  
**Files:** Map component JavaScript  
**Independence Level:** ⭐⭐⭐⭐ (Mostly independent)

#### Responsibilities:
- Map rendering and interaction
- Heatmap generation from real data
- Marker clustering and optimization
- Geospatial data processing
- Interactive map features

#### Your Files:
```
js/
└── map-component.js  - Google Maps integration (232 lines)
```

#### Data Sources Available:
- **Real Sightings:** `data/sample_user_sightings.json` (1,354 sightings)
- **Probability Grid:** `data/firebase_orca_probability_data.json` (50x50 grid)
- **Environmental:** `data/environmental_data_*.json`

#### Quick Start:
1. **Your component:** `ORCASTMap` class handles all map functionality
2. **Real data access:** `window.dataLoader.filterRealSightingsData()`
3. **Focus areas:**
   - Improve heatmap visualization
   - Add clustering for dense marker areas
   - Implement zoom-level adaptive rendering
   - Create custom map styles

#### Example Tasks:
- Add marker clustering for better performance
- Implement time-based animation of sightings
- Create custom orca-themed map markers
- Add polygon overlay for feeding zones
- Optimize rendering for mobile devices

---

### Track 3: Backend Integration Developer
**Owner:** API endpoints, data processing, external service integration  
**Files:** Data loader and API testing modules  
**Independence Level:** ⭐⭐⭐⭐ (Mostly independent)

#### Responsibilities:
- Real data loading and caching
- API endpoint testing and monitoring
- External service integration
- Data validation and error handling
- Performance optimization

#### Your Files:
```
js/
├── data-loader.js  - Real data processing (125 lines)
└── api-tester.js   - Backend endpoint testing (58 lines)
```

#### Current API Endpoints:
- `GET /api/predictions` - Behavioral prediction results
- `GET /api/behavioral-analysis` - TagTools analysis  
- `GET /api/real-time-data` - Environmental conditions
- `GET /api/feeding-zones` - Feeding zone analytics
- `GET /api/dtag-data` - Biologging device data

#### Quick Start:
1. **Data processing:** Modify `DataLoader` class methods
2. **API testing:** Enhance `APITester` for better debugging
3. **Focus areas:**
   - Add data caching mechanisms
   - Implement real-time data updates
   - Add error recovery and retry logic
   - Create data validation pipelines

#### Example Tasks:
- Add WebSocket support for real-time updates
- Implement intelligent data caching
- Create background data refresh system
- Add data quality monitoring
- Build offline mode with cached data

---

### Track 4: UI Controller & Experience Developer
**Owner:** User interactions, tab system, interface logic  
**Files:** UI controller and main application flow  
**Independence Level:** ⭐⭐⭐ (Some coordination needed)

#### Responsibilities:
- Tab navigation system
- User interaction handling
- Application state management
- Global UI coordination
- User experience flows

#### Your Files:
```
js/
└── ui-controller.js  - Interface management (107 lines)
index.html           - Main application structure (323 lines)
```

#### Quick Start:
1. **Your component:** `UIController` class manages all interactions
2. **Global functions:** Tab switching, time controls, thresholds
3. **Focus areas:**
   - Enhance tab navigation
   - Add keyboard shortcuts
   - Implement user preferences
   - Create guided tour system

#### Example Tasks:
- Add keyboard navigation (arrow keys, space bar)
- Implement user preference saving
- Create guided onboarding tour
- Add search/filter functionality
- Build export/sharing features

---

## 🔄 Integration Points

### How Components Communicate:

```javascript
// Data flows between components:
DataLoader → MapComponent → UIController
     ↓           ↑
APITester ← UIController → CSS Styling
```

### Key Integration APIs:

```javascript
// 1. Data Loader (Backend Dev owns)
window.dataLoader.filterRealSightingsData(timeUnit, offset, threshold)

// 2. Map Component (Map Dev owns)  
orcastMap.updateHeatmapData()
orcastMap.setTimeUnit(unit)

// 3. UI Controller (UI Dev owns)
window.uiController.switchTab(tabName)
window.uiController.setupGlobalFunctions()

// 4. API Tester (Backend Dev owns)
window.apiTester.testEndpoint(endpoint, responseId)
```

---

## 🚀 Development Workflow

### Day 1 Morning: Setup & Parallel Work
1. **All Devs:** Clone repo, test `firebase serve` locally
2. **Frontend Dev:** Start with `css/base.css` improvements
3. **Map Dev:** Enhance `js/map-component.js` clustering
4. **Backend Dev:** Optimize `js/data-loader.js` caching
5. **UI Dev:** Add keyboard shortcuts to `js/ui-controller.js`

### Day 1 Afternoon: Integration Testing
1. **All Devs:** Test individual changes locally
2. **Integration:** Merge and test component interactions
3. **Deploy:** `firebase deploy --only hosting`
4. **Demo:** Test complete user flows

### Day 2: Polish & Demo Prep
1. **Frontend:** Final styling and animations
2. **Map:** Performance optimization and visual polish
3. **Backend:** Error handling and reliability
4. **UI:** User experience improvements and demo features

---

## 🔧 Technical Setup

### Prerequisites:
```bash
# Install Firebase CLI
npm install -g firebase-tools

# Authenticate
firebase login

# Start local development
firebase serve
```

### File Watching for Live Development:
- **CSS changes:** Refresh browser immediately  
- **JavaScript changes:** Refresh browser to reload modules
- **HTML changes:** Refresh browser

### Deployment:
```bash
# Deploy all changes
firebase deploy --only hosting

# Test at: https://orcast.org
```

---

## 📊 Current Data Assets

### Real Research Data Available:
- **1,354 orca sightings** with GPS coordinates, behaviors, confidence levels
- **427KB probability grid** (50x50 resolution) 
- **Environmental data** from NOAA/DART sources
- **TagTools analysis** from biologging devices

### API Response Examples:
```json
// Sighting data structure:
{
  "lat": 48.515, "lng": -123.152,
  "probability": 85, "behavior": "foraging",
  "confidence": "high", "verified": true,
  "timestamp": 1751348556181
}

// Probability grid structure:
{
  "metadata": {"grid_resolution": {"lat": 50, "lon": 50}},
  "coordinate_arrays": {"latitudes": [...], "longitudes": [...]}
}
```

---

## 🎯 Hackathon Success Metrics

### Core Demo Features (Must Have):
- ✅ Interactive map with real orca data
- ✅ Time period navigation (weeks/months/years)
- ✅ Probability threshold filtering  
- ✅ Working API endpoint demonstrations
- ✅ Professional visual design

### Stretch Goals (Nice to Have):
- 🎯 Real-time data updates
- 🎯 Mobile responsiveness
- 🎯 Export/sharing functionality
- 🎯 Guided user tour
- 🎯 Advanced data visualizations

---

## 🤝 Communication Protocol

### Daily Standups:
- **What:** 5-minute status updates
- **When:** Morning and after lunch
- **Format:** Current task, blockers, next steps

### Integration Points:
- **CSS → HTML:** Coordinate class names and structure
- **JS → HTML:** Coordinate element IDs and event handlers  
- **Data → Map:** Coordinate data format expectations
- **API → UI:** Coordinate loading states and error handling

### Conflict Resolution:
- **CSS conflicts:** Frontend dev has final say
- **JavaScript structure:** Backend dev coordinates module interfaces
- **UX decisions:** UI dev drives user experience choices
- **Map features:** Map dev owns visualization decisions

---

## 📞 Need Help?

### Quick Debug Commands:
```bash
# Check if everything is loading
firebase serve
# Open browser console and look for errors

# Test API endpoints
curl https://orcast.org/api/predictions

# Validate CSS
# Open browser dev tools → Styles tab

# Test JavaScript modules  
# Browser console → Check for module load errors
```

### File Dependencies:
- **CSS files:** Independent (no dependencies)
- **JavaScript files:** Some dependencies (see integration APIs above)
- **HTML file:** Imports all modules (coordinate with UI dev for changes)

**Remember: The architecture is designed for independence. When in doubt, focus on your track and coordinate at integration points!** 🚀

## Questions?
The modular architecture means you can experiment freely in your domain. Most changes won't break other developers' work! 