"""Token Blacklist Middleware - Validates JWT tokens against blacklist on each request.

This middleware ensures that revoked tokens (from logout, password change, admin action)
are rejected before reaching the application logic. It uses a two-tier approach:
1. Redis cache for fast checks (5-minute TTL)
2. PostgreSQL database for authoritative storage across server restarts

Performance strategy:
- Cache hit: ~1-2ms (Redis operation)
- Cache miss: ~10-50ms (database query + cache refresh)
- Index on token_hash ensures O(1) database performance
"""

import logging
from typing import Optional
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.token_blacklist_repository import TokenBlacklistRepository
from app.services.token_blacklist_cache import get_token_blacklist_cache

logger = logging.getLogger(__name__)


class TokenBlacklistMiddleware:
    """Middleware to check if JWT tokens are blacklisted."""

    def __init__(self):
        """Initialize middleware."""
        self.cache = get_token_blacklist_cache()

    async def check_token_blacklist(
        self,
        token_hash: str,
        db: AsyncSession
    ) -> bool:
        """
        Check if a token is blacklisted using two-tier caching strategy.

        Flow:
        1. Check Redis cache first (5-minute TTL)
        2. If miss, query PostgreSQL database
        3. If found in database, cache the result
        4. Return boolean indicating if token is blacklisted

        Args:
            token_hash: SHA-256 hash of the JWT token
            db: Async database session

        Returns:
            True if token is blacklisted, False if valid

        Postcondition:
            - First call queries database (slow ~10-50ms)
            - Subsequent calls within TTL use cache (fast ~1-2ms)
        """
        # Step 1: Try cache first
        cached_result = await self.cache.get(token_hash)
        if cached_result is not None:
            logger.debug(
                "Token blacklist check (cache hit)",
                token_hash=token_hash[:8] + "..."
            )
            return True  # Cached as blacklisted

        # Step 2: Query database
        try:
            is_blacklisted = await TokenBlacklistRepository.is_blacklisted(db, token_hash)

            # Step 3: Cache result if blacklisted
            if is_blacklisted:
                await self.cache.set(token_hash)
                logger.debug(
                    "Token blacklist check (database hit, cached)",
                    token_hash=token_hash[:8] + "..."
                )
            else:
                logger.debug(
                    "Token blacklist check (not blacklisted)",
                    token_hash=token_hash[:8] + "..."
                )

            return is_blacklisted
        except Exception as e:
            logger.error(
                "Token blacklist check error",
                error=str(e),
                token_hash=token_hash[:8] + "..."
            )
            # On database error, allow request (fail-safe to avoid blocking all traffic)
            return False

    async def invalidate_token_cache(self, token_hash: str) -> None:
        """
        Immediately invalidate a token in the cache.

        Called after logout to ensure immediate effect.

        Args:
            token_hash: SHA-256 hash of the token to invalidate
        """
        await self.cache.delete(token_hash)
        logger.debug(
            "Token cache invalidated",
            token_hash=token_hash[:8] + "..."
        )


# Global middleware instance
_middleware_instance: Optional[TokenBlacklistMiddleware] = None


def get_token_blacklist_middleware() -> TokenBlacklistMiddleware:
    """Get the global token blacklist middleware instance."""
    global _middleware_instance
    if _middleware_instance is None:
        _middleware_instance = TokenBlacklistMiddleware()
    return _middleware_instance
