# ORCAST Angular - Live AI Demo Platform

🐋 **Real-time orca probability mapping with multi-agent AI coordination**

**Live Demo:** [https://orca-904de.web.app](https://orca-904de.web.app)  
**Demo Video:** [YouTube Recording](https://youtu.be/y5YW2WoxRYs)  
**Website:** [orcast.org](https://orcast.org) - *Press the "Live Demo" button for real-time AI demo*

## ✨ **New Features - Real Data Integration**

### 🌩️ **Forecast Probability Clouds**
Weather-map style probability visualization overlaid on San Juan Islands:
- **Red/Orange clouds** = High probability zones (>70%)
- **Yellow clouds** = Medium probability zones (50-70%)  
- **Green/Blue clouds** = Lower probability zones (<50%)
- **Cloud size** scales with prediction confidence

### 🔍 **Live Database Integration**
- **Real sightings** from production database (not hardcoded)
- **Dynamic loading** of all historical orca data
- **Live API responses** from backend endpoints
- **Multi-agent coordination** with real-time transcripts

### 🎯 **Live AI Demo Component**
Located in: `src/app/components/live-ai-demo/`
- **Map-centered interface** with San Juan Islands focus
- **Real-time agent transcripts** showing coordination
- **Production endpoint integration** 
- **Forecast cloud generation** like weather radar

## Development server

To start a local development server, run:

```bash
ng serve
```

Once the server is running, open your browser and navigate to `http://localhost:4200/`. The application will automatically reload whenever you modify any of the source files.

## Production Build & Deploy

```bash
# Build for production
npm run build:prod

# Deploy to Firebase (from parent directory)
cd .. && firebase deploy --only hosting
```

## Live Demo Testing

Run automated Cypress tests with video recording:

```bash
# Run full demo test with video
npx cypress run --spec "cypress/e2e/live-demo-recording.cy.ts" --headed --browser chrome

# Check video output
ls -la cypress/videos/
```

## Code scaffolding

Angular CLI includes powerful code scaffolding tools. To generate a new component, run:

```bash
ng generate component component-name
```

For a complete list of available schematics (such as `components`, `directives`, or `pipes`), run:

```bash
ng generate --help
```

## Real API Endpoints

The live demo integrates with these production endpoints:

| Endpoint | Purpose | Component Integration |
|----------|---------|----------------------|
| `/api/recent-sightings` | Real orca database | `fetchRecentSightings()` |
| `/api/ml-predictions` | ML model outputs | `fetchMLPredictions()` + `createForecastClouds()` |
| `/api/environmental-data` | NOAA/DFO data | `fetchEnvironmentalData()` |
| `/api/hydrophone-data` | Acoustic monitoring | `fetchHydrophoneData()` |

## Map Configuration

- **Bounds locked** to San Juan Islands region
- **No recentering** on mode switches  
- **Dynamic overlays** for all data types
- **Probability clouds** generated via HTML5 Canvas
- **Real-time updates** from agent coordination

## Agent Transcript System

Live agent messages show:
- **Endpoint responses** with data counts
- **ML model status** and prediction confidence  
- **Environmental conditions** from real APIs
- **Forecast generation** with probability zones

Perfect for demonstrating that all backend services are functional!
