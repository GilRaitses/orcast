#!/usr/bin/env python3
"""
ORCAST SINDy Symbolic Regression Framework
Sparse Identification of Nonlinear Dynamics for Orca Behavioral Equations

This module automatically discovers the mathematical equations governing 
orca behavior directly from data using sparse regression and symbolic mathematics.
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import Lasso, LassoCV
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.pipeline import Pipeline
import sympy as sp
from sympy import symbols, simplify, latex, sin, cos, exp, log
from itertools import combinations_with_replacement
import warnings
warnings.filterwarnings('ignore')

class OrcaSINDyFramework:
    """
    SINDy (Sparse Identification of Nonlinear Dynamics) for Orca Behavior
    
    Automatically discovers sparse, interpretable equations that govern
    orca behavioral dynamics from observational data.
    """
    
    def __init__(self, max_degree=3, threshold=0.01, alpha_candidates=None):
        self.max_degree = max_degree
        self.threshold = threshold
        self.alpha_candidates = alpha_candidates or np.logspace(-6, 2, 100)
        
        # Symbolic variables for environmental features
        self.symbol_map = {
            'latitude': symbols('lat'),
            'longitude': symbols('lng'), 
            'depth': symbols('d'),
            'temperature': symbols('T'),
            'tidal_flow': symbols('tidal'),
            'prey_density': symbols('prey'),
            'noise_level': symbols('noise'),
            'visibility': symbols('vis'),
            'current_speed': symbols('curr'),
            'salinity': symbols('sal'),
            'pod_size': symbols('N'),
            'hour_of_day': symbols('h'),
            'day_of_year': symbols('day')
        }
        
        # Discovered equations
        self.discovered_equations = {}
        self.feature_names = []
        self.coefficients = {}
        
        print("🔬 SINDy Framework initialized for automatic equation discovery")
    
    def create_feature_library(self, X_data, feature_names):
        """
        Create comprehensive nonlinear feature library for SINDy
        """
        
        print(f"🏗️ Building feature library (degree {self.max_degree})...")
        
        # Start with original features
        feature_library = X_data.copy()
        library_names = feature_names.copy()
        
        n_features = X_data.shape[1]
        
        # Add quadratic terms
        if self.max_degree >= 2:
            for i in range(n_features):
                for j in range(i, n_features):
                    if i == j:
                        # Squared terms
                        new_feature = X_data[:, i] ** 2
                        feature_library = np.column_stack([feature_library, new_feature])
                        library_names.append(f"{feature_names[i]}^2")
                    else:
                        # Interaction terms
                        new_feature = X_data[:, i] * X_data[:, j]
                        feature_library = np.column_stack([feature_library, new_feature])
                        library_names.append(f"{feature_names[i]}*{feature_names[j]}")
        
        # Add cubic terms for most important features
        if self.max_degree >= 3:
            for i in range(min(5, n_features)):  # Limit to first 5 features to avoid explosion
                new_feature = X_data[:, i] ** 3
                feature_library = np.column_stack([feature_library, new_feature])
                library_names.append(f"{feature_names[i]}^3")
        
        # Add trigonometric terms for temporal features
        temporal_indices = [i for i, name in enumerate(feature_names) 
                          if 'hour' in name or 'day' in name]
        
        for idx in temporal_indices:
            # Sine and cosine for periodic patterns
            if 'hour' in feature_names[idx]:
                period = 24
            else:
                period = 365
                
            sin_features = np.sin(2 * np.pi * X_data[:, idx] / period)
            cos_features = np.cos(2 * np.pi * X_data[:, idx] / period)
            
            feature_library = np.column_stack([feature_library, sin_features, cos_features])
            library_names.extend([f'sin({feature_names[idx]})', f'cos({feature_names[idx]})'])
        
        # Add exponential terms for key environmental variables
        env_indices = [i for i, name in enumerate(feature_names)
                      if any(env in name for env in ['depth', 'temperature', 'prey_density'])]
        
        for idx in env_indices:
            # Normalized exponential terms
            normalized_data = X_data[:, idx] / (np.std(X_data[:, idx]) + 1e-8)
            exp_features = np.exp(-np.abs(normalized_data))
            
            feature_library = np.column_stack([feature_library, exp_features])
            library_names.append(f'exp(-|{feature_names[idx]}|)')
        
        print(f"✅ Feature library created: {feature_library.shape[1]} candidate terms")
        
        return feature_library, library_names
    
    def sparse_regression(self, feature_library, y_data, library_names):
        """
        Perform sparse regression to identify active terms
        """
        
        print("🎯 Performing sparse regression...")
        
        # Handle NaN and infinite values
        finite_mask = np.isfinite(feature_library).all(axis=1) & np.isfinite(y_data)
        feature_library_clean = feature_library[finite_mask]
        y_data_clean = y_data[finite_mask]
        
        # Standardize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(feature_library_clean)
        
        # Remove features with zero variance
        nonzero_var = np.var(X_scaled, axis=0) > 1e-10
        X_scaled = X_scaled[:, nonzero_var]
        filtered_names = [library_names[i] for i in range(len(library_names)) if nonzero_var[i]]
        
        # Lasso with cross-validation
        lasso_cv = LassoCV(alphas=self.alpha_candidates, cv=5, max_iter=2000, random_state=42)
        lasso_cv.fit(X_scaled, y_data_clean)
        
        # Get coefficients
        coefficients = lasso_cv.coef_
        alpha_optimal = lasso_cv.alpha_
        
        # Apply threshold
        active_indices = np.abs(coefficients) > self.threshold
        active_coefficients = coefficients[active_indices]
        active_features = [filtered_names[i] for i in range(len(filtered_names)) if active_indices[i]]
        
        # Transform coefficients back to original scale
        if len(active_coefficients) > 0:
            feature_scales = scaler.scale_[nonzero_var][active_indices]
            original_coefficients = active_coefficients / feature_scales
        else:
            original_coefficients = np.array([])
        
        print(f"✅ Sparse regression complete:")
        print(f"   • Optimal α: {alpha_optimal:.6f}")
        print(f"   • Active terms: {len(active_features)}/{len(filtered_names)}")
        if len(filtered_names) > 0:
            print(f"   • Sparsity: {(1 - len(active_features)/len(filtered_names))*100:.1f}%")
        
        return active_features, original_coefficients, alpha_optimal
    
    def construct_symbolic_equation(self, feature_names, coefficients, equation_name):
        """
        Construct symbolic equation from discovered terms and coefficients
        """
        
        print(f"🔣 Constructing symbolic equation for {equation_name}...")
        
        if len(feature_names) == 0:
            print(f"⚠️ No active terms found for {equation_name}")
            return symbols('0')
        
        # Build symbolic expression
        equation_terms = []
        
        for feature_name, coeff in zip(feature_names, coefficients):
            # Convert coefficient to float to avoid numpy type issues
            coeff_val = float(coeff)
            
            # Parse feature name to create symbolic term
            symbolic_term = self.parse_feature_to_symbol(feature_name, coeff_val)
            equation_terms.append(symbolic_term)
        
        # Sum all terms
        equation = sum(equation_terms) if equation_terms else symbols('0')
        
        # Simplify the equation
        try:
            simplified_equation = simplify(equation)
        except:
            simplified_equation = equation
        
        print(f"✅ Discovered equation for {equation_name}:")
        print(f"   {simplified_equation}")
        
        return simplified_equation
    
    def parse_feature_to_symbol(self, feature_name, coefficient):
        """
        Convert feature name string to symbolic expression
        """
        
        # Map common feature names to symbols
        base_symbol_mapping = {
            'latitude': self.symbol_map['latitude'],
            'longitude': self.symbol_map['longitude'],
            'depth': self.symbol_map['depth'],
            'temperature': self.symbol_map['temperature'],
            'tidal_flow': self.symbol_map['tidal_flow'],
            'prey_density': self.symbol_map['prey_density'],
            'noise_level': self.symbol_map['noise_level'],
            'visibility': self.symbol_map['visibility'],
            'current_speed': self.symbol_map['current_speed'],
            'salinity': self.symbol_map['salinity'],
            'pod_size': self.symbol_map['pod_size'],
            'hour_of_day': self.symbol_map['hour_of_day'],
            'day_of_year': self.symbol_map['day_of_year']
        }
        
        # Handle basic features
        if feature_name in base_symbol_mapping:
            return coefficient * base_symbol_mapping[feature_name]
        
        # Handle squared terms like "depth^2"
        if '^2' in feature_name:
            base_name = feature_name.replace('^2', '')
            if base_name in base_symbol_mapping:
                return coefficient * (base_symbol_mapping[base_name] ** 2)
        
        # Handle cubic terms like "depth^3"
        if '^3' in feature_name:
            base_name = feature_name.replace('^3', '')
            if base_name in base_symbol_mapping:
                return coefficient * (base_symbol_mapping[base_name] ** 3)
        
        # Handle interaction terms like "depth*temperature"
        if '*' in feature_name:
            terms = feature_name.split('*')
            symbolic_product = 1
            for term in terms:
                term = term.strip()
                if term in base_symbol_mapping:
                    symbolic_product *= base_symbol_mapping[term]
                else:
                    symbolic_product *= symbols(term)
            return coefficient * symbolic_product
        
        # Handle trigonometric terms
        if feature_name.startswith('sin(') and feature_name.endswith(')'):
            inner = feature_name[4:-1]  # Remove 'sin(' and ')'
            if inner in base_symbol_mapping:
                return coefficient * sin(base_symbol_mapping[inner])
            else:
                return coefficient * sin(symbols(inner))
        
        if feature_name.startswith('cos(') and feature_name.endswith(')'):
            inner = feature_name[4:-1]  # Remove 'cos(' and ')'
            if inner in base_symbol_mapping:
                return coefficient * cos(base_symbol_mapping[inner])
            else:
                return coefficient * cos(symbols(inner))
        
        # Handle exponential terms
        if feature_name.startswith('exp(') and feature_name.endswith(')'):
            inner = feature_name[4:-1]  # Remove 'exp(' and ')'
            if inner.startswith('-|') and inner.endswith('|'):
                var_name = inner[2:-1]  # Remove '-|' and '|'
                if var_name in base_symbol_mapping:
                    return coefficient * exp(-sp.Abs(base_symbol_mapping[var_name]))
                else:
                    return coefficient * exp(-sp.Abs(symbols(var_name)))
        
        # Default: create new symbol for unrecognized terms
        clean_name = feature_name.replace(' ', '_').replace('-', '_')
        return coefficient * symbols(clean_name)
    
    def discover_behavioral_equations(self, sighting_data, behavioral_outcomes):
        """
        Main method to discover orca behavioral equations from data
        """
        
        print("🌊 Discovering Orca Behavioral Equations with SINDy...")
        print("=" * 60)
        
        # Define feature names
        feature_names = [
            'latitude', 'longitude', 'depth', 'temperature', 'tidal_flow',
            'prey_density', 'noise_level', 'visibility', 'current_speed',
            'salinity', 'pod_size', 'hour_of_day', 'day_of_year'
        ]
        
        # Create comprehensive feature library
        feature_library, library_names = self.create_feature_library(sighting_data, feature_names)
        
        # Discover equations for each behavioral outcome
        discovered_equations = {}
        
        if behavioral_outcomes.ndim == 1:
            # Single behavioral outcome
            active_features, coefficients, alpha = self.sparse_regression(
                feature_library, behavioral_outcomes, library_names
            )
            
            equation = self.construct_symbolic_equation(
                active_features, coefficients, "orca_behavior"
            )
            
            discovered_equations["orca_behavior"] = {
                'equation': equation,
                'features': active_features,
                'coefficients': coefficients,
                'alpha': alpha,
                'latex': latex(equation)
            }
        
        else:
            # Multiple behavioral outcomes
            behavior_names = ['feeding', 'socializing', 'traveling', 'resting']
            
            for i, behavior_name in enumerate(behavior_names[:behavioral_outcomes.shape[1]]):
                print(f"\n🔍 Discovering equation for {behavior_name} behavior...")
                
                active_features, coefficients, alpha = self.sparse_regression(
                    feature_library, behavioral_outcomes[:, i], library_names
                )
                
                equation = self.construct_symbolic_equation(
                    active_features, coefficients, behavior_name
                )
                
                discovered_equations[behavior_name] = {
                    'equation': equation,
                    'features': active_features,
                    'coefficients': coefficients,
                    'alpha': alpha,
                    'latex': latex(equation)
                }
        
        self.discovered_equations = discovered_equations
        
        print("\n🎉 SINDy Equation Discovery Complete!")
        print("=" * 60)
        
        return discovered_equations
    
    def generate_interpretable_report(self):
        """
        Generate human-readable report of discovered equations
        """
        
        report = """
