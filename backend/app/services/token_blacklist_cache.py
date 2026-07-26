"""Token Blacklist Cache - Redis-backed cache layer for fast token checks.

This module provides a Redis cache for frequently-checked blacklisted tokens.
Caching reduces database queries significantly for the common case where
tokens are checked multiple times within their TTL window.

Cache Strategy:
- Key format: "blacklist:{token_hash}"
- TTL: 5 minutes (configurable)
- Refresh on miss: Query database and refresh cache
- Lazy expiration: Redis automatically deletes expired keys
"""

import logging
from typing import Optional
import redis.asyncio as redis
from app.config import settings

logger = logging.getLogger(__name__)

# Cache configuration (in seconds)
DEFAULT_CACHE_TTL = 300  # 5 minutes
CACHE_KEY_PREFIX = "blacklist:"


class TokenBlacklistCache:
    """Redis cache for token blacklist entries."""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        Initialize the cache layer.

        Args:
            redis_client: Optional Redis client (uses settings.REDIS_URL if not provided)
        """
        self.redis_client = redis_client
        self.ttl = getattr(settings, 'TOKEN_BLACKLIST_CACHE_TTL_SECONDS', DEFAULT_CACHE_TTL)

    async def _get_redis_client(self) -> redis.Redis:
        """Get or create Redis client lazily."""
        if self.redis_client is None:
            self.redis_client = await redis.from_url(settings.REDIS_URL)
        return self.redis_client

    async def get(self, token_hash: str) -> Optional[bool]:
        """
        Check if a token is cached as blacklisted.

        Args:
            token_hash: SHA-256 hash of the token

        Returns:
            True if token is cached as blacklisted, None if not in cache, False if not blacklisted
        """
        try:
            client = await self._get_redis_client()
            cache_key = f"{CACHE_KEY_PREFIX}{token_hash}"
            value = await client.get(cache_key)

            if value is not None:
                logger.debug(
                    "Token blacklist cache hit",
                    token_hash=token_hash[:8] + "..."
                )
                return True

            return None  # Not in cache
        except Exception as e:
            logger.warning(
                "Token blacklist cache read error",
                error=str(e),
                token_hash=token_hash[:8] + "..."
            )
            return None  # Cache error, allow database query

    async def set(self, token_hash: str, value: bool = True) -> bool:
        """
        Cache a token as blacklisted.

        Args:
            token_hash: SHA-256 hash of the token
            value: Whether the token is blacklisted (always True in this context)

        Returns:
            True if cache write succeeded, False if error occurred
        """
        try:
            client = await self._get_redis_client()
            cache_key = f"{CACHE_KEY_PREFIX}{token_hash}"

            # Use SETEX to set with automatic expiration
            await client.setex(
                cache_key,
                self.ttl,
                "revoked"  # Value doesn't matter, we just check existence
            )

            logger.debug(
                "Token blacklist cached",
                token_hash=token_hash[:8] + "...",
                ttl_seconds=self.ttl
            )
            return True
        except Exception as e:
            logger.warning(
                "Token blacklist cache write error",
                error=str(e),
                token_hash=token_hash[:8] + "..."
            )
            return False  # Cache write failed, but allow normal operation

    async def delete(self, token_hash: str) -> bool:
        """
        Remove a token from cache.

        Used when a token is removed from blacklist or for manual cache invalidation.

        Args:
            token_hash: SHA-256 hash of the token

        Returns:
            True if deletion succeeded, False if error occurred
        """
        try:
            client = await self._get_redis_client()
            cache_key = f"{CACHE_KEY_PREFIX}{token_hash}"
            await client.delete(cache_key)

            logger.debug(
                "Token removed from blacklist cache",
                token_hash=token_hash[:8] + "..."
            )
            return True
        except Exception as e:
            logger.warning(
                "Token blacklist cache delete error",
                error=str(e),
                token_hash=token_hash[:8] + "..."
            )
            return False

    async def clear_all(self) -> int:
        """
        Clear all token blacklist cache entries.

        Used for maintenance or testing.

        Returns:
            Number of entries deleted
        """
        try:
            client = await self._get_redis_client()
            cursor = "0"
            deleted_count = 0

            # Use SCAN to iterate through keys matching pattern
            while True:
                cursor, keys = await client.scan(cursor, match=f"{CACHE_KEY_PREFIX}*")
                if keys:
                    deleted_count += await client.delete(*keys)
                if cursor == 0:
                    break

            logger.info(
                "Token blacklist cache cleared",
                deleted_count=deleted_count
            )
            return deleted_count
        except Exception as e:
            logger.warning(
                "Token blacklist cache clear error",
                error=str(e)
            )
            return 0

    async def close(self) -> None:
        """Close the Redis connection."""
        if self.redis_client is not None:
            await self.redis_client.close()


# Global cache instance
_cache_instance: Optional[TokenBlacklistCache] = None


def get_token_blacklist_cache() -> TokenBlacklistCache:
    """Get the global token blacklist cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = TokenBlacklistCache()
    return _cache_instance
