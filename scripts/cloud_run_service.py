"""
OrCast Behavioral ML Service for Cloud Run
Simplified version that starts without BigQuery authentication issues
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="OrCast Behavioral ML Service", version="1.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for lazy loading
bq_client = None
ml_service = None

def get_bq_client():
    """Get or create BigQuery client"""
    global bq_client
    if bq_client is None:
        try:
            from google.cloud import bigquery
            bq_client = bigquery.Client()
            logger.info("BigQuery client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize BigQuery client: {e}")
            bq_client = None
    return bq_client

def get_ml_service():
    """Get or create ML service"""
    global ml_service
    if ml_service is None:
        try:
            # Import here to avoid startup issues
            from behavioral_ml_service import BehavioralMLService
            ml_service = BehavioralMLService()
            logger.info("ML service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ML service: {e}")
            ml_service = None
    return ml_service

# === PYDANTIC MODELS ===

class SightingData(BaseModel):
    """Orca sighting data"""
    sighting_id: str
    timestamp: datetime
    latitude: float
    longitude: float
    pod_size: int
    environmental_context: Dict = {}
    data_quality_score: float = 0.5

class PredictionRequest(BaseModel):
    """Prediction request"""
    sighting_data: SightingData
    include_explanation: bool = True

class PredictionResponse(BaseModel):
    """Prediction response"""
    behavior: str
    probability: float
    confidence: float
    feeding_strategy: Optional[str] = None
    success_probability: Optional[float] = None
    explanation: Optional[Dict] = None

# === ENDPOINTS ===

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "OrCast Behavioral ML Service",
        "version": "1.0",
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    health = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "bigquery": "unknown",
        "ml_service": "unknown"
    }
    
    # Check BigQuery connection
    client = get_bq_client()
    if client:
        health["bigquery"] = "connected"
    else:
        health["bigquery"] = "disconnected"
    
    # Check ML service
    service = get_ml_service()
    if service:
        health["ml_service"] = "loaded"
    else:
        health["ml_service"] = "not_loaded"
    
    return health

@app.post("/predict", response_model=PredictionResponse)
async def predict_behavior(request: PredictionRequest):
    """Predict orca behavior"""
    try:
        service = get_ml_service()
        if service is None:
            # Simple fallback prediction
            return PredictionResponse(
                behavior="foraging",
                probability=0.7,
                confidence=0.6,
                feeding_strategy="surface_feeding",
                success_probability=0.65,
                explanation={"note": "Fallback prediction - ML service not available"}
            )
        
        # Use full ML service if available
        result = service.predict_behavior(request.sighting_data.dict())
        
        return PredictionResponse(
            behavior=result.get("behavior", "unknown"),
            probability=result.get("probability", 0.5),
            confidence=result.get("confidence", 0.5),
            feeding_strategy=result.get("feeding_strategy"),
            success_probability=result.get("success_probability"),
            explanation=result.get("explanation")
        )
        
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/model/status")
async def model_status():
    """Get model status"""
    service = get_ml_service()
    if service:
        return {
            "status": "loaded",
            "model_type": "RandomForest + HMC",
            "features": ["location", "time", "environmental"],
            "last_updated": datetime.now().isoformat()
        }
    else:
        return {
            "status": "not_loaded",
            "error": "ML service not available"
        }

@app.post("/train")
async def train_model():
    """Train the model"""
    try:
        service = get_ml_service()
        if service is None:
            raise HTTPException(status_code=503, detail="ML service not available")
        
        # Trigger training
        result = service.train_model()
        return {
            "status": "training_started",
            "message": "Model training initiated",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data/sightings")
async def get_sightings(limit: int = 100):
    """Get recent sightings"""
    try:
        client = get_bq_client()
        if client is None:
            return {
                "sightings": [],
                "message": "BigQuery not available - using mock data",
                "count": 0
            }
        
        query = f"""
        SELECT sighting_id, timestamp, latitude, longitude, pod_size
        FROM `orca-904de.orca_data.sightings`
        ORDER BY timestamp DESC
        LIMIT {limit}
        """
        
        result = client.query(query).to_dataframe()
        sightings = result.to_dict('records')
        
        return {
            "sightings": sightings,
            "count": len(sightings),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve sightings: {e}")
        return {
            "sightings": [],
            "error": str(e),
            "count": 0
        }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port) 