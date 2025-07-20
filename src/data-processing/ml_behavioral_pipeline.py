"""
ML Behavioral Pipeline for ORCAST
Processes whale detections through behavioral analysis models
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
import firebase_admin
from firebase_admin import firestore
from google.cloud import bigquery
from scipy.spatial.distance import cdist
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import joblib
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ORCASTBehavioralProcessor:
    """ML processor for whale behavioral analysis"""
    
    def __init__(self):
        # Initialize Firebase
        try:
            if not firebase_admin._apps:
                firebase_admin.initialize_app()
            self.firestore_client = firestore.client()
        except Exception as e:
            logger.warning(f"Firebase initialization failed: {e}")
            self.firestore_client = None
        
        # Initialize BigQuery
        try:
            self.bq_client = bigquery.Client()
        except Exception as e:
            logger.warning(f"BigQuery initialization failed: {e}")
            self.bq_client = None
        
        # Load or initialize behavioral models
        self.behavioral_models = self._load_behavioral_models()
        
        # Behavioral analysis parameters
        self.spatial_threshold_km = 5.0
        self.temporal_threshold_hours = 2.0
        self.min_cluster_size = 2
    
    def _load_behavioral_models(self) -> Dict[str, Any]:
        """Load or create behavioral analysis models"""
        
        models = {}
        
        try:
            # Try to load existing models
            if os.path.exists('orcast_behavioral_models.joblib'):
                models = joblib.load('orcast_behavioral_models.joblib')
                logger.info("✅ Loaded existing behavioral models")
            else:
                # Create new models
                models = self._create_default_models()
                logger.info("🔧 Created default behavioral models")
        
        except Exception as e:
            logger.warning(f"Model loading failed: {e}")
            models = self._create_default_models()
        
        return models
    
    def _create_default_models(self) -> Dict[str, Any]:
        """Create default behavioral analysis models"""
        
        return {
            'foraging_classifier': {
                'type': 'heuristic',
                'parameters': {
                    'call_frequency_weight': 0.3,
                    'spatial_clustering_weight': 0.3,
                    'call_duration_weight': 0.2,
                    'confidence_weight': 0.2
                }
            },
            'social_activity_scorer': {
                'type': 'heuristic',
                'parameters': {
                    'cluster_size_weight': 0.4,
                    'temporal_clustering_weight': 0.3,
                    'call_variety_weight': 0.3
                }
            },
            'movement_predictor': {
                'type': 'kinematic',
                'parameters': {
                    'max_speed_kmh': 25.0,
                    'typical_speed_kmh': 8.0,
                    'direction_persistence': 0.7
                }
            }
        }
    
    async def fetch_unprocessed_detections(self) -> List[Dict]:
        """Fetch unprocessed detections from Firestore"""
        
        if not self.firestore_client:
            logger.error("Firestore client not available")
            return []
        
        try:
            # Query for unprocessed detections
            detections_ref = self.firestore_client.collection('whale_detections')
            query = detections_ref.where('ml_analysis_pending', '==', True).limit(100)
            
            docs = query.stream()
            detections = []
            
            for doc in docs:
                detection_data = doc.to_dict()
                detection_data['firestore_id'] = doc.id
                detections.append(detection_data)
            
            logger.info(f"📥 Fetched {len(detections)} unprocessed detections")
            return detections
        
        except Exception as e:
            logger.error(f"Failed to fetch detections: {e}")
            return []
    
    def extract_behavioral_features(self, detections: List[Dict]) -> pd.DataFrame:
        """Extract behavioral features from detections"""
        
        logger.info(f"🧠 Extracting behavioral features from {len(detections)} detections...")
        
        features_list = []
        
        for detection in detections:
            try:
                # Basic detection info
                features = {
                    'detection_id': detection.get('id', ''),
                    'firestore_id': detection.get('firestore_id', ''),
                    'timestamp': detection.get('timestamp', ''),
                    'hydrophone_id': detection.get('hydrophone_id', ''),
                    'latitude': float(detection.get('latitude', 0)),
                    'longitude': float(detection.get('longitude', 0)),
                    'confidence': float(detection.get('confidence', 0)),
                    'call_type': detection.get('call_type', 'unknown'),
                    'audio_duration': float(detection.get('audio_duration_seconds', 3.0)),
                    'region': detection.get('region', 'unknown')
                }
                
                # Calculate contextual features
                context_features = self._calculate_contextual_features(detection, detections)
                features.update(context_features)
                
                features_list.append(features)
                
            except Exception as e:
                logger.warning(f"Failed to extract features for detection {detection.get('id', 'unknown')}: {e}")
                continue
        
        df = pd.DataFrame(features_list)
        logger.info(f"✅ Extracted features: {df.shape[0]} detections, {df.shape[1]} features")
        
        return df
    
    def _calculate_contextual_features(self, detection: Dict, all_detections: List[Dict]) -> Dict:
        """Calculate contextual features for a detection"""
        
        # Parse timestamp
        try:
            det_time = pd.to_datetime(detection['timestamp'])
        except:
            det_time = datetime.now()
        
        det_lat = float(detection.get('latitude', 0))
        det_lng = float(detection.get('longitude', 0))
        
        # Find nearby detections in space and time
        nearby_detections = []
        
        for other_det in all_detections:
            if other_det.get('id') == detection.get('id'):
                continue
            
            try:
                other_time = pd.to_datetime(other_det['timestamp'])
                other_lat = float(other_det.get('latitude', 0))
                other_lng = float(other_det.get('longitude', 0))
                
                # Calculate temporal and spatial distance
                time_diff_hours = abs((det_time - other_time).total_seconds()) / 3600
                spatial_dist_km = self._haversine_distance(det_lat, det_lng, other_lat, other_lng)
                
                # Check if within thresholds
                if (time_diff_hours <= self.temporal_threshold_hours and 
                    spatial_dist_km <= self.spatial_threshold_km):
                    nearby_detections.append({
                        'detection': other_det,
                        'time_diff_hours': time_diff_hours,
                        'spatial_dist_km': spatial_dist_km
                    })
            
            except Exception as e:
                continue
        
        # Calculate contextual features
        features = {
            'nearby_detection_count': len(nearby_detections),
            'avg_nearby_confidence': np.mean([d['detection'].get('confidence', 0) for d in nearby_detections]) if nearby_detections else 0,
            'min_spatial_distance_km': min([d['spatial_dist_km'] for d in nearby_detections]) if nearby_detections else float('inf'),
            'min_temporal_distance_hours': min([d['time_diff_hours'] for d in nearby_detections]) if nearby_detections else float('inf'),
            'call_type_variety': len(set([d['detection'].get('call_type', 'unknown') for d in nearby_detections] + [detection.get('call_type', 'unknown')])),
            'hydrophone_variety': len(set([d['detection'].get('hydrophone_id', '') for d in nearby_detections] + [detection.get('hydrophone_id', '')]))
        }
        
        return features
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in kilometers"""
        from math import radians, cos, sin, asin, sqrt
        
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Radius of earth in kilometers
        return c * r
    
    def perform_spatial_clustering(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """Perform spatial clustering on detections"""
        
        if len(features_df) < 2:
            features_df['spatial_cluster'] = 0
            return features_df
        
        # Prepare coordinates for clustering
        coords = features_df[['latitude', 'longitude']].values
        
        # Use DBSCAN for spatial clustering
        # eps parameter: ~5km in degrees (rough approximation)
        eps_degrees = 5.0 / 111.0  # Convert km to degrees
        
        clustering = DBSCAN(eps=eps_degrees, min_samples=self.min_cluster_size)
        cluster_labels = clustering.fit_predict(coords)
        
        features_df['spatial_cluster'] = cluster_labels
        
        n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
        logger.info(f"🗺️ Identified {n_clusters} spatial clusters")
        
        return features_df
    
    def perform_temporal_clustering(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """Perform temporal clustering on detections"""
        
        if len(features_df) < 2:
            features_df['temporal_cluster'] = 0
            return features_df
        
        # Convert timestamps to unix timestamps for clustering
        timestamps = pd.to_datetime(features_df['timestamp']).astype(int) / 10**9  # Convert to seconds
        timestamps_scaled = StandardScaler().fit_transform(timestamps.values.reshape(-1, 1))
        
        # Use DBSCAN for temporal clustering
        # eps parameter: 2 hours in scaled units
        eps_temporal = 2.0 / 24.0  # 2 hours as fraction of day
        
        clustering = DBSCAN(eps=eps_temporal, min_samples=self.min_cluster_size)
        cluster_labels = clustering.fit_predict(timestamps_scaled)
        
        features_df['temporal_cluster'] = cluster_labels
        
        n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
        logger.info(f"⏰ Identified {n_clusters} temporal clusters")
        
        return features_df
    
    def calculate_behavioral_scores(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """Calculate behavioral analysis scores"""
        
        logger.info("🎯 Calculating behavioral scores...")
        
        # Foraging probability
        features_df['foraging_probability'] = self._calculate_foraging_probability(features_df)
        
        # Social activity score
        features_df['social_activity_score'] = self._calculate_social_activity_score(features_df)
        
        # Movement patterns
        movement_features = self._calculate_movement_patterns(features_df)
        features_df = pd.concat([features_df, movement_features], axis=1)
        
        # Overall behavioral score
        features_df['behavioral_score'] = (
            features_df['foraging_probability'] * 0.4 +
            features_df['social_activity_score'] * 0.3 +
            features_df['confidence'] / 100.0 * 0.3
        )
        
        return features_df
    
    def _calculate_foraging_probability(self, df: pd.DataFrame) -> pd.Series:
        """Calculate foraging probability for each detection"""
        
        foraging_scores = []
        
        for _, row in df.iterrows():
            score = 0.0
            
            # High activity (multiple nearby detections) suggests foraging
            if row['nearby_detection_count'] > 3:
                score += 0.3
            elif row['nearby_detection_count'] > 1:
                score += 0.15
            
            # Echolocation clicks suggest foraging
            if row['call_type'] == 'echolocation_click':
                score += 0.25
            elif row['call_type'] == 'foraging_call':
                score += 0.35
            
            # Longer duration calls suggest active behavior
            if row['audio_duration'] > 5.0:
                score += 0.2
            elif row['audio_duration'] > 3.0:
                score += 0.1
            
            # High confidence detections
            if row['confidence'] > 80:
                score += 0.1
            
            # Spatial clustering suggests feeding aggregations
            if row['spatial_cluster'] >= 0:  # Not noise (-1)
                score += 0.1
            
            foraging_scores.append(min(1.0, score))
        
        return pd.Series(foraging_scores, index=df.index)
    
    def _calculate_social_activity_score(self, df: pd.DataFrame) -> pd.Series:
        """Calculate social activity score for each detection"""
        
        social_scores = []
        
        for _, row in df.iterrows():
            score = 0.0
            
            # Multiple nearby detections suggest social activity
            nearby_count = row['nearby_detection_count']
            score += min(0.4, nearby_count * 0.1)
            
            # Call type variety suggests social interaction
            call_variety = row['call_type_variety']
            score += min(0.2, call_variety * 0.05)
            
            # Social call type
            if row['call_type'] == 'social_call':
                score += 0.3
            
            # Temporal clustering suggests coordinated activity
            if row['temporal_cluster'] >= 0:
                score += 0.15
            
            # Multiple hydrophones suggest movement/traveling
            if row['hydrophone_variety'] > 1:
                score += 0.1
            
            social_scores.append(min(1.0, score))
        
        return pd.Series(social_scores, index=df.index)
    
    def _calculate_movement_patterns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate movement patterns from detection sequences"""
        
        movement_df = pd.DataFrame(index=df.index)
        
        # Initialize with default values
        movement_df['estimated_speed_kmh'] = 0.0
        movement_df['estimated_direction_degrees'] = 0.0
        movement_df['movement_consistency'] = 0.0
        
        # Group by temporal clusters to analyze movement
        for cluster_id in df['temporal_cluster'].unique():
            if cluster_id == -1:  # Skip noise
                continue
            
            cluster_detections = df[df['temporal_cluster'] == cluster_id].copy()
            
            if len(cluster_detections) < 2:
                continue
            
            # Sort by timestamp
            cluster_detections = cluster_detections.sort_values('timestamp')
            
            for i in range(1, len(cluster_detections)):
                current_idx = cluster_detections.index[i]
                prev_idx = cluster_detections.index[i-1]
                
                current = cluster_detections.iloc[i]
                previous = cluster_detections.iloc[i-1]
                
                # Calculate movement metrics
                try:
                    time_diff_hours = abs(pd.to_datetime(current['timestamp']) - pd.to_datetime(previous['timestamp'])).total_seconds() / 3600
                    distance_km = self._haversine_distance(
                        previous['latitude'], previous['longitude'],
                        current['latitude'], current['longitude']
                    )
                    
                    if time_diff_hours > 0:
                        speed_kmh = distance_km / time_diff_hours
                        
                        # Only record reasonable whale speeds
                        if speed_kmh <= 25.0:  # Max reasonable whale speed
                            movement_df.loc[current_idx, 'estimated_speed_kmh'] = speed_kmh
                            
                            # Calculate direction
                            lat_diff = current['latitude'] - previous['latitude']
                            lng_diff = current['longitude'] - previous['longitude']
                            direction = np.degrees(np.arctan2(lng_diff, lat_diff))
                            movement_df.loc[current_idx, 'estimated_direction_degrees'] = direction
                
                except Exception as e:
                    continue
        
        # Calculate movement consistency (how consistent is the direction?)
        for cluster_id in df['temporal_cluster'].unique():
            if cluster_id == -1:
                continue
            
            cluster_indices = df[df['temporal_cluster'] == cluster_id].index
            directions = movement_df.loc[cluster_indices, 'estimated_direction_degrees']
            directions = directions[directions != 0]  # Remove default values
            
            if len(directions) > 1:
                # Calculate circular variance for direction consistency
                direction_radians = np.radians(directions)
                mean_direction = np.arctan2(np.sin(direction_radians).mean(), np.cos(direction_radians).mean())
                consistency = np.cos(direction_radians - mean_direction).mean()
                
                movement_df.loc[cluster_indices, 'movement_consistency'] = max(0, consistency)
        
        return movement_df
    
    async def store_ml_results_to_firestore(self, results_df: pd.DataFrame) -> bool:
        """Store ML analysis results back to Firestore"""
        
        if not self.firestore_client:
            logger.error("Firestore client not available")
            return False
        
        logger.info(f"💾 Storing ML results for {len(results_df)} detections to Firestore...")
        
        try:
            batch = self.firestore_client.batch()
            
            for _, row in results_df.iterrows():
                # Update original detection document
                detection_ref = self.firestore_client.collection('whale_detections').document(row['firestore_id'])
                
                ml_analysis = {
                    'foraging_probability': float(row['foraging_probability']),
                    'social_activity_score': float(row['social_activity_score']),
                    'behavioral_score': float(row['behavioral_score']),
                    'spatial_cluster': int(row['spatial_cluster']),
                    'temporal_cluster': int(row['temporal_cluster']),
                    'estimated_speed_kmh': float(row['estimated_speed_kmh']),
                    'estimated_direction_degrees': float(row['estimated_direction_degrees']),
                    'movement_consistency': float(row['movement_consistency']),
                    'nearby_detection_count': int(row['nearby_detection_count']),
                    'ml_processed_at': datetime.now().isoformat(),
                    'ml_analysis_pending': False,
                    'ml_version': '1.0'
                }
                
                batch.update(detection_ref, {'ml_analysis': ml_analysis, 'ml_analysis_pending': False})
                
                # Also create separate ML analysis document
                ml_doc_ref = self.firestore_client.collection('ml_analysis_results').document(f"ml_{row['detection_id']}")
                
                ml_document = {
                    'detection_id': row['detection_id'],
                    'timestamp': row['timestamp'],
                    'hydrophone_id': row['hydrophone_id'],
                    'analysis_results': ml_analysis,
                    'processed_at': datetime.now().isoformat()
                }
                
                batch.set(ml_doc_ref, ml_document)
            
            # Commit batch
            batch.commit()
            logger.info("✅ ML results stored to Firestore")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store ML results: {e}")
            return False
    
    async def run_behavioral_analysis_pipeline(self) -> Dict[str, Any]:
        """Run complete behavioral analysis pipeline"""
        
        logger.info("🧠 Starting ML Behavioral Analysis Pipeline...")
        
        pipeline_results = {
            'timestamp': datetime.now().isoformat(),
            'detections_processed': 0,
            'features_extracted': False,
            'clustering_completed': False,
            'behavioral_scores_calculated': False,
            'results_stored': False,
            'pipeline_status': 'started'
        }
        
        try:
            # Step 1: Fetch unprocessed detections
            detections = await self.fetch_unprocessed_detections()
            pipeline_results['detections_processed'] = len(detections)
            
            if not detections:
                pipeline_results['pipeline_status'] = 'no_unprocessed_detections'
                logger.info("📭 No unprocessed detections found")
                return pipeline_results
            
            # Step 2: Extract behavioral features
            features_df = self.extract_behavioral_features(detections)
            pipeline_results['features_extracted'] = True
            
            # Step 3: Perform clustering
            features_df = self.perform_spatial_clustering(features_df)
            features_df = self.perform_temporal_clustering(features_df)
            pipeline_results['clustering_completed'] = True
            
            # Step 4: Calculate behavioral scores
            features_df = self.calculate_behavioral_scores(features_df)
            pipeline_results['behavioral_scores_calculated'] = True
            
            # Step 5: Store results
            storage_success = await self.store_ml_results_to_firestore(features_df)
            pipeline_results['results_stored'] = storage_success
            
            if storage_success:
                pipeline_results['pipeline_status'] = 'completed'
                
                # Generate summary insights
                summary = self._generate_behavioral_insights(features_df)
                pipeline_results['behavioral_insights'] = summary
                
                # Store summary to Firestore
                if self.firestore_client:
                    summary_ref = self.firestore_client.collection('behavioral_insights').document(
                        f"insights_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    )
                    summary_ref.set({
                        'timestamp': datetime.now().isoformat(),
                        'detection_count': len(features_df),
                        'insights': summary,
                        'processing_pipeline': 'ml_behavioral_analysis'
                    })
            
            else:
                pipeline_results['pipeline_status'] = 'storage_failed'
            
            logger.info("📊 Behavioral Analysis Pipeline Summary:")
            logger.info(f"   Detections processed: {pipeline_results['detections_processed']}")
            logger.info(f"   Features extracted: {pipeline_results['features_extracted']}")
            logger.info(f"   Clustering completed: {pipeline_results['clustering_completed']}")
            logger.info(f"   Behavioral scores calculated: {pipeline_results['behavioral_scores_calculated']}")
            logger.info(f"   Results stored: {pipeline_results['results_stored']}")
            logger.info(f"   Status: {pipeline_results['pipeline_status']}")
            
            return pipeline_results
            
        except Exception as e:
            logger.error(f"Behavioral analysis pipeline failed: {e}")
            pipeline_results['pipeline_status'] = 'failed'
            pipeline_results['error'] = str(e)
            return pipeline_results
    
    def _generate_behavioral_insights(self, features_df: pd.DataFrame) -> Dict[str, Any]:
        """Generate high-level behavioral insights"""
        
        insights = {
            'total_detections': len(features_df),
            'spatial_clusters': len(features_df['spatial_cluster'].unique()) - (1 if -1 in features_df['spatial_cluster'].values else 0),
            'temporal_clusters': len(features_df['temporal_cluster'].unique()) - (1 if -1 in features_df['temporal_cluster'].values else 0),
            'avg_foraging_probability': float(features_df['foraging_probability'].mean()),
            'avg_social_activity': float(features_df['social_activity_score'].mean()),
            'avg_behavioral_score': float(features_df['behavioral_score'].mean()),
            'active_regions': features_df['region'].value_counts().to_dict(),
            'active_hydrophones': features_df['hydrophone_id'].value_counts().to_dict(),
            'call_type_distribution': features_df['call_type'].value_counts().to_dict(),
            'high_activity_areas': []
        }
        
        # Identify high activity areas
        high_activity = features_df[features_df['behavioral_score'] > 0.7]
        if len(high_activity) > 0:
            for region in high_activity['region'].unique():
                region_data = high_activity[high_activity['region'] == region]
                insights['high_activity_areas'].append({
                    'region': region,
                    'detection_count': len(region_data),
                    'avg_behavioral_score': float(region_data['behavioral_score'].mean()),
                    'dominant_call_type': region_data['call_type'].mode().iloc[0] if len(region_data) > 0 else 'unknown'
                })
        
        return insights

async def main():
    """Main execution function"""
    print("🧠 ORCAST ML Behavioral Analysis Pipeline")
    
    processor = ORCASTBehavioralProcessor()
    
    # Run behavioral analysis pipeline
    results = await processor.run_behavioral_analysis_pipeline()
    
    print(f"\n📊 Pipeline Results:")
    print(f"   Status: {results['pipeline_status']}")
    print(f"   Detections processed: {results['detections_processed']}")
    print(f"   Features extracted: {'✅' if results['features_extracted'] else '❌'}")
    print(f"   Clustering completed: {'✅' if results['clustering_completed'] else '❌'}")
    print(f"   Behavioral scores calculated: {'✅' if results['behavioral_scores_calculated'] else '❌'}")
    print(f"   Results stored: {'✅' if results['results_stored'] else '❌'}")
    
    if 'behavioral_insights' in results:
        insights = results['behavioral_insights']
        print(f"\n🎯 Behavioral Insights:")
        print(f"   Total detections: {insights['total_detections']}")
        print(f"   Spatial clusters: {insights['spatial_clusters']}")
        print(f"   Avg foraging probability: {insights['avg_foraging_probability']:.2f}")
        print(f"   Avg social activity: {insights['avg_social_activity']:.2f}")
        print(f"   High activity areas: {len(insights['high_activity_areas'])}")
    
    print(f"\n🔄 Pipeline ready for route optimization!")

if __name__ == "__main__":
    asyncio.run(main()) 