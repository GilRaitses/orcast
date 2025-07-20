// ORCAST Configuration
// Global configuration object for the ORCAST orca behavioral analysis application

window.ORCA_CONFIG = {
    // Firebase configuration
    firebase: {
        apiKey: "AIzaSyD9aM6oj1wpVG-VungMtIpyNWeHp3Q7XjU",
        authDomain: "orca-tracking-904de.firebaseapp.com",
        projectId: "orca-tracking-904de",
        storageBucket: "orca-tracking-904de.appspot.com",
        messagingSenderId: "293403666260",
        appId: "1:293403666260:web:placeholder"
    },
    
    // API Keys
    apiKeys: {
        GOOGLE_MAPS: "AIzaSyD9aM6oj1wpVG-VungMtIpyNWeHp3Q7XjU"
    },
    
    // Map configuration
    map: {
        center: { lat: 48.5465, lng: -123.0307 },
        zoom: 12,
        bounds: {
            north: 48.8,
            south: 48.3,
            east: -122.7,
            west: -123.4
        }
    },
    
    // Temporal analysis configuration
    temporalConfig: {
        confidenceThreshold: 0.6,
        timeResolution: 'hours',
        forecastWindow: 72, // hours
        historicalWindow: 168 // hours (1 week)
    },
    
    // Agent configuration
    agentConfig: {
        enabled: true,
        autoUpdate: true,
        updateInterval: 30000, // 30 seconds
        maxResponses: 100
    },
    
    // Backend endpoints
    endpoints: {
        base: "https://orcast-behavioral-ml-293403666260.us-central1.run.app",
        prediction: "/predict",
        historical: "/historical",
        realtime: "/realtime",
        agent: "/agent"
    },
    
    // UI Configuration
    ui: {
        theme: 'dark',
        animations: true,
        autoHideLoading: 3000 // milliseconds
    },
    
    // Data sources
    dataSources: {
        orcaNetwork: "https://www.orcanetwork.org/",
        whaleResearch: "https://www.whaleresearch.com/",
        noaa: "https://www.fisheries.noaa.gov/"
    }
};

// Initialize configuration
console.log('ORCAST Configuration loaded:', window.ORCA_CONFIG); 