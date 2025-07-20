# ORCAST - Orca Behavioral Analysis Platform

🐋 **Real-time orca probability mapping using machine learning and biologging data**

**Live Demo:** [orcast.org](https://orcast.org)

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

### 🏗️ Architecture
```
ORCAST (323 lines clean HTML)
├── CSS Modules (511 lines across 4 files)
├── JS Components (522 lines across 4 files)  
├── Real Data (1,354 orca sightings + 427KB grid)
└── API Endpoints (5 working JSON endpoints)
```

### 📊 What's Already Built
✅ **Interactive map** with real orca sightings  
✅ **Time navigation** (weeks/months/years of historical data)  
✅ **Probability filtering** with confidence thresholds  
✅ **API inspection** panels for backend testing  
✅ **Real research data** from San Juan Islands  
✅ **Professional UI** with modular CSS  

### 🎯 Hackathon Goals
- **Day 1:** Parallel development on assigned tracks
- **Day 1 PM:** Integration testing and deployment
- **Day 2:** Polish, optimization, and demo prep

### 🔧 Development Commands
```bash
# Deploy changes
firebase deploy --only hosting

# Test API endpoints
curl https://orcast.org/api/predictions

# Check logs
firebase logs
```

### 📞 Need Help?
1. **Read:** [TEAM_DEVELOPER_GUIDE.md](./TEAM_DEVELOPER_GUIDE.md)
2. **Debug:** Open browser console for errors
3. **Test:** Refresh browser after changes
4. **Deploy:** `firebase deploy --only hosting`

---

## 📁 File Structure
```
firebase_orca_app/
├── index.html (323 lines - main app)
├── css/
│   ├── base.css (global styles)
│   ├── sidebar.css (controls)
│   ├── tabs.css (navigation)
│   └── inspection.css (panels)
├── js/
│   ├── data-loader.js (real data)
│   ├── map-component.js (Google Maps)
│   ├── api-tester.js (backend testing)
│   └── ui-controller.js (interactions)
└── data/
    ├── sample_user_sightings.json (1,354 sightings)
    ├── firebase_orca_probability_data.json (427KB grid)
    └── environmental_data_*.json (NOAA data)
```

**The codebase is designed for parallel development - each developer can work independently without conflicts!** 