"""
Server-Sent Events (SSE) endpoint for real-time OrCast updates
Bridges Redis pub/sub to web browsers for live sighting feeds, predictions, and alerts
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import AsyncGenerator, Dict, Any
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from redis_cache import OrCastRedisCache
import threading
import queue

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealTimeSSE:
    """
    Server-Sent Events handler for real-time OrCast updates
    
    Subscribes to Redis pub/sub channels and streams updates to web clients
    """
    
    def __init__(self, redis_cache: OrCastRedisCache):
        self.redis_cache = redis_cache
        self.active_connections = set()
        self.message_queue = queue.Queue()
        self.redis_listener = None
        self.listener_thread = None
        self.running = False
        
    def start_redis_listener(self):
        """Start Redis pub/sub listener in separate thread"""
        if self.running:
            return
            
        self.running = True
        self.listener_thread = threading.Thread(target=self._redis_listener_worker)
        self.listener_thread.daemon = True
        self.listener_thread.start()
        
        logger.info("Redis listener started for real-time updates")
    
    def stop_redis_listener(self):
        """Stop Redis pub/sub listener"""
        self.running = False
        if self.listener_thread:
            self.listener_thread.join(timeout=5)
            
        logger.info("Redis listener stopped")
    
    def _redis_listener_worker(self):
        """Worker thread for Redis pub/sub listening"""
        try:
            # Subscribe to all channels
            channels = [
                'orca_sightings',
                'prediction_updates', 
                'environmental_updates',
                'orca_alerts'
            ]
            
            # Create new Redis connection for pub/sub
            pubsub = self.redis_cache.redis_client.pubsub()
            for channel in channels:
                pubsub.subscribe(channel)
            
            logger.info(f"Subscribed to Redis channels: {channels}")
            
            # Listen for messages
            for message in pubsub.listen():
                if not self.running:
                    break
                    
                if message['type'] == 'message':
                    try:
                        channel = message['channel'].decode('utf-8')
                        data = json.loads(message['data'])
                        
                        # Determine event type based on channel
                        event_type = self._get_event_type(channel)
                        
                        # Add to message queue
                        sse_event = {
                            'event': event_type,
                            'data': data,
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        self.message_queue.put(sse_event)
                        logger.debug(f"Queued {event_type} event")
                        
                    except Exception as e:
                        logger.error(f"Error processing Redis message: {e}")
                        
        except Exception as e:
            logger.error(f"Redis listener error: {e}")
        finally:
            if 'pubsub' in locals():
                pubsub.close()
    
    def _get_event_type(self, channel: str) -> str:
        """Map Redis channel to SSE event type"""
        channel_mapping = {
            'orca_sightings': 'sighting',
            'prediction_updates': 'prediction',
            'environmental_updates': 'environmental',
            'orca_alerts': 'alert'
        }
        return channel_mapping.get(channel, 'unknown')
    
    async def event_stream(self, request: Request) -> AsyncGenerator[str, None]:
        """
        Generate Server-Sent Events stream
        
        Yields SSE-formatted messages from Redis pub/sub
        """
        connection_id = f"conn_{datetime.now().timestamp()}"
        self.active_connections.add(connection_id)
        
        logger.info(f"New SSE connection: {connection_id}")
        
        try:
            # Send initial connection event
            yield self._format_sse_event('connection', {
                'status': 'connected',
                'connection_id': connection_id,
                'timestamp': datetime.now().isoformat()
            })
            
            # Send periodic heartbeat and process messages
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    logger.info(f"Client disconnected: {connection_id}")
                    break
                
                try:
                    # Get message from queue (non-blocking)
                    message = self.message_queue.get_nowait()
                    yield self._format_sse_event(message['event'], message['data'])
                    
                except queue.Empty:
                    # No messages, send heartbeat
                    yield self._format_sse_event('heartbeat', {
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # Wait before next check
                    await asyncio.sleep(5)
                    
        except Exception as e:
            logger.error(f"SSE stream error for {connection_id}: {e}")
        finally:
            self.active_connections.discard(connection_id)
            logger.info(f"SSE connection closed: {connection_id}")
    
    def _format_sse_event(self, event_type: str, data: Dict[str, Any]) -> str:
        """Format data as Server-Sent Event"""
        return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
    
    def get_connection_count(self) -> int:
        """Get number of active SSE connections"""
        return len(self.active_connections)
    
    def broadcast_custom_event(self, event_type: str, data: Dict[str, Any]):
        """Broadcast custom event to all connected clients"""
        sse_event = {
            'event': event_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        
        self.message_queue.put(sse_event)
        logger.info(f"Broadcasted custom event: {event_type}")

# Global SSE handler instance
sse_handler = None

def initialize_sse(redis_cache: OrCastRedisCache):
    """Initialize SSE handler with Redis cache"""
    global sse_handler
    sse_handler = RealTimeSSE(redis_cache)
    sse_handler.start_redis_listener()
    return sse_handler

# FastAPI endpoints for SSE
def add_sse_endpoints(app: FastAPI, redis_cache: OrCastRedisCache):
    """Add SSE endpoints to FastAPI app"""
    
    # Initialize SSE handler
    sse = initialize_sse(redis_cache)
    
    @app.get("/api/realtime/events")
    async def realtime_events(request: Request):
        """Server-Sent Events endpoint for real-time updates"""
        return StreamingResponse(
            sse.event_stream(request),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )
    
    @app.get("/api/realtime/status")
    async def realtime_status():
        """Get real-time connection status"""
        return {
            "active_connections": sse.get_connection_count(),
            "redis_listening": sse.running,
            "timestamp": datetime.now().isoformat()
        }
    
    @app.post("/api/realtime/broadcast")
    async def broadcast_event(event_data: dict):
        """Broadcast custom event to all connected clients"""
        event_type = event_data.get('event_type', 'custom')
        data = event_data.get('data', {})
        
        sse.broadcast_custom_event(event_type, data)
        
        return {
            "success": True,
            "event_type": event_type,
            "connections_notified": sse.get_connection_count()
        }
    
    @app.post("/api/realtime/subscribe")
    async def subscribe_to_location(request_data: dict):
        """Subscribe to updates for specific location"""
        location = request_data.get('location')
        
        # This would add location-specific filtering
        # For now, just acknowledge subscription
        
        return {
            "success": True,
            "location": location,
            "message": f"Subscribed to updates for {location}"
        }
    
    @app.post("/api/realtime/unsubscribe")
    async def unsubscribe_from_location(request_data: dict):
        """Unsubscribe from location updates"""
        location = request_data.get('location')
        
        return {
            "success": True,
            "location": location,
            "message": f"Unsubscribed from updates for {location}"
        }
    
    # Health check endpoint
    @app.get("/api/realtime/health")
    async def realtime_health():
        """Health check for real-time system"""
        redis_health = redis_cache.health_check()
        
        return {
            "sse_handler": {
                "running": sse.running,
                "active_connections": sse.get_connection_count(),
                "message_queue_size": sse.message_queue.qsize()
            },
            "redis": redis_health,
            "overall_status": "healthy" if sse.running and redis_health.get('connected') else "degraded"
        }

# Cleanup function
def cleanup_sse():
    """Cleanup SSE resources"""
    global sse_handler
    if sse_handler:
        sse_handler.stop_redis_listener()
        sse_handler = None

# Example usage and testing
class RealTimeTestClient:
    """Test client for real-time features"""
    
    def __init__(self, redis_cache: OrCastRedisCache):
        self.redis_cache = redis_cache
    
    def simulate_sighting(self, location: str = "Lime Kiln Point"):
        """Simulate a new sighting for testing"""
        sighting_data = {
            "type": "new_sighting",
            "data": {
                "location": location,
                "behavior": "feeding",
                "pod_size": 8,
                "confidence": 0.9,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        self.redis_cache.publish_sighting(sighting_data['data'])
        logger.info(f"Simulated sighting at {location}")
    
    def simulate_prediction(self, location: str = "San Juan Channel"):
        """Simulate a prediction update for testing"""
        prediction_data = {
            "behavior": "traveling",
            "confidence": 0.75,
            "hmc_uncertainty": {
                "uncertainty_std": 0.15,
                "credible_interval": [0.6, 0.9]
            }
        }
        
        self.redis_cache.publish_prediction_update(prediction_data, location)
        logger.info(f"Simulated prediction for {location}")
    
    def simulate_alert(self, location: str = "Rosario Strait"):
        """Simulate an alert for testing"""
        alert_data = {
            "type": "high_confidence_sighting",
            "message": "High confidence feeding behavior detected",
            "location": location,
            "confidence": 0.92
        }
        
        self.redis_cache.publish_alert(
            alert_data['type'],
            alert_data['message'],
            alert_data['location'],
            alert_data['confidence']
        )
        logger.info(f"Simulated alert for {location}")
    
    def simulate_environmental_update(self, location: str = "Haro Strait"):
        """Simulate environmental update for testing"""
        env_data = {
            "tidal_flow": 0.3,
            "temperature": 15.2,
            "weather_conditions": "clear"
        }
        
        self.redis_cache.publish_environmental_update(env_data, location)
        logger.info(f"Simulated environmental update for {location}")

if __name__ == "__main__":
    # Test the SSE system
    from redis_cache import OrCastRedisCache
    
    redis_cache = OrCastRedisCache()
    test_client = RealTimeTestClient(redis_cache)
    
    # Initialize SSE handler
    sse = initialize_sse(redis_cache)
    
    # Simulate some events
    test_client.simulate_sighting("Lime Kiln Point")
    test_client.simulate_prediction("San Juan Channel") 
    test_client.simulate_alert("Rosario Strait")
    test_client.simulate_environmental_update("Haro Strait")
    
    print("SSE system initialized and test events sent")
    print("Connect to /api/realtime/events to receive real-time updates") 