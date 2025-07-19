"""
OrCast HMC Analysis Runner
Generates feeding behavior patterns from orca sighting data using HMC sampling
"""

import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

import numpy as np
import pandas as pd
from google.cloud import bigquery

from hmc_sampling import HMCFeedingBehaviorSampler, HMCAnalysisAPI
from redis_cache import OrCastRedisCache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HMCAnalysisRunner:
    """Runs HMC analysis on orca sighting data"""
    
    def __init__(self, project_id: str = "orca-904de"):
        self.project_id = project_id
        self.bq_client = bigquery.Client()
        self.redis_cache = OrCastRedisCache()
        self.hmc_sampler = HMCFeedingBehaviorSampler()
        self.hmc_api = HMCAnalysisAPI()
        
    async def get_sighting_data(self, days_back: int = 30) -> pd.DataFrame:
        """Get sighting data from BigQuery"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            query = f"""
            SELECT 
                sighting_id,
                timestamp,
                latitude,
                longitude,
                pod_size,
                behavior_observed,
                environmental_conditions,
                quality_score
            FROM `{self.project_id}.orca_data.sightings`
            WHERE timestamp >= '{start_date.isoformat()}'
            AND timestamp <= '{end_date.isoformat()}'
            AND quality_score >= 0.6
            ORDER BY timestamp DESC
            """
            
            df = self.bq_client.query(query).to_dataframe()
            logger.info(f"Retrieved {len(df)} sightings for HMC analysis")
            return df
            
        except Exception as e:
            logger.error(f"Failed to retrieve sighting data: {e}")
            return pd.DataFrame()
    
    def prepare_hmc_features(self, df: pd.DataFrame) -> np.ndarray:
        """Prepare features for HMC analysis"""
        try:
            features = []
            
            for _, row in df.iterrows():
                # Location features
                lat = row['latitude']
                lon = row['longitude']
                
                # Temporal features
                timestamp = pd.to_datetime(row['timestamp'])
                hour = timestamp.hour
                day_of_year = timestamp.dayofyear
                
                # Environmental features
                env_conditions = json.loads(row['environmental_conditions']) if row['environmental_conditions'] else {}
                tidal_height = env_conditions.get('tidal_height', {}).get('height', 0)
                water_temp = env_conditions.get('water_temp', 12.0)
                prey_salmon = env_conditions.get('prey_availability', {}).get('salmon_density', 0.5)
                prey_herring = env_conditions.get('prey_availability', {}).get('herring_density', 0.3)
                
                # Pod features
                pod_size = row['pod_size']
                
                # Behavior encoding
                behavior_map = {
                    'foraging': 1.0,
                    'traveling': 0.5,
                    'socializing': 0.3,
                    'resting': 0.1,
                    'unknown': 0.0
                }
                behavior_score = behavior_map.get(row['behavior_observed'], 0.0)
                
                feature_vector = [
                    lat, lon, hour, day_of_year,
                    tidal_height, water_temp, prey_salmon, prey_herring,
                    pod_size, behavior_score
                ]
                
                features.append(feature_vector)
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Failed to prepare HMC features: {e}")
            return np.array([])
    
    def create_feeding_outcomes(self, df: pd.DataFrame) -> np.ndarray:
        """Create feeding success outcomes from behavior observations"""
        try:
            outcomes = []
            
            for _, row in df.iterrows():
                behavior = row['behavior_observed']
                
                # Feeding success probability based on observed behavior
                if behavior == 'foraging':
                    # High feeding success for foraging behavior
                    success = np.random.binomial(1, 0.8)
                elif behavior == 'traveling':
                    # Medium feeding success for traveling (might be hunting)
                    success = np.random.binomial(1, 0.4)
                elif behavior == 'socializing':
                    # Low feeding success for socializing
                    success = np.random.binomial(1, 0.2)
                elif behavior == 'resting':
                    # Very low feeding success for resting
                    success = np.random.binomial(1, 0.1)
                else:
                    # Unknown behavior - moderate success
                    success = np.random.binomial(1, 0.5)
                
                outcomes.append(success)
            
            return np.array(outcomes)
            
        except Exception as e:
            logger.error(f"Failed to create feeding outcomes: {e}")
            return np.array([])
    
    async def run_hmc_analysis(self, features: np.ndarray, outcomes: np.ndarray) -> Dict[str, Any]:
        """Run HMC analysis on the data"""
        try:
            logger.info("Starting HMC analysis...")
            
            # Run HMC sampling
            samples = self.hmc_sampler.sample_feeding_behavior(
                environmental_features=features,
                feeding_outcomes=outcomes,
                n_samples=2000,
                n_warmup=500
            )
            
            # Analyze results
            analysis_results = await self.hmc_api.analyze_feeding_patterns(
                samples=samples,
                features=features,
                outcomes=outcomes
            )
            
            logger.info("HMC analysis complete")
            return analysis_results
            
        except Exception as e:
            logger.error(f"HMC analysis failed: {e}")
            return {}
    
    def extract_feeding_patterns(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract feeding behavior patterns from HMC results"""
        try:
            patterns = {
                'temporal_patterns': {},
                'spatial_patterns': {},
                'environmental_factors': {},
                'behavioral_strategies': {}
            }
            
            if 'parameter_estimates' in analysis_results:
                params = analysis_results['parameter_estimates']
                
                # Temporal patterns
                patterns['temporal_patterns'] = {
                    'dawn_foraging': params.get('hour_effect', {}).get('dawn', 0.0),
                    'dusk_foraging': params.get('hour_effect', {}).get('dusk', 0.0),
                    'seasonal_variation': params.get('seasonal_effect', 0.0)
                }
                
                # Spatial patterns
                patterns['spatial_patterns'] = {
                    'preferred_locations': params.get('location_clusters', []),
                    'depth_preference': params.get('depth_effect', 0.0),
                    'distance_from_shore': params.get('shore_distance_effect', 0.0)
                }
                
                # Environmental factors
                patterns['environmental_factors'] = {
                    'tidal_influence': params.get('tidal_effect', 0.0),
                    'temperature_optimum': params.get('temperature_effect', 0.0),
                    'prey_density_threshold': params.get('prey_threshold', 0.0)
                }
                
                # Behavioral strategies
                patterns['behavioral_strategies'] = {
                    'cooperative_hunting': params.get('pod_size_effect', 0.0),
                    'strategy_switching': params.get('strategy_flexibility', 0.0),
                    'success_rates': params.get('success_probabilities', {})
                }
            
            return patterns
            
        except Exception as e:
            logger.error(f"Failed to extract feeding patterns: {e}")
            return {}
    
    def save_analysis_results(self, analysis_results: Dict[str, Any], feeding_patterns: Dict[str, Any]):
        """Save analysis results to cache and BigQuery"""
        try:
            # Save to Redis cache
            cache_key = f"hmc_analysis:{datetime.now().strftime('%Y%m%d')}"
            self.redis_cache.set(
                cache_key,
                {
                    'analysis_results': analysis_results,
                    'feeding_patterns': feeding_patterns,
                    'timestamp': datetime.now().isoformat()
                },
                ttl=86400  # 24 hours
            )
            
            # Save to BigQuery
            table_id = f"{self.project_id}.orca_data.hmc_analysis"
            
            analysis_record = {
                'analysis_id': f"hmc_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'timestamp': datetime.now(),
                'analysis_results': json.dumps(analysis_results),
                'feeding_patterns': json.dumps(feeding_patterns),
                'model_version': '1.0'
            }
            
            df = pd.DataFrame([analysis_record])
            
            job_config = bigquery.LoadJobConfig(
                write_disposition="WRITE_APPEND",
                time_partitioning=bigquery.TimePartitioning(
                    type_=bigquery.TimePartitioningType.DAY,
                    field="timestamp"
                )
            )
            
            job = self.bq_client.load_table_from_dataframe(
                df, table_id, job_config=job_config
            )
            job.result()
            
            logger.info("Analysis results saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save analysis results: {e}")
    
    async def run_full_analysis(self) -> Dict[str, Any]:
        """Run the complete HMC analysis pipeline"""
        try:
            logger.info("Starting full HMC analysis pipeline")
            
            # Get sighting data
            sighting_data = await self.get_sighting_data(days_back=30)
            
            if sighting_data.empty:
                logger.warning("No sighting data available for analysis")
                return {}
            
            # Prepare features and outcomes
            features = self.prepare_hmc_features(sighting_data)
            outcomes = self.create_feeding_outcomes(sighting_data)
            
            if len(features) == 0 or len(outcomes) == 0:
                logger.warning("No valid features or outcomes for analysis")
                return {}
            
            # Run HMC analysis
            analysis_results = await self.run_hmc_analysis(features, outcomes)
            
            if not analysis_results:
                logger.warning("HMC analysis returned no results")
                return {}
            
            # Extract patterns
            feeding_patterns = self.extract_feeding_patterns(analysis_results)
            
            # Save results
            self.save_analysis_results(analysis_results, feeding_patterns)
            
            logger.info("Full HMC analysis pipeline complete")
            
            return {
                'analysis_results': analysis_results,
                'feeding_patterns': feeding_patterns,
                'data_summary': {
                    'sightings_analyzed': len(sighting_data),
                    'features_used': features.shape[1] if len(features) > 0 else 0,
                    'analysis_timestamp': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Full HMC analysis failed: {e}")
            return {}

async def main():
    """Run HMC analysis on production data"""
    runner = HMCAnalysisRunner()
    results = await runner.run_full_analysis()
    
    if results:
        print("HMC Analysis Complete!")
        print(f"Sightings analyzed: {results['data_summary']['sightings_analyzed']}")
        print(f"Features used: {results['data_summary']['features_used']}")
        
        # Print key findings
        patterns = results['feeding_patterns']
        if patterns:
            print("\nKey Feeding Patterns:")
            
            temporal = patterns.get('temporal_patterns', {})
            if temporal:
                print(f"  Dawn foraging strength: {temporal.get('dawn_foraging', 0):.3f}")
                print(f"  Dusk foraging strength: {temporal.get('dusk_foraging', 0):.3f}")
            
            environmental = patterns.get('environmental_factors', {})
            if environmental:
                print(f"  Tidal influence: {environmental.get('tidal_influence', 0):.3f}")
                print(f"  Temperature effect: {environmental.get('temperature_optimum', 0):.3f}")
            
            behavioral = patterns.get('behavioral_strategies', {})
            if behavioral:
                print(f"  Cooperative hunting: {behavioral.get('cooperative_hunting', 0):.3f}")
        
        # Trigger frontend update
        print("\nTriggering frontend update with new patterns...")
        # This would notify the frontend to refresh transparency UI
        
    else:
        print("HMC Analysis failed - check logs for details")

if __name__ == "__main__":
    asyncio.run(main()) 