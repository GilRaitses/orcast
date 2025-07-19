"""
OrCast Behavioral ML Service
Cloud Run service for real-time orca behavioral classification and interpretability
"""

import os
import sys
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

import numpy as np
import pandas as pd

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from google.cloud import bigquery
from google.cloud.exceptions import NotFound

from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import shap
import lime
import lime.lime_tabular

from hmc_sampling import HMCFeedingBehaviorSampler, HMCAnalysisAPI
from redis_cache import OrCastRedisCache, CachedHMCAnalysis, CachedEnvironmentalData

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="OrCast Behavioral ML Service",
    description="Real-time orca behavioral classification and interpretability",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize BigQuery client (lazy loading for Cloud Run)
bq_client = None

def get_bq_client():
    """Get or create BigQuery client"""
    global bq_client
    if bq_client is None:
        try:
            bq_client = bigquery.Client()
        except Exception as e:
            logger.error(f"Failed to initialize BigQuery client: {e}")
            # For development/testing, continue without BigQuery
            pass
    return bq_client

# === DATA MODELS ===

@dataclass
class SightingData:
    """Orca sighting data structure"""
    sighting_id: str
    timestamp: datetime
    latitude: float
    longitude: float
    pod_size: int
    environmental_context: Dict
    data_quality_score: float

@dataclass
class BehavioralFeatures:
    """Behavioral features for ML prediction"""
    spatial_features: List[float]
    temporal_features: List[float]
    environmental_features: List[float]
    social_features: List[float]
    historical_features: List[float]

@dataclass
class BehavioralPrediction:
    """Behavioral prediction result"""
    behavior: str
    probability: float
    confidence: float
    feeding_strategy: Optional[str] = None
    success_probability: Optional[float] = None
    explanation: Optional[Dict] = None

class SightingInput(BaseModel):
    """API input for sighting data"""
    timestamp: str
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    pod_size: int = Field(..., ge=1, le=100)
    environmental_context: Dict
    data_quality_score: float = Field(..., ge=0.0, le=1.0)

class PredictionResponse(BaseModel):
    """API response for behavioral prediction"""
    sighting_id: str
    predictions: List[Dict]
    feature_importance: List[Dict]
    explanation: Dict
    model_confidence: float
    processing_time_ms: float

# === ML MODEL MANAGEMENT ===