# 🐋 ORCAST SINDy Discovered Equations Report

## Automatically Discovered Orca Behavioral Dynamics

This report contains the mathematical equations governing orca behavior 
that were automatically discovered from observational data using SINDy 
(Sparse Identification of Nonlinear Dynamics).

"""
        
        for behavior_name, equation_data in self.discovered_equations.items():
            report += f"""
### {behavior_name.title()} Behavior Equation

**Discovered Mathematical Law:**
```
{equation_data['equation']}
```

**LaTeX Format:**
```latex
{equation_data['latex']}
```

**Key Factors ({len(equation_data['features'])} terms):**
"""
            
            # Sort features by coefficient magnitude
            if len(equation_data['coefficients']) > 0:
                feature_importance = list(zip(equation_data['features'], 
                                            np.abs(equation_data['coefficients'])))
                feature_importance.sort(key=lambda x: x[1], reverse=True)
                
                for feature, importance in feature_importance[:5]:  # Top 5 factors
                    report += f"- {feature}: {importance:.4f}\n"
            
            report += f"\n**Sparsity Level:** {equation_data['alpha']:.6f}\n"
            report += f"**Equation Complexity:** {len(equation_data['features'])} active terms\n\n"
        
        report += """
## Biological Interpretation

These equations reveal the fundamental mathematical relationships that 
govern orca behavior in their natural environment. Unlike hand-coded 
models, these equations were discovered directly from data and represent 
the actual underlying dynamics of orca decision-making.

