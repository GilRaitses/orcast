#!/usr/bin/env python3
"""
ORCAST Complete System Deployment
Deploy SINDy + HMC + Firestore integration for production

Run this script to:
1. Load discovered SINDy equations
2. Generate spatial forecasts with HMC uncertainty
3. Store predictions in Firestore
4. Serve live predictions via API
"""

import os
import sys
import json
from datetime import datetime, timedelta
import numpy as np
from orcast_complete_sindy_hmc_firestore import ORCASTCompletePredictionSystem

def deploy_orcast_system():
    """
    Deploy the complete ORCAST system for production use
    """
    
    print("🚀 Deploying ORCAST Complete System")
    print("=" * 60)
    
    # Check for Firebase credentials
    credentials_path = "client_secret_126424997157-9qnuuaoos5g92t3cuoq6b6dtlsatjpip.apps.googleusercontent.com.json"
    
    if not os.path.exists(credentials_path):
        print("⚠️ Firebase credentials not found. Running without Firestore...")
        credentials_path = None
    else:
        print("🔥 Firebase credentials found")
    
    # Initialize complete system
    print("\n1️⃣ Initializing ORCAST System...")
    system = ORCASTCompletePredictionSystem(credentials_path)
    
    # Load SINDy equations
    print("\n2️⃣ Loading SINDy Discovered Equations...")
    system.sindy_service.load_discovered_equations()
    
    print("   ✅ Loaded equations:")
    for behavior, eq_data in system.sindy_service.discovered_equations.items():
        print(f"      • {behavior}: {len(eq_data['key_factors'])} key factors")
    
    # Define forecast region (Salish Sea / San Juan Islands)
    forecast_region = {
        'lat_range': (48.4, 48.8),  # San Juan Islands area
        'lng_range': (-123.3, -122.8),
        'name': 'Salish Sea Orca Habitat'
    }
    
    # Set up environmental baseline
    base_environment = {
        'depth': 50.0,
        'temperature': 12.5,  # Summer temperature
        'tidal_flow': 0.2,
        'prey_density': 0.6,  # Good salmon runs
        'noise_level': 95.0,
        'visibility': 18.0,
        'current_speed': 0.4,
        'salinity': 30.2,
        'pod_size': 8,  # Typical pod size
        'day_of_year': datetime.now().timetuple().tm_yday
    }
    
    print(f"\n3️⃣ Generating Spatial Forecast for {forecast_region['name']}...")
    print(f"   Region: {forecast_region['lat_range']} × {forecast_region['lng_range']}")
    
    # Generate spatial forecast with SINDy + HMC
    spatial_forecast = system.generate_spatial_forecast_grid(
        lat_range=forecast_region['lat_range'],
        lng_range=forecast_region['lng_range'],
        base_environment=base_environment,
        grid_resolution=15,  # 15x15 grid for production
        time_hours=24  # 24-hour forecast
    )
    
    print(f"   ✅ Generated {len(spatial_forecast)} forecast points")
    
    # Store in Firestore if available
    if system.db:
        print("\n4️⃣ Storing Forecast in Firestore...")
        success = system.store_forecast_in_firestore(spatial_forecast)
        
        if success:
            print("   ✅ Forecast stored in Firestore")
            print("   📊 Available collections:")
            print("      • orca_spatial_forecasts: Grid predictions")
            print("      • forecast_metadata: Summary data")
        else:
            print("   ❌ Failed to store forecast")
    else:
        print("\n4️⃣ Skipping Firestore storage (no credentials)")
    
    # Test live prediction
    print("\n5️⃣ Testing Live Prediction API...")
    test_locations = [
        {'name': 'San Juan Island', 'lat': 48.5156, 'lng': -123.0123},
        {'name': 'Orcas Island', 'lat': 48.6020, 'lng': -122.9481},
        {'name': 'Lopez Island', 'lat': 48.4729, 'lng': -122.8873}
    ]
    
    for location in test_locations:
        prediction = system.get_live_prediction(
            latitude=location['lat'],
            longitude=location['lng'],
            additional_env_data=base_environment
        )
        
        print(f"\n   📍 {location['name']} ({location['lat']:.3f}, {location['lng']:.3f}):")
        for behavior, pred in prediction.items():
            mean_prob = pred['hmc_mean_probability']
            uncertainty = pred['confidence_band_width']
            print(f"      {behavior}: {mean_prob:.3f} ± {uncertainty:.3f}")
    
    # Generate API endpoint data structure
    print("\n6️⃣ Preparing API Response Format...")
    
    api_response = {
        'forecast_metadata': {
            'generated_at': datetime.utcnow().isoformat(),
            'region': forecast_region['name'],
            'grid_points': len(spatial_forecast),
            'method': 'sindy_hmc_integrated',
            'version': '1.0'
        },
        'spatial_grid': [
            {
                'lat': point['latitude'],
                'lng': point['longitude'],
                'feeding': {
                    'probability': point['spatial_averages']['feeding_probability'],
                    'uncertainty_lower': point['spatial_averages']['feeding_uncertainty_lower'],
                    'uncertainty_upper': point['spatial_averages']['feeding_uncertainty_upper']
                },
                'socializing': {
                    'probability': point['spatial_averages']['socializing_probability']
                },
                'traveling': {
                    'probability': point['spatial_averages']['traveling_probability']
                }
            }
            for point in spatial_forecast[:50]  # First 50 points for API
        ],
        'sindy_equations': {
            behavior: {
                'key_factors': eq_data['key_factors'],
                'complexity': len(eq_data['key_factors'])
            }
            for behavior, eq_data in system.sindy_service.discovered_equations.items()
        }
    }
    
    # Save API response
    with open('orcast_api_response.json', 'w') as f:
        json.dump(api_response, f, indent=2)
    
    print("   ✅ API response saved to 'orcast_api_response.json'")
    
    # Generate deployment summary
    print("\n" + "="*60)
    print("🎯 ORCAST DEPLOYMENT SUMMARY")
    print("="*60)
    print(f"✅ SINDy Equations: {len(system.sindy_service.discovered_equations)} behaviors")
    print(f"✅ HMC Uncertainty: Bayesian confidence intervals")
    print(f"✅ Spatial Forecast: {len(spatial_forecast)} grid points")
    print(f"✅ Firestore Integration: {'Ready' if system.db else 'Credentials needed'}")
    print(f"✅ API Response: 'orcast_api_response.json'")
    
    print("\n🌊 SYSTEM CAPABILITIES:")
    print("   • Automatic equation discovery from orca behavior data")
    print("   • Real-time predictions with uncertainty quantification")
    print("   • Spatial forecasting for marine protected area planning")
    print("   • Live API endpoints for web applications")
    print("   • Scientific interpretability and biological insights")
    
    print("\n📡 NEXT STEPS:")
    print("   1. Deploy API server: python -m uvicorn app:app --host 0.0.0.0 --port 8000")
    print("   2. Update frontend to use orcast_api_response.json")
    print("   3. Schedule hourly forecast updates")
    print("   4. Monitor prediction accuracy and retrain SINDy equations")
    
    return system, spatial_forecast, api_response

