#!/usr/bin/env python3
"""
ORCAST Behavioral ML Service - Production Ready
Uses pre-trained models for real-time orca behavioral classification
"""

import os
import json
import logging
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="ORCAST Behavioral ML Service",
    description="Real-time orca behavioral classification using trained models",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === DATA MODELS ===

class EnvironmentalFeatures(BaseModel):
    """Environmental features for prediction"""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in degrees")
    pod_size: int = Field(..., ge=1, le=50, description="Number of orcas in pod")
    water_depth: float = Field(..., ge=0, le=1000, description="Water depth in meters")
    tidal_flow: float = Field(..., ge=-3, le=3, description="Tidal flow velocity in m/s")
    temperature: float = Field(..., ge=0, le=25, description="Water temperature in Celsius")
    salinity: float = Field(..., ge=20, le=40, description="Salinity in PSU")
    visibility: float = Field(..., ge=0, le=100, description="Visibility in meters")
    current_speed: float = Field(..., ge=0, le=5, description="Current speed in m/s")
    noise_level: float = Field(..., ge=80, le=180, description="Noise level in dB")
    prey_density: float = Field(..., ge=0, le=1, description="Prey density index 0-1")
    hour_of_day: int = Field(..., ge=0, le=23, description="Hour of day (0-23)")
    day_of_year: int = Field(..., ge=1, le=366, description="Day of year (1-366)")

class BehaviorPrediction(BaseModel):
    """Behavioral prediction response"""
    predicted_behavior: str
    confidence: float
    probabilities: Dict[str, float]
    feeding_success_probability: Optional[float] = None
    model_version: str
    prediction_timestamp: str

class BatchPredictionRequest(BaseModel):
    """Batch prediction request"""
    features: List[EnvironmentalFeatures]
    return_explanations: bool = False

class BatchPredictionResponse(BaseModel):
    """Batch prediction response"""
    predictions: List[BehaviorPrediction]
    processing_time_ms: float
    total_predictions: int

# === ML MODEL MANAGER ===

class OrcastMLModel:
    """Pre-trained ORCAST behavioral classification model"""
    
    def __init__(self, models_dir: str = "models"):
        self.models_dir = models_dir
        self.behavior_model = None
        self.success_model = None
        self.scaler = None
        self.encoder = None
        self.model_metadata = None
        
        # Load models on initialization
        self.load_models()
    
    def load_models(self):
        """Load pre-trained models from disk"""
        try:
            logger.info(f"🤖 Loading models from {self.models_dir}...")
            
            # Load behavior classifier
            behavior_model_path = os.path.join(self.models_dir, "behavior_model.joblib")
            self.behavior_model = joblib.load(behavior_model_path)
            logger.info(f"✅ Loaded behavior model: {type(self.behavior_model).__name__}")
            
            # Load feature scaler
            scaler_path = os.path.join(self.models_dir, "behavior_scaler.joblib")
            self.scaler = joblib.load(scaler_path)
            logger.info(f"✅ Loaded feature scaler: {type(self.scaler).__name__}")
            
            # Load label encoder
            encoder_path = os.path.join(self.models_dir, "behavior_encoder.joblib")
            self.encoder = joblib.load(encoder_path)
            logger.info(f"✅ Loaded label encoder with classes: {list(self.encoder.classes_)}")
            
            # Load success model if available
            success_model_path = os.path.join(self.models_dir, "success_model.joblib")
            if os.path.exists(success_model_path):
                self.success_model = joblib.load(success_model_path)
                logger.info(f"✅ Loaded feeding success model: {type(self.success_model).__name__}")
            
            # Load metadata
            metadata_path = os.path.join(self.models_dir, "model_metadata.json")
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    self.model_metadata = json.load(f)
                logger.info(f"✅ Loaded model metadata: {self.model_metadata['timestamp']}")
            
            logger.info("🎉 All models loaded successfully!")
            
        except Exception as e:
            logger.error(f"❌ Failed to load models: {e}")
            raise RuntimeError(f"Model loading failed: {e}")
    
    def extract_features(self, env_features: EnvironmentalFeatures) -> np.ndarray:
        """Extract 13D feature vector from environmental data"""
        feature_vector = np.array([
            env_features.latitude,
            env_features.longitude,
            env_features.pod_size,
            env_features.water_depth,
            env_features.tidal_flow,
            env_features.temperature,
            env_features.salinity,
            env_features.visibility,
            env_features.current_speed,
            env_features.noise_level,
            env_features.prey_density,
            env_features.hour_of_day,
            env_features.day_of_year
        ]).reshape(1, -1)
        
        return feature_vector
    
    def predict_behavior(self, env_features: EnvironmentalFeatures) -> BehaviorPrediction:
        """Predict orca behavior from environmental features"""
        
        if self.behavior_model is None:
            raise RuntimeError("Behavior model not loaded")
        
        # Extract and scale features
        features = self.extract_features(env_features)
        features_scaled = self.scaler.transform(features)
        
        # Predict behavior
        behavior_pred = self.behavior_model.predict(features_scaled)[0]
        behavior_proba = self.behavior_model.predict_proba(features_scaled)[0]
        
        # Decode prediction
        predicted_behavior = self.encoder.inverse_transform([behavior_pred])[0]
        confidence = max(behavior_proba)
        
        # Create probability dictionary
        probabilities = {
            behavior: float(prob) 
            for behavior, prob in zip(self.encoder.classes_, behavior_proba)
        }
        
        # Predict feeding success if behavior is feeding
        feeding_success_prob = None
        if predicted_behavior == 'feeding' and self.success_model is not None:
            try:
                success_pred = self.success_model.predict_proba(features_scaled)[0]
                feeding_success_prob = float(success_pred[1])  # Probability of success
            except Exception as e:
                logger.warning(f"Failed to predict feeding success: {e}")
        
        # Create response
        prediction = BehaviorPrediction(
            predicted_behavior=predicted_behavior,
            confidence=float(confidence),
            probabilities=probabilities,
            feeding_success_probability=feeding_success_prob,
            model_version=self.model_metadata.get('timestamp', 'unknown') if self.model_metadata else 'unknown',
            prediction_timestamp=datetime.now().isoformat()
        )
        
        return prediction

