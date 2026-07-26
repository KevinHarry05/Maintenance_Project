"""Token Blacklist Repository - Database operations for persistent token revocation.

This repository handles all database interactions for the TokenBlacklist model,
providing a clean abstraction for token revocation and cleanup operations.

Design:
- add_to_blacklist(): Adds a revoked token to persistent storage
- is_blacklisted(): Checks if a token is revoked (O(1) via index)
- cleanup_expired_tokens(): Removes expired entries during scheduled maintenance
"""

import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.models.token_blacklist import TokenBlacklist

logger = logging.getLogger(__name__)


class TokenBlacklistRepository:
    """Repository for TokenBlacklist database operations."""

    @staticmethod
    async def add_to_blacklist(
        db: AsyncSession,
        token_hash: str,
        user_id: str,
        expires_at: datetime,
        revocation_reason: str = "user_logout"
    ) -> TokenBlacklist:
        """
        Add a revoked JWT token to the blacklist.

        Args:
            db: Async database session
            token_hash: SHA-256 hash of the JWT token (never store plaintext)
            user_id: ID of the user who owned this token
            expires_at: When the original JWT expires (used for auto-cleanup)
            revocation_reason: Why the token was revoked (e.g., user_logout, admin_revoke)

        Returns:
            The created TokenBlacklist entry

        Postcondition:
            - TokenBlacklist entry is persisted to database
            - Token is immediately unavailable for use
            - Entry will be automatically cleaned up after expiration
        """
        blacklist_entry = TokenBlacklist(
            token_hash=token_hash,
            user_id=user_id,
            expires_at=expires_at,
            revocation_reason=revocation_reason
        )
        db.add(blacklist_entry)
        await db.commit()
        await db.refresh(blacklist_entry)

        logger.info(
            "Token added to blacklist",
            user_id=user_id,
            reason=revocation_reason,
            expires_at=expires_at
        )

        return blacklist_entry

    @staticmethod
    async def is_blacklisted(db: AsyncSession, token_hash: str) -> bool:
        """
        Check if a token is in the blacklist.

        Uses index on token_hash for O(1) lookup performance.

        Args:
            db: Async database session
            token_hash: SHA-256 hash of the token to check

        Returns:
            True if token is blacklisted, False otherwise

        Postcondition:
            - Query uses idx_token_blacklist_token_hash index
            - Operation completes in constant time regardless of table size
        """
        result = await db.execute(
            select(TokenBlacklist).where(TokenBlacklist.token_hash == token_hash).limit(1)
        )
        entry = result.scalar_one_or_none()
        return entry is not None

    @staticmethod
    async def cleanup_expired_tokens(db: AsyncSession) -> int:
        """
        Delete all expired tokens from the blacklist.

        This is meant to be called by a scheduled task (daily at 2 AM UTC by default).
        Removes entries where the original JWT has expired.

        Args:
            db: Async database session

        Returns:
            Number of entries deleted

        Postcondition:
            - All TokenBlacklist entries with expires_at < now are deleted
            - Database size is cleaned up (expired tokens no longer needed)
            - Log entry is created with count of deleted entries
        """
        now = datetime.now(timezone.utc)

        # Count entries before deletion for logging
        count_result = await db.execute(
            select(TokenBlacklist).where(TokenBlacklist.expires_at < now)
        )
        entries_to_delete = count_result.scalars().all()
        count = len(entries_to_delete)

        # Delete expired entries
        await db.execute(
            delete(TokenBlacklist).where(TokenBlacklist.expires_at < now)
        )
        await db.commit()

        logger.info(
            "Token blacklist cleanup completed",
            deleted_count=count,
            cleanup_time=datetime.now(timezone.utc).isoformat()
        )

        return count

    @staticmethod
    async def get_blacklist_entry(db: AsyncSession, token_hash: str) -> TokenBlacklist | None:
        """
        Retrieve a specific blacklist entry.

        Args:
            db: Async database session
            token_hash: SHA-256 hash of the token

        Returns:
            TokenBlacklist entry if found, None otherwise
        """
        result = await db.execute(
            select(TokenBlacklist).where(TokenBlacklist.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_blacklisted_tokens(db: AsyncSession, user_id: str) -> list[TokenBlacklist]:
        """
        Get all blacklisted tokens for a specific user.

        Used during user management/audit operations.

        Args:
            db: Async database session
            user_id: User ID to query

        Returns:
            List of blacklisted tokens for this user
        """
        result = await db.execute(
            select(TokenBlacklist).where(TokenBlacklist.user_id == user_id)
        )
        return result.scalars().all()

    @staticmethod
    async def remove_user_tokens(db: AsyncSession, user_id: str) -> int:
        """
        Revoke all tokens for a user (e.g., force logout from all devices).

        Args:
            db: Async database session
            user_id: User ID whose tokens should be revoked

        Returns:
            Number of tokens deleted
        """
        result = await db.execute(
            delete(TokenBlacklist).where(TokenBlacklist.user_id == user_id)
        )
        await db.commit()

        logger.info(
            "All tokens revoked for user",
            user_id=user_id,
            deleted_count=result.rowcount
        )

        return result.rowcount if result.rowcount else 0
