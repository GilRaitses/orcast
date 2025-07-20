# Fix ORCAST.org Deployment - Replace Backend Dashboard with Map Interface

## **🎯 The Problem**
Currently orcast.org shows a backend API inspection dashboard instead of the actual ORCAST map interface with our new ML services.

## **📁 Current Deployment Issue**
- **Live site**: Uses `PNW_summer25/firebase_orca_app/index.html` (old backend dashboard)
- **Better frontend**: Available in `orcast/public/index.html` (actual map interface)
- **New services**: ML predictions, spatial forecasting, HMC physics models (not integrated)

## **🚀 Quick Fix - Deploy Updated Frontend**

### **Option 1: Update Firebase Deployment (Recommended)**

1. **Copy the new frontend to the deployed directory:**
```bash
# Navigate to the deployed Firebase app
cd /Users/gilraitses/PNW_summer25/firebase_orca_app/

# Backup current version
cp index.html index-old-backend-dashboard.html

# Replace with our new integrated frontend
cp /Users/gilraitses/orcast/deploy_updated_frontend.html index.html

# Deploy to Firebase
firebase deploy --only hosting
```

2. **The new frontend integrates:**
   - ✅ Interactive map with real-time visualization
   - ✅ Spatial forecasting with time slider
   - ✅ Behavioral prediction models (feeding, socializing, traveling)
   - ✅ Physics-informed HMC predictions
   - ✅ Live ML service status monitoring
   - ✅ Probability heatmaps and confidence overlays

### **Option 2: Update Firebase Configuration**

Update `firebase.json` to point to the better frontend:

```json
{
  "hosting": {
    "public": "/Users/gilraitses/orcast/public",
    "ignore": ["firebase.json", "**/.*", "**/node_modules/**"]
  }
}
```

## **🔧 What The New Frontend Provides**

### **Instead of Backend API Dashboard:**
```
❌ Old: API testing panels
❌ Old: JSON response viewers  
❌ Old: Backend inspection interface
❌ Old: No map interaction
❌ Old: No real forecasting
```

### **Now Shows Advanced Map Interface:**
```
✅ Interactive Leaflet map of San Juan Islands
✅ Real-time orca probability heatmaps
✅ Time slider for spatial forecasting (Now, +6h, +12h)
✅ Behavior type selection (Feeding, Social, Travel, Confidence)
✅ Live ML service status monitoring
✅ Physics-informed predictions with uncertainty
✅ Spatial forecast generation
✅ Professional marine conservation interface
```

## **🌊 Live Feature Demonstration**

### **Time Slider Forecasting:**
- **Now**: Current orca probability distribution
- **+6 Hours**: Short-term behavioral forecasts  
- **+12 Hours**: Medium-term spatial predictions

### **Behavior Type Visualization:**
- **Feeding**: Probability heatmaps for feeding behavior
- **Socializing**: Pod interaction likelihood zones
- **Traveling**: Movement corridor predictions
- **Confidence**: Model uncertainty overlays

### **ML Service Integration:**
- **Basic ML**: `localhost:8080` - Random Forest predictions
- **Firestore ML**: `localhost:8082` - Spatial forecasting with Firebase
- **Physics HMC**: `localhost:8083` - Advanced physics-informed modeling

## **📊 Expected User Experience After Update**

### **User visits orcast.org and sees:**

1. **Professional marine conservation interface** (not API testing dashboard)
2. **Interactive map** centered on San Juan Islands
3. **Time slider controls** for temporal forecasting
4. **Behavior selection buttons** for different prediction types
5. **Live prediction panel** showing current behavioral forecasts
6. **Real-time ML service status** monitoring
7. **Probability heatmaps** overlaying the map
8. **Professional scientific visualization** for marine researchers

## **🔄 Deployment Commands**

```bash
# Quick deployment fix
cd /Users/gilraitses/PNW_summer25/firebase_orca_app/
cp /Users/gilraitses/orcast/deploy_updated_frontend.html index.html
firebase deploy --only hosting

# Verify deployment
curl -s https://orcast.org | grep "Advanced Behavioral Forecasting"
```

## **✅ Verification Steps**

After deployment, orcast.org should show:

1. ✅ **Map interface** instead of API dashboard
2. ✅ **ORCAST Advanced Behavioral Forecasting** title
3. ✅ **Interactive map** with San Juan Islands
4. ✅ **Time slider** for forecast periods
5. ✅ **Behavior buttons** (Feeding, Social, Travel, Confidence)
6. ✅ **Live prediction panel** with forecasts
7. ✅ **ML service status** monitoring
8. ✅ **Professional UI** for marine conservation

## **🎯 Result: Professional Marine Conservation Platform**

Instead of showing backend API testing panels, users will see a sophisticated marine conservation forecasting platform that demonstrates the full capabilities of your ORCAST system with spatial forecasting, behavioral predictions, and physics-informed modeling.

**The updated frontend showcases your advanced ML work properly!** 🌊🐋🔬 