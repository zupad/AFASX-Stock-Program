"""
Redis caching service for AFI Stock Tracker
Provides intelligent caching to reduce API calls and improve performance
"""

import redis
import json
import pickle
import pandas as pd
from typing import Any, Optional, Union, Dict, List
from datetime import datetime, timedelta
import logging
import hashlib
from functools import wraps
import asyncio
import aioredis


class CacheService:
    """Redis-based caching service with intelligent TTL management"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", db: int = 0):
        self.redis_url = redis_url
        self.db = db
        self.client = None
        self.async_client = None
        self.logger = logging.getLogger(__name__)
        
        # Cache TTL settings (in seconds)
        self.ttl_settings = {
            'stock_price_current': 60,      # 1 minute for current prices
            'stock_price_historical': 3600, # 1 hour for historical data
            'company_info': 86400,          # 24 hours for company info
            'technical_indicators': 1800,   # 30 minutes for technical analysis
            'news': 900,                    # 15 minutes for news
            'dividends': 86400,             # 24 hours for dividend data
            'default': 1800                 # 30 minutes default
        }
    
    def connect(self) -> bool:
        """Connect to Redis server"""
        try:
            self.client = redis.from_url(self.redis_url, db=self.db, decode_responses=False)
            self.client.ping()
            self.logger.info("Connected to Redis successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to Redis: {e}")
            return False
    
    async def connect_async(self) -> bool:
        """Connect to Redis server asynchronously"""
        try:
            self.async_client = aioredis.from_url(self.redis_url, db=self.db)
            await self.async_client.ping()
            self.logger.info("Connected to Redis async client successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to Redis async: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from Redis"""
        if self.client:
            self.client.close()
            self.client = None
    
    async def disconnect_async(self):
        """Disconnect from Redis asynchronously"""
        if self.async_client:
            await self.async_client.close()
            self.async_client = None
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from prefix and parameters"""
        # Create a unique key based on function arguments
        key_data = f"{prefix}:{':'.join(map(str, args))}"
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            kwargs_str = ':'.join(f"{k}={v}" for k, v in sorted_kwargs)
            key_data += f":{kwargs_str}"
        
        # Hash long keys to keep them manageable
        if len(key_data) > 200:
            key_hash = hashlib.md5(key_data.encode()).hexdigest()
            return f"{prefix}:hash:{key_hash}"
        
        return key_data
    
    def _serialize_data(self, data: Any) -> bytes:
        """Serialize data for Redis storage"""
        if isinstance(data, pd.DataFrame):
            # Store DataFrames as pickle for efficiency
            return pickle.dumps(data)
        elif isinstance(data, (dict, list)):
            # Store JSON-serializable data as JSON
            return json.dumps(data, default=str).encode('utf-8')
        else:
            # Use pickle for other objects
            return pickle.dumps(data)
    
    def _deserialize_data(self, data: bytes) -> Any:
        """Deserialize data from Redis storage"""
        try:
            # Try pickle first (for DataFrames and complex objects)
            return pickle.loads(data)
        except:
            try:
                # Try JSON for simple objects
                return json.loads(data.decode('utf-8'))
            except:
                # Return raw bytes if all else fails
                return data
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, cache_type: str = 'default') -> bool:
        """Store data in cache with optional TTL"""
        if not self.client:
            return False
        
        try:
            serialized_data = self._serialize_data(value)
            ttl = ttl or self.ttl_settings.get(cache_type, self.ttl_settings['default'])
            
            if ttl:
                self.client.setex(key, ttl, serialized_data)
            else:
                self.client.set(key, serialized_data)
            
            self.logger.debug(f"Cached data with key: {key}, TTL: {ttl}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to cache data: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Retrieve data from cache"""
        if not self.client:
            return None
        
        try:
            data = self.client.get(key)
            if data is None:
                return None
            
            result = self._deserialize_data(data)
            self.logger.debug(f"Cache hit for key: {key}")
            return result
        except Exception as e:
            self.logger.error(f"Failed to retrieve cached data: {e}")
            return None
    
    async def set_async(self, key: str, value: Any, ttl: Optional[int] = None, cache_type: str = 'default') -> bool:
        """Store data in cache asynchronously"""
        if not self.async_client:
            return False
        
        try:
            serialized_data = self._serialize_data(value)
            ttl = ttl or self.ttl_settings.get(cache_type, self.ttl_settings['default'])
            
            if ttl:
                await self.async_client.setex(key, ttl, serialized_data)
            else:
                await self.async_client.set(key, serialized_data)
            
            self.logger.debug(f"Cached data async with key: {key}, TTL: {ttl}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to cache data async: {e}")
            return False
    
    async def get_async(self, key: str) -> Optional[Any]:
        """Retrieve data from cache asynchronously"""
        if not self.async_client:
            return None
        
        try:
            data = await self.async_client.get(key)
            if data is None:
                return None
            
            result = self._deserialize_data(data)
            self.logger.debug(f"Cache hit async for key: {key}")
            return result
        except Exception as e:
            self.logger.error(f"Failed to retrieve cached data async: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete data from cache"""
        if not self.client:
            return False
        
        try:
            self.client.delete(key)
            self.logger.debug(f"Deleted cache key: {key}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete cache key: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching a pattern"""
        if not self.client:
            return 0
        
        try:
            keys = self.client.keys(pattern)
            if keys:
                deleted = self.client.delete(*keys)
                self.logger.info(f"Deleted {deleted} keys matching pattern: {pattern}")
                return deleted
            return 0
        except Exception as e:
            self.logger.error(f"Failed to clear pattern {pattern}: {e}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.client:
            return {}
        
        try:
            info = self.client.info()
            return {
                'connected_clients': info.get('connected_clients', 0),
                'used_memory_human': info.get('used_memory_human', '0B'),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'expired_keys': info.get('expired_keys', 0),
                'evicted_keys': info.get('evicted_keys', 0)
            }
        except Exception as e:
            self.logger.error(f"Failed to get cache stats: {e}")
            return {}


# Decorator for automatic caching
def cached(cache_type: str = 'default', ttl: Optional[int] = None):
    """Decorator to automatically cache function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if not hasattr(self, '_cache_service') or not self._cache_service:
                return func(self, *args, **kwargs)
            
            # Generate cache key
            key = self._cache_service._generate_key(f"{func.__name__}", *args, **kwargs)
            
            # Try to get from cache
            cached_result = self._cache_service.get(key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(self, *args, **kwargs)
            if result is not None:
                self._cache_service.set(key, result, ttl, cache_type)
            
            return result
        return wrapper
    return decorator


def async_cached(cache_type: str = 'default', ttl: Optional[int] = None):
    """Decorator to automatically cache async function results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            if not hasattr(self, '_cache_service') or not self._cache_service:
                return await func(self, *args, **kwargs)
            
            # Generate cache key
            key = self._cache_service._generate_key(f"{func.__name__}", *args, **kwargs)
            
            # Try to get from cache
            cached_result = await self._cache_service.get_async(key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(self, *args, **kwargs)
            if result is not None:
                await self._cache_service.set_async(key, result, ttl, cache_type)
            
            return result
        return wrapper
    return decorator


# Global cache instance
cache_service = CacheService()


class CachedYahooFinanceClient:
    """Yahoo Finance client with caching support"""
    
    def __init__(self, cache_service: CacheService = None):
        from .yahoo_client import YahooFinanceClient
        self._base_client = YahooFinanceClient()
        self._cache_service = cache_service or cache_service
        
        if self._cache_service:
            self._cache_service.connect()
    
    @cached(cache_type='stock_price_current', ttl=60)
    def get_current_price(self, symbol: str = None) -> Optional[float]:
        """Get current price with caching"""
        return self._base_client.get_current_price(symbol)
    
    @cached(cache_type='stock_price_historical', ttl=3600)
    def get_historical_data(self, symbol: str = None, period: str = "1y") -> Optional[pd.DataFrame]:
        """Get historical data with caching"""
        return self._base_client.get_historical_data(symbol, period)
    
    @cached(cache_type='company_info', ttl=86400)
    def get_company_info(self, symbol: str = None) -> Optional[Dict[str, Any]]:
        """Get company info with caching"""
        return self._base_client.get_company_info(symbol)
    
    @cached(cache_type='dividends', ttl=86400)
    def get_dividend_history(self, symbol: str = None) -> Optional[pd.DataFrame]:
        """Get dividend history with caching"""
        return self._base_client.get_dividend_history(symbol)
    
    def clear_cache(self, symbol: str = None):
        """Clear cache for specific symbol or all data"""
        if symbol:
            pattern = f"*{symbol}*"
        else:
            pattern = "*"
        
        if self._cache_service:
            return self._cache_service.clear_pattern(pattern)
        return 0