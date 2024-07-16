"""
Module for interacting with Redis cache using aioredis.

This module provides a RedisCache class for managing Redis connections and
operations, including setting, getting, deleting keys, and clearing the cache.
"""

import aioredis

from config import settings


class RedisCache:
    """
    Represents a Redis cache client for managing cache operations.
    """

    def __init__(self, redis_url: str):
        """
        Initialize the RedisCache with a Redis URL.

        Args:
            redis_url (str): The URL of the Redis server.
        """
        self.redis_url = redis_url
        self.redis = None

    async def init_cache(self):
        """
        Initialize the Redis connection asynchronously.
        """
        self.redis = await aioredis.from_url(self.redis_url)

    async def close_cache(self):
        """
        Close the Redis connection asynchronously.
        """
        if self.redis:
            await self.redis.close()

    async def set(self, key: str, value: str, ttl: None | int = 30):
        """
        Set a key-value pair in the Redis cache.

        Args:
            key (str): The key to set.
            value (str): The value to set for the key.
            ttl (int | None, optional): Time-to-live (TTL) for the key
            in seconds. Default is 30 seconds.

        Raises:
            TypeError: If ttl is provided but not an integer.

        Note:
            If ttl is None, the key will not expire.

        Example:
            await redis.set("key", "value")
            await redis.set("key", "value", ttl=60)
        """
        if ttl:
            await self.redis.set(key, value, ex=ttl)
        else:
            await self.redis.set(key, value)

    async def get(self, key: str):
        """
        Retrieve the value associated with a key from the Redis cache.

        Args:
            key (str): The key to retrieve.

        Returns:
            str | None: The value associated with the key, or None if key
            doesn't exist.

        Example:
            result = await redis.get("key")
        """
        value = await self.redis.get(key)
        if value is not None:
            value = value.decode("utf-8")
        return value

    async def delete(self, key: str):
        """
        Delete a key from the Redis cache.

        Args:
            key (str): The key to delete.

        Example:
            await redis.delete("key")
        """
        await self.redis.delete(key)

    async def clear_cache(self):
        """
        Clear all keys from the Redis cache.

        Example:
            await redis.clear_cache()
        """
        await self.redis.flushdb()


redis = RedisCache(
    f"redis://{settings.DOCKER_REDIS}:{settings.DOCKER_REDIS_PORT}/"
    f"{settings.REDIS_DB_CACHE}"
)
