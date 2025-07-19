#!/usr/bin/env python3
"""
ORCAST Advanced ML Service - Physics-Informed with HMC Sampling
Integrates your proprietary Hamiltonian Monte Carlo and physics-informed modeling
for sophisticated orca behavioral predictions with uncertainty quantification
"""

import os
import json
import logging
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

# Import your proprietary HMC framework
from scripts.ml_services.hmc_sampling import (
    HMCFeedingBehaviorSampler, 
    FeedingBehaviorParameters,
    EnvironmentalConditions
)

# JAX/NumPyro for probabilistic modeling
import jax
import jax.numpy as jnp
from jax import random
import numpyro
import numpyro.distributions as dist

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="ORCAST Advanced Physics-Informed ML Service",
    description="Sophisticated orca behavioral modeling using HMC sampling and physics-informed priors",
    version="4.0.0"
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
        firebase_admin.get_app()
        logger.info("✅ Firebase already initialized")
    except ValueError:
        try:
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, {
                'projectId': 'orca-466204',
            })
            logger.info("✅ Firebase initialized with Application Default Credentials")
        except Exception as e:
            logger.warning(f"⚠️ Firebase initialization failed: {e}")
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

# === PHYSICS-INFORMED DATA MODELS ===

class PhysicsInformedFeatures(BaseModel):
    """Physics-informed environmental features for orca behavior modeling"""
    # Spatial dynamics
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in degrees")
    
    # Oceanographic physics
    water_depth: float = Field(..., ge=0, le=1000, description="Water depth in meters")
    tidal_flow: float = Field(..., ge=-3, le=3, description="Tidal flow velocity in m/s")
    current_speed: float = Field(..., ge=0, le=5, description="Current speed in m/s")
    
    # Thermodynamic conditions
    temperature: float = Field(..., ge=0, le=25, description="Water temperature in Celsius")
    salinity: float = Field(..., ge=20, le=40, description="Salinity in PSU")
    
    # Acoustic environment
    noise_level: float = Field(..., ge=80, le=180, description="Noise level in dB")
    
    # Biological factors
    prey_density: float = Field(..., ge=0, le=1, description="Prey density index 0-1")
    visibility: float = Field(..., ge=0, le=100, description="Visibility in meters")
    
    # Temporal dynamics
    hour_of_day: int = Field(..., ge=0, le=23, description="Hour of day (0-23)")
    day_of_year: int = Field(..., ge=1, le=366, description="Day of year (1-366)")
    
    # Pod social dynamics
    pod_size: int = Field(..., ge=1, le=50, description="Number of orcas in pod")

class ProbabilisticPrediction(BaseModel):
    """Probabilistic prediction with uncertainty quantification"""
    predicted_behavior: str
    probability_distribution: Dict[str, float]
    confidence_interval: Dict[str, Tuple[float, float]]
    uncertainty_score: float
    feeding_success_probability: Optional[float] = None
    feeding_success_ci: Optional[Tuple[float, float]] = None
    model_version: str
    prediction_timestamp: str
    hmc_diagnostics: Dict[str, Any]

class SpatialPhysicsForecast(BaseModel):
    """Spatial forecast with physics-informed modeling"""
    region: str
    timestamp: str
    physics_parameters: Dict[str, Any]
    uncertainty_map: List[Dict]
    confidence_map: List[Dict]

# === ADVANCED PHYSICS-INFORMED ML MODEL ===

