"""
Route Optimization Pipeline for ORCAST
Generates optimized whale watching routes based on behavioral analysis
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
import json
import firebase_admin
from firebase_admin import firestore
from geopy.distance import geodesic
import math

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ORCASTRouteOptimizer:
    """Route optimization system for whale watching"""
    
    def __init__(self):
        # Initialize Firebase
        try:
            if not firebase_admin._apps:
                firebase_admin.initialize_app()
            self.firestore_client = firestore.client()
        except Exception as e:
            logger.warning(f"Firebase initialization failed: {e}")
            self.firestore_client = None
        
        # Route optimization parameters
        self.max_route_duration_hours = 6
        self.max_travel_distance_km = 50
        self.min_success_probability = 0.3
        self.departure_locations = self._get_departure_locations()
        
        # Boat travel parameters
        self.boat_speed_kmh = 35  # Typical whale watching boat speed
        self.setup_time_minutes = 15  # Time for departure setup
        self.viewing_time_minutes = 30  # Minimum time at each location
    
    def _get_departure_locations(self) -> List[Dict]:
        """Get common whale watching departure locations"""
        return [
            {
                'id': 'friday_harbor',
                'name': 'Friday Harbor, San Juan Island',
                'latitude': 48.5344,
                'longitude': -123.0134,
                'region': 'San Juan Islands'
            },
            {
                'id': 'anacortes',
                'name': 'Anacortes',
                'latitude': 48.5126,
                'longitude': -122.6057,
                'region': 'North Puget Sound'
            },
            {
                'id': 'edmonds',
                'name': 'Edmonds',
                'latitude': 47.8107,
                'longitude': -122.3773,
                'region': 'Central Puget Sound'
            },
            {
                'id': 'seattle_waterfront',
                'name': 'Seattle Waterfront',
                'latitude': 47.6062,
                'longitude': -122.3321,
                'region': 'Central Puget Sound'
            }
        ]
    
    async def fetch_behavioral_insights(self) -> List[Dict]:
        """Fetch latest behavioral insights from Firestore"""
        
        if not self.firestore_client:
            logger.error("Firestore client not available")
            return []
        
        try:
            # Get recent behavioral insights
            insights_ref = self.firestore_client.collection('behavioral_insights')
            query = insights_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(5)
            
            docs = query.stream()
            insights_list = []
            
            for doc in docs:
                insight_data = doc.to_dict()
                insight_data['doc_id'] = doc.id
                insights_list.append(insight_data)
            
            logger.info(f"📊 Fetched {len(insights_list)} behavioral insight documents")
            return insights_list
            
        except Exception as e:
            logger.error(f"Failed to fetch behavioral insights: {e}")
            return []
    
    async def fetch_recent_detections_with_ml(self) -> List[Dict]:
        """Fetch recent detections with ML analysis results"""
        
        if not self.firestore_client:
            return []
        
        try:
            # Get recent detections that have been processed by ML
            detections_ref = self.firestore_client.collection('whale_detections')
            query = detections_ref.where('ml_analysis_pending', '==', False).limit(50)
            
            docs = query.stream()
            detections = []
            
            for doc in docs:
                detection_data = doc.to_dict()
                detection_data['doc_id'] = doc.id
                
                # Only include detections with ML analysis
                if 'ml_analysis' in detection_data:
                    detections.append(detection_data)
            
            logger.info(f"📍 Fetched {len(detections)} ML-processed detections")
            return detections
            
        except Exception as e:
            logger.error(f"Failed to fetch ML detections: {e}")
            return []
    
    def identify_hotspots(self, detections: List[Dict]) -> List[Dict]:
        """Identify current whale activity hotspots"""
        
        logger.info("🔥 Identifying whale activity hotspots...")
        
        if not detections:
            return []
        
        # Group detections by location/region
        location_groups = {}
        
        for detection in detections:
            try:
                # Use hydrophone as primary grouping
                hydrophone_id = detection.get('hydrophone_id', 'unknown')
                
                if hydrophone_id not in location_groups:
                    location_groups[hydrophone_id] = {
                        'detections': [],
                        'hydrophone_id': hydrophone_id,
                        'hydrophone_name': detection.get('hydrophone_name', 'Unknown'),
                        'region': detection.get('region', 'Unknown'),
                        'center_lat': detection.get('latitude', 0),
                        'center_lng': detection.get('longitude', 0)
                    }
                
                location_groups[hydrophone_id]['detections'].append(detection)
                
            except Exception as e:
                logger.warning(f"Error processing detection: {e}")
                continue
        
        # Calculate hotspot metrics
        hotspots = []
        
        for location_id, group in location_groups.items():
            try:
                detections_list = group['detections']
                
                if len(detections_list) < 1:
                    continue
                
                # Calculate aggregate metrics
                ml_analyses = [d.get('ml_analysis', {}) for d in detections_list if 'ml_analysis' in d]
                
                if not ml_analyses:
                    continue
                
                avg_foraging_prob = np.mean([ml.get('foraging_probability', 0) for ml in ml_analyses])
                avg_social_score = np.mean([ml.get('social_activity_score', 0) for ml in ml_analyses])
                avg_behavioral_score = np.mean([ml.get('behavioral_score', 0) for ml in ml_analyses])
                avg_confidence = np.mean([d.get('confidence', 0) for d in detections_list])
                
                # Calculate recency score (more recent = higher score)
                now = datetime.now()
                recency_scores = []
                
                for detection in detections_list:
                    try:
                        det_time = pd.to_datetime(detection['timestamp'])
                        hours_ago = (now - det_time.replace(tzinfo=None)).total_seconds() / 3600
                        recency_score = max(0, 1 - (hours_ago / 24))  # Decay over 24 hours
                        recency_scores.append(recency_score)
                    except:
                        recency_scores.append(0.5)  # Default moderate recency
                
                avg_recency = np.mean(recency_scores)
                
                # Calculate overall hotspot score
                hotspot_score = (
                    avg_behavioral_score * 0.3 +
                    avg_foraging_prob * 0.25 +
                    avg_social_score * 0.15 +
                    (avg_confidence / 100) * 0.15 +
                    avg_recency * 0.1 +
                    min(len(detections_list) / 5, 1.0) * 0.05  # Detection frequency bonus
                )
                
                hotspot = {
                    'hotspot_id': f"hotspot_{location_id}",
                    'hydrophone_id': location_id,
                    'name': group['hydrophone_name'],
                    'region': group['region'],
                    'center_coordinates': {
                        'latitude': group['center_lat'],
                        'longitude': group['center_lng']
                    },
                    'detection_count': len(detections_list),
                    'hotspot_score': hotspot_score,
                    'behavioral_metrics': {
                        'avg_foraging_probability': avg_foraging_prob,
                        'avg_social_activity': avg_social_score,
                        'avg_behavioral_score': avg_behavioral_score,
                        'avg_confidence': avg_confidence,
                        'recency_score': avg_recency
                    },
                    'latest_detection': max([d.get('timestamp', '') for d in detections_list]),
                    'recommended_visit_duration_minutes': self._calculate_visit_duration(avg_behavioral_score, len(detections_list))
                }
                
                hotspots.append(hotspot)
                
            except Exception as e:
                logger.warning(f"Error calculating hotspot metrics for {location_id}: {e}")
                continue
        
        # Sort by hotspot score
        hotspots.sort(key=lambda x: x['hotspot_score'], reverse=True)
        
        # Filter to meaningful hotspots
        significant_hotspots = [h for h in hotspots if h['hotspot_score'] >= self.min_success_probability]
        
        logger.info(f"🎯 Identified {len(significant_hotspots)} significant hotspots")
        
        return significant_hotspots
    
    def _calculate_visit_duration(self, behavioral_score: float, detection_count: int) -> int:
        """Calculate recommended visit duration for a hotspot"""
        
        base_duration = self.viewing_time_minutes
        
        # Increase duration for high activity
        if behavioral_score > 0.7:
            base_duration += 20
        elif behavioral_score > 0.5:
            base_duration += 10
        
        # Increase duration for multiple detections
        if detection_count > 3:
            base_duration += 15
        elif detection_count > 1:
            base_duration += 5
        
        return min(base_duration, 60)  # Max 1 hour per location
    
    def generate_optimized_routes(self, hotspots: List[Dict]) -> List[Dict]:
        """Generate optimized whale watching routes"""
        
        logger.info(f"🗺️ Generating optimized routes from {len(hotspots)} hotspots...")
        
        if not hotspots:
            return []
        
        routes = []
        
        # Generate routes from each departure location
        for departure in self.departure_locations:
            try:
                # Find hotspots within reasonable travel distance
                accessible_hotspots = []
                
                for hotspot in hotspots:
                    distance_km = self._calculate_distance(
                        departure['latitude'], departure['longitude'],
                        hotspot['center_coordinates']['latitude'],
                        hotspot['center_coordinates']['longitude']
                    )
                    
                    travel_time_hours = distance_km / self.boat_speed_kmh
                    
                    if distance_km <= self.max_travel_distance_km:
                        hotspot_with_travel = hotspot.copy()
                        hotspot_with_travel['distance_from_departure_km'] = distance_km
                        hotspot_with_travel['travel_time_hours'] = travel_time_hours
                        accessible_hotspots.append(hotspot_with_travel)
                
                if not accessible_hotspots:
                    continue
                
                # Sort by combination of score and proximity
                def route_priority(h):
                    return h['hotspot_score'] * 0.7 + (1 - min(h['distance_from_departure_km'] / 30, 1)) * 0.3
                
                accessible_hotspots.sort(key=route_priority, reverse=True)
                
                # Generate different route options
                route_options = self._generate_route_variations(departure, accessible_hotspots)
                routes.extend(route_options)
                
            except Exception as e:
                logger.warning(f"Error generating routes from {departure['name']}: {e}")
                continue
        
        # Sort all routes by success probability
        routes.sort(key=lambda r: r['success_probability'], reverse=True)
        
        # Return top routes
        top_routes = routes[:10]  # Top 10 routes
        logger.info(f"✅ Generated {len(top_routes)} optimized routes")
        
        return top_routes
    
    def _generate_route_variations(self, departure: Dict, hotspots: List[Dict]) -> List[Dict]:
        """Generate different route variations for a departure location"""
        
        route_variations = []
        
        # Single hotspot routes (highest priority hotspots)
        for i, hotspot in enumerate(hotspots[:3]):  # Top 3 hotspots
            route = self._create_single_hotspot_route(departure, hotspot, i)
            if route:
                route_variations.append(route)
        
        # Multi-hotspot routes (if time permits)
        if len(hotspots) >= 2:
            multi_routes = self._create_multi_hotspot_routes(departure, hotspots)
            route_variations.extend(multi_routes)
        
        return route_variations
    
    def _create_single_hotspot_route(self, departure: Dict, hotspot: Dict, priority_rank: int) -> Optional[Dict]:
        """Create a route to a single hotspot"""
        
        try:
            # Calculate timing
            travel_time_hours = hotspot['travel_time_hours']
            viewing_time_hours = hotspot['recommended_visit_duration_minutes'] / 60
            total_time_hours = (travel_time_hours * 2) + viewing_time_hours + (self.setup_time_minutes / 60)
            
            if total_time_hours > self.max_route_duration_hours:
                return None  # Route too long
            
            # Calculate success probability
            base_probability = hotspot['hotspot_score']
            proximity_bonus = max(0, (30 - hotspot['distance_from_departure_km']) / 30 * 0.1)
            success_probability = min(1.0, base_probability + proximity_bonus)
            
            # Determine optimal departure time
            optimal_departure = self._calculate_optimal_departure_time(total_time_hours)
            
            route = {
                'route_id': f"single_{departure['id']}_to_{hotspot['hotspot_id']}",
                'route_type': 'single_hotspot',
                'departure_location': departure,
                'primary_destination': hotspot,
                'waypoints': [hotspot],
                'total_distance_km': hotspot['distance_from_departure_km'] * 2,  # Round trip
                'estimated_duration_hours': total_time_hours,
                'success_probability': success_probability,
                'priority_rank': priority_rank + 1,
                'optimal_departure_times': optimal_departure,
                'route_summary': f"Direct route to {hotspot['name']} - {hotspot['detection_count']} recent detections",
                'recommendations': self._generate_route_recommendations(hotspot),
                'created_at': datetime.now().isoformat()
            }
            
            return route
            
        except Exception as e:
            logger.warning(f"Error creating single hotspot route: {e}")
            return None
    
    def _create_multi_hotspot_routes(self, departure: Dict, hotspots: List[Dict]) -> List[Dict]:
        """Create multi-hotspot routes"""
        
        multi_routes = []
        
        # Try combinations of top hotspots
        for i in range(len(hotspots[:3])):  # Consider top 3 hotspots
            for j in range(i + 1, len(hotspots[:3])):
                try:
                    hotspot1 = hotspots[i]
                    hotspot2 = hotspots[j]
                    
                    # Calculate inter-hotspot distance
                    inter_distance = self._calculate_distance(
                        hotspot1['center_coordinates']['latitude'],
                        hotspot1['center_coordinates']['longitude'],
                        hotspot2['center_coordinates']['latitude'],
                        hotspot2['center_coordinates']['longitude']
                    )
                    
                    # Check if route is feasible
                    total_distance = (hotspot1['distance_from_departure_km'] + 
                                    inter_distance + 
                                    hotspot2['distance_from_departure_km'])
                    
                    total_travel_time = total_distance / self.boat_speed_kmh
                    total_viewing_time = (hotspot1['recommended_visit_duration_minutes'] + 
                                        hotspot2['recommended_visit_duration_minutes']) / 60
                    total_time = total_travel_time + total_viewing_time + (self.setup_time_minutes / 60)
                    
                    if total_time <= self.max_route_duration_hours:
                        # Create multi-hotspot route
                        combined_success = (hotspot1['hotspot_score'] + hotspot2['hotspot_score']) / 2
                        
                        route = {
                            'route_id': f"multi_{departure['id']}_to_{hotspot1['hotspot_id']}_{hotspot2['hotspot_id']}",
                            'route_type': 'multi_hotspot',
                            'departure_location': departure,
                            'primary_destination': hotspot1,
                            'waypoints': [hotspot1, hotspot2],
                            'total_distance_km': total_distance,
                            'estimated_duration_hours': total_time,
                            'success_probability': combined_success * 0.9,  # Slight penalty for complexity
                            'priority_rank': 10 + i + j,  # Lower priority than single routes
                            'optimal_departure_times': self._calculate_optimal_departure_time(total_time),
                            'route_summary': f"Multi-location route: {hotspot1['name']} → {hotspot2['name']}",
                            'recommendations': self._generate_multi_route_recommendations([hotspot1, hotspot2]),
                            'created_at': datetime.now().isoformat()
                        }
                        
                        multi_routes.append(route)
                
                except Exception as e:
                    logger.warning(f"Error creating multi-hotspot route: {e}")
                    continue
        
        return multi_routes
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in kilometers"""
        return geodesic((lat1, lon1), (lat2, lon2)).kilometers
    
    def _calculate_optimal_departure_time(self, total_duration_hours: float) -> List[Dict]:
        """Calculate optimal departure times"""
        
        # Optimal times based on whale activity patterns and weather
        base_times = [
            {'time': '07:00', 'period': 'early_morning', 'conditions': 'calm_seas'},
            {'time': '09:00', 'period': 'morning', 'conditions': 'good_visibility'},
            {'time': '13:00', 'period': 'afternoon', 'conditions': 'stable_weather'},
            {'time': '15:30', 'period': 'late_afternoon', 'conditions': 'optimal_light'}
        ]
        
        optimal_times = []
        
        for time_option in base_times:
            departure_hour = int(time_option['time'].split(':')[0])
            return_hour = departure_hour + total_duration_hours
            
            # Check if return time is reasonable (before dark)
            if return_hour <= 19:  # Return by 7 PM
                optimal_times.append({
                    'departure_time': time_option['time'],
                    'estimated_return_time': f"{int(return_hour):02d}:{int((return_hour % 1) * 60):02d}",
                    'period': time_option['period'],
                    'conditions': time_option['conditions'],
                    'recommended': departure_hour in [7, 9]  # Prefer morning departures
                })
        
        return optimal_times
    
    def _generate_route_recommendations(self, hotspot: Dict) -> List[str]:
        """Generate specific recommendations for a route"""
        
        recommendations = []
        
        # Behavioral-based recommendations
        metrics = hotspot['behavioral_metrics']
        
        if metrics['avg_foraging_probability'] > 0.6:
            recommendations.append("High foraging activity detected - expect feeding behaviors and echolocation")
        
        if metrics['avg_social_activity'] > 0.5:
            recommendations.append("Social activity observed - multiple whales likely present")
        
        if metrics['recency_score'] > 0.8:
            recommendations.append("Very recent activity - high probability of current presence")
        
        if hotspot['detection_count'] > 3:
            recommendations.append(f"Active hotspot with {hotspot['detection_count']} recent detections")
        
        # General recommendations
        recommendations.append("Bring binoculars and camera for best viewing experience")
        recommendations.append("Check current weather conditions before departure")
        
        return recommendations
    
    def _generate_multi_route_recommendations(self, hotspots: List[Dict]) -> List[str]:
        """Generate recommendations for multi-hotspot routes"""
        
        recommendations = []
        recommendations.append(f"Multi-location tour visiting {len(hotspots)} active areas")
        recommendations.append("Allow flexibility in timing at each location based on whale activity")
        
        for i, hotspot in enumerate(hotspots):
            recommendations.append(f"Stop {i+1}: {hotspot['name']} - {hotspot['detection_count']} recent detections")
        
        return recommendations
    
    async def store_route_recommendations(self, routes: List[Dict]) -> bool:
        """Store route recommendations to Firestore"""
        
        if not self.firestore_client:
            logger.error("Firestore client not available")
            return False
        
        if not routes:
            logger.info("No routes to store")
            return True
        
        logger.info(f"💾 Storing {len(routes)} route recommendations to Firestore...")
        
        try:
            batch = self.firestore_client.batch()
            
            # Store individual routes
            for route in routes:
                route_ref = self.firestore_client.collection('route_recommendations').document(route['route_id'])
                batch.set(route_ref, route)
            
            # Store route summary
            summary_ref = self.firestore_client.collection('route_summaries').document(
                f"routes_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            
            summary = {
                'timestamp': datetime.now().isoformat(),
                'total_routes': len(routes),
                'route_types': list(set([r['route_type'] for r in routes])),
                'top_destinations': [r['primary_destination']['name'] for r in routes[:5]],
                'avg_success_probability': np.mean([r['success_probability'] for r in routes]),
                'available_departure_locations': [r['departure_location']['name'] for r in routes[:5]],
                'valid_until': (datetime.now() + timedelta(hours=6)).isoformat()
            }
            
            batch.set(summary_ref, summary)
            
            # Commit batch
            batch.commit()
            
            logger.info("✅ Route recommendations stored to Firestore")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store route recommendations: {e}")
            return False
    
    async def run_route_optimization_pipeline(self) -> Dict[str, Any]:
        """Run complete route optimization pipeline"""
        
        logger.info("🚀 Starting Route Optimization Pipeline...")
        
        pipeline_results = {
            'timestamp': datetime.now().isoformat(),
            'behavioral_insights_fetched': False,
            'detections_analyzed': 0,
            'hotspots_identified': 0,
            'routes_generated': 0,
            'routes_stored': False,
            'pipeline_status': 'started'
        }
        
        try:
            # Step 1: Fetch behavioral insights
            behavioral_insights = await self.fetch_behavioral_insights()
            pipeline_results['behavioral_insights_fetched'] = len(behavioral_insights) > 0
            
            # Step 2: Fetch recent detections with ML analysis
            detections = await self.fetch_recent_detections_with_ml()
            pipeline_results['detections_analyzed'] = len(detections)
            
            if not detections:
                pipeline_results['pipeline_status'] = 'no_recent_detections'
                logger.warning("⚠️ No recent ML-processed detections found")
                return pipeline_results
            
            # Step 3: Identify hotspots
            hotspots = self.identify_hotspots(detections)
            pipeline_results['hotspots_identified'] = len(hotspots)
            
            if not hotspots:
                pipeline_results['pipeline_status'] = 'no_significant_hotspots'
                logger.warning("⚠️ No significant hotspots identified")
                return pipeline_results
            
            # Step 4: Generate optimized routes
            routes = self.generate_optimized_routes(hotspots)
            pipeline_results['routes_generated'] = len(routes)
            
            if not routes:
                pipeline_results['pipeline_status'] = 'no_feasible_routes'
                logger.warning("⚠️ No feasible routes generated")
                return pipeline_results
            
            # Step 5: Store routes
            storage_success = await self.store_route_recommendations(routes)
            pipeline_results['routes_stored'] = storage_success
            
            if storage_success:
                pipeline_results['pipeline_status'] = 'completed'
                
                # Add route summary to results
                pipeline_results['route_summary'] = {
                    'top_route': routes[0] if routes else None,
                    'available_departure_locations': list(set([r['departure_location']['name'] for r in routes])),
                    'max_success_probability': max([r['success_probability'] for r in routes]) if routes else 0,
                    'route_types': list(set([r['route_type'] for r in routes]))
                }
            else:
                pipeline_results['pipeline_status'] = 'storage_failed'
            
            logger.info("📊 Route Optimization Pipeline Summary:")
            logger.info(f"   Behavioral insights fetched: {pipeline_results['behavioral_insights_fetched']}")
            logger.info(f"   Detections analyzed: {pipeline_results['detections_analyzed']}")
            logger.info(f"   Hotspots identified: {pipeline_results['hotspots_identified']}")
            logger.info(f"   Routes generated: {pipeline_results['routes_generated']}")
            logger.info(f"   Routes stored: {pipeline_results['routes_stored']}")
            logger.info(f"   Status: {pipeline_results['pipeline_status']}")
            
            return pipeline_results
            
        except Exception as e:
            logger.error(f"Route optimization pipeline failed: {e}")
            pipeline_results['pipeline_status'] = 'failed'
            pipeline_results['error'] = str(e)
            return pipeline_results

async def main():
    """Main execution function"""
    print("🗺️ ORCAST Route Optimization Pipeline")
    
    optimizer = ORCASTRouteOptimizer()
    
    # Run route optimization pipeline
    results = await optimizer.run_route_optimization_pipeline()
    
    print(f"\n📊 Pipeline Results:")
    print(f"   Status: {results['pipeline_status']}")
    print(f"   Detections analyzed: {results['detections_analyzed']}")
    print(f"   Hotspots identified: {results['hotspots_identified']}")
    print(f"   Routes generated: {results['routes_generated']}")
    print(f"   Routes stored: {'✅' if results['routes_stored'] else '❌'}")
    
    if 'route_summary' in results:
        summary = results['route_summary']
        print(f"\n🎯 Route Summary:")
        print(f"   Best route success probability: {summary['max_success_probability']:.2f}")
        print(f"   Available departure locations: {len(summary['available_departure_locations'])}")
        print(f"   Route types: {', '.join(summary['route_types'])}")
        
        if summary['top_route']:
            top_route = summary['top_route']
            print(f"   Top recommendation: {top_route['route_summary']}")
    
    print(f"\n🎯 Complete pipeline ready for frontend consumption!")

if __name__ == "__main__":
    asyncio.run(main()) 