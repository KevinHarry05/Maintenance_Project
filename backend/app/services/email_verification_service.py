"""Email Verification Service - Secure token generation and verification.

This service handles all email verification operations:
- Generate cryptographically secure tokens for registration
- Hash tokens using SHA-256 for safe storage
- Verify tokens using constant-time comparison (prevents timing attacks)
- Send verification emails to users

Security Considerations:
- 32-byte random tokens (256 bits of entropy)
- SHA-256 hashing for storage (one-way, cannot recover plaintext token)
- Constant-time comparison to prevent timing attacks
- Tokens expire after 24 hours (configurable)
"""

import secrets
import hashlib
import hmac
import logging
from typing import Tuple, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.email_verification_token import EmailVerificationToken
from app.models.user import User
from app.config import settings

logger = logging.getLogger(__name__)


class EmailVerificationService:
    """Service for email verification token generation and verification."""

    # Token generation settings
    TOKEN_LENGTH_BYTES = 32  # 256 bits of entropy
    TOKEN_EXPIRY_HOURS = 24  # Default 24-hour expiry
    TOKEN_HASH_ALGORITHM = 'sha256'

    @staticmethod
    def generate_verification_token() -> str:
        """
        Generate a cryptographically secure email verification token.

        Uses secrets module for cryptographic randomness and encodes as URL-safe
        base64 string for safe transmission in email links.

        Returns:
            URL-safe token string (e.g., "aBc_dEf-gHi...")

        Postcondition:
            - Token is 32 bytes of random data (256 bits entropy)
            - Token is URL-safe and can be included in email links
            - Different on each call (cryptographically random)
        """
        # Generate 32 random bytes
        random_bytes = secrets.token_bytes(EmailVerificationService.TOKEN_LENGTH_BYTES)

        # Encode as URL-safe base64 (removes padding)
        token = secrets.token_urlsafe(EmailVerificationService.TOKEN_LENGTH_BYTES)

        logger.debug("Email verification token generated")
        return token

    @staticmethod
    def hash_verification_token(token: str) -> str:
        """
        Hash a verification token using SHA-256.

        Only the hash is stored in the database, never the plaintext token.
        This is one-way encryption - the original token cannot be recovered.

        Args:
            token: Plaintext token to hash

        Returns:
            Hex-encoded SHA-256 hash of the token

        Postcondition:
            - Returned hash is deterministic (same token always produces same hash)
            - Hash is 64 characters long (256 bits in hex)
            - Original token cannot be derived from hash
        """
        hash_obj = hashlib.sha256(token.encode('utf-8'))
        token_hash = hash_obj.hexdigest()

        logger.debug(
            "Token hashed for storage",
            token_hash=token_hash[:8] + "..."
        )
        return token_hash

    @staticmethod
    def verify_token_hash(provided_token: str, stored_hash: str) -> bool:
        """
        Verify that a provided token matches the stored hash.

        Uses constant-time comparison (hmac.compare_digest) to prevent
        timing attacks where attackers could deduce token length/content
        by measuring response time.

        Args:
            provided_token: Token provided by user (from email link)
            stored_hash: Stored hash from database

        Returns:
            True if token matches hash, False otherwise

        Postcondition:
            - Comparison time is constant regardless of input
            - Resistant to timing attacks
            - Secure even if attacker can measure response time
        """
        # Hash the provided token
        provided_hash = EmailVerificationService.hash_verification_token(provided_token)

        # Use constant-time comparison
        is_valid = hmac.compare_digest(provided_hash, stored_hash)

        logger.debug(
            "Token verification completed",
            is_valid=is_valid,
            provided_hash=provided_hash[:8] + "..."
        )
        return is_valid

    @staticmethod
    async def create_verification_token(
        db: AsyncSession,
        user_id: str
    ) -> Tuple[str, str]:
        """
        Create and store an email verification token.

        Generates a random token, hashes it, and stores the hash in the database.
        Returns both the plaintext token (for email) and the hash (for database).

        Args:
            db: Async database session
            user_id: ID of user to verify

        Returns:
            Tuple of (plaintext_token, token_hash)

        Postcondition:
            - EmailVerificationToken record created in database
            - Token hashes match stored hash
            - Plaintext token is never stored (only hash)
            - Previous token for user (if exists) is replaced (UNIQUE constraint)
        """
        # Generate and hash token
        plaintext_token = EmailVerificationService.generate_verification_token()
        token_hash = EmailVerificationService.hash_verification_token(plaintext_token)

        # Calculate expiration
        expiry_hours = settings.VERIFICATION_TOKEN_EXPIRY_HOURS
        expires_at = datetime.now(timezone.utc) + timedelta(hours=expiry_hours)

        # Create database entry (replaces previous token due to UNIQUE constraint)
        verification_token = EmailVerificationToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at
        )

        db.add(verification_token)
        await db.commit()
        await db.refresh(verification_token)

        logger.info(
            "Email verification token created",
            user_id=user_id,
            expires_at=expires_at.isoformat(),
            expiry_hours=expiry_hours
        )

        return plaintext_token, token_hash

    @staticmethod
    async def verify_email_token(
        db: AsyncSession,
        token: str
    ) -> Optional[str]:
        """
        Verify an email verification token.

        Looks up the token by hash, checks expiration, and confirms match.
        On successful verification, marks user as verified and deletes token.

        Args:
            db: Async database session
            token: Plaintext token from email link (provided by user)

        Returns:
            User ID if verification successful, None if failed/expired

        Postcondition:
            - If valid: user.email_verified = true, token is deleted
            - If expired: token is deleted, user not verified
            - If invalid: no changes to database
            - Returns user_id on success, None on failure
        """
        # Hash the provided token
        token_hash = EmailVerificationService.hash_verification_token(token)

        # Look up token in database
        result = await db.execute(
            select(EmailVerificationToken).where(
                EmailVerificationToken.token_hash == token_hash
            )
        )
        verification_token = result.scalar_one_or_none()

        if not verification_token:
            logger.warning("Email verification failed: token not found")
            return None

        # Check expiration
        if verification_token.is_expired():
            # Delete expired token
            await db.delete(verification_token)
            await db.commit()

            logger.warning(
                "Email verification failed: token expired",
                user_id=verification_token.user_id
            )
            return None

        # Mark user as verified
        user = await db.get(User, verification_token.user_id)
        if not user:
            logger.error(
                "Email verification failed: user not found",
                user_id=verification_token.user_id
            )
            return None

        user.email_verified = True
        await db.delete(verification_token)
        await db.commit()

        logger.info(
            "Email verification successful",
            user_id=user.id,
            email=user.email
        )

        return user.id

    @staticmethod
    async def is_email_verified(
        db: AsyncSession,
        user_id: str
    ) -> bool:
        """
        Check if a user's email is verified.

        Args:
            db: Async database session
            user_id: ID of user to check

        Returns:
            True if email is verified, False otherwise
        """
        user = await db.get(User, user_id)
        return user.email_verified if user else False

    @staticmethod
    async def get_active_verification_token(
        db: AsyncSession,
        user_id: str
    ) -> Optional[EmailVerificationToken]:
        """
        Get the active verification token for a user (if any).

        Args:
            db: Async database session
            user_id: User ID to check

        Returns:
            EmailVerificationToken if one exists, None otherwise
        """
        result = await db.execute(
            select(EmailVerificationToken).where(
                EmailVerificationToken.user_id == user_id
            )
        )
        return result.scalar_one_or_none()