class BehavioralMLModel:
    """Orca behavioral classification model"""
    
    def __init__(self):
        self.behavior_model = None
        self.strategy_model = None
        self.success_model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_names = []
        self.model_version = "1.0.0"
        self.last_trained = None
        
        # SHAP explainer for interpretability
        self.shap_explainer = None
        
        # LIME explainer for local interpretability
        self.lime_explainer = None
        
    def load_training_data(self, start_date: str, end_date: str) -> Tuple[np.ndarray, np.ndarray]:
        """Load training data from BigQuery"""
        
        query = f"""
        SELECT 
            features.spatial,
            features.temporal,
            features.environmental,
            features.social,
            features.historical,
            behavior_label,
            feeding_strategy_label,
            success_label,
            data_quality_score
        FROM `orcast-app-2024.orca_data.ml_training_data`
        WHERE DATE(created_at) BETWEEN '{start_date}' AND '{end_date}'
            AND train_test_split = 'train'
            AND data_quality_score > 0.7
        ORDER BY created_at DESC
        """
        
        try:
            client = get_bq_client()
        if client is None:
            return pd.DataFrame()
        df = client.query(query).to_dataframe()
            
            # Process features
            features = []
            labels = []
            
            for _, row in df.iterrows():
                # Combine all feature arrays
                feature_vector = (
                    row['features']['spatial'] +
                    row['features']['temporal'] +
                    row['features']['environmental'] +
                    row['features']['social'] +
                    row['features']['historical']
                )
                features.append(feature_vector)
                labels.append(row['behavior_label'])
            
            X = np.array(features)
            y = np.array(labels)
            
            # Store feature names for interpretability
            self.feature_names = [
                'distance_to_shore_km', 'water_depth_m', 'distance_to_feeding_zone_km',  # spatial
                'hour_of_day', 'day_of_year', 'tidal_height_normalized',  # temporal
                'sst_anomaly_c', 'tidal_velocity_ms', 'chlorophyll_concentration',  # environmental
                'pod_cohesion_index', 'social_activity_level',  # social
                'recent_sightings_24h', 'days_since_last_feeding'  # historical
            ]
            
            logger.info(f"Loaded {len(X)} training samples with {X.shape[1]} features")
            return X, y
            
        except Exception as e:
            logger.error(f"Error loading training data: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to load training data: {str(e)}")
    
    def train_behavior_model(self, X: np.ndarray, y: np.ndarray):
        """Train the primary behavior classification model"""
        
        # Encode labels
        if 'behavior' not in self.label_encoders:
            self.label_encoders['behavior'] = LabelEncoder()
        
        y_encoded = self.label_encoders['behavior'].fit_transform(y)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train Random Forest model for interpretability
        self.behavior_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        
        self.behavior_model.fit(X_scaled, y_encoded)
        
        # Initialize SHAP explainer
        self.shap_explainer = shap.TreeExplainer(self.behavior_model)
        
        # Initialize LIME explainer
        self.lime_explainer = lime.lime_tabular.LimeTabularExplainer(
            X_scaled,
            feature_names=self.feature_names,
            class_names=self.label_encoders['behavior'].classes_,
            mode='classification'
        )
        
        # Evaluate model
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y_encoded, test_size=0.2, random_state=42
        )
        
        y_pred = self.behavior_model.predict(X_test)
        accuracy = (y_pred == y_test).mean()
        
        logger.info(f"Behavior model trained with accuracy: {accuracy:.3f}")
        
        # Log classification report
        report = classification_report(
            y_test, y_pred, 
            target_names=self.label_encoders['behavior'].classes_
        )
        logger.info(f"Classification report:\n{report}")
        
        self.last_trained = datetime.now()
    
    def train_strategy_model(self, X: np.ndarray, strategies: np.ndarray):
        """Train the feeding strategy classification model"""
        
        # Filter for feeding behaviors only
        feeding_mask = strategies != 'none'
        X_feeding = X[feeding_mask]
        strategies_feeding = strategies[feeding_mask]
        
        if len(X_feeding) == 0:
            logger.warning("No feeding strategy data available")
            return
        
        # Encode labels
        if 'strategy' not in self.label_encoders:
            self.label_encoders['strategy'] = LabelEncoder()
        
        y_encoded = self.label_encoders['strategy'].fit_transform(strategies_feeding)
        
        # Scale features
        X_scaled = self.scaler.transform(X_feeding)
        
        # Train model
        self.strategy_model = RandomForestClassifier(
            n_estimators=50,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        
        self.strategy_model.fit(X_scaled, y_encoded)
        
        logger.info(f"Strategy model trained with {len(X_feeding)} feeding samples")
    
    def train_success_model(self, X: np.ndarray, success: np.ndarray):
        """Train the feeding success prediction model"""
        
        # Filter for feeding behaviors only
        feeding_mask = success != -1  # -1 indicates non-feeding behavior
        X_feeding = X[feeding_mask]
        success_feeding = success[feeding_mask]
        
        if len(X_feeding) == 0:
            logger.warning("No feeding success data available")
            return
        
        # Scale features
        X_scaled = self.scaler.transform(X_feeding)
        
        # Train model
        self.success_model = RandomForestClassifier(
            n_estimators=50,
            max_depth=8,
            random_state=42,
            n_jobs=-1
        )
        
        self.success_model.fit(X_scaled, success_feeding)
        
        logger.info(f"Success model trained with {len(X_feeding)} feeding samples")
    
    def predict_behavior(self, features: BehavioralFeatures) -> List[BehavioralPrediction]:
        """Predict orca behavior with interpretability"""
        
        if self.behavior_model is None:
            raise HTTPException(status_code=503, detail="Model not trained")
        
        # Prepare feature vector
        feature_vector = np.array([
            features.spatial_features +
            features.temporal_features +
            features.environmental_features +
            features.social_features +
            features.historical_features
        ])
        
        # Scale features
        X_scaled = self.scaler.transform(feature_vector)
        
        # Predict behavior
        behavior_probs = self.behavior_model.predict_proba(X_scaled)[0]
        behavior_classes = self.label_encoders['behavior'].classes_
        
        predictions = []
        
        for i, prob in enumerate(behavior_probs):
            behavior = behavior_classes[i]
            
            # Get SHAP explanation
            shap_values = self.shap_explainer.shap_values(X_scaled)
            
            # Get feature importance for this prediction
            feature_importance = []
            for j, feature_name in enumerate(self.feature_names):
                importance = float(shap_values[i][0][j])
                feature_importance.append({
                    'feature': feature_name,
                    'importance': importance,
                    'explanation': self.get_feature_explanation(feature_name, importance)
                })
            
            # Sort by absolute importance
            feature_importance.sort(key=lambda x: abs(x['importance']), reverse=True)
            
            # Predict feeding strategy if behavior is feeding
            feeding_strategy = None
            success_probability = None
            
            if behavior == 'feeding' and self.strategy_model is not None:
                strategy_probs = self.strategy_model.predict_proba(X_scaled)[0]
                strategy_classes = self.label_encoders['strategy'].classes_
                
                # Get most likely strategy
                strategy_idx = np.argmax(strategy_probs)
                feeding_strategy = strategy_classes[strategy_idx]
                
                # Predict success probability
                if self.success_model is not None:
                    success_probs = self.success_model.predict_proba(X_scaled)[0]
                    success_probability = float(success_probs[1])  # Probability of success
            
            predictions.append(BehavioralPrediction(
                behavior=behavior,
                probability=float(prob),
                confidence=self.calculate_confidence(prob, feature_importance),
                feeding_strategy=feeding_strategy,
                success_probability=success_probability,
                explanation={
                    'feature_importance': feature_importance[:5],  # Top 5 features
                    'model_version': self.model_version,
                    'interpretation': self.generate_interpretation(behavior, feature_importance[:3])
                }
            ))
        
        # Sort by probability
        predictions.sort(key=lambda x: x.probability, reverse=True)
        
        return predictions
    
    def get_feature_explanation(self, feature_name: str, importance: float) -> str:
        """Generate human-readable explanation for feature importance"""
        
        explanations = {
            'distance_to_shore_km': 'Distance from shore affects prey availability and orca behavior patterns',
            'water_depth_m': 'Water depth influences hunting strategies and prey distribution',
            'distance_to_feeding_zone_km': 'Proximity to known feeding areas increases feeding probability',
            'hour_of_day': 'Orcas have daily activity patterns with peak feeding times',
            'day_of_year': 'Seasonal patterns affect prey availability and orca behavior',
            'tidal_height_normalized': 'Tidal conditions influence prey movement and orca hunting success',
            'sst_anomaly_c': 'Water temperature affects marine ecosystem and prey distribution',
            'tidal_velocity_ms': 'Tidal current strength concentrates prey in predictable areas',
            'chlorophyll_concentration': 'Plankton levels indicate ecosystem productivity and food web strength',
            'pod_cohesion_index': 'Pod social structure affects hunting coordination and behavior',
            'social_activity_level': 'Social interactions influence feeding vs. socializing behavior',
            'recent_sightings_24h': 'Recent orca activity in the area affects behavioral patterns',
            'days_since_last_feeding': 'Time since last feeding affects motivation and hunting behavior'
        }
        
        base_explanation = explanations.get(feature_name, 'This feature influences orca behavior')
        
        if importance > 0:
            return f"{base_explanation} (increases {feature_name.replace('_', ' ')} likelihood)"
        else:
            return f"{base_explanation} (decreases {feature_name.replace('_', ' ')} likelihood)"
    
    def calculate_confidence(self, probability: float, feature_importance: List[Dict]) -> float:
        """Calculate prediction confidence based on probability and feature importance"""
        
        # Base confidence from probability
        prob_confidence = min(probability * 2, 1.0)  # Scale up lower probabilities
        
        # Feature importance spread (higher spread = lower confidence)
        importances = [abs(fi['importance']) for fi in feature_importance]
        if len(importances) > 1:
            importance_spread = np.std(importances) / np.mean(importances)
            spread_confidence = 1.0 / (1.0 + importance_spread)
        else:
            spread_confidence = 0.5
        
        # Combine confidences
        combined_confidence = (prob_confidence * 0.7) + (spread_confidence * 0.3)
        
        return float(combined_confidence)
    
    def generate_interpretation(self, behavior: str, top_features: List[Dict]) -> str:
        """Generate natural language interpretation of prediction"""
        
        if not top_features:
            return f"Predicted behavior: {behavior}"
        
        # Start with behavior
        interpretation = f"Orcas are likely {behavior}"
        
        # Add top influencing factors
        positive_factors = [f for f in top_features if f['importance'] > 0]
        negative_factors = [f for f in top_features if f['importance'] < 0]
        
        if positive_factors:
            factor_names = [f['feature'].replace('_', ' ') for f in positive_factors[:2]]
            interpretation += f" due to favorable {' and '.join(factor_names)}"
        
        if negative_factors:
            factor_names = [f['feature'].replace('_', ' ') for f in negative_factors[:1]]
            interpretation += f", despite limiting {' and '.join(factor_names)}"
        
        return interpretation

# Global model instance
ml_model = BehavioralMLModel()

# === FEATURE EXTRACTION ===

def extract_behavioral_features(sighting: SightingData) -> BehavioralFeatures:
    """Extract behavioral features from sighting data"""
    
    # Spatial features
    spatial_features = [
        calculate_distance_to_shore(sighting.latitude, sighting.longitude),
        sighting.environmental_context.get('water_depth_m', 50.0),
        calculate_distance_to_feeding_zone(sighting.latitude, sighting.longitude)
    ]
    
    # Temporal features
    temporal_features = [
        sighting.timestamp.hour,
        sighting.timestamp.timetuple().tm_yday,
        normalize_tidal_height(sighting.environmental_context.get('tidal_height', 0.0))
    ]
    
    # Environmental features
    environmental_features = [
        sighting.environmental_context.get('sst_anomaly_c', 0.0),
        sighting.environmental_context.get('tidal_velocity_ms', 0.0),
        sighting.environmental_context.get('chlorophyll_concentration', 1.0)
    ]
    
    # Social features
    social_features = [
        calculate_pod_cohesion_index(sighting.pod_size),
        estimate_social_activity_level(sighting.environmental_context)
    ]
    
    # Historical features
    historical_features = [
        get_recent_sightings_24h(sighting.latitude, sighting.longitude),
        get_days_since_last_feeding(sighting.latitude, sighting.longitude)
    ]
    
    return BehavioralFeatures(
        spatial_features=spatial_features,
        temporal_features=temporal_features,
        environmental_features=environmental_features,
        social_features=social_features,
        historical_features=historical_features
    )

def calculate_distance_to_shore(lat: float, lng: float) -> float:
    """Calculate distance to nearest shore (simplified)"""
    # This would use actual coastline data in production
    # For now, use a simplified calculation
    return min(abs(lat - 48.5), abs(lng + 123.0)) * 111.0  # Rough km conversion

def calculate_distance_to_feeding_zone(lat: float, lng: float) -> float:
    """Calculate distance to nearest feeding zone"""
    # Known feeding zone centers (from feeding_zone_dynamics.js)
    feeding_zones = [
        (48.52, -123.15),  # West Side Feeding Complex
        (48.65, -122.88),  # East Sound Foraging Area
        (48.58, -123.05)   # Spyne Channel Hunting Grounds
    ]
    
    distances = []
    for zone_lat, zone_lng in feeding_zones:
        distance = ((lat - zone_lat)**2 + (lng - zone_lng)**2)**0.5 * 111.0
        distances.append(distance)
    
    return min(distances)

def normalize_tidal_height(tidal_height: float) -> float:
    """Normalize tidal height to -1 to 1 range"""
    # Assuming tidal range of -3 to 3 meters
    return max(-1.0, min(1.0, tidal_height / 3.0))

def calculate_pod_cohesion_index(pod_size: int) -> float:
    """Calculate pod cohesion index based on size"""
    # Larger pods tend to have lower cohesion
    return max(0.1, min(1.0, 1.0 - (pod_size - 1) * 0.1))

def estimate_social_activity_level(environmental_context: Dict) -> float:
    """Estimate social activity level from environmental context"""
    # Higher activity in calm conditions
    wave_height = environmental_context.get('wave_height_m', 1.0)
    wind_speed = environmental_context.get('wind_speed_knots', 10.0)
    
    # Scale 1-5 based on conditions
    activity = 5.0 - (wave_height * 0.5) - (wind_speed * 0.05)
    return max(1.0, min(5.0, activity))

def get_recent_sightings_24h(lat: float, lng: float) -> int:
    """Get recent sightings in area within 24 hours"""
    # Query BigQuery for recent sightings
    query = f"""
    SELECT COUNT(*) as count
    FROM `orcast-app-2024.orca_data.sightings`
    WHERE ST_DWITHIN(location, ST_GEOGPOINT({lng}, {lat}), 5000)
        AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
    """
    
    try:
        result = bq_client.query(query).to_dataframe()
        return int(result['count'].iloc[0])
    except Exception as e:
        logger.warning(f"Error querying recent sightings: {str(e)}")
        return 0

def get_days_since_last_feeding(lat: float, lng: float) -> int:
    """Get days since last feeding event in area"""
    query = f"""
    SELECT DATE_DIFF(CURRENT_DATE(), DATE(timestamp), DAY) as days_since
    FROM `orcast-app-2024.orca_data.sightings`
    WHERE ST_DWITHIN(location, ST_GEOGPOINT({lng}, {lat}), 5000)
        AND behavior_primary = 'feeding'
    ORDER BY timestamp DESC
    LIMIT 1
    """
    
    try:
        result = bq_client.query(query).to_dataframe()
        if len(result) > 0:
            return int(result['days_since'].iloc[0])
        else:
            return 30  # Default if no recent feeding
    except Exception as e:
        logger.warning(f"Error querying last feeding: {str(e)}")
        return 30

# === API ENDPOINTS ===

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "OrCast Behavioral ML Service",
        "version": "1.0.0",
        "status": "healthy",
        "model_trained": ml_model.last_trained is not None,
        "last_trained": ml_model.last_trained.isoformat() if ml_model.last_trained else None
    }

