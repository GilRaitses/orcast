# ORCAST - Orca Behavioral Analysis Platform

🐋 **Real-time orca probability mapping using machine learning and biologging data**

**Live Demo:** [https://orca-904de.web.app](https://orca-904de.web.app) - *Press the "Live Demo" button*  
**Demo Video:** [YouTube Demo Recording](https://youtu.be/y5YW2WoxRYs)  
**Website:** [orcast.org](https://orcast.org) - *Click "Live Demo" to see real-time AI coordination*

## 🎬 **NEW: Live AI Demo with Real Data Integration**

### ✨ **Latest Features (July 2025)**
🌩️ **Forecast Probability Clouds** - Weather-map style probability overlays  
🔍 **Real Database Integration** - Live sightings from production endpoints  
🧠 **Multi-Agent AI Orchestration** - Gemma 3 powered coordination  
🎤 **Live Hydrophone Network** - Real-time acoustic monitoring  
📊 **ML Prediction Visualization** - kernel-forecast (LNP/GLM) intensity on map *(legacy hackathon copy mentioned "PINN"; the honest modeling approach is the leveled kernel/LNP program, not a full PINN -- see SYNTHESIS_signal_modeling.md / M2)*  

### 🚀 **Live Demo Endpoints**
| Endpoint | Purpose | Status |
|----------|---------|--------|
| `/api/recent-sightings` | Real orca sightings from database | ✅ Live |
| `/api/ml-predictions` | ML model predictions for probability clouds | ✅ Live |
| `/api/environmental-data` | NOAA/DFO environmental conditions | ✅ Live |
| `/api/hydrophone-data` | Acoustic monitoring stations | ✅ Live |

### 🌊 **Forecast Clouds System**
**Like weather radar, but for orcas!**
- **Red/Orange clouds** = High probability zones (>70%)
- **Yellow clouds** = Medium probability zones (50-70%)
- **Green/Blue clouds** = Lower probability zones (<50%)
- **Cloud size** scales with prediction confidence
- **Real-time updates** from ML models

## Quick Start for Hackathon Team

### 📋 Team Onboarding
**👉 [READ THE TEAM DEVELOPER GUIDE](./TEAM_DEVELOPER_GUIDE.md) 👈**

### 🚀 Instant Setup
```bash
# 1. Install Firebase CLI
npm install -g firebase-tools

# 2. Start local development  
firebase serve

# 3. Open http://localhost:5000
```

### 👥 Parallel Development Tracks

| Track | Owner | Files | Independence |
|-------|-------|-------|--------------|
| **Frontend UI/UX** | Visual design | `css/*.css` | ⭐⭐⭐⭐⭐ |
| **Map Visualization** | Google Maps | `js/map-component.js` | ⭐⭐⭐⭐ |
| **Backend Integration** | APIs & Data | `js/data-loader.js`, `js/api-tester.js` | ⭐⭐⭐⭐ |
| **UI Controller** | User experience | `js/ui-controller.js`, `index.html` | ⭐⭐⭐ |
| **🆕 AI Demo** | Live agent coordination | `orcast-angular/src/app/components/live-ai-demo/` | ⭐⭐⭐⭐⭐ |

### 🏗️ Architecture
```
ORCAST (Real-time AI Platform)
├── Angular Frontend (Live AI Demo + Map Interface)
├── Multi-Agent AI System (Gemma 3 Orchestration)
├── Real Database Integration (Production Endpoints)
├── ML Pipeline (kernel-forecast LNP/GLM; legacy "PINN" label retired)
├── Forecast Clouds System (Probability Visualization)
└── Live Data Sources (NOAA, DFO, Hydrophones)
```

### 📊 What's Already Built
✅ **Interactive map** with real orca sightings  
✅ **Time navigation** (weeks/months/years of historical data)  
✅ **Probability filtering** with confidence thresholds  
✅ **API inspection** panels for backend testing  
✅ **Real research data** from San Juan Islands  
✅ **Professional UI** with modular CSS  
✅ **🆕 Live AI agent coordination** with real-time transcripts  
✅ **🆕 Forecast probability clouds** like weather maps  
✅ **🆕 Real database integration** from production endpoints  
✅ **🆕 Multi-modal data fusion** (acoustic, visual, environmental)  

### 🎯 Hackathon Goals
- **Day 1:** Multi-agent AI demonstration
- **Day 2:** Real data integration validation  
- **Day 3:** Forecast system optimization
- **Demo:** Live spatial analysis with probability clouds 