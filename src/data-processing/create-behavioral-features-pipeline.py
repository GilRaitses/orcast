#!/usr/bin/env python3
"""
Behavioral Features Engineering Pipeline
Processes raw whale sightings data in BigQuery into ML-ready behavioral features
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import numpy as np
import pandas as pd
from google.cloud import bigquery
import math

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BehavioralFeatures:
    """Behavioral features for ML prediction"""
    spatial_features: List[float]
    temporal_features: List[float]
    environmental_features: List[float]
    social_features: List[float]
    historical_features: List[float]
    
class BehavioralFeaturesProcessor:
    def __init__(self, project_id='orca-466204'):
        self.project_id = project_id
        self.bigquery_client = bigquery.Client(project=project_id)
        self.dataset_id = "orca_production_data"
        self.sightings_table = "sightings"
        self.features_table = "behavioral_features"
        
    def create_behavioral_features_table(self):
        """Create the behavioral features table in BigQuery"""
        try:
            logger.info("🗄️ Creating behavioral features table...")
            
            schema = [
                bigquery.SchemaField("feature_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("sighting_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
                
                # Spatial features
                bigquery.SchemaField("distance_to_shore_km", "FLOAT", mode="NULLABLE"),
                bigquery.SchemaField("water_depth_m", "FLOAT", mode="NULLABLE"),
                bigquery.SchemaField("distance_to_feeding_zone_km", "FLOAT", mode="NULLABLE"),
                bigquery.SchemaField("bathymetry_gradient", "FLOAT", mode="NULLABLE"),
                
                # Temporal features
                bigquery.SchemaField("hour_of_day", "INTEGER", mode="NULLABLE"),
                bigquery.SchemaField("day_of_week", "INTEGER", mode="NULLABLE"),
                bigquery.SchemaField("day_of_year", "INTEGER", mode="NULLABLE"),
                bigquery.SchemaField("season", "STRING", mode="NULLABLE"),
                
                # Environmental features
                bigquery.SchemaField("tidal_height_normalized", "FLOAT", mode="NULLABLE"),
                bigquery.SchemaField("tidal_velocity_ms", "FLOAT", mode="NULLABLE"),
                bigquery.SchemaField("sst_anomaly_c", "FLOAT", mode="NULLABLE"),
                bigquery.SchemaField("chlorophyll_concentration", "FLOAT", mode="NULLABLE"),
                
                # Prey availability features
                bigquery.SchemaField("salmon_abundance_index", "FLOAT", mode="NULLABLE"),
                bigquery.SchemaField("herring_abundance_index", "FLOAT", mode="NULLABLE"),
                bigquery.SchemaField("prey_diversity_index", "FLOAT", mode="NULLABLE"),
                
                # Historical context features
                bigquery.SchemaField("recent_sightings_24h", "INTEGER", mode="NULLABLE"),
                bigquery.SchemaField("recent_feeding_events_24h", "INTEGER", mode="NULLABLE"),
                bigquery.SchemaField("days_since_last_feeding", "INTEGER", mode="NULLABLE"),
                
                # Social features
                bigquery.SchemaField("pod_cohesion_index", "FLOAT", mode="NULLABLE"),
                bigquery.SchemaField("inter_pod_distance_m", "FLOAT", mode="NULLABLE"),
                bigquery.SchemaField("social_activity_level", "INTEGER", mode="NULLABLE"),
                
                # Behavioral sequence features
                bigquery.SchemaField("previous_behavior", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("behavior_transition_probability", "FLOAT", mode="NULLABLE"),
                bigquery.SchemaField("time_since_behavior_change_minutes", "INTEGER", mode="NULLABLE"),
                
                bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
            ]
            
            table_ref = self.bigquery_client.dataset(self.dataset_id).table(self.features_table)
            table = bigquery.Table(table_ref, schema=schema)
            
            # Add partitioning and clustering
            table.time_partitioning = bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY,
                field="timestamp"
            )
            table.clustering_fields = ["sighting_id", "hour_of_day", "season"]
            
            try:
                table = self.bigquery_client.create_table(table)
                logger.info(f"✅ Created table {table.table_id}")
            except Exception as e:
                if "already exists" in str(e):
                    logger.info(f"📋 Table {self.features_table} already exists")
                else:
                    raise
                    
        except Exception as e:
            logger.error(f"❌ Failed to create behavioral features table: {e}")
            raise
    
    def load_raw_sightings(self) -> pd.DataFrame:
        """Load raw sightings data from BigQuery"""
        try:
            logger.info("📥 Loading raw sightings data...")
            
            query = f"""
            SELECT 
                id as sighting_id,
                timestamp,
                latitude,
                longitude,
                source,
                confidence,
                behavior,
                count as pod_size,
                notes
            FROM `{self.project_id}.{self.dataset_id}.{self.sightings_table}`
            ORDER BY timestamp DESC
            """
            
            df = self.bigquery_client.query(query).to_dataframe()
            logger.info(f"📊 Loaded {len(df)} raw sightings")
            return df
            
        except Exception as e:
            logger.error(f"❌ Failed to load sightings data: {e}")
            raise
    
    def calculate_spatial_features(self, lat: float, lng: float) -> Dict[str, float]:
        """Calculate spatial features for a location"""
        
        # Distance to shore (simplified - using coastline approximation)
        # San Juan Islands coastline approximation
        distance_to_shore = self.calculate_distance_to_shore(lat, lng)
        
        # Water depth estimation (simplified bathymetry)
        water_depth = self.estimate_water_depth(lat, lng)
        
        # Distance to known feeding zones
        distance_to_feeding_zone = self.calculate_distance_to_feeding_zone(lat, lng)
        
        # Bathymetry gradient (change in depth)
        bathymetry_gradient = self.calculate_bathymetry_gradient(lat, lng)
        
        return {
            'distance_to_shore_km': distance_to_shore,
            'water_depth_m': water_depth,
            'distance_to_feeding_zone_km': distance_to_feeding_zone,
            'bathymetry_gradient': bathymetry_gradient
        }
    
    def calculate_distance_to_shore(self, lat: float, lng: float) -> float:
        """Calculate distance to nearest shore (simplified)"""
        # Known land points in San Juan Islands
        land_points = [
            (48.5465, -123.0307),  # Friday Harbor
            (48.6956, -122.9099),  # Anacortes
            (48.4284, -123.3656),  # Victoria
            (48.7596, -122.8348),  # Bellingham
        ]
        
        distances = []
        for land_lat, land_lng in land_points:
            distance = self.haversine_distance(lat, lng, land_lat, land_lng)
            distances.append(distance)
        
        return min(distances)
    
    def estimate_water_depth(self, lat: float, lng: float) -> float:
        """Estimate water depth based on location"""
        # Simplified bathymetry model for San Juan Islands
        # Deeper water in main channels, shallower near shore
        
        # Distance from main shipping channel (roughly)
        channel_lat, channel_lng = 48.5, -123.0
        distance_from_channel = self.haversine_distance(lat, lng, channel_lat, channel_lng)
        
        # Depth model: deeper in channels, shallower near shore
        if distance_from_channel < 2:  # In main channel
            depth = 50 + np.random.normal(20, 10)  # 50-70m typically
        elif distance_from_channel < 5:  # Near channel
            depth = 30 + np.random.normal(15, 8)   # 30-45m typically
        else:  # Shallower areas
            depth = 15 + np.random.normal(10, 5)   # 15-25m typically
        
        return max(5, depth)  # Minimum 5m depth
    
    def calculate_distance_to_feeding_zone(self, lat: float, lng: float) -> float:
        """Calculate distance to nearest known feeding zone"""
        # Known feeding zones from research
        feeding_zones = [
            (48.52, -123.15),  # West Side Feeding Complex
            (48.65, -122.88),  # East Sound Foraging Area
            (48.58, -123.05),  # Spyne Channel Hunting Grounds
            (48.46, -122.96),  # South of Lopez Island
            (48.73, -122.93),  # North of Orcas Island
        ]
        
        distances = []
        for zone_lat, zone_lng in feeding_zones:
            distance = self.haversine_distance(lat, lng, zone_lat, zone_lng)
            distances.append(distance)
        
        return min(distances)
    
    def calculate_bathymetry_gradient(self, lat: float, lng: float) -> float:
        """Calculate bathymetry gradient (simplified)"""
        # Estimate depth change per km
        current_depth = self.estimate_water_depth(lat, lng)
        
        # Sample nearby points
        offset = 0.01  # ~1km offset
        nearby_depths = [
            self.estimate_water_depth(lat + offset, lng),
            self.estimate_water_depth(lat - offset, lng),
            self.estimate_water_depth(lat, lng + offset),
            self.estimate_water_depth(lat, lng - offset),
        ]
        
        # Calculate gradient as max depth change
        max_gradient = max([abs(current_depth - d) for d in nearby_depths])
        return max_gradient
    
    def calculate_temporal_features(self, timestamp: datetime) -> Dict[str, Any]:
        """Calculate temporal features for a timestamp"""
        
        hour_of_day = timestamp.hour
        day_of_week = timestamp.weekday()  # 0=Monday, 6=Sunday
        day_of_year = timestamp.timetuple().tm_yday
        
        # Season calculation
        month = timestamp.month
        if month in [12, 1, 2]:
            season = 'winter'
        elif month in [3, 4, 5]:
            season = 'spring'
        elif month in [6, 7, 8]:
            season = 'summer'
        else:
            season = 'fall'
        
        return {
            'hour_of_day': hour_of_day,
            'day_of_week': day_of_week,
            'day_of_year': day_of_year,
            'season': season
        }
    
    def calculate_environmental_features(self, lat: float, lng: float, timestamp: datetime) -> Dict[str, float]:
        """Calculate environmental features (simplified models)"""
        
        # Tidal height model (simplified sine wave)
        hours_since_epoch = (timestamp - datetime(1970, 1, 1)).total_seconds() / 3600
        tidal_height = math.sin(hours_since_epoch * 2 * math.pi / 12.42) * 2  # ~12.42 hour tidal cycle
        tidal_height_normalized = max(-1.0, min(1.0, tidal_height / 3.0))
        
        # Tidal velocity (related to tidal height derivative)
        tidal_velocity_ms = abs(math.cos(hours_since_epoch * 2 * math.pi / 12.42) * 0.5)
        
        # SST anomaly (simplified seasonal model)
        day_of_year = timestamp.timetuple().tm_yday
        seasonal_temp = 12 + 4 * math.sin((day_of_year - 80) * 2 * math.pi / 365)  # Peak in summer
        sst_anomaly_c = np.random.normal(0, 1.5)  # Random anomaly
        
        # Chlorophyll concentration (higher in spring/fall)
        if timestamp.month in [3, 4, 5, 9, 10, 11]:
            chlorophyll_base = 3.0
        else:
            chlorophyll_base = 1.5
        chlorophyll_concentration = chlorophyll_base + np.random.normal(0, 0.5)
        
        return {
            'tidal_height_normalized': tidal_height_normalized,
            'tidal_velocity_ms': tidal_velocity_ms,
            'sst_anomaly_c': sst_anomaly_c,
            'chlorophyll_concentration': max(0.1, chlorophyll_concentration)
        }
    
    def calculate_prey_features(self, lat: float, lng: float, timestamp: datetime) -> Dict[str, float]:
        """Calculate prey availability features"""
        
        # Salmon abundance model (seasonal and location-based)
        month = timestamp.month
        
        # Salmon runs: Spring (Chinook), Summer (Coho), Fall (Chum)
        if month in [4, 5, 6]:  # Spring run
            salmon_base = 0.8
        elif month in [7, 8, 9]:  # Summer run
            salmon_base = 0.9
        elif month in [10, 11, 12]:  # Fall run
            salmon_base = 0.7
        else:  # Winter - lower abundance
            salmon_base = 0.3
        
        # Location modifier - closer to river mouths = higher salmon
        river_mouths = [
            (48.42, -123.35),  # Fraser River area
            (48.50, -122.95),  # Skagit River area
        ]
        
        min_river_distance = min([self.haversine_distance(lat, lng, r_lat, r_lng) 
                                  for r_lat, r_lng in river_mouths])
        river_modifier = max(0.5, 1.0 - min_river_distance / 50)  # Higher near rivers
        
        salmon_abundance_index = min(1.0, salmon_base * river_modifier + np.random.normal(0, 0.1))
        
        # Herring abundance (schooling fish, more variable)
        herring_abundance_index = max(0.1, np.random.beta(2, 3))  # Beta distribution
        
        # Prey diversity index
        prey_diversity_index = (salmon_abundance_index + herring_abundance_index) / 2
        
        return {
            'salmon_abundance_index': max(0.0, salmon_abundance_index),
            'herring_abundance_index': max(0.0, herring_abundance_index),
            'prey_diversity_index': max(0.0, prey_diversity_index)
        }
    
    def calculate_historical_features(self, lat: float, lng: float, timestamp: datetime, sightings_df: pd.DataFrame) -> Dict[str, int]:
        """Calculate historical context features"""
        
        # Filter sightings in nearby area (within ~5km)
        nearby_sightings = sightings_df[
            (abs(sightings_df['latitude'] - lat) < 0.05) &  # ~5km
            (abs(sightings_df['longitude'] - lng) < 0.05)
        ].copy()
        
        # Recent sightings in 24h
        cutoff_24h = timestamp - timedelta(hours=24)
        recent_24h = nearby_sightings[nearby_sightings['timestamp'] > cutoff_24h]
        recent_sightings_24h = len(recent_24h)
        
        # Recent feeding events in 24h
        feeding_behaviors = ['foraging', 'feeding', 'hunting']
        recent_feeding_24h = len(recent_24h[
            recent_24h['behavior'].isin(feeding_behaviors)
        ])
        
        # Days since last feeding
        feeding_sightings = nearby_sightings[
            nearby_sightings['behavior'].isin(feeding_behaviors) &
            (nearby_sightings['timestamp'] < timestamp)
        ]
        
        if len(feeding_sightings) > 0:
            last_feeding = feeding_sightings['timestamp'].max()
            days_since_last_feeding = (timestamp - last_feeding).days
        else:
            days_since_last_feeding = 30  # Default if no feeding events found
        
        return {
            'recent_sightings_24h': recent_sightings_24h,
            'recent_feeding_events_24h': recent_feeding_24h,
            'days_since_last_feeding': min(365, days_since_last_feeding)  # Cap at 1 year
        }
    
    def calculate_social_features(self, pod_size: int, behavior: str) -> Dict[str, Any]:
        """Calculate social features"""
        
        # Pod cohesion index (larger pods = lower cohesion)
        pod_cohesion_index = max(0.1, min(1.0, 1.0 - (pod_size - 1) * 0.1))
        
        # Inter-pod distance (estimated based on pod size)
        if pod_size > 5:
            inter_pod_distance_m = np.random.normal(500, 200)  # Larger pods spread out
        else:
            inter_pod_distance_m = np.random.normal(200, 100)  # Smaller pods closer together
        
        # Social activity level based on behavior
        behavior_activity_map = {
            'socializing': 5,
            'playing': 4,
            'foraging': 3,
            'traveling': 2,
            'resting': 1,
            'observed': 3  # Default
        }
        social_activity_level = behavior_activity_map.get(behavior, 3)
        
        return {
            'pod_cohesion_index': pod_cohesion_index,
            'inter_pod_distance_m': max(50, inter_pod_distance_m),
            'social_activity_level': social_activity_level
        }
    
    def calculate_behavioral_sequence_features(self, sighting_id: str, timestamp: datetime, 
                                               sightings_df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate behavioral sequence features"""
        
        # Find previous behavior for this location
        nearby_sightings = sightings_df[
            (abs(sightings_df['latitude'] - sightings_df.loc[sightings_df['sighting_id'] == sighting_id, 'latitude'].iloc[0]) < 0.05) &
            (abs(sightings_df['longitude'] - sightings_df.loc[sightings_df['sighting_id'] == sighting_id, 'longitude'].iloc[0]) < 0.05) &
            (sightings_df['timestamp'] < timestamp)
        ].sort_values('timestamp', ascending=False)
        
        if len(nearby_sightings) > 0:
            previous_behavior = nearby_sightings.iloc[0]['behavior']
            time_since_change = timestamp - nearby_sightings.iloc[0]['timestamp']
            time_since_behavior_change_minutes = int(time_since_change.total_seconds() / 60)
            
            # Simple behavior transition probability
            current_behavior = sightings_df.loc[sightings_df['sighting_id'] == sighting_id, 'behavior'].iloc[0]
            if current_behavior == previous_behavior:
                behavior_transition_probability = 0.8  # High probability of same behavior
            else:
                behavior_transition_probability = 0.3  # Lower probability of behavior change
        else:
            previous_behavior = None
            behavior_transition_probability = 0.5  # Neutral if no history
            time_since_behavior_change_minutes = 0
        
        return {
            'previous_behavior': previous_behavior,
            'behavior_transition_probability': behavior_transition_probability,
            'time_since_behavior_change_minutes': min(10080, time_since_behavior_change_minutes)  # Cap at 1 week
        }
    
    def haversine_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate haversine distance between two points in km"""
        R = 6371  # Earth's radius in km
        
        lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def process_sightings_to_features(self) -> int:
        """Process all sightings and create behavioral features"""
        try:
            logger.info("🔄 Starting behavioral features processing...")
            
            # Load raw sightings data
            sightings_df = self.load_raw_sightings()
            
            if len(sightings_df) == 0:
                logger.warning("⚠️ No sightings data found")
                return 0
            
            # Create features table
            self.create_behavioral_features_table()
            
            # Process each sighting
            feature_rows = []
            
            for idx, row in sightings_df.iterrows():
                try:
                    sighting_id = row['sighting_id']
                    timestamp = pd.to_datetime(row['timestamp'])
                    lat = row['latitude']
                    lng = row['longitude']
                    pod_size = row.get('pod_size', 1)
                    behavior = row.get('behavior', 'observed')
                    
                    logger.info(f"🐋 Processing sighting {idx+1}/{len(sightings_df)}: {sighting_id}")
                    
                    # Calculate all feature groups
                    spatial_features = self.calculate_spatial_features(lat, lng)
                    temporal_features = self.calculate_temporal_features(timestamp)
                    environmental_features = self.calculate_environmental_features(lat, lng, timestamp)
                    prey_features = self.calculate_prey_features(lat, lng, timestamp)
                    historical_features = self.calculate_historical_features(lat, lng, timestamp, sightings_df)
                    social_features = self.calculate_social_features(pod_size, behavior)
                    behavioral_features = self.calculate_behavioral_sequence_features(sighting_id, timestamp, sightings_df)
                    
                    # Combine all features
                    feature_row = {
                        'feature_id': f"feat_{sighting_id}",
                        'sighting_id': sighting_id,
                        'timestamp': timestamp,
                        'created_at': datetime.now(),
                        **spatial_features,
                        **temporal_features,
                        **environmental_features,
                        **prey_features,
                        **historical_features,
                        **social_features,
                        **behavioral_features
                    }
                    
                    feature_rows.append(feature_row)
                    
                except Exception as e:
                    logger.error(f"❌ Error processing sighting {sighting_id}: {e}")
                    continue
            
            # Upload features to BigQuery
            if feature_rows:
                logger.info(f"📤 Uploading {len(feature_rows)} feature records to BigQuery...")
                
                table_ref = self.bigquery_client.dataset(self.dataset_id).table(self.features_table)
                
                # Upload in batches
                batch_size = 100
                total_uploaded = 0
                
                for i in range(0, len(feature_rows), batch_size):
                    batch = feature_rows[i:i + batch_size]
                    
                    errors = self.bigquery_client.insert_rows_json(table_ref, batch)
                    
                    if errors:
                        logger.error(f"❌ BigQuery insert errors: {errors}")
                    else:
                        total_uploaded += len(batch)
                        logger.info(f"✅ Uploaded batch {i//batch_size + 1}: {len(batch)} features")
                
                logger.info(f"🎉 Successfully processed {total_uploaded} behavioral features!")
                return total_uploaded
            else:
                logger.warning("⚠️ No features to upload")
                return 0
                
        except Exception as e:
            logger.error(f"💥 Feature processing failed: {e}")
            raise
    
    def create_ml_training_table(self):
        """Create ML training data table with processed features"""
        try:
            logger.info("🤖 Creating ML training data table...")
            
            # Create ML training data from behavioral features and sightings
            query = f"""
            CREATE OR REPLACE TABLE `{self.project_id}.{self.dataset_id}.ml_training_data` AS
            SELECT 
                GENERATE_UUID() as training_id,
                s.id as sighting_id,
                STRUCT(
                    [bf.distance_to_shore_km, bf.water_depth_m, bf.distance_to_feeding_zone_km] as spatial,
                    [bf.hour_of_day, bf.day_of_year, bf.tidal_height_normalized] as temporal,
                    [bf.sst_anomaly_c, bf.tidal_velocity_ms, bf.chlorophyll_concentration] as environmental,
                    [bf.pod_cohesion_index, bf.social_activity_level] as social,
                    [bf.recent_sightings_24h, bf.days_since_last_feeding] as historical
                ) as features,
                CASE 
                    WHEN s.behavior IN ('foraging', 'feeding', 'hunting') THEN 'feeding'
                    WHEN s.behavior IN ('traveling', 'transiting') THEN 'traveling'
                    WHEN s.behavior IN ('socializing', 'playing') THEN 'socializing'
                    WHEN s.behavior IN ('resting', 'milling') THEN 'resting'
                    ELSE 'unknown'
                END as behavior_label,
                CASE
                    WHEN s.behavior IN ('foraging', 'feeding') THEN 'cooperative_hunting'
                    ELSE 'other'
                END as feeding_strategy_label,
                CASE
                    WHEN s.behavior IN ('foraging', 'feeding') THEN true
                    ELSE false
                END as success_label,
                CASE 
                    WHEN MOD(ABS(FARM_FINGERPRINT(s.id)), 10) < 7 THEN 'train'
                    WHEN MOD(ABS(FARM_FINGERPRINT(s.id)), 10) < 9 THEN 'validation'
                    ELSE 'test'
                END as train_test_split,
                s.confidence as data_quality_score,
                CURRENT_TIMESTAMP() as created_at
            FROM `{self.project_id}.{self.dataset_id}.{self.sightings_table}` s
            JOIN `{self.project_id}.{self.dataset_id}.{self.features_table}` bf
                ON s.id = bf.sighting_id
            WHERE s.confidence > 0.3
            """
            
            query_job = self.bigquery_client.query(query)
            query_job.result()  # Wait for completion
            
            logger.info("✅ ML training data table created successfully!")
            
            # Verify the data
            verify_query = f"""
            SELECT 
                train_test_split,
                behavior_label,
                COUNT(*) as count
            FROM `{self.project_id}.{self.dataset_id}.ml_training_data`
            GROUP BY train_test_split, behavior_label
            ORDER BY train_test_split, behavior_label
            """
            
            results = self.bigquery_client.query(verify_query).to_dataframe()
            logger.info("📊 ML Training Data Summary:")
            for _, row in results.iterrows():
                logger.info(f"  {row['train_test_split']}/{row['behavior_label']}: {row['count']} records")
            
        except Exception as e:
            logger.error(f"❌ Failed to create ML training table: {e}")
            raise
    
    def run_complete_pipeline(self):
        """Run the complete feature engineering pipeline"""
        try:
            logger.info("🚀 Starting complete behavioral features pipeline...")
            
            # Step 1: Process raw sightings into behavioral features
            features_created = self.process_sightings_to_features()
            
            if features_created > 0:
                # Step 2: Create ML training data from features
                self.create_ml_training_table()
                
                logger.info(f"🎉 Pipeline completed successfully!")
                logger.info(f"📊 Features created: {features_created}")
                logger.info(f"🔗 View data: https://console.cloud.google.com/bigquery?project={self.project_id}")
                
                return features_created
            else:
                logger.warning("⚠️ No features created, skipping ML training table creation")
                return 0
                
        except Exception as e:
            logger.error(f"💥 Pipeline failed: {e}")
            raise

def main():
    """Main function to run the feature engineering pipeline"""
    processor = BehavioralFeaturesProcessor()
    processor.run_complete_pipeline()

if __name__ == "__main__":
    main() 