@app.post("/predict", response_model=PredictionResponse)
async def predict_behavior(sighting: SightingInput):
    """Predict orca behavior from sighting data"""
    
    start_time = datetime.now()
    
    try:
        # Convert input to internal format
        sighting_data = SightingData(
            sighting_id=f"sighting_{int(datetime.now().timestamp())}",
            timestamp=datetime.fromisoformat(sighting.timestamp.replace('Z', '+00:00')),
            latitude=sighting.latitude,
            longitude=sighting.longitude,
            pod_size=sighting.pod_size,
            environmental_context=sighting.environmental_context,
            data_quality_score=sighting.data_quality_score
        )
        
        # Extract features
        features = extract_behavioral_features(sighting_data)
        
        # Make prediction
        predictions = ml_model.predict_behavior(features)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Format response
        prediction_dicts = []
        feature_importance = []
        
        for pred in predictions:
            prediction_dicts.append({
                'behavior': pred.behavior,
                'probability': pred.probability,
                'confidence': pred.confidence,
                'feeding_strategy': pred.feeding_strategy,
                'success_probability': pred.success_probability
            })
            
            # Get feature importance from top prediction
            if pred == predictions[0] and pred.explanation:
                feature_importance = pred.explanation.get('feature_importance', [])
        
        return PredictionResponse(
            sighting_id=sighting_data.sighting_id,
            predictions=prediction_dicts,
            feature_importance=feature_importance,
            explanation={
                'interpretation': predictions[0].explanation.get('interpretation', '') if predictions else '',
                'model_version': ml_model.model_version,
                'data_quality_impact': sighting.data_quality_score
            },
            model_confidence=sum(p.confidence for p in predictions) / len(predictions) if predictions else 0.0,
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error in prediction: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.post("/train")
async def train_model(background_tasks: BackgroundTasks):
    """Train the behavioral classification model"""
    
    def train_background():
        try:
            # Load training data from last 2 years
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=730)
            
            X, y = ml_model.load_training_data(start_date.isoformat(), end_date.isoformat())
            
            # Train models
            ml_model.train_behavior_model(X, y)
            
            # Load additional data for strategy and success models
            # This would be more sophisticated in production
            strategies = np.random.choice(['carousel', 'surface_feeding', 'deep_diving', 'none'], len(y))
            success = np.random.choice([0, 1, -1], len(y))  # -1 for non-feeding
            
            ml_model.train_strategy_model(X, strategies)
            ml_model.train_success_model(X, success)
            
            logger.info("Model training completed successfully")
            
        except Exception as e:
            logger.error(f"Error in background training: {str(e)}")
    
    background_tasks.add_task(train_background)
    
    return {
        "message": "Model training started",
        "status": "training",
        "estimated_completion": "10-15 minutes"
    }

