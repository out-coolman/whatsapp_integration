"""
Redis client configuration and utilities.
"""
import redis
import json
from typing import Any, Optional
import logging

from .config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis client wrapper with JSON serialization support."""

    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)

    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis with JSON deserialization."""
        try:
            value = self.redis.get(key)
            if value is None:
                return None
            return json.loads(value)
        except (redis.RedisError, json.JSONDecodeError) as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None

    def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """Set value in Redis with JSON serialization."""
        try:
            serialized_value = json.dumps(value, default=str)
            return self.redis.set(key, serialized_value, ex=ex)
        except (redis.RedisError, json.JSONEncodeError) as e:
            logger.error(f"Redis set error for key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from Redis."""
        try:
            return bool(self.redis.delete(key))
        except redis.RedisError as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        try:
            return bool(self.redis.exists(key))
        except redis.RedisError as e:
            logger.error(f"Redis exists error for key {key}: {e}")
            return False

    def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment counter in Redis."""
        try:
            return self.redis.incr(key, amount)
        except redis.RedisError as e:
            logger.error(f"Redis incr error for key {key}: {e}")
            return None

    def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for key."""
        try:
            return bool(self.redis.expire(key, seconds))
        except redis.RedisError as e:
            logger.error(f"Redis expire error for key {key}: {e}")
            return False

    def keys(self, pattern: str = "*") -> list:
        """Get keys matching pattern."""
        try:
            return self.redis.keys(pattern)
        except redis.RedisError as e:
            logger.error(f"Redis keys error for pattern {pattern}: {e}")
            return []


# Global Redis client instance
redis_client = RedisClient()