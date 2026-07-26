import uuid
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    """
    User model with email verification support.
    
    Attributes:
        id: Unique user identifier (UUID v4)
        name: User's display name
        email: User's email address (unique, indexed)
        password: Hashed password
        role: User role (student, worker, admin)
        email_verified: Whether user has verified their email address
        created_at: Account creation timestamp
    
    Email Verification:
        - New users are created with email_verified=False
        - Users cannot login until email_verified=True
        - A verification token is emailed to confirm ownership
        - See EmailVerificationToken model for token management
    
    Backward Compatibility:
        - Existing users are treated as email_verified=True
        - Allows migration without forcing all users to reverify
    """
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="student", nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())