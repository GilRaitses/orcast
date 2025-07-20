"""
OrcaHello Behavioral Data Processor for ORCAST
Transforms real-time acoustic detections into behavioral modeling features
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
from dataclasses import dataclass, asdict
import asyncio
import json
from scipy.spatial.distance import cdist
from scipy.signal import find_peaks
import firebase_admin
from firebase_admin import firestore

from orcahello_api_client import ORCASTOrcaHelloIntegration, WhaleDetection

logger = logging.getLogger(__name__)

@dataclass
class BehavioralFeatures:
    """Behavioral features extracted from acoustic detections"""
    detection_id: str
    timestamp: datetime
    location_id: str
    latitude: float
    longitude: float
    
    # Acoustic behavioral features
    call_frequency: float          # Calls per minute
    call_intensity: float          # Average confidence
    call_duration_pattern: List[float]  # Duration patterns
    spatial_clustering: float      # Spatial clustering coefficient
    temporal_clustering: float     # Temporal clustering coefficient
    
    # Movement inference features
    estimated_speed: Optional[float] = None
    estimated_direction: Optional[float] = None
    foraging_probability: float = 0.0
    social_activity_score: float = 0.0
    
    # Environmental context
    depth_zone: str = "unknown"    # shallow, medium, deep
    current_strength: float = 0.0
    tidal_phase: str = "unknown"

class OrcaHelloBehavioralProcessor:
    """Processes OrcaHello detections into behavioral features for ORCAST models"""
    
    def __init__(self, firestore_client=None):
        self.integration_client = ORCASTOrcaHelloIntegration()
        self.detection_history = []
        self.behavioral_features = []
        self.firestore_client = firestore_client
        
        # Behavioral analysis parameters
        self.spatial_threshold_km = 5.0  # km for spatial clustering
        self.temporal_threshold_min = 30  # minutes for temporal clustering
        self.movement_inference_window = 60  # minutes for movement analysis
        
        # Initialize Firebase if not provided
        if not self.firestore_client:
            try:
                if not firebase_admin._apps:
                    firebase_admin.initialize_app()
                self.firestore_client = firestore.client()
            except Exception as e:
                logger.warning(f"Could not initialize Firebase: {e}")
    
    async def process_real_time_stream(self):
        """Start processing real-time OrcaHello detections"""
        logger.info("🐋 Starting OrcaHello behavioral processing stream...")
        
        async def detection_callback(new_detections: List[WhaleDetection]):
            """Process new detections from OrcaHello"""
            await self.process_detection_batch(new_detections)
        
        # Start the real-time stream
        async with self.integration_client.api_client as client:
            await client.stream_real_time_detections(detection_callback)
    
    async def process_detection_batch(self, detections: List[WhaleDetection]):
        """Process a batch of new whale detections"""
        logger.info(f"Processing {len(detections)} new whale detections...")
        
        # Add to detection history
        self.detection_history.extend(detections)
        
        # Keep only last 24 hours of data
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.detection_history = [
            d for d in self.detection_history 
            if d.timestamp > cutoff_time
        ]
        
        # Extract behavioral features for each detection
        for detection in detections:
            features = await self.extract_behavioral_features(detection)
            if features:
                self.behavioral_features.append(features)
                await self.save_behavioral_features(features)
        
        # Generate behavioral insights
        insights = await self.generate_behavioral_insights()
        await self.save_behavioral_insights(insights)
        
        logger.info(f"Generated behavioral features for {len(detections)} detections")
    
    async def extract_behavioral_features(self, detection: WhaleDetection) -> Optional[BehavioralFeatures]:
        """Extract behavioral features from a single detection"""
        try:
            # Get detection context (nearby detections in space and time)
            context_detections = self._get_detection_context(detection)
            
            # Calculate acoustic behavioral features
            call_frequency = self._calculate_call_frequency(detection, context_detections)
            call_intensity = detection.confidence / 100.0
            call_duration_pattern = self._analyze_call_duration_pattern(detection)
            
            # Calculate spatial and temporal clustering
            spatial_clustering = self._calculate_spatial_clustering(detection, context_detections)
            temporal_clustering = self._calculate_temporal_clustering(detection, context_detections)
            
            # Infer movement patterns
            movement_data = self._infer_movement_patterns(detection, context_detections)
            
            # Calculate behavioral scores
            foraging_prob = self._calculate_foraging_probability(detection, context_detections)
            social_score = self._calculate_social_activity_score(detection, context_detections)
            
            # Get environmental context
            env_context = await self._get_environmental_context(detection)
            
            features = BehavioralFeatures(
                detection_id=detection.detection_id,
                timestamp=detection.timestamp,
                location_id=detection.location.id,
                latitude=detection.location.latitude,
                longitude=detection.location.longitude,
                call_frequency=call_frequency,
                call_intensity=call_intensity,
                call_duration_pattern=call_duration_pattern,
                spatial_clustering=spatial_clustering,
                temporal_clustering=temporal_clustering,
                estimated_speed=movement_data.get('speed'),
                estimated_direction=movement_data.get('direction'),
                foraging_probability=foraging_prob,
                social_activity_score=social_score,
                **env_context
            )
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting behavioral features: {e}")
            return None
    
    def _get_detection_context(self, detection: WhaleDetection, time_window_min: int = 60) -> List[WhaleDetection]:
        """Get nearby detections in space and time"""
        context_detections = []
        
        time_threshold = timedelta(minutes=time_window_min)
        
        for other_detection in self.detection_history:
            if other_detection.detection_id == detection.detection_id:
                continue
            
            # Check temporal proximity
            time_diff = abs(detection.timestamp - other_detection.timestamp)
            if time_diff > time_threshold:
                continue
            
            # Check spatial proximity
            distance_km = self._calculate_distance_km(
                detection.location.latitude, detection.location.longitude,
                other_detection.location.latitude, other_detection.location.longitude
            )
            
            if distance_km <= self.spatial_threshold_km:
                context_detections.append(other_detection)
        
        return context_detections
    
    def _calculate_distance_km(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in kilometers"""
        from math import radians, cos, sin, asin, sqrt
        
        # Haversine formula
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Radius of earth in kilometers
        return c * r
    
    def _calculate_call_frequency(self, detection: WhaleDetection, context: List[WhaleDetection]) -> float:
        """Calculate call frequency in calls per minute"""
        if not context:
            return 1.0  # Single call
        
        # Count calls in the last 10 minutes
        recent_time = detection.timestamp - timedelta(minutes=10)
        recent_calls = [d for d in context if d.timestamp >= recent_time]
        
        return len(recent_calls) / 10.0  # calls per minute
    
    def _analyze_call_duration_pattern(self, detection: WhaleDetection) -> List[float]:
        """Analyze call duration patterns from predictions"""
        durations = []
        
        for prediction in detection.predictions:
            duration = prediction.get('duration', 2.5)  # Default 2.5s
            durations.append(duration)
        
        if not durations:
            durations = [2.5]  # Default call duration
        
        return durations
    
    def _calculate_spatial_clustering(self, detection: WhaleDetection, context: List[WhaleDetection]) -> float:
        """Calculate spatial clustering coefficient"""
        if len(context) < 2:
            return 0.0
        
        # Get coordinates of all detections
        coords = [(detection.location.latitude, detection.location.longitude)]
        coords.extend([(d.location.latitude, d.location.longitude) for d in context])
        
        # Calculate pairwise distances
        distances = cdist(coords, coords, metric='euclidean')
        
        # Calculate clustering coefficient (inverse of mean distance)
        mean_distance = np.mean(distances[distances > 0])
        return 1.0 / (1.0 + mean_distance * 100)  # Normalized clustering score
    
    def _calculate_temporal_clustering(self, detection: WhaleDetection, context: List[WhaleDetection]) -> float:
        """Calculate temporal clustering coefficient"""
        if not context:
            return 0.0
        
        # Get time differences in minutes
        time_diffs = []
        for other in context:
            diff_min = abs((detection.timestamp - other.timestamp).total_seconds()) / 60.0
            time_diffs.append(diff_min)
        
        if not time_diffs:
            return 0.0
        
        # Calculate clustering coefficient (inverse of mean time difference)
        mean_time_diff = np.mean(time_diffs)
        return 1.0 / (1.0 + mean_time_diff / 30.0)  # Normalized by 30-minute window
    
    def _infer_movement_patterns(self, detection: WhaleDetection, context: List[WhaleDetection]) -> Dict:
        """Infer movement speed and direction from detection patterns"""
        movement_data = {'speed': None, 'direction': None}
        
        if len(context) < 2:
            return movement_data
        
        # Sort context by time
        sorted_context = sorted(context, key=lambda x: x.timestamp)
        
        # Calculate movement between consecutive detections
        speeds = []
        directions = []
        
        prev_detection = detection
        for next_detection in sorted_context[:3]:  # Use up to 3 points
            # Calculate distance and time
            distance_km = self._calculate_distance_km(
                prev_detection.location.latitude, prev_detection.location.longitude,
                next_detection.location.latitude, next_detection.location.longitude
            )
            
            time_hours = abs((next_detection.timestamp - prev_detection.timestamp).total_seconds()) / 3600.0
            
            if time_hours > 0 and distance_km > 0.1:  # Minimum movement threshold
                speed_kmh = distance_km / time_hours
                if speed_kmh <= 50:  # Reasonable whale speed limit
                    speeds.append(speed_kmh)
                    
                    # Calculate bearing (simplified)
                    lat_diff = next_detection.location.latitude - prev_detection.location.latitude
                    lon_diff = next_detection.location.longitude - prev_detection.location.longitude
                    direction = np.degrees(np.arctan2(lon_diff, lat_diff))
                    directions.append(direction)
            
            prev_detection = next_detection
        
        if speeds:
            movement_data['speed'] = np.mean(speeds)
        if directions:
            movement_data['direction'] = np.mean(directions)
        
        return movement_data
    
    def _calculate_foraging_probability(self, detection: WhaleDetection, context: List[WhaleDetection]) -> float:
        """Calculate probability that whales are foraging"""
        foraging_indicators = 0.0
        
        # High call frequency suggests social foraging
        call_freq = self._calculate_call_frequency(detection, context)
        if call_freq > 3.0:  # More than 3 calls per minute
            foraging_indicators += 0.3
        
        # Spatial clustering suggests feeding aggregation
        spatial_clustering = self._calculate_spatial_clustering(detection, context)
        if spatial_clustering > 0.5:
            foraging_indicators += 0.3
        
        # Multiple call types suggest foraging communication
        call_durations = self._analyze_call_duration_pattern(detection)
        duration_variety = len(set([round(d, 1) for d in call_durations]))
        if duration_variety > 1:
            foraging_indicators += 0.2
        
        # Low movement speed suggests stationary feeding
        movement = self._infer_movement_patterns(detection, context)
        if movement['speed'] and movement['speed'] < 5.0:  # Less than 5 km/h
            foraging_indicators += 0.2
        
        return min(1.0, foraging_indicators)
    
    def _calculate_social_activity_score(self, detection: WhaleDetection, context: List[WhaleDetection]) -> float:
        """Calculate social activity score"""
        social_score = 0.0
        
        # Number of nearby detections
        nearby_count = len(context)
        social_score += min(0.4, nearby_count * 0.1)
        
        # Temporal clustering suggests coordinated activity
        temporal_clustering = self._calculate_temporal_clustering(detection, context)
        social_score += temporal_clustering * 0.3
        
        # High confidence suggests clear vocalizations
        confidence_score = detection.confidence / 100.0
        social_score += confidence_score * 0.3
        
        return min(1.0, social_score)
    
    async def _get_environmental_context(self, detection: WhaleDetection) -> Dict:
        """Get environmental context for the detection"""
        # Simplified environmental context
        # In a full implementation, this would integrate with NOAA APIs
        
        # Estimate depth zone based on location
        depth_zone = "medium"  # Default
        if detection.location.latitude > 48.5:  # Northern areas tend to be deeper
            depth_zone = "deep"
        elif detection.location.longitude > -122.5:  # Eastern areas tend to be shallower
            depth_zone = "shallow"
        
        return {
            'depth_zone': depth_zone,
            'current_strength': 0.5,  # Placeholder
            'tidal_phase': "rising"   # Placeholder
        }
    
    async def save_behavioral_features(self, features: BehavioralFeatures):
        """Save behavioral features to Firestore"""
        if not self.firestore_client:
            return
        
        try:
            doc_ref = self.firestore_client.collection('orcahello_behavioral_features').document(
                features.detection_id
            )
            
            features_dict = asdict(features)
            # Convert datetime to string for Firestore
            features_dict['timestamp'] = features.timestamp.isoformat()
            
            doc_ref.set(features_dict)
            logger.debug(f"Saved behavioral features for detection {features.detection_id}")
            
        except Exception as e:
            logger.error(f"Error saving behavioral features: {e}")
    
    async def generate_behavioral_insights(self) -> Dict:
        """Generate high-level behavioral insights from recent features"""
        if not self.behavioral_features:
            return {}
        
        recent_features = [
            f for f in self.behavioral_features 
            if f.timestamp > datetime.now() - timedelta(hours=6)
        ]
        
        if not recent_features:
            return {}
        
        insights = {
            'summary': {
                'total_detections': len(recent_features),
                'avg_foraging_probability': np.mean([f.foraging_probability for f in recent_features]),
                'avg_social_activity': np.mean([f.social_activity_score for f in recent_features]),
                'active_locations': len(set([f.location_id for f in recent_features])),
            },
            'hotspots': self._identify_behavioral_hotspots(recent_features),
            'movement_patterns': self._analyze_movement_patterns(recent_features),
            'behavioral_state': self._infer_behavioral_state(recent_features),
            'timestamp': datetime.now().isoformat()
        }
        
        return insights
    
    def _identify_behavioral_hotspots(self, features: List[BehavioralFeatures]) -> List[Dict]:
        """Identify locations with high behavioral activity"""
        location_activity = {}
        
        for feature in features:
            loc_id = feature.location_id
            if loc_id not in location_activity:
                location_activity[loc_id] = {
                    'detection_count': 0,
                    'avg_foraging_prob': 0,
                    'avg_social_score': 0,
                    'coordinates': (feature.latitude, feature.longitude)
                }
            
            loc_data = location_activity[loc_id]
            loc_data['detection_count'] += 1
            loc_data['avg_foraging_prob'] = (
                (loc_data['avg_foraging_prob'] * (loc_data['detection_count'] - 1) + 
                 feature.foraging_probability) / loc_data['detection_count']
            loc_data['avg_social_score'] = (
                (loc_data['avg_social_score'] * (loc_data['detection_count'] - 1) + 
                 feature.social_activity_score) / loc_data['detection_count']
        
        # Sort by activity level
        hotspots = [
            {
                'location_id': loc_id,
                'coordinates': data['coordinates'],
                'activity_score': data['detection_count'] * data['avg_foraging_prob'] * data['avg_social_score'],
                'detection_count': data['detection_count'],
                'foraging_probability': data['avg_foraging_prob'],
                'social_activity': data['avg_social_score']
            }
            for loc_id, data in location_activity.items()
        ]
        
        return sorted(hotspots, key=lambda x: x['activity_score'], reverse=True)
    
    def _analyze_movement_patterns(self, features: List[BehavioralFeatures]) -> Dict:
        """Analyze movement patterns from behavioral features"""
        speeds = [f.estimated_speed for f in features if f.estimated_speed is not None]
        directions = [f.estimated_direction for f in features if f.estimated_direction is not None]
        
        movement_analysis = {
            'avg_speed_kmh': np.mean(speeds) if speeds else None,
            'speed_variance': np.var(speeds) if speeds else None,
            'dominant_direction': np.mean(directions) if directions else None,
            'movement_consistency': 1.0 - (np.std(directions) / 180.0) if directions else None
        }
        
        return movement_analysis
    
    def _infer_behavioral_state(self, features: List[BehavioralFeatures]) -> str:
        """Infer overall behavioral state"""
        avg_foraging = np.mean([f.foraging_probability for f in features])
        avg_social = np.mean([f.social_activity_score for f in features])
        
        if avg_foraging > 0.7:
            return "active_foraging"
        elif avg_social > 0.6:
            return "social_interaction"
        elif avg_foraging > 0.4 and avg_social > 0.4:
            return "mixed_activity"
        else:
            return "traveling"
    
    async def save_behavioral_insights(self, insights: Dict):
        """Save behavioral insights to Firestore"""
        if not self.firestore_client or not insights:
            return
        
        try:
            doc_ref = self.firestore_client.collection('orcahello_behavioral_insights').document(
                f"insights_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            
            doc_ref.set(insights)
            logger.info("Saved behavioral insights to Firestore")
            
        except Exception as e:
            logger.error(f"Error saving behavioral insights: {e}")

# Example usage
async def test_behavioral_processor():
    """Test the behavioral processor"""
    processor = OrcaHelloBehavioralProcessor()
    
    print("🧠 Testing OrcaHello Behavioral Processor...")
    
    # Process recent detections
    await processor.integration_client.get_recent_whale_activity(hours_back=6)
    
    # Generate insights
    insights = await processor.generate_behavioral_insights()
    
    print(f"\n📊 Behavioral Insights:")
    if insights and 'summary' in insights:
        summary = insights['summary']
        print(f"Total detections: {summary.get('total_detections', 0)}")
        print(f"Avg foraging probability: {summary.get('avg_foraging_probability', 0):.2f}")
        print(f"Avg social activity: {summary.get('avg_social_activity', 0):.2f}")
        print(f"Behavioral state: {insights.get('behavioral_state', 'unknown')}")

if __name__ == "__main__":
    asyncio.run(test_behavioral_processor()) 