#!/usr/bin/env python3
"""
Train Behavioral ML Models
Uses BigQuery data in the format expected by behavioral_ml_service.py
"""

import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple

from google.cloud import bigquery
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import joblib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BehavioralMLTrainer:
    """Train orca behavioral prediction models"""
    
    def __init__(self, project_id="orca-466204"):
        self.project_id = project_id
        self.client = bigquery.Client(project=project_id)
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        
    def load_training_data(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Load training data from BigQuery in ML service format"""
        
        logger.info("📊 Loading training data from BigQuery...")
        
        # Simplified query to avoid type conflicts
        query = f"""
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
        FROM `{self.project_id}.orca_data.sightings` s
        JOIN `{self.project_id}.orca_data.behavioral_data` b
        ON s.sighting_id = b.sighting_id
        WHERE s.timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 365 DAY)
        AND b.primary_behavior IS NOT NULL
        AND s.water_depth IS NOT NULL
        AND s.tidal_flow IS NOT NULL
        AND s.prey_density IS NOT NULL
        ORDER BY s.timestamp DESC
        """
        
        try:
            # Create job configuration to avoid dtype inference issues
            job_config = bigquery.QueryJobConfig()
            job_config.use_query_cache = True
            
            # Execute query and get results as records first
            query_job = self.client.query(query, job_config=job_config)
            results = query_job.result()
            
            # Convert to list of dictionaries first
            records = [dict(row) for row in results]
            
            if not records:
                raise ValueError("No training data available")
            
            # Create DataFrame from records to avoid type inference
            df = pd.DataFrame(records)
            logger.info(f"✅ Loaded {len(df)} training records")
            
            # Clean data types - handle 'unknown' values and convert to numeric
            logger.info("🧹 Cleaning data types...")
            df['pod_size'] = pd.to_numeric(df['pod_size'], errors='coerce').fillna(1)
            df['water_depth'] = pd.to_numeric(df['water_depth'], errors='coerce').fillna(50)
            df['tidal_flow'] = pd.to_numeric(df['tidal_flow'], errors='coerce').fillna(0)
            df['temperature'] = pd.to_numeric(df['temperature'], errors='coerce').fillna(15)
            df['salinity'] = pd.to_numeric(df['salinity'], errors='coerce').fillna(30)
            df['visibility'] = pd.to_numeric(df['visibility'], errors='coerce').fillna(20)
            df['current_speed'] = pd.to_numeric(df['current_speed'], errors='coerce').fillna(0.5)
            df['noise_level'] = pd.to_numeric(df['noise_level'], errors='coerce').fillna(120)
            df['prey_density'] = pd.to_numeric(df['prey_density'], errors='coerce').fillna(0.5)
            
            # Extract features (same order as ML service expects)
            feature_columns = [
                'latitude', 'longitude', 'pod_size', 'water_depth', 'tidal_flow',
                'temperature', 'salinity', 'visibility', 'current_speed', 
                'noise_level', 'prey_density', 'hour_of_day', 'day_of_year'
            ]
            
            X = df[feature_columns].values
            
            # Handle any remaining missing values
            X = np.nan_to_num(X, nan=0.0)
            
            # Extract labels
            behavior_labels = df['primary_behavior'].fillna('unknown').values
            strategy_labels = df['feeding_strategy'].fillna('unknown').values
            success_labels = df['feeding_success'].fillna(False).values
            
            logger.info(f"📈 Feature matrix shape: {X.shape}")
            logger.info(f"🎯 Behavior distribution:")
            behavior_counts = pd.Series(behavior_labels).value_counts()
            for behavior, count in behavior_counts.items():
                logger.info(f"   • {behavior}: {count} samples")
            
            return X, behavior_labels, strategy_labels, success_labels
            
        except Exception as e:
            logger.error(f"❌ Error loading training data: {e}")
            raise
    
    def train_behavior_classifier(self, X, y):
        """Train primary behavior classifier"""
        
        logger.info("🤖 Training behavior classifier...")
        
        # Encode labels
        self.encoders['behavior'] = LabelEncoder()
        y_encoded = self.encoders['behavior'].fit_transform(y)
        
        # Scale features
        self.scalers['behavior'] = StandardScaler()
        X_scaled = self.scalers['behavior'].fit_transform(X)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
        )
        
        # Train multiple models
        models = {
            'random_forest': RandomForestClassifier(
                n_estimators=100, 
                max_depth=10, 
                random_state=42,
                class_weight='balanced'
            ),
            'gradient_boosting': GradientBoostingClassifier(
                n_estimators=100, 
                learning_rate=0.1, 
                max_depth=6,
                random_state=42
            ),
            'logistic_regression': LogisticRegression(
                max_iter=1000, 
                random_state=42,
                class_weight='balanced'
            )
        }
        
        best_model = None
        best_score = 0
        
        for name, model in models.items():
            # Train model
            model.fit(X_train, y_train)
            
            # Evaluate
            train_score = model.score(X_train, y_train)
            test_score = model.score(X_test, y_test)
            cv_scores = cross_val_score(model, X_scaled, y_encoded, cv=5)
            
            logger.info(f"📊 {name}:")
            logger.info(f"   • Train accuracy: {train_score:.3f}")
            logger.info(f"   • Test accuracy: {test_score:.3f}")
            logger.info(f"   • CV accuracy: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
            
            if cv_scores.mean() > best_score:
                best_score = cv_scores.mean()
                best_model = (name, model)
        
        # Use best model
        model_name, model = best_model
        logger.info(f"🏆 Best model: {model_name} (CV score: {best_score:.3f})")
        
        # Final evaluation
        y_pred = model.predict(X_test)
        logger.info(f"\n📋 Classification Report:")
        logger.info(classification_report(y_test, y_pred, 
                                        target_names=self.encoders['behavior'].classes_))
        
        self.models['behavior'] = model
        
        return model, test_score
    
    def train_feeding_strategy_classifier(self, X, y_behavior, y_strategy):
        """Train feeding strategy classifier (only for feeding behaviors)"""
        
        logger.info("🍽️ Training feeding strategy classifier...")
        
        # Filter for feeding behaviors only
        feeding_mask = y_behavior == 'feeding'
        X_feeding = X[feeding_mask]
        y_strategy_feeding = y_strategy[feeding_mask]
        
        if len(X_feeding) < 10:
            logger.warning("⚠️ Not enough feeding samples for strategy classification")
            return None, 0
        
        # Remove unknown strategies
        known_mask = y_strategy_feeding != 'unknown'
        X_feeding = X_feeding[known_mask]
        y_strategy_feeding = y_strategy_feeding[known_mask]
        
        if len(X_feeding) < 5:
            logger.warning("⚠️ Not enough known feeding strategies")
            return None, 0
        
        # Encode labels
        self.encoders['strategy'] = LabelEncoder()
        y_encoded = self.encoders['strategy'].fit_transform(y_strategy_feeding)
        
        # Scale features (reuse behavior scaler)
        X_scaled = self.scalers['behavior'].transform(X_feeding)
        
        # Train model
        model = RandomForestClassifier(
            n_estimators=50, 
            max_depth=8, 
            random_state=42,
            class_weight='balanced'
        )
        
        if len(np.unique(y_encoded)) < 2:
            logger.warning("⚠️ Only one feeding strategy class available")
            return None, 0
        
        # Split and train
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y_encoded, test_size=0.3, random_state=42
        )
        
        model.fit(X_train, y_train)
        test_score = model.score(X_test, y_test)
        
        logger.info(f"📊 Feeding strategy classifier:")
        logger.info(f"   • Test accuracy: {test_score:.3f}")
        logger.info(f"   • Classes: {list(self.encoders['strategy'].classes_)}")
        
        self.models['strategy'] = model
        
        return model, test_score
    
    def train_feeding_success_classifier(self, X, y_behavior, y_success):
        """Train feeding success predictor"""
        
        logger.info("✅ Training feeding success predictor...")
        
        # Filter for feeding behaviors only
        feeding_mask = y_behavior == 'feeding'
        X_feeding = X[feeding_mask]
        y_success_feeding = y_success[feeding_mask]
        
        if len(X_feeding) < 10:
            logger.warning("⚠️ Not enough feeding samples for success prediction")
            return None, 0
        
        # Scale features
        X_scaled = self.scalers['behavior'].transform(X_feeding)
        
        # Train model
        model = GradientBoostingClassifier(
            n_estimators=50, 
            learning_rate=0.1, 
            max_depth=4,
            random_state=42
        )
        
        # Split and train
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y_success_feeding, test_size=0.3, random_state=42
        )
        
        model.fit(X_train, y_train)
        test_score = model.score(X_test, y_test)
        
        logger.info(f"📊 Feeding success predictor:")
        logger.info(f"   • Test accuracy: {test_score:.3f}")
        
        self.models['success'] = model
        
        return model, test_score
    
    def save_models(self, output_dir="models"):
        """Save trained models and preprocessors"""
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Save models
        for name, model in self.models.items():
            filepath = os.path.join(output_dir, f"{name}_model.joblib")
            joblib.dump(model, filepath)
            logger.info(f"💾 Saved {name} model to {filepath}")
        
        # Save scalers
        for name, scaler in self.scalers.items():
            filepath = os.path.join(output_dir, f"{name}_scaler.joblib")
            joblib.dump(scaler, filepath)
            logger.info(f"💾 Saved {name} scaler to {filepath}")
        
        # Save encoders
        for name, encoder in self.encoders.items():
            filepath = os.path.join(output_dir, f"{name}_encoder.joblib")
            joblib.dump(encoder, filepath)
            logger.info(f"💾 Saved {name} encoder to {filepath}")
        
        # Save model metadata
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'models': list(self.models.keys()),
            'scalers': list(self.scalers.keys()),
            'encoders': list(self.encoders.keys()),
            'classes': {name: encoder.classes_.tolist() 
                       for name, encoder in self.encoders.items()}
        }
        
        metadata_path = os.path.join(output_dir, "model_metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"📋 Saved metadata to {metadata_path}")
    
    def test_prediction_pipeline(self, X, y_behavior):
        """Test the complete prediction pipeline"""
        
        logger.info("🧪 Testing prediction pipeline...")
        
        # Take a few samples
        n_samples = min(5, len(X))
        X_test = X[:n_samples]
        
        for i in range(n_samples):
            features = X_test[i:i+1]
            
            # Scale features
            features_scaled = self.scalers['behavior'].transform(features)
            
            # Predict behavior
            behavior_pred = self.models['behavior'].predict(features_scaled)[0]
            behavior_prob = self.models['behavior'].predict_proba(features_scaled)[0]
            behavior_name = self.encoders['behavior'].inverse_transform([behavior_pred])[0]
            
            logger.info(f"🔍 Sample {i+1}:")
            logger.info(f"   • Predicted behavior: {behavior_name}")
            logger.info(f"   • Confidence: {max(behavior_prob):.3f}")
            
            # If feeding, predict strategy and success
            if behavior_name == 'feeding':
                if 'strategy' in self.models:
                    strategy_pred = self.models['strategy'].predict(features_scaled)[0]
                    strategy_name = self.encoders['strategy'].inverse_transform([strategy_pred])[0]
                    logger.info(f"   • Feeding strategy: {strategy_name}")
                
                if 'success' in self.models:
                    success_pred = self.models['success'].predict(features_scaled)[0]
                    success_prob = self.models['success'].predict_proba(features_scaled)[0]
                    logger.info(f"   • Success probability: {success_prob[1]:.3f}")

def main():
    """Main training pipeline"""
    
    logger.info("🚀 Starting ML training pipeline...")
    
    # Initialize trainer
    trainer = BehavioralMLTrainer()
    
    # Load data
    try:
        X, y_behavior, y_strategy, y_success = trainer.load_training_data()
    except Exception as e:
        logger.error(f"❌ Failed to load data. Make sure to run create_ml_service_schema.py first!")
        logger.error(f"Error: {e}")
        return
    
    # Train models
    behavior_model, behavior_score = trainer.train_behavior_classifier(X, y_behavior)
    strategy_model, strategy_score = trainer.train_feeding_strategy_classifier(X, y_behavior, y_strategy)
    success_model, success_score = trainer.train_feeding_success_classifier(X, y_behavior, y_success)
    
    # Save models
    trainer.save_models()
    
    # Test pipeline
    trainer.test_prediction_pipeline(X, y_behavior)
    
    # Summary
    logger.info("🎉 Training complete!")
    logger.info(f"📊 Model Performance:")
    logger.info(f"   • Behavior classifier: {behavior_score:.3f}")
    if strategy_model:
        logger.info(f"   • Strategy classifier: {strategy_score:.3f}")
    if success_model:
        logger.info(f"   • Success predictor: {success_score:.3f}")
    
    logger.info("✅ Models saved and ready for deployment!")

if __name__ == "__main__":
    main() 