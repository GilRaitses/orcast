"""
ORCAST-OrcaHello Real-Time Integration Client
Connects to Orcasound's live whale detection API for real-time data
"""

import requests
import json
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class HydrophoneLocation:
    """Hydrophone location data structure"""
    id: str
    name: str
    longitude: float
    latitude: float

@dataclass
class WhaleDetection:
    """Whale detection data structure"""
    detection_id: str
    timestamp: datetime
    location: HydrophoneLocation
    confidence: float
    state: str  # Unreviewed, Positive, Negative
    predictions: List[Dict]
    audio_uri: Optional[str] = None
    image_uri: Optional[str] = None

class OrcaHelloAPIClient:
    """Real-time API client for OrcaHello whale detection system"""
    
    def __init__(self, base_url: str = "https://aifororcas.azurewebsites.net/api"):
        self.base_url = base_url
        self.session = None
        
        # Hardcoded hydrophone locations from Orcasound source code
        self.hydrophone_locations = {
            "rpi_bush_point": HydrophoneLocation(
                "rpi_bush_point", "Bush Point", -122.6040035, 48.0336664
            ),
            "rpi_mast_center": HydrophoneLocation(
                "rpi_mast_center", "Mast Center", -122.32512, 47.34922
            ),
            "rpi_north_sjc": HydrophoneLocation(
                "rpi_north_sjc", "North San Juan Channel", -123.058779, 48.591294
            ),
            "rpi_orcasound_lab": HydrophoneLocation(
                "rpi_orcasound_lab", "Orcasound Lab", -123.1735774, 48.5583362
            ),
            "rpi_point_robinson": HydrophoneLocation(
                "rpi_point_robinson", "Point Robinson", -122.37267, 47.388383
            ),
            "rpi_port_townsend": HydrophoneLocation(
                "rpi_port_townsend", "Port Townsend", -122.760614, 48.135743
            ),
            "rpi_sunset_bay": HydrophoneLocation(
                "rpi_sunset_bay", "Sunset Bay", -122.33393605795372, 47.86497296593844
            )
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def get_recent_detections(self, hours_back: int = 24) -> List[WhaleDetection]:
        """
        Get recent whale detections from all hydrophones
        
        Args:
            hours_back: How many hours back to search
            
        Returns:
            List of whale detections with coordinates
        """
        detections = []
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=hours_back)
        
        try:
            # Use their tag-based search (we'll search for any whale-related tags)
            whale_tags = ["whale", "orca", "click", "call", "multiple"]
            
            for tag in whale_tags:
                tag_detections = await self._get_detections_by_tag(
                    tag, start_date, end_date
                )
                detections.extend(tag_detections)
            
            # Remove duplicates by detection_id
            unique_detections = {d.detection_id: d for d in detections}
            
            logger.info(f"Retrieved {len(unique_detections)} unique whale detections")
            return list(unique_detections.values())
            
        except Exception as e:
            logger.error(f"Error fetching recent detections: {e}")
            return []
    
    async def _get_detections_by_tag(
        self, 
        tag: str, 
        start_date: datetime, 
        end_date: datetime,
        page_size: int = 50
    ) -> List[WhaleDetection]:
        """Get detections for a specific tag"""
        if not self.session:
            raise RuntimeError("Client session not initialized")
        
        detections = []
        page = 1
        
        try:
            url = f"{self.base_url}/detections/bytag/{tag}"
            params = {
                'fromDate': start_date.strftime('%m/%d/%Y'),
                'toDate': end_date.strftime('%m/%d/%Y'),
                'page': page,
                'pageSize': page_size
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Parse the response structure
                    if 'detections' in data:
                        for det_data in data['detections']:
                            detection = self._parse_detection(det_data)
                            if detection:
                                detections.append(detection)
                
                logger.info(f"Got {len(detections)} detections for tag '{tag}'")
                
        except Exception as e:
            logger.warning(f"Error fetching detections for tag '{tag}': {e}")
        
        return detections
    
    def _parse_detection(self, detection_data: Dict) -> Optional[WhaleDetection]:
        """Parse detection data from API response"""
        try:
            # Extract location info
            location_data = detection_data.get('location', {})
            location_id = location_data.get('id', '')
            
            # Get hydrophone location from our mapping
            hydrophone = self.hydrophone_locations.get(location_id)
            if not hydrophone:
                # Fallback to creating location from API data
                hydrophone = HydrophoneLocation(
                    location_id,
                    location_data.get('name', 'Unknown'),
                    location_data.get('longitude', 0.0),
                    location_data.get('latitude', 0.0)
                )
            
            # Parse timestamp
            timestamp_str = detection_data.get('timestamp', '')
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            
            # Create whale detection
            detection = WhaleDetection(
                detection_id=detection_data.get('id', ''),
                timestamp=timestamp,
                location=hydrophone,
                confidence=detection_data.get('whaleFoundConfidence', 0.0),
                state=detection_data.get('state', 'Unreviewed'),
                predictions=detection_data.get('predictions', []),
                audio_uri=detection_data.get('audioUri'),
                image_uri=detection_data.get('imageUri')
            )
            
            return detection
            
        except Exception as e:
            logger.warning(f"Error parsing detection: {e}")
            return None
    
    async def get_hydrophone_locations(self) -> List[HydrophoneLocation]:
        """Get all hydrophone locations"""
        if not self.session:
            raise RuntimeError("Client session not initialized")
        
        try:
            url = f"{self.base_url}/hydrophones"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    locations = []
                    if 'hydrophones' in data:
                        for hydro_data in data['hydrophones']:
                            location = HydrophoneLocation(
                                hydro_data.get('id', ''),
                                hydro_data.get('name', ''),
                                hydro_data.get('longitude', 0.0),
                                hydro_data.get('latitude', 0.0)
                            )
                            locations.append(location)
                    
                    logger.info(f"Retrieved {len(locations)} hydrophone locations")
                    return locations
                else:
                    logger.warning(f"Failed to get hydrophones: {response.status}")
                    return list(self.hydrophone_locations.values())
                    
        except Exception as e:
            logger.error(f"Error fetching hydrophone locations: {e}")
            # Return hardcoded locations as fallback
            return list(self.hydrophone_locations.values())
    
    async def stream_real_time_detections(self, callback_func):
        """
        Stream real-time whale detections
        
        Args:
            callback_func: Function to call with new detections
        """
        logger.info("Starting real-time whale detection stream...")
        
        last_check = datetime.now()
        
        while True:
            try:
                # Check for new detections since last check
                current_time = datetime.now()
                time_diff = (current_time - last_check).total_seconds() / 3600
                
                new_detections = await self.get_recent_detections(
                    hours_back=max(1, int(time_diff + 1))
                )
                
                # Filter to only detections since last check
                recent_detections = [
                    d for d in new_detections 
                    if d.timestamp > last_check
                ]
                
                if recent_detections:
                    logger.info(f"Found {len(recent_detections)} new detections")
                    await callback_func(recent_detections)
                
                last_check = current_time
                
                # Wait 30 seconds before next check
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error in real-time stream: {e}")
                await asyncio.sleep(60)  # Wait longer on error

class ORCASTOrcaHelloIntegration:
    """Integration layer between OrcaHello and ORCAST behavioral models"""
    
    def __init__(self):
        self.api_client = OrcaHelloAPIClient()
        self.detection_buffer = []
    
    async def process_new_detections(self, detections: List[WhaleDetection]):
        """Process new whale detections for ORCAST system"""
        for detection in detections:
            # Transform detection for ORCAST behavioral modeling
            orcast_data = self._transform_to_orcast_format(detection)
            
            # Add to processing buffer
            self.detection_buffer.append(orcast_data)
            
            logger.info(
                f"Processed detection at {detection.location.name} "
                f"({detection.location.latitude:.4f}, {detection.location.longitude:.4f}) "
                f"with confidence {detection.confidence:.2f}"
            )
    
    def _transform_to_orcast_format(self, detection: WhaleDetection) -> Dict:
        """Transform OrcaHello detection to ORCAST format"""
        return {
            'source': 'orcahello',
            'detection_id': detection.detection_id,
            'timestamp': detection.timestamp.isoformat(),
            'latitude': detection.location.latitude,
            'longitude': detection.location.longitude,
            'location_name': detection.location.name,
            'location_id': detection.location.id,
            'confidence': detection.confidence / 100.0,  # Normalize to 0-1
            'validation_state': detection.state,
            'acoustic_predictions': detection.predictions,
            'audio_uri': detection.audio_uri,
            'spectrogram_uri': detection.image_uri,
            'detection_type': 'acoustic_hydrophone'
        }
    
    async def get_recent_whale_activity(self, hours_back: int = 6) -> Dict:
        """Get recent whale activity summary for ORCAST planning"""
        async with self.api_client as client:
            detections = await client.get_recent_detections(hours_back)
            
            # Process detections for behavioral analysis
            await self.process_new_detections(detections)
            
            # Generate activity summary
            activity_summary = {
                'total_detections': len(detections),
                'locations_with_activity': {},
                'recent_activity_hotspots': [],
                'confidence_distribution': [],
                'temporal_patterns': {}
            }
            
            # Analyze by location
            for detection in detections:
                loc_name = detection.location.name
                if loc_name not in activity_summary['locations_with_activity']:
                    activity_summary['locations_with_activity'][loc_name] = {
                        'count': 0,
                        'coordinates': (detection.location.latitude, detection.location.longitude),
                        'avg_confidence': 0,
                        'latest_detection': None
                    }
                
                loc_data = activity_summary['locations_with_activity'][loc_name]
                loc_data['count'] += 1
                loc_data['avg_confidence'] = (
                    (loc_data['avg_confidence'] * (loc_data['count'] - 1) + detection.confidence) 
                    / loc_data['count']
                )
                
                if (not loc_data['latest_detection'] or 
                    detection.timestamp > loc_data['latest_detection']):
                    loc_data['latest_detection'] = detection.timestamp
            
            # Identify hotspots (locations with high activity)
            hotspots = [
                {
                    'location': loc_name,
                    'coordinates': data['coordinates'],
                    'activity_score': data['count'] * (data['avg_confidence'] / 100),
                    'detection_count': data['count']
                }
                for loc_name, data in activity_summary['locations_with_activity'].items()
                if data['count'] >= 3  # Minimum threshold for hotspot
            ]
            
            # Sort by activity score
            activity_summary['recent_activity_hotspots'] = sorted(
                hotspots, 
                key=lambda x: x['activity_score'], 
                reverse=True
            )
            
            logger.info(f"Activity summary: {len(hotspots)} hotspots from {len(detections)} detections")
            
            return activity_summary

# Example usage function
async def test_orcahello_integration():
    """Test the OrcaHello integration"""
    integration = ORCASTOrcaHelloIntegration()
    
    print("🐋 Testing ORCAST-OrcaHello Integration...")
    
    # Get recent activity
    activity = await integration.get_recent_whale_activity(hours_back=12)
    
    print(f"\n📊 Recent Activity Summary:")
    print(f"Total detections: {activity['total_detections']}")
    print(f"Active locations: {len(activity['locations_with_activity'])}")
    print(f"Activity hotspots: {len(activity['recent_activity_hotspots'])}")
    
    # Print hotspots
    if activity['recent_activity_hotspots']:
        print(f"\n🎯 Top Activity Hotspots:")
        for i, hotspot in enumerate(activity['recent_activity_hotspots'][:3]):
            print(f"{i+1}. {hotspot['location']}")
            print(f"   Coordinates: {hotspot['coordinates']}")
            print(f"   Activity Score: {hotspot['activity_score']:.2f}")
            print(f"   Detection Count: {hotspot['detection_count']}")

if __name__ == "__main__":
    asyncio.run(test_orcahello_integration()) 