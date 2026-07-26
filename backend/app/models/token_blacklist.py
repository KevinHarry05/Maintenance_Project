"""TokenBlacklist model for persistent JWT token revocation storage.

This model stores invalidated JWT tokens to prevent their reuse across
server restarts and deployment cycles. Tokens are automatically removed
after expiration via a scheduled cleanup task.

Security considerations:
- Tokens are stored as SHA-256 hashes, not plaintext
- Indexed for O(1) lookup performance during request validation
- Redis cache layer provides faster checks for frequently-used tokens
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class TokenBlacklist(Base):
    """
    Persistent storage for revoked JWT tokens.
    
    Attributes:
        id: Primary key identifier
        token_hash: SHA-256 hash of the JWT token (indexed for O(1) lookup)
        user_id: ID of the user who owned this token (foreign key to User)
        expires_at: When the original JWT token expires (used for auto-cleanup)
        created_at: When token was added to blacklist
        revocation_reason: Why the token was revoked (e.g., user_logout, admin_revoke)
    
    Relationships:
        user: Reference to the User model who owned this token
    """
    __tablename__ = "token_blacklist"

    id = Column(Integer, primary_key=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    revocation_reason = Column(String(255), nullable=True)

    # Relationship to User
    user = relationship("User", backref="blacklisted_tokens")

    def is_expired(self) -> bool:
        """
        Check if this token's expiration time has passed.
        
        Returns:
            True if the token has expired, False otherwise
        
        Postcondition:
            - Returns boolean indicating whether expires_at < current_time (UTC)
        """
        return datetime.now(timezone.utc) > self.expires_at

    def __repr__(self) -> str:
        return f"<TokenBlacklist(id={self.id}, user_id={self.user_id}, reason={self.revocation_reason})>"