# Initialize model manager
ml_model = OrcastMLModel()

# === API ENDPOINTS ===

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "ORCAST Behavioral ML Service",
        "version": "2.0.0",
        "status": "healthy",
        "models_loaded": ml_model.behavior_model is not None,
        "available_classes": list(ml_model.encoder.classes_) if ml_model.encoder else [],
        "features_expected": 13,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "models": {
            "behavior_model": ml_model.behavior_model is not None,
            "success_model": ml_model.success_model is not None,
            "scaler": ml_model.scaler is not None,
            "encoder": ml_model.encoder is not None
        },
        "classes": list(ml_model.encoder.classes_) if ml_model.encoder else [],
        "metadata": ml_model.model_metadata,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/predict", response_model=BehaviorPrediction)
async def predict_behavior(features: EnvironmentalFeatures):
    """Predict orca behavior from environmental features"""
    try:
        start_time = datetime.now()
        
        # Make prediction
        prediction = ml_model.predict_behavior(features)
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        logger.info(f"🔮 Prediction: {prediction.predicted_behavior} "
                   f"(confidence: {prediction.confidence:.3f}, "
                   f"time: {processing_time:.1f}ms)")
        
        return prediction
        
    except Exception as e:
        logger.error(f"❌ Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")

@app.post("/predict/batch", response_model=BatchPredictionResponse)
async def predict_batch(request: BatchPredictionRequest):
    """Batch prediction for multiple feature sets"""
    try:
        start_time = datetime.now()
        
        predictions = []
        for features in request.features:
            prediction = ml_model.predict_behavior(features)
            predictions.append(prediction)
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        response = BatchPredictionResponse(
            predictions=predictions,
            processing_time_ms=processing_time,
            total_predictions=len(predictions)
        )
        
        logger.info(f"📊 Batch prediction: {len(predictions)} predictions "
                   f"in {processing_time:.1f}ms")
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Batch prediction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {e}")

@app.get("/models/info")
async def model_info():
    """Get model information and statistics"""
    return {
        "behavior_classes": list(ml_model.encoder.classes_) if ml_model.encoder else [],
        "feature_names": [
            "latitude", "longitude", "pod_size", "water_depth", "tidal_flow",
            "temperature", "salinity", "visibility", "current_speed", 
            "noise_level", "prey_density", "hour_of_day", "day_of_year"
        ],
        "model_type": type(ml_model.behavior_model).__name__ if ml_model.behavior_model else None,
        "success_model_available": ml_model.success_model is not None,
        "metadata": ml_model.model_metadata,
        "feature_dimensions": 13
    }

@app.post("/predict/simple")
async def predict_simple(data: Dict[str, Any]):
    """Simplified prediction endpoint accepting raw dictionary"""
    try:
        # Convert dict to EnvironmentalFeatures
        features = EnvironmentalFeatures(**data)
        
        # Make prediction
        prediction = ml_model.predict_behavior(features)
        
        # Return simplified response
        return {
            "behavior": prediction.predicted_behavior,
            "confidence": prediction.confidence,
            "probabilities": prediction.probabilities,
            "feeding_success": prediction.feeding_success_probability,
            "timestamp": prediction.prediction_timestamp
        }
        
    except Exception as e:
        logger.error(f"❌ Simple prediction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")

# === EXAMPLE DATA ===

@app.get("/example")
async def get_example_data():
    """Get example input data for testing"""
    return {
        "example_input": {
            "latitude": 48.5,
            "longitude": -123.0,
            "pod_size": 3,
            "water_depth": 50.0,
            "tidal_flow": 0.2,
            "temperature": 15.5,
            "salinity": 30.1,
            "visibility": 20.0,
            "current_speed": 0.5,
            "noise_level": 120.0,
            "prey_density": 0.6,
            "hour_of_day": 14,
            "day_of_year": 200
        },
        "description": "Example environmental features for San Juan Islands orca habitat",
        "usage": "POST this data to /predict endpoint for behavioral classification"
    }

# === MAIN ===

if __name__ == "__main__":
    logger.info("🚀 Starting ORCAST Behavioral ML Service...")
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=int(os.getenv("PORT", "8080")),
        log_level="info"
    ) 