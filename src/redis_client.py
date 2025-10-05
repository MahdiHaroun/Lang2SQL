import redis
import json
import os
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_client = None
        self._connect()
    
    def _connect(self):
        """Connect to Redis with error handling"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established successfully")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
        except Exception as e:
            logger.error(f"Unexpected Redis error: {e}")
            self.redis_client = None
    
    def is_connected(self) -> bool:
        """Check if Redis is connected"""
        try:
            if self.redis_client:
                self.redis_client.ping()
                return True
        except:
            pass
        return False
    
    def reconnect(self):
        """Attempt to reconnect to Redis"""
        self._connect()
    
    def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """Set a key-value pair with optional expiration"""
        try:
            if not self.is_connected():
                self.reconnect()
            
            if self.redis_client:
                serialized_value = json.dumps(value) if not isinstance(value, str) else value
                return self.redis_client.set(key, serialized_value, ex=ex)
        except Exception as e:
            logger.error(f"Redis SET error for key {key}: {e}")
        return False
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value by key"""
        try:
            if not self.is_connected():
                self.reconnect()
            
            if self.redis_client:
                value = self.redis_client.get(key)
                if value:
                    try:
                        return json.loads(value)
                    except json.JSONDecodeError:
                        return value
        except Exception as e:
            logger.error(f"Redis GET error for key {key}: {e}")
        return None
    
    def hset(self, name: str, key: str, value: Any) -> bool:
        """Set a hash field"""
        try:
            if not self.is_connected():
                self.reconnect()
            
            if self.redis_client:
                serialized_value = json.dumps(value) if not isinstance(value, str) else value
                return self.redis_client.hset(name, key, serialized_value)
        except Exception as e:
            logger.error(f"Redis HSET error for hash {name}, key {key}: {e}")
        return False
    
    def hget(self, name: str, key: str) -> Optional[Any]:
        """Get a hash field"""
        try:
            if not self.is_connected():
                self.reconnect()
            
            if self.redis_client:
                value = self.redis_client.hget(name, key)
                if value:
                    try:
                        return json.loads(value)
                    except json.JSONDecodeError:
                        return value
        except Exception as e:
            logger.error(f"Redis HGET error for hash {name}, key {key}: {e}")
        return None
    
    def hdel(self, name: str, *keys: str) -> int:
        """Delete hash fields"""
        try:
            if not self.is_connected():
                self.reconnect()
            
            if self.redis_client:
                return self.redis_client.hdel(name, *keys)
        except Exception as e:
            logger.error(f"Redis HDEL error for hash {name}: {e}")
        return 0
    
    def delete(self, *keys: str) -> int:
        """Delete keys"""
        try:
            if not self.is_connected():
                self.reconnect()
            
            if self.redis_client:
                return self.redis_client.delete(*keys)
        except Exception as e:
            logger.error(f"Redis DELETE error: {e}")
        return 0
    
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            if not self.is_connected():
                self.reconnect()
            
            if self.redis_client:
                return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Redis EXISTS error for key {key}: {e}")
        return False
    
    def expire(self, key: str, time: int) -> bool:
        """Set expiration for a key"""
        try:
            if not self.is_connected():
                self.reconnect()
            
            if self.redis_client:
                return self.redis_client.expire(key, time)
        except Exception as e:
            logger.error(f"Redis EXPIRE error for key {key}: {e}")
        return False
    
    def keys(self, pattern: str = "*") -> list:
        """Get keys matching pattern"""
        try:
            if not self.is_connected():
                self.reconnect()
            
            if self.redis_client:
                return self.redis_client.keys(pattern)
        except Exception as e:
            logger.error(f"Redis KEYS error for pattern {pattern}: {e}")
        return []

# Global Redis client instance
redis_client = RedisClient()