class ORCASTPhysicsML:
    """
    Advanced Physics-Informed ML Model for Orca Behavior
    
    Integrates:
    - Hamiltonian Monte Carlo for uncertainty quantification
    - Physics-informed priors based on marine biology
    - Bayesian inference for feeding behavior parameters
    - Spatial-temporal dynamics modeling
    """
    
    def __init__(self):
        self.hmc_sampler = HMCFeedingBehaviorSampler(project_id="orca-466204")
        self.db = db
        self.rng_key = random.PRNGKey(42)
        
        # Physics-informed priors (based on marine biology)
        self.physics_priors = {
            'optimal_depth_range': (30, 80),  # meters, optimal feeding depth
            'optimal_temperature': 16.0,      # Celsius, preferred temperature
            'optimal_tidal_flow': 0.5,        # m/s, optimal tidal conditions
            'min_prey_density': 0.3,          # minimum viable prey density
            'noise_tolerance': 120.0,         # dB, maximum tolerable noise
            'optimal_visibility': 25.0,       # meters, optimal visibility
        }
        
        # Cached HMC samples for fast prediction
        self.cached_samples = None
        self.sample_timestamp = None
        
        logger.info("🧠 Advanced Physics-Informed ML Model initialized")
    
    def physics_informed_priors(self, environmental_data: jnp.ndarray) -> Dict[str, Any]:
        """
        Generate physics-informed priors based on marine biology principles
        
        Args:
            environmental_data: Environmental conditions array
            
        Returns:
            Dictionary of informed prior parameters
        """
        # Extract environmental features
        water_depth = environmental_data[:, 2]
        temperature = environmental_data[:, 5]
        tidal_flow = environmental_data[:, 3]
        prey_density = environmental_data[:, 8]
        noise_level = environmental_data[:, 7]
        
        # Physics-informed adjustments
        depth_preference = jnp.where(
            (water_depth >= self.physics_priors['optimal_depth_range'][0]) &
            (water_depth <= self.physics_priors['optimal_depth_range'][1]),
            1.0, 0.5
        )
        
        temperature_preference = jnp.exp(
            -0.5 * ((temperature - self.physics_priors['optimal_temperature']) / 3.0) ** 2
        )
        
        tidal_preference = jnp.exp(
            -0.5 * ((tidal_flow - self.physics_priors['optimal_tidal_flow']) / 0.3) ** 2
        )
        
        return {
            'depth_preference_prior': depth_preference.mean(),
            'temperature_preference_prior': temperature_preference.mean(),
            'tidal_preference_prior': tidal_preference.mean(),
            'feeding_viability': (prey_density >= self.physics_priors['min_prey_density']).mean()
        }
    
    def advanced_feeding_model(self, environmental_data: jnp.ndarray,
                             feeding_outcomes: Optional[jnp.ndarray] = None):
        """
        Advanced physics-informed feeding behavior model with HMC
        
        Incorporates:
        - Marine biology priors
        - Spatial-temporal correlations
        - Environmental interaction effects
        - Uncertainty quantification
        """
        n_obs, n_features = environmental_data.shape
        
        # Get physics-informed priors
        physics_priors = self.physics_informed_priors(environmental_data)
        
        # Hierarchical physics-informed parameters
        # Depth preference with marine biology prior
        depth_pref = numpyro.sample("depth_preference", 
                                   dist.Normal(physics_priors['depth_preference_prior'], 0.5))
        
        # Temperature sensitivity based on thermoregulation
        temp_sens = numpyro.sample("temperature_sensitivity", 
                                  dist.Normal(physics_priors['temperature_preference_prior'], 0.3))
        
        # Tidal flow effects on prey availability
        tidal_effect = numpyro.sample("tidal_flow_effect", 
                                     dist.Normal(physics_priors['tidal_preference_prior'], 0.4))
        
        # Prey density threshold with biological constraints
        prey_threshold = numpyro.sample("prey_density_threshold", 
                                       dist.Beta(2.0, 5.0))  # Biased toward lower thresholds
        
        # Acoustic sensitivity (noise impacts)
        noise_sensitivity = numpyro.sample("noise_sensitivity", 
                                          dist.Normal(-0.5, 0.2))  # Negative effect prior
        
        # Visibility effects on hunting success
        visibility_effect = numpyro.sample("visibility_effect", 
                                          dist.Normal(0.3, 0.2))  # Positive effect prior
        
        # Social dynamics (pod size effects)
        social_cooperation = numpyro.sample("social_cooperation", 
                                           dist.Normal(0.2, 0.1))  # Cooperative hunting
        
        # Spatial correlation parameters
        spatial_correlation = numpyro.sample("spatial_correlation", 
                                           dist.Normal(0.0, 0.3))
        
        # Temporal dynamics
        temporal_persistence = numpyro.sample("temporal_persistence", 
                                             dist.Beta(3.0, 2.0))  # Memory effects
        
        # Model uncertainty
        model_uncertainty = numpyro.sample("model_uncertainty", dist.HalfNormal(0.2))
        
        with numpyro.plate("observations", n_obs):
            # Extract environmental features
            lat = environmental_data[:, 0]
            lng = environmental_data[:, 1]
            water_depth = environmental_data[:, 2]
            tidal_flow = environmental_data[:, 3]
            current_speed = environmental_data[:, 4]
            temperature = environmental_data[:, 5]
            salinity = environmental_data[:, 6]
            noise_level = environmental_data[:, 7]
            prey_density = environmental_data[:, 8]
            visibility = environmental_data[:, 9]
            hour = environmental_data[:, 10]
            day_year = environmental_data[:, 11]
            pod_size = environmental_data[:, 12]
            
            # Physics-informed feature transformations
            # Depth suitability (bell curve around optimal depth)
            depth_suitability = jnp.exp(
                -0.5 * ((water_depth - 50.0) / 25.0) ** 2
            )
            
            # Temperature optimality
            temp_optimality = jnp.exp(
                -0.5 * ((temperature - 16.0) / 4.0) ** 2
            )
            
            # Tidal flow benefits (moderate flow is optimal)
            tidal_benefits = tidal_effect * jnp.abs(tidal_flow) * jnp.exp(-jnp.abs(tidal_flow))
            
            # Prey availability with threshold effects
            prey_availability = jnp.where(
                prey_density > prey_threshold,
                jnp.log(prey_density / prey_threshold),
                -2.0  # Strong penalty below threshold
            )
            
            # Acoustic interference
            acoustic_penalty = noise_sensitivity * (noise_level - 100.0) / 50.0
            
            # Visibility hunting advantage
            visibility_advantage = visibility_effect * visibility / 30.0
            
            # Social hunting benefits
            social_benefits = social_cooperation * jnp.log(pod_size)
            
            # Spatial effects (simplified)
            spatial_effect = spatial_correlation * (lat - 48.6) * (lng + 123.0)
            
            # Temporal effects (circadian and seasonal)
            circadian_effect = 0.3 * jnp.sin(2 * jnp.pi * hour / 24)
            seasonal_effect = 0.2 * jnp.sin(2 * jnp.pi * (day_year - 180) / 365)
            
            # Combined feeding success logit
            logit_success = (
                depth_pref * depth_suitability +
                temp_sens * temp_optimality +
                tidal_benefits +
                prey_availability +
                acoustic_penalty +
                visibility_advantage +
                social_benefits +
                spatial_effect +
                circadian_effect +
                seasonal_effect
            )
            
            # Success probability with physics constraints
            p_success = jnp.sigmoid(logit_success)
            
            # Add model uncertainty
            p_success_uncertain = numpyro.sample("p_success_latent",
                                               dist.Beta(p_success * 10, (1 - p_success) * 10))
            
            # Likelihood
            if feeding_outcomes is not None:
                numpyro.sample("feeding_success",
                              dist.Bernoulli(p_success_uncertain),
                              obs=feeding_outcomes)
            else:
                numpyro.sample("feeding_success",
                              dist.Bernoulli(p_success_uncertain))
    
    def predict_with_uncertainty(self, features: PhysicsInformedFeatures, 
                                n_samples: int = 1000) -> ProbabilisticPrediction:
        """
        Make probabilistic prediction with full uncertainty quantification
        
        Args:
            features: Physics-informed environmental features
            n_samples: Number of HMC samples for uncertainty quantification
            
        Returns:
            Probabilistic prediction with confidence intervals
        """
        start_time = time.time()
        
        # Convert features to array
        feature_array = jnp.array([[
            features.latitude, features.longitude, features.water_depth,
            features.tidal_flow, features.current_speed, features.temperature,
            features.salinity, features.noise_level, features.prey_density,
            features.visibility, features.hour_of_day, features.day_of_year,
            features.pod_size
        ]])
        
        # Run HMC sampling
        try:
            samples = self.hmc_sampler.sample_posterior(
                environmental_data=feature_array,
                feeding_outcomes=None,
                n_samples=n_samples,
                n_warmup=500,
                n_chains=2,
                model_type="feeding_behavior"
            )
            
            # Extract feeding success probabilities
            feeding_probs = samples['samples']['feeding_success']
            
            # Calculate statistics
            mean_prob = float(jnp.mean(feeding_probs))
            prob_ci = (float(jnp.percentile(feeding_probs, 2.5)),
                      float(jnp.percentile(feeding_probs, 97.5)))
            
            # Determine predicted behavior
            if mean_prob > 0.6:
                predicted_behavior = "feeding"
            elif mean_prob > 0.4:
                predicted_behavior = "foraging"
            elif features.pod_size > 3:
                predicted_behavior = "socializing"
            else:
                predicted_behavior = "traveling"
            
            # Calculate uncertainty score
            uncertainty = float(jnp.std(feeding_probs))
            
            # Feeding success prediction if feeding behavior
            feeding_success_prob = None
            feeding_success_ci = None
            if predicted_behavior in ["feeding", "foraging"]:
                feeding_success_prob = mean_prob
                feeding_success_ci = prob_ci
            
            # HMC diagnostics
            diagnostics = {
                'n_samples': n_samples,
                'mean_acceptance_prob': float(jnp.mean(samples.get('accept_prob', 0.8))),
                'n_divergences': int(samples.get('divergences', 0)),
                'sampling_time_ms': (time.time() - start_time) * 1000
            }
            
            # Probability distribution (simplified)
            prob_dist = {
                'feeding': float(jnp.clip(mean_prob, 0, 1)),
                'socializing': float(jnp.clip(0.8 - mean_prob, 0, 1)) if features.pod_size > 2 else 0.1,
                'traveling': float(jnp.clip(0.6 - mean_prob, 0, 1)),
                'resting': float(jnp.clip(0.3 - mean_prob, 0, 1)),
            }
            
            # Normalize probabilities
            total_prob = sum(prob_dist.values())
            prob_dist = {k: v/total_prob for k, v in prob_dist.items()}
            
            return ProbabilisticPrediction(
                predicted_behavior=predicted_behavior,
                probability_distribution=prob_dist,
                confidence_interval={'feeding': prob_ci},
                uncertainty_score=uncertainty,
                feeding_success_probability=feeding_success_prob,
                feeding_success_ci=feeding_success_ci,
                model_version="physics-informed-hmc-v4.0",
                prediction_timestamp=datetime.now().isoformat(),
                hmc_diagnostics=diagnostics
            )
            
        except Exception as e:
            logger.error(f"❌ HMC prediction failed: {e}")
            # Fallback to physics-informed prediction without HMC
            return self.fallback_physics_prediction(features)
    
    def fallback_physics_prediction(self, features: PhysicsInformedFeatures) -> ProbabilisticPrediction:
        """Fallback physics-informed prediction without HMC sampling"""
        
        # Physics-based feature scoring
        depth_score = np.exp(-0.5 * ((features.water_depth - 50.0) / 25.0) ** 2)
        temp_score = np.exp(-0.5 * ((features.temperature - 16.0) / 4.0) ** 2)
        prey_score = max(0, features.prey_density - 0.3)
        noise_penalty = max(0, (features.noise_level - 120.0) / 50.0)
        
        # Combined feeding probability
        feeding_prob = float(np.clip(
            0.5 * depth_score + 0.3 * temp_score + 0.4 * prey_score - 0.2 * noise_penalty,
            0, 1
        ))
        
        # Determine behavior
        if feeding_prob > 0.6:
            behavior = "feeding"
        elif features.pod_size > 3:
            behavior = "socializing"
        else:
            behavior = "traveling"
        
        # Simple probability distribution
        prob_dist = {
            'feeding': feeding_prob,
            'socializing': 0.8 - feeding_prob if features.pod_size > 2 else 0.1,
            'traveling': 0.6 - feeding_prob,
            'resting': 0.3 - feeding_prob,
        }
        
        total = sum(prob_dist.values())
        prob_dist = {k: max(0, v/total) for k, v in prob_dist.items()}
        
        return ProbabilisticPrediction(
            predicted_behavior=behavior,
            probability_distribution=prob_dist,
            confidence_interval={'feeding': (feeding_prob - 0.1, feeding_prob + 0.1)},
            uncertainty_score=0.2,
            feeding_success_probability=feeding_prob if behavior == "feeding" else None,
            feeding_success_ci=(feeding_prob - 0.1, feeding_prob + 0.1) if behavior == "feeding" else None,
            model_version="physics-informed-fallback-v4.0",
            prediction_timestamp=datetime.now().isoformat(),
            hmc_diagnostics={'fallback': True}
        )