@app.get("/model/status")
async def get_model_status():
    """Get current model status and performance metrics"""
    
    return {
        "model_version": ml_model.model_version,
        "last_trained": ml_model.last_trained.isoformat() if ml_model.last_trained else None,
        "models_available": {
            "behavior": ml_model.behavior_model is not None,
            "strategy": ml_model.strategy_model is not None,
            "success": ml_model.success_model is not None
        },
        "feature_count": len(ml_model.feature_names),
        "behavior_classes": ml_model.label_encoders.get('behavior', {}).classes_.tolist() if 'behavior' in ml_model.label_encoders else [],
        "interpretability": {
            "shap_available": ml_model.shap_explainer is not None,
            "lime_available": ml_model.lime_explainer is not None
        }
    }

@app.get("/features/importance")
async def get_feature_importance():
    """Get global feature importance for the behavior model"""
    
    if ml_model.behavior_model is None:
        raise HTTPException(status_code=503, detail="Model not trained")
    
    # Get feature importance from Random Forest
    importance_scores = ml_model.behavior_model.feature_importances_
    
    feature_importance = []
    for i, importance in enumerate(importance_scores):
        feature_importance.append({
            'feature': ml_model.feature_names[i],
            'importance': float(importance),
            'rank': i + 1
        })
    
    # Sort by importance
    feature_importance.sort(key=lambda x: x['importance'], reverse=True)
    
    # Update ranks
    for i, feature in enumerate(feature_importance):
        feature['rank'] = i + 1
    
    return {
        'feature_importance': feature_importance,
        'model_version': ml_model.model_version,
        'total_features': len(ml_model.feature_names)
    }