def create_deployment_api():
    """
    Create FastAPI deployment for the ORCAST system
    """
    
    api_code = '''
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
from datetime import datetime
from orcast_complete_sindy_hmc_firestore import ORCASTCompletePredictionSystem

app = FastAPI(title="ORCAST API", description="Orca Behavioral Prediction System")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize system
orcast_system = ORCASTCompletePredictionSystem("client_secret_126424997157-9qnuuaoos5g92t3cuoq6b6dtlsatjpip.apps.googleusercontent.com.json")
orcast_system.sindy_service.load_discovered_equations()

@app.get("/")
async def root():
    return {"message": "ORCAST Orca Behavioral Prediction API", "version": "1.0"}

@app.get("/predict/{lat}/{lng}")
async def get_prediction(lat: float, lng: float):
    """Get live orca behavior prediction for specific coordinates"""
    try:
        prediction = orcast_system.get_live_prediction(lat, lng)
        return {
            "location": {"latitude": lat, "longitude": lng},
            "predictions": prediction,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/spatial_forecast")
async def get_spatial_forecast():
    """Get complete spatial forecast grid"""
    try:
        with open('orcast_api_response.json', 'r') as f:
            forecast = json.load(f)
        return forecast
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Forecast not available")

@app.get("/equations")
async def get_sindy_equations():
    """Get discovered SINDy equations"""
    return {
        "equations": orcast_system.sindy_service.discovered_equations,
        "method": "sindy_automatic_discovery"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''
    
    with open('orcast_api.py', 'w') as f:
        f.write(api_code)
    
    print("📡 API server created: 'orcast_api.py'")

if __name__ == "__main__":
    # Deploy the complete system
    system, forecast, api_data = deploy_orcast_system()
    
    # Create API server
    create_deployment_api()
    
    print("\n🎉 ORCAST Complete System deployed successfully!")
    print("🌊 Ready for orca behavioral prediction and conservation planning!") 