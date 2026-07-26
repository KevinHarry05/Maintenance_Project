"""EmailVerificationToken model for temporary email verification storage.

This model stores email verification tokens that are sent to users during
registration or when requesting to resend verification. Tokens are hashed
for security and automatically expire after 24 hours.

Security considerations:
- Only the SHA-256 hash of the token is stored, never the plaintext token
- UNIQUE constraint on user_id ensures only one active token per user
- Tokens automatically expire after configured duration
- Constant-time comparison prevents timing attacks during verification
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class EmailVerificationToken(Base):
    """
    Temporary storage for email verification tokens.
    
    Attributes:
        id: Primary key identifier
        user_id: ID of the user being verified (unique - only one active token per user)
        token_hash: SHA-256 hash of the verification token (indexed for lookup)
        expires_at: When this verification token expires (default 24 hours)
        created_at: When this token was created
    
    Relationships:
        user: Reference to the User model being verified
    
    Constraints:
        - Only one active verification token per user (UNIQUE on user_id)
        - Token hash must be unique (UNIQUE on token_hash)
    """
    __tablename__ = "email_verification_tokens"

    id = Column(Integer, primary_key=True)
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship to User
    user = relationship("User", backref="email_verification_tokens")

    def is_expired(self) -> bool:
        """
        Check if this verification token has expired.
        
        Returns:
            True if the token expiration time has passed, False otherwise
        
        Postcondition:
            - Returns boolean indicating whether expires_at < current_time (UTC)
        """
        return datetime.now(timezone.utc) > self.expires_at

    def __repr__(self) -> str:
        return f"<EmailVerificationToken(id={self.id}, user_id={self.user_id}, expired={self.is_expired()})>"
