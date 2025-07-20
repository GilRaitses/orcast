"""
ORCAST-OrcaHello Multi-Agent Integration System
Connects real-time whale detection data with behavioral modeling and trip planning
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import json
import numpy as np
from dataclasses import asdict
import firebase_admin
from firebase_admin import firestore

from orcahello_api_client import ORCASTOrcaHelloIntegration, WhaleDetection
from orcahello_behavioral_processor import OrcaHelloBehavioralProcessor, BehavioralFeatures

logger = logging.getLogger(__name__)

class ORCASTOrcaHelloOrchestrator:
    """
    Master orchestrator that integrates OrcaHello real-time data 
    with ORCAST multi-agent whale watching optimization system
    """
    
    def __init__(self, firestore_client=None):
        self.orcahello_integration = ORCASTOrcaHelloIntegration()
        self.behavioral_processor = OrcaHelloBehavioralProcessor(firestore_client)
        
        # Initialize Firebase
        if not firestore_client:
            try:
                if not firebase_admin._apps:
                    firebase_admin.initialize_app()
                self.firestore_client = firestore.client()
            except Exception as e:
                logger.warning(f"Could not initialize Firebase: {e}")
                self.firestore_client = None
        else:
            self.firestore_client = firestore_client
        
        # System state
        self.active_predictions = {}
        self.route_recommendations = {}
        self.behavioral_insights = {}
        
        # Configuration
        self.prediction_horizon_hours = 6
        self.update_interval_minutes = 5
        self.confidence_threshold = 0.3
    
    async def start_real_time_orchestration(self):
        """Start the real-time ORCAST-OrcaHello orchestration system"""
        logger.info("🚀 Starting ORCAST-OrcaHello Real-Time Orchestration System")
        
        # Start parallel tasks
        tasks = [
            self._run_behavioral_processing_loop(),
            self._run_route_optimization_loop(),
            self._run_prediction_update_loop(),
            self._run_data_sync_loop()
        ]
        
        await asyncio.gather(*tasks)
    
    async def _run_behavioral_processing_loop(self):
        """Run continuous behavioral processing from OrcaHello data"""
        logger.info("🧠 Starting behavioral processing loop...")
        
        while True:
            try:
                # Get recent whale activity from OrcaHello
                activity = await self.orcahello_integration.get_recent_whale_activity(
                    hours_back=self.prediction_horizon_hours
                )
                
                # Process through behavioral models
                behavioral_insights = await self._generate_behavioral_predictions(activity)
                
                # Update system state
                self.behavioral_insights = behavioral_insights
                
                # Save to Firebase
                await self._save_behavioral_predictions(behavioral_insights)
                
                logger.info(f"Updated behavioral insights: {len(behavioral_insights.get('hotspots', []))} hotspots identified")
                
                # Wait before next update
                await asyncio.sleep(self.update_interval_minutes * 60)
                
            except Exception as e:
                logger.error(f"Error in behavioral processing loop: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def _run_route_optimization_loop(self):
        """Run continuous route optimization based on behavioral insights"""
        logger.info("🗺️ Starting route optimization loop...")
        
        while True:
            try:
                if self.behavioral_insights:
                    # Generate optimized routes
                    routes = await self._optimize_whale_watching_routes()
                    
                    # Update route recommendations
                    self.route_recommendations = routes
                    
                    # Save to Firebase
                    await self._save_route_recommendations(routes)
                    
                    logger.info(f"Updated route recommendations: {len(routes.get('recommended_routes', []))} routes")
                
                # Wait before next optimization
                await asyncio.sleep(self.update_interval_minutes * 60 * 2)  # Every 10 minutes
                
            except Exception as e:
                logger.error(f"Error in route optimization loop: {e}")
                await asyncio.sleep(600)  # Wait 10 minutes on error
    
    async def _run_prediction_update_loop(self):
        """Run continuous prediction updates for whale locations"""
        logger.info("🔮 Starting prediction update loop...")
        
        while True:
            try:
                # Generate forward predictions using behavioral models
                predictions = await self._generate_whale_location_predictions()
                
                # Update active predictions
                self.active_predictions = predictions
                
                # Save to Firebase
                await self._save_whale_predictions(predictions)
                
                logger.info(f"Updated whale predictions: {len(predictions.get('location_predictions', []))} predictions")
                
                # Wait before next prediction update
                await asyncio.sleep(self.update_interval_minutes * 60)
                
            except Exception as e:
                logger.error(f"Error in prediction update loop: {e}")
                await asyncio.sleep(300)
    
    async def _run_data_sync_loop(self):
        """Run continuous data synchronization with Firebase"""
        logger.info("🔄 Starting data sync loop...")
        
        while True:
            try:
                # Sync system state to Firebase
                system_state = {
                    'last_update': datetime.now().isoformat(),
                    'active_predictions': len(self.active_predictions.get('location_predictions', [])),
                    'route_recommendations': len(self.route_recommendations.get('recommended_routes', [])),
                    'behavioral_hotspots': len(self.behavioral_insights.get('hotspots', [])),
                    'system_status': 'active'
                }
                
                await self._save_system_state(system_state)
                
                # Wait before next sync
                await asyncio.sleep(60)  # Every minute
                
            except Exception as e:
                logger.error(f"Error in data sync loop: {e}")
                await asyncio.sleep(120)
    
    async def _generate_behavioral_predictions(self, activity_data: Dict) -> Dict:
        """Generate behavioral predictions from OrcaHello activity data"""
        try:
            # Extract hotspots from activity data
            hotspots = activity_data.get('recent_activity_hotspots', [])
            
            behavioral_predictions = {
                'timestamp': datetime.now().isoformat(),
                'data_source': 'orcahello',
                'hotspots': [],
                'behavioral_patterns': {},
                'foraging_zones': [],
                'social_interaction_areas': [],
                'movement_corridors': []
            }
            
            # Process each hotspot
            for hotspot in hotspots:
                # Enhanced behavioral analysis
                behavioral_features = await self._analyze_hotspot_behavior(hotspot)
                
                enhanced_hotspot = {
                    'location': hotspot['location'],
                    'coordinates': hotspot['coordinates'],
                    'activity_score': hotspot['activity_score'],
                    'detection_count': hotspot['detection_count'],
                    'behavioral_features': behavioral_features,
                    'predicted_activity_trend': await self._predict_activity_trend(hotspot),
                    'whale_watching_suitability': self._calculate_watching_suitability(hotspot, behavioral_features)
                }
                
                behavioral_predictions['hotspots'].append(enhanced_hotspot)
                
                # Categorize by behavior
                if behavioral_features.get('foraging_probability', 0) > 0.6:
                    behavioral_predictions['foraging_zones'].append(enhanced_hotspot)
                
                if behavioral_features.get('social_activity_score', 0) > 0.5:
                    behavioral_predictions['social_interaction_areas'].append(enhanced_hotspot)
            
            # Identify movement corridors
            behavioral_predictions['movement_corridors'] = await self._identify_movement_corridors(hotspots)
            
            return behavioral_predictions
            
        except Exception as e:
            logger.error(f"Error generating behavioral predictions: {e}")
            return {}
    
    async def _analyze_hotspot_behavior(self, hotspot: Dict) -> Dict:
        """Analyze behavioral characteristics of a hotspot"""
        # This would integrate with the SINDy behavioral models
        # For now, we'll create a simplified analysis
        
        behavior_analysis = {
            'foraging_probability': 0.5 + (hotspot['activity_score'] * 0.3),
            'social_activity_score': min(1.0, hotspot['detection_count'] * 0.1),
            'temporal_stability': 0.7,  # Placeholder for temporal analysis
            'environmental_favorability': 0.6,  # Placeholder for environmental factors
            'accessibility_score': self._calculate_accessibility(hotspot['coordinates'])
        }
        
        return behavior_analysis
    
    def _calculate_accessibility(self, coordinates: Tuple[float, float]) -> float:
        """Calculate how accessible a location is for whale watching boats"""
        lat, lon = coordinates
        
        # Simple accessibility calculation based on proximity to common departure points
        departure_points = [
            (48.5583, -123.1736),  # Orcasound Lab area
            (48.5499, -123.2167),  # Another area
            (47.3892, -122.3727)   # Point Robinson area
        ]
        
        min_distance = float('inf')
        for dep_lat, dep_lon in departure_points:
            distance = ((lat - dep_lat) ** 2 + (lon - dep_lon) ** 2) ** 0.5
            min_distance = min(min_distance, distance)
        
        # Normalize to 0-1 scale (closer = higher accessibility)
        return max(0.1, 1.0 - (min_distance * 10))
    
    async def _predict_activity_trend(self, hotspot: Dict) -> str:
        """Predict activity trend for a hotspot"""
        # Simplified trend prediction
        activity_score = hotspot['activity_score']
        detection_count = hotspot['detection_count']
        
        if activity_score > 5.0 and detection_count > 5:
            return "increasing"
        elif activity_score > 2.0 and detection_count > 2:
            return "stable"
        else:
            return "decreasing"
    
    def _calculate_watching_suitability(self, hotspot: Dict, behavioral_features: Dict) -> float:
        """Calculate how suitable a location is for whale watching"""
        suitability_score = 0.0
        
        # Activity level (30%)
        activity_component = min(1.0, hotspot['activity_score'] / 10.0) * 0.3
        suitability_score += activity_component
        
        # Behavioral predictability (25%)
        behavioral_component = behavioral_features.get('temporal_stability', 0.5) * 0.25
        suitability_score += behavioral_component
        
        # Accessibility (25%)
        accessibility_component = behavioral_features.get('accessibility_score', 0.5) * 0.25
        suitability_score += accessibility_component
        
        # Environmental factors (20%)
        environmental_component = behavioral_features.get('environmental_favorability', 0.5) * 0.2
        suitability_score += environmental_component
        
        return min(1.0, suitability_score)
    
    async def _identify_movement_corridors(self, hotspots: List[Dict]) -> List[Dict]:
        """Identify movement corridors between hotspots"""
        corridors = []
        
        # Simple corridor identification based on hotspot proximity
        for i, hotspot1 in enumerate(hotspots):
            for j, hotspot2 in enumerate(hotspots[i+1:], i+1):
                coord1 = hotspot1['coordinates']
                coord2 = hotspot2['coordinates']
                
                # Calculate distance
                distance_km = self._calculate_distance_km(
                    coord1[0], coord1[1], coord2[0], coord2[1]
                )
                
                # If hotspots are reasonably close, consider a corridor
                if 5 <= distance_km <= 25:  # 5-25 km apart
                    corridor_strength = (
                        hotspot1['activity_score'] + hotspot2['activity_score']
                    ) / distance_km
                    
                    corridor = {
                        'start_location': hotspot1['location'],
                        'end_location': hotspot2['location'],
                        'start_coordinates': coord1,
                        'end_coordinates': coord2,
                        'distance_km': distance_km,
                        'corridor_strength': corridor_strength,
                        'estimated_travel_time_hours': distance_km / 8  # Assume 8 km/h whale speed
                    }
                    
                    corridors.append(corridor)
        
        # Sort by corridor strength
        corridors.sort(key=lambda x: x['corridor_strength'], reverse=True)
        
        return corridors[:5]  # Return top 5 corridors
    
    def _calculate_distance_km(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in kilometers"""
        from math import radians, cos, sin, asin, sqrt
        
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Radius of earth in kilometers
        return c * r
    
    async def _optimize_whale_watching_routes(self) -> Dict:
        """Optimize whale watching routes based on behavioral insights"""
        try:
            hotspots = self.behavioral_insights.get('hotspots', [])
            corridors = self.behavioral_insights.get('movement_corridors', [])
            
            route_optimization = {
                'timestamp': datetime.now().isoformat(),
                'recommended_routes': [],
                'optimal_departure_times': [],
                'route_success_probabilities': {}
            }
            
            # Generate route recommendations
            for i, primary_hotspot in enumerate(hotspots[:3]):  # Top 3 hotspots
                route = await self._generate_route_to_hotspot(primary_hotspot, hotspots, corridors)
                if route:
                    route_optimization['recommended_routes'].append(route)
            
            # Calculate optimal departure times
            departure_times = await self._calculate_optimal_departure_times(hotspots)
            route_optimization['optimal_departure_times'] = departure_times
            
            return route_optimization
            
        except Exception as e:
            logger.error(f"Error optimizing routes: {e}")
            return {}
    
    async def _generate_route_to_hotspot(
        self, 
        primary_hotspot: Dict, 
        all_hotspots: List[Dict], 
        corridors: List[Dict]
    ) -> Optional[Dict]:
        """Generate optimized route to a primary hotspot"""
        
        route = {
            'route_id': f"route_{primary_hotspot['location'].replace(' ', '_').lower()}",
            'primary_destination': primary_hotspot,
            'waypoints': [],
            'estimated_duration_hours': 0,
            'success_probability': primary_hotspot['whale_watching_suitability'],
            'route_type': 'direct',
            'recommendations': []
        }
        
        # Add secondary hotspots if they're on the way
        for hotspot in all_hotspots:
            if hotspot['location'] != primary_hotspot['location']:
                # Check if this hotspot is reasonably close to primary
                distance = self._calculate_distance_km(
                    primary_hotspot['coordinates'][0], primary_hotspot['coordinates'][1],
                    hotspot['coordinates'][0], hotspot['coordinates'][1]
                )
                
                if distance <= 15:  # Within 15 km
                    route['waypoints'].append({
                        'location': hotspot,
                        'detour_distance_km': distance,
                        'additional_probability': hotspot['whale_watching_suitability'] * 0.3
                    })
        
        # Calculate route metrics
        route['estimated_duration_hours'] = 2 + len(route['waypoints']) * 0.5
        route['success_probability'] += sum([w['additional_probability'] for w in route['waypoints']])
        route['success_probability'] = min(1.0, route['success_probability'])
        
        # Add route recommendations
        if primary_hotspot['behavioral_features']['foraging_probability'] > 0.6:
            route['recommendations'].append("High foraging activity - expect feeding behaviors")
        
        if primary_hotspot['detection_count'] > 5:
            route['recommendations'].append("Multiple recent detections - high encounter probability")
        
        if len(route['waypoints']) > 0:
            route['route_type'] = 'multi_stop'
            route['recommendations'].append(f"Consider {len(route['waypoints'])} additional viewing locations")
        
        return route
    
    async def _calculate_optimal_departure_times(self, hotspots: List[Dict]) -> List[Dict]:
        """Calculate optimal departure times based on whale activity patterns"""
        departure_times = []
        
        # Simple heuristic: whales are often more active in early morning and late afternoon
        base_times = [
            {'time': '06:00', 'period': 'early_morning', 'activity_modifier': 1.2},
            {'time': '08:00', 'period': 'morning', 'activity_modifier': 1.0},
            {'time': '14:00', 'period': 'afternoon', 'activity_modifier': 0.8},
            {'time': '16:00', 'period': 'late_afternoon', 'activity_modifier': 1.1},
        ]
        
        for time_slot in base_times:
            # Calculate expected success rate for this departure time
            success_rate = 0.5 * time_slot['activity_modifier']  # Base rate
            
            # Add boost based on current hotspot activity
            if hotspots:
                avg_suitability = np.mean([h['whale_watching_suitability'] for h in hotspots])
                success_rate += avg_suitability * 0.3
            
            departure_times.append({
                'departure_time': time_slot['time'],
                'period': time_slot['period'],
                'expected_success_rate': min(1.0, success_rate),
                'recommended_duration_hours': 3 if time_slot['period'] in ['morning', 'afternoon'] else 2,
                'confidence_level': 0.7
            })
        
        return departure_times
    
    async def _generate_whale_location_predictions(self) -> Dict:
        """Generate forward predictions for whale locations"""
        try:
            predictions = {
                'timestamp': datetime.now().isoformat(),
                'prediction_horizon_hours': self.prediction_horizon_hours,
                'location_predictions': [],
                'movement_predictions': [],
                'confidence_intervals': {}
            }
            
            # Use current behavioral insights to predict future locations
            hotspots = self.behavioral_insights.get('hotspots', [])
            corridors = self.behavioral_insights.get('movement_corridors', [])
            
            # Generate location predictions for each hotspot
            for hotspot in hotspots:
                location_prediction = await self._predict_hotspot_evolution(hotspot)
                predictions['location_predictions'].append(location_prediction)
            
            # Generate movement predictions along corridors
            for corridor in corridors:
                movement_prediction = await self._predict_corridor_activity(corridor)
                predictions['movement_predictions'].append(movement_prediction)
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error generating whale predictions: {e}")
            return {}
    
    async def _predict_hotspot_evolution(self, hotspot: Dict) -> Dict:
        """Predict how a hotspot will evolve over time"""
        current_activity = hotspot['activity_score']
        trend = hotspot.get('predicted_activity_trend', 'stable')
        
        # Simple trend-based prediction
        if trend == 'increasing':
            predicted_activity = min(10.0, current_activity * 1.2)
        elif trend == 'decreasing':
            predicted_activity = max(1.0, current_activity * 0.8)
        else:  # stable
            predicted_activity = current_activity
        
        prediction = {
            'location': hotspot['location'],
            'coordinates': hotspot['coordinates'],
            'current_activity': current_activity,
            'predicted_activity': predicted_activity,
            'prediction_confidence': 0.7,
            'recommended_visit_window': self._calculate_visit_window(predicted_activity, trend),
            'expected_encounter_probability': min(1.0, predicted_activity / 10.0)
        }
        
        return prediction
    
    def _calculate_visit_window(self, activity_level: float, trend: str) -> Dict:
        """Calculate optimal visit window for a location"""
        base_window = 2  # hours
        
        if activity_level > 5.0:
            window_hours = base_window + 1
        elif activity_level < 2.0:
            window_hours = base_window - 0.5
        else:
            window_hours = base_window
        
        # Adjust based on trend
        if trend == 'increasing':
            start_offset = 0  # Visit soon
        elif trend == 'decreasing':
            start_offset = 1  # Visit immediately
        else:
            start_offset = 0.5  # Flexible timing
        
        now = datetime.now()
        start_time = now + timedelta(hours=start_offset)
        end_time = start_time + timedelta(hours=window_hours)
        
        return {
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_hours': window_hours,
            'urgency': 'high' if trend == 'decreasing' else 'medium'
        }
    
    async def _predict_corridor_activity(self, corridor: Dict) -> Dict:
        """Predict activity along movement corridors"""
        prediction = {
            'corridor_id': f"{corridor['start_location']}_{corridor['end_location']}",
            'start_coordinates': corridor['start_coordinates'],
            'end_coordinates': corridor['end_coordinates'],
            'predicted_transit_probability': min(1.0, corridor['corridor_strength'] / 5.0),
            'estimated_transit_time': corridor['estimated_travel_time_hours'],
            'optimal_intercept_location': self._calculate_intercept_point(corridor),
            'intercept_timing': self._calculate_intercept_timing(corridor)
        }
        
        return prediction
    
    def _calculate_intercept_point(self, corridor: Dict) -> Dict:
        """Calculate optimal intercept point along corridor"""
        # Midpoint of corridor
        start_coords = corridor['start_coordinates']
        end_coords = corridor['end_coordinates']
        
        mid_lat = (start_coords[0] + end_coords[0]) / 2
        mid_lon = (start_coords[1] + end_coords[1]) / 2
        
        return {
            'latitude': mid_lat,
            'longitude': mid_lon,
            'distance_from_start_km': corridor['distance_km'] / 2
        }
    
    def _calculate_intercept_timing(self, corridor: Dict) -> Dict:
        """Calculate optimal timing to intercept whales in corridor"""
        transit_time = corridor['estimated_travel_time_hours']
        
        # Assume whales started transit recently, intercept at midpoint
        intercept_delay = transit_time / 2
        
        intercept_time = datetime.now() + timedelta(hours=intercept_delay)
        
        return {
            'intercept_time': intercept_time.isoformat(),
            'confidence': 0.6,
            'time_window_hours': 1.0  # ±1 hour window
        }
    
    # Firebase integration methods
    async def _save_behavioral_predictions(self, predictions: Dict):
        """Save behavioral predictions to Firebase"""
        if not self.firestore_client or not predictions:
            return
        
        try:
            doc_ref = self.firestore_client.collection('orcast_behavioral_predictions').document(
                f"predictions_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            doc_ref.set(predictions)
            logger.debug("Saved behavioral predictions to Firebase")
        except Exception as e:
            logger.error(f"Error saving behavioral predictions: {e}")
    
    async def _save_route_recommendations(self, routes: Dict):
        """Save route recommendations to Firebase"""
        if not self.firestore_client or not routes:
            return
        
        try:
            doc_ref = self.firestore_client.collection('orcast_route_recommendations').document(
                f"routes_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            doc_ref.set(routes)
            logger.debug("Saved route recommendations to Firebase")
        except Exception as e:
            logger.error(f"Error saving route recommendations: {e}")
    
    async def _save_whale_predictions(self, predictions: Dict):
        """Save whale predictions to Firebase"""
        if not self.firestore_client or not predictions:
            return
        
        try:
            doc_ref = self.firestore_client.collection('orcast_whale_predictions').document(
                f"whale_predictions_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            doc_ref.set(predictions)
            logger.debug("Saved whale predictions to Firebase")
        except Exception as e:
            logger.error(f"Error saving whale predictions: {e}")
    
    async def _save_system_state(self, state: Dict):
        """Save system state to Firebase"""
        if not self.firestore_client:
            return
        
        try:
            doc_ref = self.firestore_client.collection('orcast_system_state').document('current_state')
            doc_ref.set(state)
        except Exception as e:
            logger.error(f"Error saving system state: {e}")
    
    async def get_current_recommendations(self) -> Dict:
        """Get current whale watching recommendations"""
        return {
            'behavioral_insights': self.behavioral_insights,
            'route_recommendations': self.route_recommendations,
            'whale_predictions': self.active_predictions,
            'last_updated': datetime.now().isoformat(),
            'system_confidence': self._calculate_system_confidence()
        }
    
    def _calculate_system_confidence(self) -> float:
        """Calculate overall system confidence"""
        # Simple confidence calculation based on data recency and quantity
        confidence_factors = []
        
        # Data recency factor
        if self.behavioral_insights:
            hotspot_count = len(self.behavioral_insights.get('hotspots', []))
            if hotspot_count > 0:
                confidence_factors.append(min(1.0, hotspot_count / 5.0))
        
        # Route quality factor
        if self.route_recommendations:
            route_count = len(self.route_recommendations.get('recommended_routes', []))
            if route_count > 0:
                avg_success_prob = np.mean([
                    route.get('success_probability', 0.5) 
                    for route in self.route_recommendations['recommended_routes']
                ])
                confidence_factors.append(avg_success_prob)
        
        if confidence_factors:
            return np.mean(confidence_factors)
        else:
            return 0.3  # Default low confidence

# Example usage and testing
async def test_orcast_orcahello_integration():
    """Test the full ORCAST-OrcaHello integration"""
    orchestrator = ORCASTOrcaHelloOrchestrator()
    
    print("🐋 Testing ORCAST-OrcaHello Multi-Agent Integration...")
    
    # Get current recommendations
    recommendations = await orchestrator.get_current_recommendations()
    
    print(f"\n📊 Current System Status:")
    print(f"System confidence: {orchestrator._calculate_system_confidence():.2f}")
    print(f"Active hotspots: {len(recommendations['behavioral_insights'].get('hotspots', []))}")
    print(f"Route recommendations: {len(recommendations['route_recommendations'].get('recommended_routes', []))}")
    
    # Run one cycle of behavioral processing
    await orchestrator._run_behavioral_processing_loop()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_orcast_orcahello_integration()) 