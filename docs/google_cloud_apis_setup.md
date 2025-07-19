# Google Cloud APIs Setup for Orca Tracker

## 🗺️ Required APIs (Essential)

### 1. **Maps JavaScript API**
**Purpose**: Interactive maps with satellite imagery, heatmap layers  
**Setup**: 
```bash
gcloud services enable maps-backend.googleapis.com
```
**Cost**: $7/1000 map loads (first 28,000 free/month)  
**Usage**: Core map functionality, satellite views, user interaction

### 2. **Places API**
**Purpose**: Location search, nearby marine facilities  
**Setup**:
```bash
gcloud services enable places-backend.googleapis.com
```
**Cost**: $0.032/request  
**Usage**: "Find whale watching tours near me", marina locations

### 3. **Geocoding API**
**Purpose**: Convert addresses to coordinates for sighting reports  
**Setup**:
```bash
gcloud services enable geocoding-backend.googleapis.com
```
**Cost**: $0.005/request  
**Usage**: User location input, address validation

## 🤖 Vertex AI APIs (Intelligence Features)

### 4. **Vision AI** ⭐ **HIGHLY RECOMMENDED**
**Purpose**: Automatic orca identification from user photos  
**Setup**:
```bash
gcloud services enable vision.googleapis.com
```
**Features**:
- **Species identification**: Distinguish orcas from other whales
- **Individual recognition**: Identify specific orcas by markings
- **Photo quality assessment**: Validate sighting images
- **Behavior analysis**: Detect breaching, feeding, socializing

**Code Integration**:
```javascript
// Analyze uploaded orca photos
async function analyzeOrcaPhoto(imageBase64) {
    const response = await fetch(`https://vision.googleapis.com/v1/images:annotate?key=${API_KEY}`, {
        method: 'POST',
        body: JSON.stringify({
            requests: [{
                image: { content: imageBase64 },
                features: [
                    { type: 'LABEL_DETECTION' },
                    { type: 'OBJECT_LOCALIZATION' },
                    { type: 'SAFE_SEARCH_DETECTION' }
                ]
            }]
        })
    });
    return response.json();
}
```

### 5. **Gemini Pro API** ⭐ **HIGHLY RECOMMENDED** 
**Purpose**: Natural language processing for sighting reports  
**Setup**:
```bash
gcloud services enable aiplatform.googleapis.com
```
**Features**:
- **Smart sighting summaries**: "3 orcas seen feeding near Lime Kiln Point"
- **Behavior classification**: Extract behavior from free-text descriptions
- **Report validation**: Flag suspicious or duplicate reports
- **Predictive insights**: "Based on conditions, orcas likely foraging"

**Code Integration**:
```javascript
// Process natural language sighting reports
async function processSightingDescription(userText) {
    const prompt = `Analyze this orca sighting report and extract: 
    - Number of orcas
    - Behavior (foraging/traveling/socializing/resting)
    - Location clues
    - Confidence level
    
    Report: "${userText}"
    
    Return JSON format.`;
    
    // Call Gemini API
    const response = await callGeminiAPI(prompt);
    return response;
}
```

### 6. **AutoML** 
**Purpose**: Custom orca behavior prediction models  
**Setup**:
```bash
gcloud services enable automl.googleapis.com
```
**Features**:
- **Behavior prediction**: Train on historical sighting data
- **Environmental correlation**: Weather/tide impact on orca presence
- **Optimal viewing times**: Predict best whale watching windows

### 7. **Speech-to-Text**
**Purpose**: Voice sighting reports from boats  
**Setup**:
```bash
gcloud services enable speech.googleapis.com
```
**Features**:
- **Field reporting**: "I see 5 orcas heading north near Turn Point"
- **Hands-free operation**: Important for boat-based reporting
- **Multiple languages**: Support international whale watchers

### 8. **Translation API**
**Purpose**: Multi-language support for international users  
**Setup**:
```bash
gcloud services enable translate.googleapis.com
```
**Features**:
- **App localization**: Support Japanese, German whale watchers
- **Report translation**: Understand sightings in any language

## 🔧 Setup Instructions

### 1. Enable APIs in Google Cloud Console

```bash
# Set your project
gcloud config set project YOUR_PROJECT_ID

