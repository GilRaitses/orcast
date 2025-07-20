"""
Redis Caching System for OrCast
High-performance caching for HMC sampling, environmental data, ML predictions, and real-time features
"""

import redis
import json
import hashlib
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
import asyncio
import numpy as np
from dataclasses import dataclass, asdict
import pickle
import time
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CacheConfig:
    """Configuration for different cache types"""
    ttl: int  # Time to live in seconds
    key_prefix: str
    serializer: str = 'json'  # 'json' or 'pickle'
    compress: bool = False

class OrCastRedisCache:
    """
    High-performance Redis cache for OrCast system
    
    Provides caching for:
    - HMC sampling results
    - Environmental data
    - ML predictions
    - Real-time sighting feeds
    - User sessions
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = redis.from_url(redis_url, decode_responses=False)
        self.pubsub = self.redis_client.pubsub()
        
        # Cache configurations
        self.cache_configs = {
            'hmc_analysis': CacheConfig(
                ttl=3600,  # 1 hour
                key_prefix='hmc_analysis',
                serializer='pickle',
                compress=True
            ),
            'environmental_data': CacheConfig(
                ttl=300,  # 5 minutes
                key_prefix='env_data',
                serializer='json'
            ),
            'ml_predictions': CacheConfig(
                ttl=1800,  # 30 minutes
                key_prefix='ml_pred',
                serializer='pickle'
            ),
            'tidal_data': CacheConfig(
                ttl=600,  # 10 minutes
                key_prefix='tidal',
                serializer='json'
            ),
            'weather_data': CacheConfig(
                ttl=600,  # 10 minutes
                key_prefix='weather',
                serializer='json'
            ),
            'user_sessions': CacheConfig(
                ttl=3600,  # 1 hour
                key_prefix='user_session',
                serializer='json'
            ),
            'feeding_patterns': CacheConfig(
                ttl=7200,  # 2 hours
                key_prefix='feeding_patterns',
                serializer='pickle',
                compress=True
            )
        }
        
        # Real-time channels
        self.channels = {
            'sightings': 'orca_sightings',
            'predictions': 'prediction_updates',
            'environmental': 'environmental_updates',
            'alerts': 'orca_alerts'
        }
    
    def _generate_cache_key(self, cache_type: str, **kwargs) -> str:
        """Generate a deterministic cache key"""
        config = self.cache_configs[cache_type]
        
        # Sort kwargs for consistent hashing
        sorted_kwargs = sorted(kwargs.items())
        key_data = json.dumps(sorted_kwargs, sort_keys=True)
        
        # Create hash for long keys
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        
        return f"{config.key_prefix}:{key_hash}"
    
    def _serialize_data(self, data: Any, serializer: str, compress: bool = False) -> bytes:
        """Serialize data for Redis storage"""
        if serializer == 'json':
            serialized = json.dumps(data, default=str).encode()
        elif serializer == 'pickle':
            serialized = pickle.dumps(data)
        else:
            raise ValueError(f"Unknown serializer: {serializer}")
        
        if compress:
            import gzip
            serialized = gzip.compress(serialized)
        
        return serialized
    
    def _deserialize_data(self, data: bytes, serializer: str, compress: bool = False) -> Any:
        """Deserialize data from Redis"""
        if compress:
            import gzip
            data = gzip.decompress(data)
        
        if serializer == 'json':
            return json.loads(data.decode())
        elif serializer == 'pickle':
            return pickle.loads(data)
        else:
            raise ValueError(f"Unknown serializer: {serializer}")
    
    def get(self, cache_type: str, **kwargs) -> Optional[Any]:
        """Get cached data"""
        try:
            key = self._generate_cache_key(cache_type, **kwargs)
            config = self.cache_configs[cache_type]
            
            cached_data = self.redis_client.get(key)
            if cached_data is None:
                return None
            
            return self._deserialize_data(cached_data, config.serializer, config.compress)
        
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def set(self, cache_type: str, data: Any, **kwargs) -> bool:
        """Set cached data"""
        try:
            key = self._generate_cache_key(cache_type, **kwargs)
            config = self.cache_configs[cache_type]
            
            serialized_data = self._serialize_data(data, config.serializer, config.compress)
            
            return self.redis_client.setex(key, config.ttl, serialized_data)
        
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def delete(self, cache_type: str, **kwargs) -> bool:
        """Delete cached data"""
        try:
            key = self._generate_cache_key(cache_type, **kwargs)
            return bool(self.redis_client.delete(key))
        
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def cache_decorator(self, cache_type: str, key_func: Callable = None):
        """Decorator for automatic caching"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                # Generate cache key
                if key_func:
                    cache_kwargs = key_func(*args, **kwargs)
                else:
                    cache_kwargs = kwargs
                
                # Try to get from cache
                cached_result = self.get(cache_type, **cache_kwargs)
                if cached_result is not None:
                    logger.info(f"Cache hit for {cache_type}")
                    return cached_result
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                self.set(cache_type, result, **cache_kwargs)
                logger.info(f"Cache miss for {cache_type}, result cached")
                
                return result
            return wrapper
        return decorator
    
    # === HMC SAMPLING CACHE ===
    
    def cache_hmc_analysis(self, analysis_result: Dict[str, Any], 
                          environmental_conditions: Dict[str, Any],
                          n_samples: int = 1000) -> bool:
        """Cache HMC analysis results"""
        return self.set('hmc_analysis', analysis_result, 
                       conditions=environmental_conditions, 
                       n_samples=n_samples,
                       timestamp=datetime.now().isoformat())
    
    def get_hmc_analysis(self, environmental_conditions: Dict[str, Any],
                        n_samples: int = 1000) -> Optional[Dict[str, Any]]:
        """Get cached HMC analysis results"""
        return self.get('hmc_analysis', 
                       conditions=environmental_conditions, 
                       n_samples=n_samples)
    
    def cache_feeding_patterns(self, patterns: Dict[str, Any], 
                             analysis_date: str) -> bool:
        """Cache discovered feeding patterns"""
        return self.set('feeding_patterns', patterns, 
                       analysis_date=analysis_date)
    
    def get_feeding_patterns(self, analysis_date: str) -> Optional[Dict[str, Any]]:
        """Get cached feeding patterns"""
        return self.get('feeding_patterns', analysis_date=analysis_date)
    
    # === ENVIRONMENTAL DATA CACHE ===
    
    def cache_environmental_data(self, data: Dict[str, Any], 
                               location: str, data_type: str) -> bool:
        """Cache environmental data (tidal, weather, etc.)"""
        cache_type = f"{data_type}_data"
        return self.set(cache_type, data, 
                       location=location,
                       timestamp=datetime.now().isoformat())
    
    def get_environmental_data(self, location: str, data_type: str) -> Optional[Dict[str, Any]]:
        """Get cached environmental data"""
        cache_type = f"{data_type}_data"
        return self.get(cache_type, location=location)
    
    def cache_tidal_data(self, tidal_data: Dict[str, Any], station: str) -> bool:
        """Cache NOAA tidal data"""
        return self.set('tidal_data', tidal_data, 
                       station=station,
                       timestamp=datetime.now().isoformat())
    
    def get_tidal_data(self, station: str) -> Optional[Dict[str, Any]]:
        """Get cached tidal data"""
        return self.get('tidal_data', station=station)
    
    def cache_weather_data(self, weather_data: Dict[str, Any], location: str) -> bool:
        """Cache weather data"""
        return self.set('weather_data', weather_data, 
                       location=location,
                       timestamp=datetime.now().isoformat())
    
    def get_weather_data(self, location: str) -> Optional[Dict[str, Any]]:
        """Get cached weather data"""
        return self.get('weather_data', location=location)
    
    # === ML PREDICTION CACHE ===
    
    def cache_ml_prediction(self, prediction: Dict[str, Any], 
                          sighting_data: Dict[str, Any]) -> bool:
        """Cache ML behavioral predictions"""
        # Create a hash of the sighting data for consistent caching
        sighting_hash = hashlib.md5(
            json.dumps(sighting_data, sort_keys=True).encode()
        ).hexdigest()
        
        return self.set('ml_predictions', prediction, 
                       sighting_hash=sighting_hash,
                       timestamp=datetime.now().isoformat())
    
    def get_ml_prediction(self, sighting_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get cached ML prediction"""
        sighting_hash = hashlib.md5(
            json.dumps(sighting_data, sort_keys=True).encode()
        ).hexdigest()
        
        return self.get('ml_predictions', sighting_hash=sighting_hash)
    
    # === REAL-TIME FEATURES ===
    
    def publish_sighting(self, sighting_data: Dict[str, Any]) -> bool:
        """Publish new sighting to real-time feed"""
        try:
            message = {
                'type': 'new_sighting',
                'data': sighting_data,
                'timestamp': datetime.now().isoformat()
            }
            
            return self.redis_client.publish(
                self.channels['sightings'], 
                json.dumps(message)
            )
        
        except Exception as e:
            logger.error(f"Sighting publish error: {e}")
            return False
    
    def publish_prediction_update(self, prediction: Dict[str, Any], 
                                location: str) -> bool:
        """Publish prediction update"""
        try:
            message = {
                'type': 'prediction_update',
                'location': location,
                'prediction': prediction,
                'timestamp': datetime.now().isoformat()
            }
            
            return self.redis_client.publish(
                self.channels['predictions'], 
                json.dumps(message)
            )
        
        except Exception as e:
            logger.error(f"Prediction publish error: {e}")
            return False
    
    def publish_environmental_update(self, environmental_data: Dict[str, Any],
                                   location: str) -> bool:
        """Publish environmental condition update"""
        try:
            message = {
                'type': 'environmental_update',
                'location': location,
                'data': environmental_data,
                'timestamp': datetime.now().isoformat()
            }
            
            return self.redis_client.publish(
                self.channels['environmental'], 
                json.dumps(message)
            )
        
        except Exception as e:
            logger.error(f"Environmental publish error: {e}")
            return False
    
    def publish_alert(self, alert_type: str, message: str, 
                     location: str = None, confidence: float = None) -> bool:
        """Publish orca alert"""
        try:
            alert_data = {
                'type': alert_type,
                'message': message,
                'location': location,
                'confidence': confidence,
                'timestamp': datetime.now().isoformat()
            }
            
            return self.redis_client.publish(
                self.channels['alerts'], 
                json.dumps(alert_data)
            )
        
        except Exception as e:
            logger.error(f"Alert publish error: {e}")
            return False
    
    def subscribe_to_channel(self, channel_name: str) -> Any:
        """Subscribe to a real-time channel"""
        channel = self.channels.get(channel_name, channel_name)
        self.pubsub.subscribe(channel)
        return self.pubsub
    
    def listen_for_messages(self, channel_name: str, callback: Callable):
        """Listen for messages on a channel"""
        channel = self.channels.get(channel_name, channel_name)
        self.pubsub.subscribe(channel)
        
        for message in self.pubsub.listen():
            if message['type'] == 'message':
                try:
                    data = json.loads(message['data'])
                    callback(data)
                except Exception as e:
                    logger.error(f"Message processing error: {e}")
    
    # === SESSION MANAGEMENT ===
    
    def cache_user_session(self, user_id: str, session_data: Dict[str, Any]) -> bool:
        """Cache user session data"""
        return self.set('user_sessions', session_data, user_id=user_id)
    
    def get_user_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user session data"""
        return self.get('user_sessions', user_id=user_id)
    
    def add_user_prediction_history(self, user_id: str, prediction: Dict[str, Any]) -> bool:
        """Add prediction to user's history"""
        try:
            history_key = f"user_predictions:{user_id}"
            prediction_data = {
                'prediction': prediction,
                'timestamp': datetime.now().isoformat()
            }
            
            # Add to list (keep last 100 predictions)
            pipe = self.redis_client.pipeline()
            pipe.lpush(history_key, json.dumps(prediction_data))
            pipe.ltrim(history_key, 0, 99)  # Keep only last 100
            pipe.expire(history_key, 86400)  # Expire after 24 hours
            pipe.execute()
            
            return True
        
        except Exception as e:
            logger.error(f"User prediction history error: {e}")
            return False
    
    def get_user_prediction_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user's prediction history"""
        try:
            history_key = f"user_predictions:{user_id}"
            history_data = self.redis_client.lrange(history_key, 0, limit - 1)
            
            return [json.loads(item) for item in history_data]
        
        except Exception as e:
            logger.error(f"Get user history error: {e}")
            return []
    
    # === RATE LIMITING ===
    
    def rate_limit(self, identifier: str, limit: int, window: int) -> bool:
        """Rate limiting for API endpoints"""
        try:
            key = f"rate_limit:{identifier}"
            pipe = self.redis_client.pipeline()
            
            # Increment counter
            pipe.incr(key)
            pipe.expire(key, window)
            results = pipe.execute()
            
            current_count = results[0]
            return current_count <= limit
        
        except Exception as e:
            logger.error(f"Rate limit error: {e}")
            return True  # Allow on error
    
    # === ANALYTICS & MONITORING ===
    
    def track_prediction_request(self, location: str, user_id: str = None) -> bool:
        """Track prediction requests for analytics"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Track by location
            location_key = f"analytics:predictions:{today}:{location}"
            self.redis_client.incr(location_key)
            self.redis_client.expire(location_key, 86400 * 7)  # Keep for 7 days
            
            # Track by user if provided
            if user_id:
                user_key = f"analytics:user_requests:{today}:{user_id}"
                self.redis_client.incr(user_key)
                self.redis_client.expire(user_key, 86400 * 7)
            
            return True
        
        except Exception as e:
            logger.error(f"Analytics tracking error: {e}")
            return False
    
    def get_prediction_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get prediction analytics"""
        try:
            analytics = {}
            
            for i in range(days):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                pattern = f"analytics:predictions:{date}:*"
                
                daily_data = {}
                for key in self.redis_client.scan_iter(match=pattern):
                    key_str = key.decode() if isinstance(key, bytes) else key
                    location = key_str.split(':')[-1]
                    count = self.redis_client.get(key)
                    daily_data[location] = int(count) if count else 0
                
                analytics[date] = daily_data
            
            return analytics
        
        except Exception as e:
            logger.error(f"Analytics retrieval error: {e}")
            return {}
    
    # === CACHE WARMING ===
    
    def warm_cache(self, locations: List[str]) -> bool:
        """Pre-warm cache with common data"""
        try:
            logger.info("Starting cache warming...")
            
            # This would trigger fetching of common environmental data
            # and popular predictions to pre-populate the cache
            
            for location in locations:
                # Simulate cache warming - in real implementation,
                # this would fetch and cache common data
                logger.info(f"Warming cache for {location}")
            
            return True
        
        except Exception as e:
            logger.error(f"Cache warming error: {e}")
            return False
    
    # === HEALTH CHECK ===
    
    def health_check(self) -> Dict[str, Any]:
        """Check Redis connection and cache health"""
        try:
            # Test connection
            ping_result = self.redis_client.ping()
            
            # Get basic info
            info = self.redis_client.info()
            
            # Check cache hit rates (approximate)
            cache_stats = {}
            for cache_type in self.cache_configs:
                pattern = f"{self.cache_configs[cache_type].key_prefix}:*"
                keys = list(self.redis_client.scan_iter(match=pattern))
                cache_stats[cache_type] = len(keys)
            
            return {
                'connected': ping_result,
                'redis_info': {
                    'connected_clients': info.get('connected_clients', 0),
                    'used_memory_human': info.get('used_memory_human', 'Unknown'),
                    'uptime_in_seconds': info.get('uptime_in_seconds', 0)
                },
                'cache_stats': cache_stats,
                'channels': self.channels
            }
        
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return {
                'connected': False,
                'error': str(e)
            }

# === INTEGRATION HELPERS ===

class CachedHMCAnalysis:
    """Cached wrapper for HMC analysis"""
    
    def __init__(self, cache: OrCastRedisCache, hmc_api):
        self.cache = cache
        self.hmc_api = hmc_api
    
    def run_analysis(self, environmental_conditions: Dict[str, Any],
                    n_samples: int = 1000) -> Dict[str, Any]:
        """Run HMC analysis with caching"""
        # Try cache first
        cached_result = self.cache.get_hmc_analysis(environmental_conditions, n_samples)
        if cached_result:
            logger.info("HMC analysis cache hit")
            return cached_result
        
        # Run expensive analysis
        logger.info("HMC analysis cache miss, running computation...")
        result = self.hmc_api.run_feeding_behavior_analysis(n_samples=n_samples)
        
        # Cache result
        self.cache.cache_hmc_analysis(result, environmental_conditions, n_samples)
        
        return result

class CachedEnvironmentalData:
    """Cached wrapper for environmental data"""
    
    def __init__(self, cache: OrCastRedisCache):
        self.cache = cache
    
    def get_tidal_data(self, station: str, fetch_func: Callable) -> Dict[str, Any]:
        """Get tidal data with caching"""
        cached_data = self.cache.get_tidal_data(station)
        if cached_data:
            return cached_data
        
        # Fetch fresh data
        fresh_data = fetch_func(station)
        self.cache.cache_tidal_data(fresh_data, station)
        
        return fresh_data
    
    def get_weather_data(self, location: str, fetch_func: Callable) -> Dict[str, Any]:
        """Get weather data with caching"""
        cached_data = self.cache.get_weather_data(location)
        if cached_data:
            return cached_data
        
        # Fetch fresh data
        fresh_data = fetch_func(location)
        self.cache.cache_weather_data(fresh_data, location)
        
        return fresh_data

# Global cache instance
redis_cache = OrCastRedisCache()

# Export main components
__all__ = [
    'OrCastRedisCache',
    'CachedHMCAnalysis', 
    'CachedEnvironmentalData',
    'redis_cache'
] 