# Initialize the advanced model
physics_ml = ORCASTPhysicsML()

# === API ENDPOINTS ===

@app.get("/")
async def root():
    """Service information"""
    return {
        "service": "ORCAST Advanced Physics-Informed ML Service",
        "version": "4.0.0",
        "status": "healthy",
        "firebase_connected": db is not None,
        "hmc_sampler_loaded": physics_ml.hmc_sampler is not None,
        "physics_priors": physics_ml.physics_priors,
        "capabilities": [
            "physics_informed_prediction",
            "hmc_uncertainty_quantification",
            "bayesian_inference",
            "spatial_temporal_modeling",
            "marine_biology_priors"
        ]
    }

@app.post("/predict/physics", response_model=ProbabilisticPrediction)
async def predict_physics_informed(features: PhysicsInformedFeatures):
    """Physics-informed prediction with HMC uncertainty quantification"""
    try:
        prediction = physics_ml.predict_with_uncertainty(features)
        
        # Store in Firestore if available
        if db:
            prediction_dict = prediction.dict()
            prediction_id = f"physics_pred_{int(time.time())}_{hash(str(features.dict()))}"
            db.collection('physics_predictions').document(prediction_id).set({
                **prediction_dict,
                'input_features': features.dict(),
                'created_at': firestore.SERVER_TIMESTAMP,
                'model_type': 'physics_informed_hmc'
            })
            
        logger.info(f"🧠 Physics prediction: {prediction.predicted_behavior} "
                   f"(uncertainty: {prediction.uncertainty_score:.3f}, "
                   f"time: {prediction.hmc_diagnostics.get('sampling_time_ms', 0):.1f}ms)")
        
        return prediction
        
    except Exception as e:
        logger.error(f"❌ Physics prediction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Physics prediction failed: {e}")