# Enable all essential APIs
gcloud services enable \
    maps-backend.googleapis.com \
    places-backend.googleapis.com \
    geocoding-backend.googleapis.com \
    vision.googleapis.com \
    aiplatform.googleapis.com \
    speech.googleapis.com \
    translate.googleapis.com
```

### 2. Create API Keys

**For client-side APIs (Maps, Places, Geocoding)**:
```bash
gcloud alpha services api-keys create \
    --display-name="Orca Tracker Web App" \
    --api-target=service=maps-backend.googleapis.com \
    --api-target=service=places-backend.googleapis.com \
    --api-target=service=geocoding-backend.googleapis.com \
    --allowed-referrers="https://orca-904de.web.app/*"
```

**For server-side APIs (Vision, Gemini, Speech)**:
```bash
gcloud iam service-accounts create orca-tracker-ai \
    --display-name="Orca Tracker AI Services"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:orca-tracker-ai@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

gcloud iam service-accounts keys create orca-tracker-key.json \
    --iam-account=orca-tracker-ai@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

### 3. Update App Configuration

Replace in `index.html`:
```html
<script async defer src="https://maps.googleapis.com/maps/api/js?key=YOUR_ACTUAL_MAPS_API_KEY&libraries=visualization,geometry&callback=initMap"></script>
```

## 💰 Cost Estimates (Monthly)

**Basic Usage (100 daily users)**:
- Maps API: ~$50/month
- Places API: ~$20/month  
- Vision AI: ~$30/month
- Gemini Pro: ~$40/month
- **Total**: ~$140/month

**High Usage (1000 daily users)**:
- Maps API: ~$200/month
- Places API: ~$100/month
- Vision AI: ~$150/month  
- Gemini Pro: ~$200/month
- **Total**: ~$650/month

## 🚀 Implementation Priority

### Phase 1: Core Maps (Week 1)
1. ✅ **Maps JavaScript API** - Essential
2. ✅ **Places API** - Location search
3. ✅ **Geocoding API** - Address conversion

### Phase 2: AI Intelligence (Week 2-3) 
4. 🤖 **Vision AI** - Photo analysis
5. 🤖 **Gemini Pro** - Natural language processing

### Phase 3: Advanced Features (Week 4+)
6. 🎯 **AutoML** - Custom prediction models
7. 🎤 **Speech-to-Text** - Voice reporting
8. 🌍 **Translation** - Multi-language support

## 🔐 Security Best Practices

### API Key Restrictions
- **Maps API**: Restrict to your domain only
- **Places API**: HTTP referrer restrictions
- **AI APIs**: Use service account with minimal permissions

### Rate Limiting
```javascript
// Implement client-side rate limiting
const apiCallTracker = {
    maps: { calls: 0, resetTime: Date.now() + 3600000 },
    vision: { calls: 0, resetTime: Date.now() + 3600000 }
};
```

### Environment Variables
```bash
# In your deployment environment
export GOOGLE_MAPS_API_KEY="your_maps_key"
export GOOGLE_CLOUD_PROJECT_ID="your_project_id" 
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"
```

## 📊 Monitoring & Analytics

Enable these for production monitoring:
```bash
gcloud services enable \
    monitoring.googleapis.com \
    logging.googleapis.com \
    cloudtrace.googleapis.com
```

## 🎯 Expected Benefits

**User Experience**:
- 📱 **Better mobile maps** with satellite imagery
- 🤖 **Intelligent photo analysis** for species confirmation  
- 💬 **Natural language reporting** - just describe what you see
- 🎯 **Smarter predictions** based on AI analysis

**Scientific Value**:
- 📈 **Higher data quality** through AI validation
- 🧠 **Pattern discovery** in orca behavior
- 🌍 **Global accessibility** through translation
- 📊 **Automated insights** from large datasets

**Conservation Impact**:
- ⚡ **Faster threat detection** through real-time AI analysis
- 🎯 **Targeted protection** based on AI-predicted critical areas
- 📱 **Broader participation** through easier reporting tools 