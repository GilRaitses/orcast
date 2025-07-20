#!/usr/bin/env python3
"""
ORCAST Firestore ML Service - Integrated with Firebase
Generates spatial/temporal behavioral forecasts and stores in Firestore for map UI
"""

import os
import json
import logging
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import asyncio
import time

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Firebase imports
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud import firestore as firestore_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="ORCAST Firestore ML Service",
    description="Integrated orca behavioral forecasting with Firebase storage",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === FIREBASE INITIALIZATION ===

def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        # Check if already initialized
        firebase_admin.get_app()
        logger.info("✅ Firebase already initialized")
    except ValueError:
        # Initialize with default credentials
        try:
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, {
                'projectId': 'orca-466204',
            })
            logger.info("✅ Firebase initialized with Application Default Credentials")
        except Exception as e:
            logger.warning(f"⚠️ Firebase initialization failed: {e}")
            logger.info("Continuing without Firebase (development mode)")
            return None
    
    try:
        db = firestore.client()
        logger.info("✅ Firestore client connected")
        return db
    except Exception as e:
        logger.error(f"❌ Firestore connection failed: {e}")
        return None

# Initialize Firebase
db = initialize_firebase()

# === DATA MODELS ===

class SpatialForecastRequest(BaseModel):
    """Request for spatial forecast generation"""
    region: str = Field(default="san_juan_islands", description="Forecast region")
    grid_resolution: float = Field(default=0.01, description="Grid resolution in degrees")
    forecast_hours: int = Field(default=24, description="Hours to forecast ahead")
    time_step_hours: int = Field(default=6, description="Time step between forecasts")

class TemporalForecastRequest(BaseModel):
    """Request for temporal forecast at specific location"""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    forecast_days: int = Field(default=7, description="Days to forecast ahead")
    time_step_hours: int = Field(default=1, description="Time step between forecasts")

class ForecastResponse(BaseModel):
    """Forecast response"""
    region: str
    timestamp: str
    grid_data: List[Dict]
    metadata: Dict

# === ORCAST ML MODEL WITH FIRESTORE ===