### Key Insights:
- **Sparsity**: Only a few environmental factors truly drive each behavior
- **Nonlinearity**: Complex interactions between environmental variables
- **Interpretability**: Each term has clear biological meaning
- **Predictive Power**: Equations can forecast behavior in new conditions

## Applications:
- **Conservation Planning**: Understand critical environmental thresholds
- **Climate Impact Assessment**: Predict behavioral changes under new conditions  
- **Marine Protected Area Design**: Optimize protection based on behavioral drivers
- **Real-time Forecasting**: Use equations for live behavioral prediction

---
*Generated by ORCAST SINDy Framework - Automatic Equation Discovery*
"""
        
        return report

def test_sindy_framework():
    """
    Test the SINDy framework with synthetic orca behavioral data
    """
    
    print("🧪 Testing SINDy Framework with Synthetic Orca Data")
    print("=" * 60)
    
    # Generate synthetic environmental data
    np.random.seed(42)
    n_samples = 500
    
    # Environmental features
    latitude = np.random.uniform(48.4, 48.8, n_samples)
    longitude = np.random.uniform(-123.3, -122.8, n_samples)
    depth = np.random.uniform(10, 200, n_samples)
    temperature = np.random.uniform(8, 18, n_samples)
    tidal_flow = np.random.uniform(-1, 1, n_samples)
    prey_density = np.random.uniform(0, 1, n_samples)
    noise_level = np.random.uniform(80, 140, n_samples)
    visibility = np.random.uniform(5, 30, n_samples)
    current_speed = np.random.uniform(0, 2, n_samples)
    salinity = np.random.uniform(28, 32, n_samples)
    pod_size = np.random.randint(1, 15, n_samples)
    hour_of_day = np.random.randint(0, 24, n_samples)
    day_of_year = np.random.randint(1, 366, n_samples)
    
    X = np.column_stack([
        latitude, longitude, depth, temperature, tidal_flow,
        prey_density, noise_level, visibility, current_speed,
        salinity, pod_size, hour_of_day, day_of_year
    ])
    
    # Generate synthetic behavioral outcomes with known relationships
    # Feeding: depends on prey density, depth, and temperature
    feeding_prob = (
        0.7 * prey_density +
        0.3 * np.exp(-(depth - 50)**2 / 1000) +
        0.2 * np.exp(-(temperature - 15)**2 / 10) +
        0.1 * np.sin(2 * np.pi * hour_of_day / 24) +
        0.1 * np.random.normal(0, 0.1, n_samples)
    )
    
    # Socializing: depends on pod size and time of day
    socializing_prob = (
        0.5 * np.log(pod_size + 1) / np.log(15) +
        0.3 * np.sin(2 * np.pi * hour_of_day / 24 + np.pi/4) +
        0.2 * np.random.normal(0, 0.1, n_samples)
    )
    
    # Traveling: depends on current speed and tidal flow
    traveling_prob = (
        0.4 * current_speed +
        0.3 * np.abs(tidal_flow) +
        0.3 * np.random.normal(0, 0.1, n_samples)
    )
    
    # Normalize probabilities
    feeding_prob = np.clip(feeding_prob, 0, 1)
    socializing_prob = np.clip(socializing_prob, 0, 1)
    traveling_prob = np.clip(traveling_prob, 0, 1)
    
    y = np.column_stack([feeding_prob, socializing_prob, traveling_prob])
    
    # Initialize SINDy framework
    sindy = OrcaSINDyFramework(max_degree=2, threshold=0.01)
    
    # Discover equations
    equations = sindy.discover_behavioral_equations(X, y)
    
    # Generate report
    report = sindy.generate_interpretable_report()
    
    print("\n" + "="*60)
    print("📊 DISCOVERED EQUATIONS SUMMARY:")
    print("="*60)
    
    for behavior, eq_data in equations.items():
        print(f"\n🐋 {behavior.upper()} BEHAVIOR:")
        print(f"   Equation: {eq_data['equation']}")
        print(f"   Active terms: {len(eq_data['features'])}")
        if len(eq_data['features']) > 0:
            print(f"   Key factors: {eq_data['features'][:3]}")
    
    return sindy, equations, report

if __name__ == "__main__":
    # Run the test
    sindy_framework, discovered_equations, interpretation_report = test_sindy_framework()
    
    # Save report
    with open('orcast_sindy_discovered_equations.md', 'w') as f:
        f.write(interpretation_report)
    
    print("\n✅ SINDy test complete! Check 'orcast_sindy_discovered_equations.md' for full report.") 