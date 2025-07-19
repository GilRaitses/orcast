// OrCast Configuration
window.ORCA_CONFIG = {
    apiKeys: {
        GOOGLE_MAPS: 'AIzaSyAwvuL88RoXMjvUP5lJCFDS2mwLrwo6CVs',
        OPENWEATHER: 'cdc69fe11f584fdb9957da45e7a98af4',
        GOOGLE_TRANSLATE: 'YOUR_GOOGLE_TRANSLATE_API_KEY_HERE',
        GOOGLE_PLACES: 'YOUR_GOOGLE_PLACES_API_KEY_HERE',
        GEMINI: 'AIzaSyAwvuL88RoXMjvUP5lJCFDS2mwLrwo6CVs'
    },
    
    // Firebase Configuration
    firebase: {
        apiKey: "your-firebase-api-key",
        authDomain: "orca-904de.firebaseapp.com",
        databaseURL: "https://orca-904de-default-rtdb.firebaseio.com",
        projectId: "orca-904de",
        storageBucket: "orca-904de.appspot.com",
        messagingSenderId: "your-sender-id",
        appId: "your-app-id"
    },
    
    // San Juan Islands Configuration
    map: {
        center: { lat: 48.5465, lng: -123.0307 },
        zoom: 11,
        bounds: {
            north: 48.8,
            south: 48.3,
            east: -122.7,
            west: -123.4
        }
    },
    
    // Google Gemini API Configuration (for Agentic Planning)
    gemini: {
        apiKey: 'AIzaSyAwvuL88RoXMjvUP5lJCFDS2mwLrwo6CVs',
        projectId: 'orca-466204',
        model: 'gemini-1.5-flash',
        serviceAccountEmail: 'orca-237@orca-466204.iam.gserviceaccount.com'
    }
};

// Load Google Maps API dynamically
function loadGoogleMapsAPI() {
    if (window.google && window.google.maps) {
        return Promise.resolve();
    }
    
    return new Promise((resolve, reject) => {
        const apiKey = window.ORCA_CONFIG.apiKeys.GOOGLE_MAPS;
        if (!apiKey || apiKey === 'YOUR_GOOGLE_MAPS_API_KEY_HERE') {
            reject(new Error('Google Maps API key not configured'));
            return;
        }
        
        const script = document.createElement('script');
        script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=visualization&callback=initMap`;
        script.async = true;
        script.defer = true;
        script.onload = resolve;
        script.onerror = reject;
        document.head.appendChild(script);
    });
} 