class BehavioralMLService:
    """
    Enhanced Behavioral ML Service with Redis caching and HMC sampling
    
    Provides high-performance behavioral classification with caching,
    uncertainty quantification, and real-time features.
    """
    
    def __init__(self, project_id: str = "orca-904de"):
        self.project_id = project_id
        self.client = bigquery.Client(project=project_id)
        
        # Initialize Redis cache
        self.redis_cache = OrCastRedisCache()
        
        # Initialize ML models
        self.behavior_model = None
        self.strategy_model = None
        self.success_model = None
        
        # Initialize HMC sampler with caching
        self.hmc_sampler = HMCFeedingBehaviorSampler(project_id=project_id)
        self.hmc_api = HMCAnalysisAPI()
        self.cached_hmc = CachedHMCAnalysis(self.redis_cache, self.hmc_api)
        
        # Initialize environmental data caching
        self.cached_env_data = CachedEnvironmentalData(self.redis_cache)
        
        # Model status
        self.models_loaded = False
        self.last_training_time = None
        
        # Rate limiting
        self.rate_limits = {
            'predict': (100, 3600),  # 100 requests per hour
            'hmc_analysis': (10, 3600),  # 10 HMC analyses per hour
            'predictions': (1000, 3600)  # 1000 predictions per hour
        }
    
    def load_real_training_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """Load real training data from BigQuery with caching"""
        
        # Try cache first
        cached_data = self.redis_cache.get('environmental_data', 
                                         data_type='training', 
                                         source='bigquery')
        if cached_data:
            logger.info("Training data cache hit")
            return (np.array(cached_data['features']), 
                   np.array(cached_data['behavior_labels']),
                   np.array(cached_data['strategy_labels']),
                   np.array(cached_data['success_labels']))
        
        # Fetch from BigQuery
        query = """
        SELECT 
            s.latitude,
            s.longitude,
            s.pod_size,
            s.water_depth,
            s.tidal_flow,
            s.temperature,
            s.salinity,
            s.visibility,
            s.current_speed,
            s.noise_level,
            s.prey_density,
            EXTRACT(HOUR FROM s.timestamp) as hour_of_day,
            EXTRACT(DAYOFYEAR FROM s.timestamp) as day_of_year,
            b.primary_behavior,
            b.feeding_strategy,
            b.feeding_success
        FROM `{}.orca_data.sightings` s
        JOIN `{}.orca_data.behavioral_data` b
        ON s.sighting_id = b.sighting_id
        WHERE s.timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 365 DAY)
        AND b.primary_behavior IS NOT NULL
        AND s.water_depth IS NOT NULL
        AND s.tidal_flow IS NOT NULL
        AND s.prey_density IS NOT NULL
        ORDER BY s.timestamp DESC
        """.format(self.project_id)
        
        try:
            df = self.client.query(query).to_dataframe()
            
            if df.empty:
                raise ValueError("No training data available in BigQuery - real data required")
            
            # Prepare data
            features = df[[
                'latitude', 'longitude', 'pod_size', 'water_depth',
                'tidal_flow', 'temperature', 'salinity', 'visibility',
                'current_speed', 'noise_level', 'prey_density',
                'hour_of_day', 'day_of_year'
            ]].values
            
            behavior_labels = df['primary_behavior'].values
            strategy_labels = df['feeding_strategy'].values
            success_labels = df['feeding_success'].values
            
            # Cache the data
            training_data = {
                'features': features.tolist(),
                'behavior_labels': behavior_labels.tolist(),
                'strategy_labels': strategy_labels.tolist(),
                'success_labels': success_labels.tolist()
            }
            
            self.redis_cache.set('environmental_data', training_data,
                               data_type='training', source='bigquery')
            
            logger.info(f"Loaded {len(df)} real training samples")
            
            return features, behavior_labels, strategy_labels, success_labels
            
        except Exception as e:
            logger.error(f"Failed to load real training data: {e}")
            raise ValueError(f"Real training data unavailable: {e}")
    
    def predict_behavior_with_caching(self, sighting_data: Dict[str, Any]) -> Dict[str, Any]:
        """Predict behavior with Redis caching and rate limiting"""
        
        # Rate limiting
        user_id = sighting_data.get('user_id', 'anonymous')
        if not self.redis_cache.rate_limit(f"predict:{user_id}", 
                                         self.rate_limits['predict'][0],
                                         self.rate_limits['predict'][1]):
            raise ValueError("Rate limit exceeded for prediction requests")
        
        # Try cache first
        cached_prediction = self.redis_cache.get_ml_prediction(sighting_data)
        if cached_prediction:
            logger.info("ML prediction cache hit")
            
            # Track analytics
            self.redis_cache.track_prediction_request(
                sighting_data.get('location', 'unknown'), user_id
            )
            
            return cached_prediction
        
        # Generate fresh prediction
        prediction = self.predict_behavior_with_uncertainty(sighting_data)
        
        # Cache the prediction
        self.redis_cache.cache_ml_prediction(prediction, sighting_data)
        
        # Add to user history
        if user_id != 'anonymous':
            self.redis_cache.add_user_prediction_history(user_id, prediction)
        
        # Publish real-time update
        self.redis_cache.publish_prediction_update(
            prediction, sighting_data.get('location', 'unknown')
        )
        
        # Track analytics
        self.redis_cache.track_prediction_request(
            sighting_data.get('location', 'unknown'), user_id
        )
        
        return prediction
    
    def run_hmc_analysis_with_caching(self, environmental_conditions: Dict[str, Any],
                                    n_samples: int = 1000) -> Dict[str, Any]:
        """Run HMC analysis with caching"""
        
        # Rate limiting
        if not self.redis_cache.rate_limit("hmc_analysis", 
                                         self.rate_limits['hmc_analysis'][0],
                                         self.rate_limits['hmc_analysis'][1]):
            raise ValueError("Rate limit exceeded for HMC analysis")
        
        # Use cached HMC analysis
        result = self.cached_hmc.run_analysis(environmental_conditions, n_samples)
        
        # Cache feeding patterns
        patterns = self.get_feeding_patterns()
        if patterns:
            today = datetime.now().strftime('%Y-%m-%d')
            self.redis_cache.cache_feeding_patterns(patterns, today)
        
        return result
    
    def get_cached_environmental_data(self, location: str, data_type: str) -> Dict[str, Any]:
        """Get environmental data with caching"""
        
        def fetch_tidal_data(station: str) -> Dict[str, Any]:
            # This would call the actual NOAA API
            # For now, return simulated data
            return {
                'height': 8.5,
                'flow': 0.3,
                'next_high': '2024-01-15T14:30:00Z',
                'next_low': '2024-01-15T08:15:00Z'
            }
        
        def fetch_weather_data(location: str) -> Dict[str, Any]:
            # This would call the actual weather API
            # For now, return simulated data
            return {
                'temperature': 15.2,
                'visibility': 10.0,
                'wind_speed': 5.0,
                'conditions': 'clear'
            }
        
        if data_type == 'tidal':
            return self.cached_env_data.get_tidal_data(location, fetch_tidal_data)
        elif data_type == 'weather':
            return self.cached_env_data.get_weather_data(location, fetch_weather_data)
        else:
            return self.redis_cache.get_environmental_data(location, data_type) or {}
    
    def process_new_sighting(self, sighting_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process new sighting with real-time features"""
        
        # Get behavioral prediction
        prediction = self.predict_behavior_with_caching(sighting_data)
        
        # Publish to real-time feed
        self.redis_cache.publish_sighting(sighting_data)
        
        # Check for alerts
        if prediction.get('confidence', 0) > 0.8:
            alert_message = f"High confidence {prediction['behavior']} behavior detected"
            self.redis_cache.publish_alert(
                'high_confidence_sighting',
                alert_message,
                sighting_data.get('location'),
                prediction.get('confidence')
            )
        
        # Update environmental data cache
        location = sighting_data.get('location', 'unknown')
        environmental_data = {
            'tidal_flow': sighting_data.get('tidal_flow'),
            'temperature': sighting_data.get('temperature'),
            'weather_conditions': sighting_data.get('weather_conditions')
        }
        
        self.redis_cache.publish_environmental_update(environmental_data, location)
        
        return {
            'sighting_processed': True,
            'prediction': prediction,
            'real_time_published': True
        }
    
    def get_user_dashboard(self, user_id: str) -> Dict[str, Any]:
        """Get user dashboard with cached data"""
        
        # Get user session
        session = self.redis_cache.get_user_session(user_id) or {}
        
        # Get prediction history
        history = self.redis_cache.get_user_prediction_history(user_id, limit=20)
        
        # Get analytics
        analytics = self.redis_cache.get_prediction_analytics(days=7)
        
        return {
            'user_id': user_id,
            'session': session,
            'prediction_history': history,
            'analytics': analytics,
            'last_updated': datetime.now().isoformat()
        }
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get system health with cache status"""
        
        # Redis health
        redis_health = self.redis_cache.health_check()
        
        # ML model status
        ml_status = {
            'models_loaded': self.models_loaded,
            'hmc_available': self.hmc_sampler.samples is not None,
            'last_training': self.last_training_time.isoformat() if self.last_training_time else None
        }
        
        return {
            'redis': redis_health,
            'ml_models': ml_status,
            'timestamp': datetime.now().isoformat()
        }

# Enhanced FastAPI app with Redis integration
app = FastAPI(title="OrCast ML with Redis Caching", version="2.0")

# Global service instance
ml_service = BehavioralMLService()

@app.on_event("startup")
async def startup_event():
    """Initialize ML service with Redis caching"""
    try:
        # Check Redis connection
        redis_health = ml_service.redis_cache.health_check()
        if not redis_health.get('connected'):
            logger.warning("Redis not connected, running without cache")
        
        # Train models
        ml_service.train_models()
        
        # Warm cache for common locations
        common_locations = ['lime_kiln_point', 'san_juan_channel', 'rosario_strait']
        ml_service.redis_cache.warm_cache(common_locations)
        
        # Run initial HMC analysis
        initial_conditions = {
            'tidal_flow': 0.3,
            'water_depth': 50.0,
            'prey_density': 0.7,
            'temperature': 15.0
        }
        
        await asyncio.to_thread(
            ml_service.run_hmc_analysis_with_caching,
            initial_conditions,
            500
        )
        
        logger.info("ML service with Redis caching initialized")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

@app.get("/")
async def health_check():
    """Health check with cache status"""
    return ml_service.get_system_health()

@app.post("/predict")
async def predict_behavior(sighting_data: dict):
    """Predict behavior with caching and rate limiting"""
    try:
        result = ml_service.predict_behavior_with_caching(sighting_data)
        return result
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/sighting")
async def process_sighting(sighting_data: dict):
    """Process new sighting with real-time features"""
    try:
        result = ml_service.process_new_sighting(sighting_data)
        return result
    except Exception as e:
        logger.error(f"Sighting processing failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/hmc-analysis")
async def run_hmc_analysis(request: dict):
    """Run HMC analysis with caching"""
    try:
        conditions = request.get('environmental_conditions', {})
        n_samples = request.get('n_samples', 1000)
        
        result = await asyncio.to_thread(
            ml_service.run_hmc_analysis_with_caching,
            conditions,
            n_samples
        )
        return result
    except Exception as e:
        logger.error(f"HMC analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/environmental/{location}/{data_type}")
async def get_environmental_data(location: str, data_type: str):
    """Get cached environmental data"""
    try:
        data = ml_service.get_cached_environmental_data(location, data_type)
        return data
    except Exception as e:
        logger.error(f"Environmental data retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/user/{user_id}/dashboard")
async def get_user_dashboard(user_id: str):
    """Get user dashboard with cached data"""
    try:
        dashboard = ml_service.get_user_dashboard(user_id)
        return dashboard
    except Exception as e:
        logger.error(f"Dashboard retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics")
async def get_analytics():
    """Get system analytics"""
    try:
        analytics = ml_service.redis_cache.get_prediction_analytics(days=30)
        return {
            'analytics': analytics,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Analytics retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cache/health")
async def cache_health():
    """Check cache health"""
    return ml_service.redis_cache.health_check()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080) 