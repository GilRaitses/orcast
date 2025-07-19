# OrCast Map Setup Guide

## Setting up Google Maps API Key

### Step 1: Get Your Google Maps API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the following APIs:
   - Maps JavaScript API
   - Places API (for location search)
   - Geocoding API (for address conversion)

4. Go to "Credentials" and create a new API key
5. Restrict the API key to your domains:
   - `https://orcast.org`
   - `https://orca-904de.web.app`
   - `localhost:*` (for testing)

### Step 2: Configure Your API Key

1. Open `orca_probability_map.html`
2. Find this line:
   ```javascript
   const GOOGLE_MAPS_API_KEY = 'YOUR_API_KEY_HERE';
   ```
3. Replace `'YOUR_API_KEY_HERE'` with your actual API key

### Step 3: Deploy Updates

```bash
firebase deploy --only hosting
```

## Features Available

Once configured, your map will have:

- **Real-time Probability Heatmap**: Visual zones showing orca sighting likelihood
- **Interactive Controls**: Toggle different data layers on/off
- **Feeding Zone Markers**: Known feeding areas marked
- **User Sighting Reports**: Community-contributed sightings
- **Auto-refresh**: Updates every 30 seconds with new data
- **Mobile Responsive**: Works on all devices

## Security Notes

- Never commit your API key to version control
- Consider using environment variables for production
- Set up billing alerts in Google Cloud Console
- Monitor API usage regularly

## Troubleshooting

- If map doesn't load: Check browser console for API key errors
- If no data shows: Verify Firebase database is properly configured
- If heatmap is empty: Check that sample data generation is working

## Next Steps

1. Connect to real-time NOAA data feeds
2. Integrate with whale watching operator APIs
3. Add machine learning predictions
4. Implement user authentication for sighting reports 