class ORCASTFirestoreML:
    """ML Model with Firestore integration and spatial forecasting"""
    
    def __init__(self, models_dir: str = "models"):
        self.models_dir = models_dir
        self.behavior_model = None
        self.success_model = None
        self.scaler = None
        self.encoder = None
        self.model_metadata = None
        self.db = db
        
        # San Juan Islands region bounds
        self.region_bounds = {
            'san_juan_islands': {
                'lat_min': 48.4, 'lat_max': 48.8,
                'lng_min': -123.3, 'lng_max': -122.8
            }
        }
        
        # Load models
        self.load_models()
    
    def load_models(self):
        """Load pre-trained models"""
        try:
            logger.info(f"🤖 Loading models from {self.models_dir}...")
            
            self.behavior_model = joblib.load(os.path.join(self.models_dir, "behavior_model.joblib"))
            self.scaler = joblib.load(os.path.join(self.models_dir, "behavior_scaler.joblib"))
            self.encoder = joblib.load(os.path.join(self.models_dir, "behavior_encoder.joblib"))
            
            if os.path.exists(os.path.join(self.models_dir, "success_model.joblib")):
                self.success_model = joblib.load(os.path.join(self.models_dir, "success_model.joblib"))
            
            with open(os.path.join(self.models_dir, "model_metadata.json"), 'r') as f:
                self.model_metadata = json.load(f)
            
            logger.info("✅ All models loaded successfully!")
            
        except Exception as e:
            logger.error(f"❌ Failed to load models: {e}")
            raise RuntimeError(f"Model loading failed: {e}")
    
    def get_environmental_data(self, lat: float, lng: float, timestamp: datetime) -> Dict[str, float]:
        """Get environmental data for location and time"""
        # This would normally fetch real environmental data
        # For now, simulate based on location and time patterns
        
        hour = timestamp.hour
        day_of_year = timestamp.timetuple().tm_yday
        
        # Simulate environmental conditions based on location and time
        base_depth = 50 + (lat - 48.5) * 100 + abs(lng + 123) * 80
        water_depth = max(10, min(200, base_depth + np.random.normal(0, 5)))
        
        # Tidal patterns (M2 tide ~12.42 hours)
        tidal_flow = 0.5 * np.sin(2 * np.pi * hour / 12.42)
        
        # Seasonal temperature
        temp_seasonal = 12 + 4 * np.sin(2 * np.pi * (day_of_year - 80) / 365)
        temperature = temp_seasonal + np.random.normal(0, 0.5)
        
        # Prey density - higher at dawn/dusk and in summer
        prey_base = 0.5 + 0.3 * np.sin(2 * np.pi * (day_of_year - 150) / 365)
        time_factor = 0.3 * (np.sin(2 * np.pi * hour / 24) + 0.5)
        prey_density = max(0.1, min(1.0, prey_base + time_factor))
        
        # Noise - higher during day, lower at night
        noise_level = 115 + 10 * np.sin(2 * np.pi * hour / 24) + np.random.normal(0, 3)
        
        return {
            'water_depth': water_depth,
            'tidal_flow': tidal_flow,
            'temperature': temperature,
            'salinity': 30.0 + np.random.normal(0, 0.5),
            'visibility': max(5, 20 + np.random.normal(0, 3)),
            'current_speed': max(0, 0.5 + np.random.normal(0, 0.2)),
            'noise_level': max(80, min(150, noise_level)),
            'prey_density': prey_density
        }
    
    def predict_behavior_at_location(self, lat: float, lng: float, timestamp: datetime, 
                                   pod_size: int = 3) -> Dict[str, Any]:
        """Predict behavior at specific location and time"""
        
        # Get environmental data
        env_data = self.get_environmental_data(lat, lng, timestamp)
        
        # Create feature vector
        feature_vector = np.array([
            lat, lng, pod_size,
            env_data['water_depth'],
            env_data['tidal_flow'],
            env_data['temperature'],
            env_data['salinity'],
            env_data['visibility'],
            env_data['current_speed'],
            env_data['noise_level'],
            env_data['prey_density'],
            timestamp.hour,
            timestamp.timetuple().tm_yday
        ]).reshape(1, -1)
        
        # Scale features and predict
        features_scaled = self.scaler.transform(feature_vector)
        behavior_pred = self.behavior_model.predict(features_scaled)[0]
        behavior_proba = self.behavior_model.predict_proba(features_scaled)[0]
        
        # Decode prediction
        predicted_behavior = self.encoder.inverse_transform([behavior_pred])[0]
        probabilities = {
            behavior: float(prob) 
            for behavior, prob in zip(self.encoder.classes_, behavior_proba)
        }
        
        # Feeding success if applicable
        feeding_success_prob = None
        if predicted_behavior == 'feeding' and self.success_model is not None:
            try:
                success_pred = self.success_model.predict_proba(features_scaled)[0]
                feeding_success_prob = float(success_pred[1])
            except:
                pass
        
        return {
            'latitude': lat,
            'longitude': lng,
            'timestamp': timestamp.isoformat(),
            'predicted_behavior': predicted_behavior,
            'confidence': float(max(behavior_proba)),
            'probabilities': probabilities,
            'feeding_success_probability': feeding_success_prob,
            'environmental_data': env_data
        }
    
    def generate_spatial_forecast(self, region: str = "san_juan_islands", 
                                grid_resolution: float = 0.01,
                                forecast_hours: int = 24,
                                time_step_hours: int = 6) -> Dict[str, Any]:
        """Generate spatial forecast grid for map visualization"""
        
        logger.info(f"🗺️ Generating spatial forecast for {region}...")
        
        if region not in self.region_bounds:
            raise ValueError(f"Region {region} not supported")
        
        bounds = self.region_bounds[region]
        
        # Create grid points
        lats = np.arange(bounds['lat_min'], bounds['lat_max'], grid_resolution)
        lngs = np.arange(bounds['lng_min'], bounds['lng_max'], grid_resolution)
        
        # Time points
        base_time = datetime.now()
        time_points = [
            base_time + timedelta(hours=h) 
            for h in range(0, forecast_hours + 1, time_step_hours)
        ]
        
        grid_data = []
        total_points = len(lats) * len(lngs) * len(time_points)
        processed = 0
        
        for time_point in time_points:
            time_grid = []
            
            for lat in lats:
                for lng in lngs:
                    try:
                        prediction = self.predict_behavior_at_location(lat, lng, time_point)
                        
                        # Simplified grid point for map visualization
                        grid_point = {
                            'lat': lat,
                            'lng': lng,
                            'timestamp': time_point.isoformat(),
                            'feeding_prob': prediction['probabilities']['feeding'],
                            'socializing_prob': prediction['probabilities']['socializing'],
                            'traveling_prob': prediction['probabilities']['traveling'],
                            'predicted_behavior': prediction['predicted_behavior'],
                            'confidence': prediction['confidence']
                        }
                        
                        time_grid.append(grid_point)
                        processed += 1
                        
                        if processed % 100 == 0:
                            logger.info(f"📊 Processed {processed}/{total_points} grid points")
                    
                    except Exception as e:
                        logger.warning(f"Failed to predict at ({lat}, {lng}): {e}")
                        continue
            
            grid_data.append({
                'timestamp': time_point.isoformat(),
                'hour_offset': (time_point - base_time).total_seconds() / 3600,
                'grid_points': time_grid
            })
        
        forecast_data = {
            'region': region,
            'generated_at': base_time.isoformat(),
            'forecast_hours': forecast_hours,
            'time_step_hours': time_step_hours,
            'grid_resolution': grid_resolution,
            'grid_size': {
                'lats': len(lats),
                'lngs': len(lngs),
                'total_points': len(lats) * len(lngs)
            },
            'time_series': grid_data,
            'bounds': bounds
        }
        
        logger.info(f"✅ Generated {len(grid_data)} time slices with {len(lats)*len(lngs)} points each")
        
        return forecast_data
    
    def save_forecast_to_firestore(self, forecast_data: Dict[str, Any]) -> bool:
        """Save forecast data to Firestore"""
        
        if not self.db:
            logger.warning("⚠️ Firestore not available, skipping save")
            return False
        
        try:
            # Save main forecast document
            forecast_id = f"{forecast_data['region']}_{int(time.time())}"
            
            # Prepare metadata
            metadata = {
                'forecast_id': forecast_id,
                'region': forecast_data['region'],
                'generated_at': firestore.SERVER_TIMESTAMP,
                'forecast_hours': forecast_data['forecast_hours'],
                'grid_resolution': forecast_data['grid_resolution'],
                'grid_size': forecast_data['grid_size'],
                'bounds': forecast_data['bounds'],
                'model_version': self.model_metadata.get('timestamp', 'unknown'),
                'status': 'active'
            }
            
            # Save metadata
            self.db.collection('forecasts').document(forecast_id).set(metadata)
            
            # Save time series data in subcollection
            for i, time_slice in enumerate(forecast_data['time_series']):
                time_doc_id = f"time_{i:03d}"
                self.db.collection('forecasts').document(forecast_id)\
                       .collection('time_series').document(time_doc_id).set({
                    'timestamp': time_slice['timestamp'],
                    'hour_offset': time_slice['hour_offset'],
                    'grid_points': time_slice['grid_points'][:1000]  # Limit for Firestore
                })
            
            # Save current active forecast reference
            self.db.collection('system').document('current_forecast').set({
                'forecast_id': forecast_id,
                'region': forecast_data['region'],
                'generated_at': firestore.SERVER_TIMESTAMP,
                'status': 'active'
            })
            
            logger.info(f"✅ Forecast saved to Firestore: {forecast_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save forecast to Firestore: {e}")
            return False
    
    def get_current_forecast(self) -> Optional[Dict[str, Any]]:
        """Get current active forecast from Firestore"""
        
        if not self.db:
            return None
        
        try:
            # Get current forecast reference
            current_ref = self.db.collection('system').document('current_forecast').get()
            
            if not current_ref.exists:
                return None
            
            current_data = current_ref.to_dict()
            forecast_id = current_data['forecast_id']
            
            # Get forecast metadata
            forecast_ref = self.db.collection('forecasts').document(forecast_id).get()
            
            if not forecast_ref.exists:
                return None
            
            forecast_metadata = forecast_ref.to_dict()
            
            # Get time series data
            time_series_ref = self.db.collection('forecasts').document(forecast_id)\
                                   .collection('time_series').stream()
            
            time_series = []
            for doc in time_series_ref:
                time_series.append(doc.to_dict())
            
            # Sort by hour_offset
            time_series.sort(key=lambda x: x['hour_offset'])
            
            return {
                'forecast_id': forecast_id,
                'metadata': forecast_metadata,
                'time_series': time_series
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get current forecast: {e}")
            return None

# Initialize ML model
orcast_ml = ORCASTFirestoreML()

# === API ENDPOINTS ===

@app.get("/")
async def root():
    """Service information"""
    return {
        "service": "ORCAST Firestore ML Service",
        "version": "3.0.0",
        "status": "healthy",
        "firebase_connected": db is not None,
        "models_loaded": orcast_ml.behavior_model is not None,
        "capabilities": [
            "behavioral_prediction",
            "spatial_forecasting", 
            "temporal_forecasting",
            "firestore_integration"
        ]
    }

@app.post("/forecast/spatial")
async def generate_spatial_forecast(
    request: SpatialForecastRequest,
    background_tasks: BackgroundTasks
):
    """Generate spatial forecast and save to Firestore"""
    
    def generate_and_save():
        try:
            # Generate forecast
            forecast_data = orcast_ml.generate_spatial_forecast(
                region=request.region,
                grid_resolution=request.grid_resolution,
                forecast_hours=request.forecast_hours,
                time_step_hours=request.time_step_hours
            )
            
            # Save to Firestore
            orcast_ml.save_forecast_to_firestore(forecast_data)
            
        except Exception as e:
            logger.error(f"❌ Background forecast generation failed: {e}")
    
    # Start background task
    background_tasks.add_task(generate_and_save)
    
    return {
        "status": "accepted",
        "message": "Spatial forecast generation started",
        "region": request.region,
        "estimated_completion": f"{request.forecast_hours * request.grid_resolution * 1000:.0f} seconds"
    }

@app.get("/forecast/current")
async def get_current_forecast():
    """Get current active forecast from Firestore"""
    
    forecast = orcast_ml.get_current_forecast()
    
    if not forecast:
        raise HTTPException(status_code=404, detail="No active forecast found")
    
    return forecast

@app.post("/forecast/quick")
async def generate_quick_forecast():
    """Generate a quick low-resolution forecast for immediate use"""
    
    try:
        # Quick forecast with lower resolution
        forecast_data = orcast_ml.generate_spatial_forecast(
            region="san_juan_islands",
            grid_resolution=0.02,  # Lower resolution for speed
            forecast_hours=12,     # Shorter time horizon
            time_step_hours=6      # Fewer time steps
        )
        
        # Save to Firestore
        orcast_ml.save_forecast_to_firestore(forecast_data)
        
        return {
            "status": "completed",
            "forecast_id": f"{forecast_data['region']}_{int(time.time())}",
            "grid_points": forecast_data['grid_size']['total_points'],
            "time_slices": len(forecast_data['time_series']),
            "message": "Quick forecast generated and saved to Firestore"
        }
        
    except Exception as e:
        logger.error(f"❌ Quick forecast failed: {e}")
        raise HTTPException(status_code=500, detail=f"Forecast generation failed: {e}")

@app.get("/forecast/status")
async def forecast_status():
    """Get forecast generation status"""
    
    current = orcast_ml.get_current_forecast()
    
    return {
        "firestore_connected": db is not None,
        "models_loaded": orcast_ml.behavior_model is not None,
        "current_forecast_available": current is not None,
        "current_forecast_id": current['forecast_id'] if current else None,
        "last_generated": current['metadata']['generated_at'] if current else None
    }

@app.post("/predict/store")
async def predict_and_store(data: Dict[str, Any]):
    """Make prediction and store in Firestore"""
    
    try:
        # Extract location and time
        lat = data['latitude']
        lng = data['longitude']
        timestamp = datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat()))
        pod_size = data.get('pod_size', 3)
        
        # Make prediction
        prediction = orcast_ml.predict_behavior_at_location(lat, lng, timestamp, pod_size)
        
        # Store in Firestore if available
        if db:
            prediction_id = f"pred_{int(time.time())}_{hash(f'{lat}{lng}')}"
            db.collection('predictions').document(prediction_id).set({
                **prediction,
                'created_at': firestore.SERVER_TIMESTAMP,
                'source': 'ml_service'
            })
            
            prediction['stored_in_firestore'] = True
            prediction['prediction_id'] = prediction_id
        else:
            prediction['stored_in_firestore'] = False
        
        return prediction
        
    except Exception as e:
        logger.error(f"❌ Predict and store failed: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")

if __name__ == "__main__":
    logger.info("🚀 Starting ORCAST Firestore ML Service...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8081")),  # Different port from standalone service
        log_level="info"
    ) 