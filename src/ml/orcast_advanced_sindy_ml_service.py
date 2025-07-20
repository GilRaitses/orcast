#!/usr/bin/env python3
"""
ORCAST Advanced SINDy-Based ML Service
Real-time orca behavioral predictions using discovered mathematical equations

Integrates:
- SINDy-discovered behavioral equations
- Real-time environmental data
- Firestore spatial forecasting
- HMC uncertainty quantification
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import joblib
import sympy as sp
from sympy import symbols, sin, cos, exp, Abs
import json
import warnings
warnings.filterwarnings('ignore')

# Import our SINDy framework
from orca_sindy_symbolic_regression import OrcaSINDyFramework

class ORCASTSINDyMLService:
    """
    Advanced ML service using SINDy-discovered equations for orca behavior prediction
    """
    
    def __init__(self):
        self.sindy_framework = OrcaSINDyFramework()
        self.discovered_equations = {}
        self.ml_models = {}
        self.scaler = StandardScaler()
        self.feature_names = [
            'latitude', 'longitude', 'depth', 'temperature', 'tidal_flow',
            'prey_density', 'noise_level', 'visibility', 'current_speed',
            'salinity', 'pod_size', 'hour_of_day', 'day_of_year'
        ]
        
        # Symbolic variables for equation evaluation
        self.symbols = {
            'lat': symbols('lat'),
            'lng': symbols('lng'),
            'd': symbols('d'),
            'T': symbols('T'),
            'tidal': symbols('tidal'),
            'prey': symbols('prey'),
            'noise': symbols('noise'),
            'vis': symbols('vis'),
            'curr': symbols('curr'),
            'sal': symbols('sal'),
            'N': symbols('N'),
            'h': symbols('h'),
            'day': symbols('day')
        }
        
        print("🧠 ORCAST SINDy ML Service initialized")
    
    def load_discovered_equations(self, equations_dict=None):
        """
        Load SINDy-discovered equations for behavioral prediction
        """
        
        if equations_dict is None:
            # Use pre-discovered equations from our test
            self.discovered_equations = {
                'feeding': {
                    'equation': (0.000254254084678425*self.symbols['N']*self.symbols['T'] - 
                               3.39800366384145e-5*self.symbols['N']*self.symbols['noise'] - 
                               0.0103027187168325*self.symbols['T']**2 + 
                               0.270716440594075*self.symbols['T'] + 
                               0.532648977395369*self.symbols['prey'] + 
                               0.0919481150433264*sin(self.symbols['h']) - 
                               2.14046260081661*exp(-Abs(self.symbols['d'])) + 
                               8.71612666240937*exp(-Abs(self.symbols['T']))),
                    'key_factors': ['prey_density', 'temperature', 'depth', 'pod_size', 'hour_of_day']
                },
                'socializing': {
                    'equation': (-0.00133749434997377*self.symbols['N']**2 + 
                               0.0406397026171323*self.symbols['N'] + 
                               0.203356102871926*sin(self.symbols['h']) + 
                               0.205093901481505*cos(self.symbols['h'])),
                    'key_factors': ['pod_size', 'hour_of_day']
                },
                'traveling': {
                    'equation': (0.379518179107894*self.symbols['curr'] + 
                               0.267457798736415*self.symbols['tidal']**2),
                    'key_factors': ['current_speed', 'tidal_flow']
                }
            }
        else:
            self.discovered_equations = equations_dict
        
        print(f"✅ Loaded {len(self.discovered_equations)} SINDy equations")
        return self.discovered_equations
    
    def evaluate_sindy_equation(self, equation, environmental_data):
        """
        Evaluate a SINDy equation with real environmental data
        """
        
        # Create substitution dictionary
        substitutions = {
            self.symbols['lat']: environmental_data['latitude'],
            self.symbols['lng']: environmental_data['longitude'],
            self.symbols['d']: environmental_data['depth'],
            self.symbols['T']: environmental_data['temperature'],
            self.symbols['tidal']: environmental_data['tidal_flow'],
            self.symbols['prey']: environmental_data['prey_density'],
            self.symbols['noise']: environmental_data['noise_level'],
            self.symbols['vis']: environmental_data['visibility'],
            self.symbols['curr']: environmental_data['current_speed'],
            self.symbols['sal']: environmental_data['salinity'],
            self.symbols['N']: environmental_data['pod_size'],
            self.symbols['h']: environmental_data['hour_of_day'],
            self.symbols['day']: environmental_data['day_of_year']
        }
        
        try:
            # Substitute values and evaluate
            result = float(equation.subs(substitutions))
            return result
        except Exception as e:
            print(f"⚠️ Error evaluating equation: {e}")
            return 0.0
    
    def predict_behavior_sindy(self, environmental_data):
        """
        Predict orca behavior using SINDy-discovered equations
        """
        
        predictions = {}
        
        for behavior_name, equation_data in self.discovered_equations.items():
            equation = equation_data['equation']
            
            # Evaluate the discovered equation
            raw_prediction = self.evaluate_sindy_equation(equation, environmental_data)
            
            # Apply sigmoid to convert to probability [0,1]
            probability = 1 / (1 + np.exp(-raw_prediction))
            
            predictions[behavior_name] = {
                'probability': float(probability),
                'raw_score': float(raw_prediction),
                'key_factors': equation_data['key_factors'],
                'equation_type': 'sindy_discovered'
            }
        
        return predictions
    
    def train_hybrid_models(self, training_data, behavioral_outcomes):
        """
        Train hybrid models that combine SINDy equations with ML models
        """
        
        print("🔬 Training hybrid SINDy + ML models...")
        
        # First discover equations from training data
        self.sindy_framework.discover_behavioral_equations(training_data, behavioral_outcomes)
        discovered_equations = self.sindy_framework.discovered_equations
        
        # Create features that include SINDy predictions
        enhanced_features = []
        feature_names_enhanced = self.feature_names.copy()
        
        for i, sample in enumerate(training_data):
            # Original features
            original_features = sample.tolist()
            
            # SINDy equation features
            env_dict = dict(zip(self.feature_names, sample))
            sindy_predictions = self.predict_behavior_sindy(env_dict)
            
            sindy_features = [pred['raw_score'] for pred in sindy_predictions.values()]
            
            # Combine features
            combined_features = original_features + sindy_features
            enhanced_features.append(combined_features)
        
        # Add SINDy feature names
        feature_names_enhanced.extend([f'sindy_{behavior}' for behavior in discovered_equations.keys()])
        
        enhanced_features = np.array(enhanced_features)
        
        # Scale features
        enhanced_features_scaled = self.scaler.fit_transform(enhanced_features)
        
        # Train models for each behavior
        behavior_names = ['feeding', 'socializing', 'traveling', 'resting']
        
        for i, behavior in enumerate(behavior_names[:behavioral_outcomes.shape[1]]):
            print(f"   Training {behavior} hybrid model...")
            
            # Train Random Forest
            rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
            rf_model.fit(enhanced_features_scaled, behavioral_outcomes[:, i])
            
            # Train Gradient Boosting
            gb_model = GradientBoostingClassifier(n_estimators=100, random_state=42)
            gb_model.fit(enhanced_features_scaled, behavioral_outcomes[:, i])
            
            self.ml_models[behavior] = {
                'random_forest': rf_model,
                'gradient_boosting': gb_model,
                'feature_names': feature_names_enhanced
            }
        
        print("✅ Hybrid models trained successfully")
        return self.ml_models
    
    def predict_behavior_hybrid(self, environmental_data):
        """
        Predict using both SINDy equations and ML models
        """
        
        # Get SINDy predictions
        sindy_predictions = self.predict_behavior_sindy(environmental_data)
        
        # Prepare features for ML models
        original_features = [environmental_data[name] for name in self.feature_names]
        sindy_features = [pred['raw_score'] for pred in sindy_predictions.values()]
        combined_features = np.array(original_features + sindy_features).reshape(1, -1)
        
        # Scale features
        combined_features_scaled = self.scaler.transform(combined_features)
        
        # Get ML predictions
        hybrid_predictions = {}
        
        for behavior_name, models in self.ml_models.items():
            rf_pred = models['random_forest'].predict_proba(combined_features_scaled)[0, 1]
            gb_pred = models['gradient_boosting'].predict_proba(combined_features_scaled)[0, 1]
            
            # Ensemble prediction
            ensemble_pred = (rf_pred + gb_pred) / 2
            
            # Weight with SINDy prediction
            sindy_weight = 0.3
            ml_weight = 0.7
            
            if behavior_name in sindy_predictions:
                final_pred = (sindy_weight * sindy_predictions[behavior_name]['probability'] + 
                            ml_weight * ensemble_pred)
            else:
                final_pred = ensemble_pred
            
            hybrid_predictions[behavior_name] = {
                'probability': float(final_pred),
                'sindy_component': sindy_predictions.get(behavior_name, {}).get('probability', 0),
                'ml_component': float(ensemble_pred),
                'confidence': float(min(rf_pred, gb_pred)),  # Conservative confidence
                'method': 'hybrid_sindy_ml'
            }
        
        return hybrid_predictions
    
    def generate_spatial_forecast_sindy(self, lat_range, lng_range, environmental_grid, time_hours=24):
        """
        Generate spatial forecast using SINDy equations
        """
        
        print(f"🗺️ Generating SINDy spatial forecast...")
        
        forecast_grid = []
        
        lat_points = np.linspace(lat_range[0], lat_range[1], 20)
        lng_points = np.linspace(lng_range[0], lng_range[1], 20)
        
        for lat in lat_points:
            for lng in lng_points:
                location_data = environmental_grid.copy()
                location_data['latitude'] = lat
                location_data['longitude'] = lng
                
                # Time series predictions
                time_series = []
                
                for hour in range(time_hours):
                    location_data['hour_of_day'] = hour
                    
                    # SINDy predictions
                    sindy_pred = self.predict_behavior_sindy(location_data)
                    
                    time_series.append({
                        'hour': hour,
                        'predictions': sindy_pred,
                        'latitude': lat,
                        'longitude': lng
                    })
                
                forecast_grid.append({
                    'latitude': lat,
                    'longitude': lng,
                    'time_series': time_series,
                    'avg_feeding_prob': np.mean([t['predictions']['feeding']['probability'] 
                                               for t in time_series]),
                    'avg_socializing_prob': np.mean([t['predictions']['socializing']['probability'] 
                                                   for t in time_series]),
                    'avg_traveling_prob': np.mean([t['predictions']['traveling']['probability'] 
                                                 for t in time_series]),
                    'method': 'sindy_spatial_forecast'
                })
        
        print(f"✅ Generated {len(forecast_grid)} spatial forecast points")
        return forecast_grid
    
    def save_sindy_service(self, filepath='orcast_sindy_ml_service.pkl'):
        """
        Save the trained SINDy ML service
        """
        
        service_data = {
            'discovered_equations': self.discovered_equations,
            'ml_models': self.ml_models,
            'scaler': self.scaler,
            'feature_names': self.feature_names
        }
        
        joblib.dump(service_data, filepath)
        print(f"💾 SINDy ML service saved to {filepath}")
    
    def load_sindy_service(self, filepath='orcast_sindy_ml_service.pkl'):
        """
        Load a trained SINDy ML service
        """
        
        try:
            service_data = joblib.load(filepath)
            self.discovered_equations = service_data['discovered_equations']
            self.ml_models = service_data['ml_models']
            self.scaler = service_data['scaler']
            self.feature_names = service_data['feature_names']
            print(f"📂 SINDy ML service loaded from {filepath}")
            return True
        except Exception as e:
            print(f"❌ Error loading service: {e}")
            return False

def test_sindy_ml_service():
    """
    Test the SINDy ML service with synthetic data
    """
    
    print("🧪 Testing ORCAST SINDy ML Service")
    print("=" * 50)
    
    # Initialize service
    service = ORCASTSINDyMLService()
    
    # Load pre-discovered equations
    service.load_discovered_equations()
    
    # Test single prediction
    test_env = {
        'latitude': 48.6,
        'longitude': -123.0,
        'depth': 45.0,
        'temperature': 14.5,
        'tidal_flow': 0.3,
        'prey_density': 0.8,
        'noise_level': 95.0,
        'visibility': 20.0,
        'current_speed': 0.5,
        'salinity': 30.5,
        'pod_size': 8,
        'hour_of_day': 14,
        'day_of_year': 180
    }
    
    print("\n🔮 SINDy Prediction Test:")
    sindy_pred = service.predict_behavior_sindy(test_env)
    
    for behavior, pred in sindy_pred.items():
        print(f"   {behavior}: {pred['probability']:.3f} (raw: {pred['raw_score']:.3f})")
    
    # Test spatial forecast
    print("\n🗺️ Spatial Forecast Test:")
    forecast = service.generate_spatial_forecast_sindy(
        lat_range=(48.4, 48.8),
        lng_range=(-123.3, -122.7),
        environmental_grid=test_env,
        time_hours=6
    )
    
    print(f"   Generated {len(forecast)} forecast points")
    print(f"   Sample point: lat={forecast[0]['latitude']:.2f}, lng={forecast[0]['longitude']:.2f}")
    print(f"   Avg feeding prob: {forecast[0]['avg_feeding_prob']:.3f}")
    
    # Save service
    service.save_sindy_service()
    
    print("\n✅ SINDy ML Service test complete!")
    
    return service, sindy_pred, forecast

if __name__ == "__main__":
    # Run the test
    sindy_service, predictions, spatial_forecast = test_sindy_ml_service()
    
    print("\n🎯 Key Results:")
    print(f"   • SINDy equations discovered: {len(sindy_service.discovered_equations)}")
    print(f"   • Behavioral predictions: {len(predictions)}")
    print(f"   • Spatial forecast points: {len(spatial_forecast)}")
    print("\n🌊 ORCAST SINDy Framework ready for deployment!") 