@app.get("/physics/priors")
async def get_physics_priors():
    """Get physics-informed priors and model parameters"""
    return {
        "marine_biology_priors": physics_ml.physics_priors,
        "model_description": {
            "depth_preference": "Optimal feeding depth range based on prey distribution",
            "temperature_sensitivity": "Thermoregulation preferences for hunting efficiency",
            "tidal_effects": "Tidal flow impacts on prey availability and energy costs",
            "acoustic_sensitivity": "Noise level impacts on echolocation and communication",
            "social_dynamics": "Cooperative hunting benefits with pod size",
            "spatial_correlation": "Geographic preferences and territory effects",
            "temporal_patterns": "Circadian and seasonal behavioral cycles"
        }
    }

@app.get("/health/advanced")
async def advanced_health_check():
    """Detailed health check for physics-informed system"""
    return {
        "status": "healthy",
        "components": {
            "hmc_sampler": physics_ml.hmc_sampler is not None,
            "firebase": db is not None,
            "jax_available": jax.devices() != [],
            "numpyro_available": True
        },
        "physics_model": {
            "priors_loaded": len(physics_ml.physics_priors) > 0,
            "marine_biology_constraints": True,
            "uncertainty_quantification": True
        }
    }

if __name__ == "__main__":
    logger.info("🚀 Starting ORCAST Advanced Physics-Informed ML Service...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8083")),  # Different port for advanced service
        log_level="info"
    ) 