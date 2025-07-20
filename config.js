// OrCast Configuration
window.ORCA_CONFIG = {
    apiKeys: {
        GOOGLE_MAPS: 'AIzaSyD9aM6oj1wpVG-VungMtIpyNWeHp3Q7XjU',
        OPENWEATHER: 'cdc69fe11f584fdb9957da45e7a98af4',
        GOOGLE_TRANSLATE: 'YOUR_GOOGLE_TRANSLATE_API_KEY_HERE',
        GOOGLE_PLACES: 'YOUR_GOOGLE_PLACES_API_KEY_HERE',
        GEMINI: 'AIzaSyAwvuL88RoXMjvUP5lJCFDS2mwLrwo6CVs'
    },
    
    // Firebase Configuration
    firebase: {
        apiKey: "AIzaSyATLG7Bg6i0D1rYy3XS5GRyCkBtnghztIY",
        authDomain: "orca-904de.firebaseapp.com",
        databaseURL: "https://orca-904de-default-rtdb.firebaseio.com",
        projectId: "orca-904de",
        storageBucket: "orca-904de.firebasestorage.app",
        messagingSenderId: "293403666260",
        appId: "1:293403666260:web:05fe93499cc62adcf4cac1",
        measurementId: "G-ZBG8JHYJL2"
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
    },
    
    // Backend API Configuration (Google Cloud Run)
    backend: {
        baseUrl: 'https://orcast-production-backend-2cvqukvhga-uw.a.run.app',
        endpoints: {
            health: '/health',
            forecast: '/forecast/current',
            quickForecast: '/forecast/quick',
            mlPredict: '/api/ml/predict',
            status: '/api/status',
            realTimeEvents: '/api/real-time/events'
        }
    },
    
    // Gemma 3 Cloud Run GPU Service (for Hackathon)
    gemmaService: {
        baseUrl: 'https://orcast-gemma3-gpu-RANDOM.run.app', // Will be updated after deployment
        healthEndpoint: '/health',
        generateEndpoint: '/generate',
        constraintsEndpoint: '/extract-constraints',
        useGemmaInstead: true // Set to true for hackathon submission
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