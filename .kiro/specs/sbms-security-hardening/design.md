# SBMS Security & Performance Hardening - Technical Design Document

## Overview

This design document provides comprehensive technical implementation guidance for the SBMS Security & Performance Hardening initiative covering 8 interconnected requirements: secure building retrieval with RBAC, login rate limiting, file upload validation, persistent token blacklist, email verification, database performance indexes, N+1 query optimization, and general security hardening. The design balances security, performance, and maintainability through a layered architecture approach.

## Architecture Overview

```mermaid
graph TB
    subgraph "API Layer"
        Auth["Auth Routes<br/>(login, register, logout)"]
        Buildings["Building Routes<br/>(GET /buildings)"]
        Complaints["Complaint Routes<br/>(CRUD)"]
        Files["File Upload<br/>Routes"]
    end

    subgraph "Middleware & Security"
        RateLimit["Rate Limiter<br/>(Redis-based)"]
        TokenCheck["Token Blacklist<br/>Middleware"]
        RBAC["RBAC Decorator<br/>(role-based)"]
    end

    subgraph "Service Layer"
        AuthSvc["Auth Service<br/>(password, tokens)"]
        BuildingSvc["Building Service<br/>(RBAC queries)"]
        ComplaintSvc["Complaint Service<br/>(eager loading)"]
        FileSvc["File Validator<br/>Service"]
        EmailSvc["Email Service<br/>(verification)"]
    end

    subgraph "Data Access Layer"
        TokenRepo["Token Blacklist<br/>Repository"]
        UserRepo["User Repository<br/>(with verification)"]
        BuildingRepo["Building Repository<br/>(role-aware)"]
        ComplaintRepo["Complaint Repository<br/>(with indexes)"]
    end

    subgraph "Infrastructure"
        PostgreSQL["PostgreSQL<br/>(primary store)"]
        Redis["Redis<br/>(cache layer)"]
        Cache["Token Blacklist<br/>Cache"]
    end

    Auth --> AuthSvc
    Buildings --> BuildingSvc
    Complaints --> ComplaintSvc
    Files --> FileSvc

    RateLimit --> Redis
    TokenCheck --> Cache
    RBAC --> AuthSvc

    AuthSvc --> TokenRepo
    AuthSvc --> UserRepo
    AuthSvc --> EmailSvc
    BuildingSvc --> BuildingRepo
    ComplaintSvc --> ComplaintRepo
    FileSvc --> FileSvc

    TokenRepo --> PostgreSQL
    TokenRepo --> Cache
    UserRepo --> PostgreSQL
    BuildingRepo --> PostgreSQL
    ComplaintRepo --> PostgreSQL

    Cache --> Redis
    EmailSvc -.->|"async"| "SMTP Server"
```

## Database Schema Changes

### New Tables

#### TokenBlacklist Table

Persistent storage for revoked JWT tokens with Redis cache layer:

```sql
CREATE TABLE token_blacklist (
    id SERIAL PRIMARY KEY,
    token_hash VARCHAR(64) NOT NULL UNIQUE,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    revocation_reason VARCHAR(255),
    INDEX idx_token_hash (token_hash),
    INDEX idx_user_id (user_id),
    INDEX idx_expires_at (expires_at)
);
```

**Rationale:**
- `token_hash`: SHA-256 hash of JWT (indexed for O(1) lookup)
- `expires_at`: Used for automatic cleanup and TTL validation
- `revocation_reason`: Audit trail (logout, password-change, admin-revoke)
- Indexes enable efficient queries for cache population and cleanup jobs

#### EmailVerification Table

Temporary storage for email verification tokens:

```sql
CREATE TABLE email_verification_tokens (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(64) NOT NULL UNIQUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_token_hash (token_hash),
    INDEX idx_expires_at (expires_at)
);
```

**Rationale:**
- Only one active token per user at a time (UNIQUE constraint on user_id)
- `token_hash`: SHA-256 hash for secure storage
- Automatic cleanup via expired token records
- Used during registration and resend flow

### User Table Modifications

Add email verification support:

```sql
ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE NOT NULL;
ALTER TABLE users ADD COLUMN created_at_modified TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
```

**Rationale:**
- `email_verified`: Flag to block login for unverified emails
- Allows backward compatibility (existing users treated as verified)

### Complaint Table Indexes (Performance)

```sql
-- Status filtering for complaint lists
CREATE INDEX idx_complaints_status ON complaints(status);

-- Finding complaints assigned to specific worker
CREATE INDEX idx_complaints_assigned_to ON complaints(assigned_to);

-- Temporal filtering and sorting
CREATE INDEX idx_complaints_created_at ON complaints(created_at DESC);

-- Composite index for common queries
CREATE INDEX idx_complaints_status_created ON complaints(status, created_at DESC);
```

### Supporting Table Indexes

```sql
-- Ticket logs lookup by complaint
CREATE INDEX idx_ticket_logs_complaint_id ON ticket_logs(complaint_id);

-- Notification retrieval per user
CREATE INDEX idx_notifications_user_id ON notifications(user_id);

-- Unread notification filtering
CREATE INDEX idx_notifications_is_read ON notifications(is_read)
WHERE is_read = false;  -- Partial index for unread only
```

## SQLAlchemy ORM Modifications

### New Models

#### TokenBlacklist Model

```python
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"

    id = Column(Integer, primary_key=True)
    token_hash = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    revocation_reason = Column(String(255), nullable=True)

    # Relationship
    user = relationship("User")

    def is_expired(self) -> bool:
        """Check if token expiration has passed"""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc) > self.expires_at
```

#### EmailVerificationToken Model

```python
class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"

    id = Column(Integer, primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), 
                     unique=True, nullable=False)
    token_hash = Column(String(64), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    user = relationship("User")

    def is_expired(self) -> bool:
        """Check if verification token expiration has passed"""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc) > self.expires_at
```

### Updated User Model

```python
from sqlalchemy import Boolean

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="student", nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

### Complaint Model - Eager Loading Setup

```python
class Complaint(Base):
    __tablename__ = "complaints"
    
    # ... existing fields ...
    
    user_id = Column(String(36), ForeignKey("users.id"))
    building_id = Column(String(36), ForeignKey("buildings.id"))
    assigned_to = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    # Relationships with proper loading strategies
    created_by = relationship(
        "User",
        foreign_keys=[user_id],
        lazy="select"  # Will be loaded via selectinload in service layer
    )
    assigned_worker = relationship(
        "User",
        foreign_keys=[assigned_to],
        lazy="select"  # Will be loaded via selectinload in service layer
    )
    notifications = relationship(
        "Notification",
        back_populates="complaint",
        lazy="select"  # Will be loaded via selectinload in service layer
    )
    ticket_logs = relationship(
        "TicketLog",
        back_populates="complaint",
        lazy="select"  # Will be loaded via selectinload in service layer
    )
```

## API Endpoint Specifications

### 1. Secure Building Retrieval (Requirement 1)

#### GET /buildings - List Buildings with RBAC

**Authentication Required:** YES (JWT token)

**Request:**

```http
GET /buildings?limit=20&offset=0
Authorization: Bearer <JWT_TOKEN>
```

**Query Parameters:**
- `limit` (int, default 20): Maximum buildings to return
- `offset` (int, default 0): Pagination offset

**Response (Admin - 200 OK):**

```json
{
  "success": true,
  "data": [
    {
      "id": "building-123",
      "name": "Main Academic Block",
      "block": "A",
      "floor_count": 4,
      "campus": "main"
    },
    {
      "id": "building-456",
      "name": "Science Block",
      "block": "B",
      "floor_count": 3,
      "campus": "main"
    }
  ],
  "message": "Buildings retrieved successfully",
  "request_id": "req-12345"
}
```

**Response (Student - 200 OK):**

```json
{
  "success": true,
  "data": [
    {
      "id": "building-123",
      "name": "Main Academic Block",
      "block": "A",
      "floor_count": 4,
      "campus": "main"
    }
  ],
  "message": "Buildings for your campus retrieved successfully",
  "request_id": "req-12345"
}
```

**Response (No JWT - 401 Unauthorized):**

```json
{
  "success": false,
  "data": {},
  "message": "Authorization credentials are missing or invalid",
  "request_id": "req-12345"
}
```

**Response (Insufficient Permissions - 403 Forbidden):**

```json
{
  "success": false,
  "data": {},
  "message": "User does not have permission to access buildings",
  "request_id": "req-12345"
}
```

**OpenAPI Documentation:**

```yaml
/buildings:
  get:
    summary: List buildings with role-based filtering
    tags:
      - Buildings
    parameters:
      - in: query
        name: limit
        schema:
          type: integer
          default: 20
        description: Maximum results to return
      - in: query
        name: offset
        schema:
          type: integer
          default: 0
        description: Pagination offset
    security:
      - bearer: []
    responses:
      '200':
        description: Buildings retrieved successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                data:
                  type: array
                  items:
                    $ref: '#/components/schemas/Building'
      '401':
        description: Missing or invalid authentication token
      '403':
        description: Insufficient permissions
      '500':
        description: Internal server error
```

**Implementation Notes:**
- RBAC roles: Admin (all buildings), Worker (assigned buildings), Student (campus buildings)
- Logging: Log all access attempts with user role and result
- Performance: Uses index on building.campus and building.assigned_workers (if applicable)

---

### 2. Login Rate Limiting (Requirement 2)

#### POST /auth/login - With Rate Limiting

**Authentication Required:** NO

**Request:**

```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response (Success - 200 OK):**

```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user": {
      "id": "user-123",
      "name": "John Doe",
      "email": "user@example.com",
      "role": "admin"
    }
  },
  "message": "Login successful",
  "request_id": "req-12345"
}
```

**Response (Rate Limited - 429 Too Many Requests):**

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 30
Content-Type: application/json

{
  "success": false,
  "data": {},
  "message": "Too many login attempts. Please try again later.",
  "request_id": "req-12345"
}
```

**Response (Invalid Credentials - 401 Unauthorized):**

```json
{
  "success": false,
  "data": {},
  "message": "Invalid email or password",
  "request_id": "req-12345"
}
```

**Response (Email Not Verified - 403 Forbidden):**

```json
{
  "success": false,
  "data": {},
  "message": "Email not verified. Please verify your email to login.",
  "request_id": "req-12345"
}
```

**Rate Limiting Behavior:**
- Tracks per client IP (uses X-Forwarded-For for proxy awareness)
- Limit: 5 attempts per 60 seconds (configurable via env vars)
- Resets on successful login
- Increments on failed login
- Logging: All violations logged with IP, timestamp, and attempt count

---

### 3. File Upload Validation (Requirement 3)

#### POST /complaints/{complaint_id}/upload - File Upload with Validation

**Authentication Required:** YES

**Request:**

```http
POST /complaints/complaint-123/upload
Authorization: Bearer <JWT_TOKEN>
Content-Type: multipart/form-data

file: <binary_image_data>
```

**Response (Success - 200 OK):**

```json
{
  "success": true,
  "data": {
    "file_id": "file-uuid-123",
    "filename": "a1b2c3d4-e5f6-47g8-h9i0-j1k2l3m4n5o6.jpg",
    "original_filename": "complaint_photo.jpg",
    "size_bytes": 2048576,
    "mime_type": "image/jpeg",
    "url": "/uploads/a1b2c3d4-e5f6-47g8-h9i0-j1k2l3m4n5o6.jpg"
  },
  "message": "File uploaded successfully",
  "request_id": "req-12345"
}
```

**Response (Invalid Extension - 400 Bad Request):**

```json
{
  "success": false,
  "data": {
    "field": "file",
    "error": "invalid_extension"
  },
  "message": "File extension '.exe' is not allowed. Allowed extensions: .jpg, .jpeg, .png, .webp",
  "request_id": "req-12345"
}
```

**Response (Invalid MIME Type - 400 Bad Request):**

```json
{
  "success": false,
  "data": {
    "field": "file",
    "error": "invalid_mime_type"
  },
  "message": "MIME type 'application/x-executable' is not allowed. Allowed types: image/jpeg, image/png, image/webp",
  "request_id": "req-12345"
}
```

**Response (File Too Large - 413 Payload Too Large):**

```json
{
  "success": false,
  "data": {
    "field": "file",
    "error": "file_too_large"
  },
  "message": "File size (12 MB) exceeds maximum allowed size (10 MB)",
  "request_id": "req-12345"
}
```

**Response (Path Traversal Attempt - 400 Bad Request):**

```json
{
  "success": false,
  "data": {
    "field": "file",
    "error": "invalid_path"
  },
  "message": "Filename contains invalid characters. Path traversal attempts are blocked.",
  "request_id": "req-12345"
}
```

---

### 4. Token Blacklist Middleware (Requirement 4)

#### Token Validation Flow

**Middleware Pseudocode:**

```pascal
MIDDLEWARE checkTokenBlacklist(request)
    IF request requires authentication THEN
        token ← extractJWTFromHeader(request)
        
        IF token IS NULL THEN
            RETURN HttpError(401, "Missing authentication token")
        END IF
        
        token_hash ← sha256(token)
        
        // Try Redis cache first
        cached_entry ← redis.get("blacklist:" + token_hash)
        
        IF cached_entry EXISTS THEN
            RETURN HttpError(401, "Token has been revoked")
        END IF
        
        // Query PostgreSQL if not in cache
        blacklist_entry ← database.query(TokenBlacklist)
                            .where(token_hash = token_hash)
                            .first()
        
        IF blacklist_entry EXISTS THEN
            // Cache the result for 5 minutes
            redis.setex("blacklist:" + token_hash, 300, "revoked")
            RETURN HttpError(401, "Token has been revoked")
        END IF
        
        // Token is valid, continue
        request.user_id ← decodeJWT(token).user_id
        RETURN NextMiddleware(request)
    END IF
END MIDDLEWARE
```

**Logout Endpoint (POST /auth/logout):**

```http
POST /auth/logout
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
  "reason": "user_logout"  // optional
}
```

**Response (200 OK):**

```json
{
  "success": true,
  "data": {},
  "message": "Logged out successfully",
  "request_id": "req-12345"
}
```

**Logout Implementation:**

```python
def logout_user(token: str, request: Request, db: Session):
    """
    Add JWT token to blacklist and invalidate session
    
    Preconditions:
    - token is valid JWT extracted from Authorization header
    - token has not expired
    
    Postconditions:
    - token exists in token_blacklist table
    - token cached in Redis with 5-minute TTL
    - user's sessions are invalidated
    """
    token_hash = sha256(token.encode()).hexdigest()
    
    # Decode token to get expiration
    payload = decode_jwt(token)
    expires_at = datetime.fromtimestamp(payload['exp'], tz=timezone.utc)
    
    # Add to PostgreSQL blacklist
    blacklist_entry = TokenBlacklist(
        token_hash=token_hash,
        user_id=payload['sub'],
        expires_at=expires_at,
        revocation_reason="user_logout"
    )
    db.add(blacklist_entry)
    db.commit()
    
    # Cache in Redis for faster checks
    redis_key = f"blacklist:{token_hash}"
    redis_client.setex(redis_key, 300, "revoked")  # 5-minute TTL
    
    logger.info(
        "Token revoked",
        user_id=payload['sub'],
        reason="user_logout"
    )
```

---

### 5. Email Verification (Requirement 5)

#### POST /auth/register - Registration with Email Verification

**Request:**

```http
POST /auth/register
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "role": "student"
}
```

**Response (Success - 201 Created):**

```json
{
  "success": true,
  "data": {
    "user_id": "user-123",
    "email": "john@example.com",
    "email_verified": false,
    "message_to_user": "Verification email sent to john@example.com. Please verify your email within 24 hours."
  },
  "message": "Registration successful. Please check your email.",
  "request_id": "req-12345"
}
```

**Email Content Sent:**

```
Subject: Verify Your Email Address - SBMS

Dear John Doe,

Thank you for registering with the Smart Building Management System.

Please verify your email address by clicking the link below:

https://sbms.example.com/verify?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

This link will expire in 24 hours.

If you did not create this account, please ignore this email.

Best regards,
SBMS Team
```

#### GET /auth/verify?token=<TOKEN> - Email Verification

**Request:**

```http
GET /auth/verify?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (Success - 200 OK):**

```json
{
  "success": true,
  "data": {
    "email": "john@example.com",
    "email_verified": true
  },
  "message": "Email verified successfully. You can now login.",
  "request_id": "req-12345"
}
```

**Response (Token Expired - 400 Bad Request):**

```json
{
  "success": false,
  "data": {
    "field": "token",
    "error": "token_expired"
  },
  "message": "Verification token has expired. Please request a new verification email.",
  "request_id": "req-12345"
}
```

**Response (Invalid Token - 400 Bad Request):**

```json
{
  "success": false,
  "data": {
    "field": "token",
    "error": "invalid_token"
  },
  "message": "Invalid or malformed verification token.",
  "request_id": "req-12345"
}
```

#### POST /auth/resend-verification-email - Resend Verification

**Request:**

```http
POST /auth/resend-verification-email
Content-Type: application/json

{
  "email": "john@example.com"
}
```

**Response (Success - 200 OK):**

```json
{
  "success": true,
  "data": {
    "email": "john@example.com",
    "message_to_user": "New verification email has been sent. Please check your inbox."
  },
  "message": "Verification email resent",
  "request_id": "req-12345"
}
```

**Response (Rate Limited - 429 Too Many Requests):**

```json
{
  "success": false,
  "data": {},
  "message": "Too many resend requests. Please try again in 20 minutes.",
  "request_id": "req-12345"
}
```

**Email Verification Flow:**

```pascal
PROCEDURE registerUser(credentials)
    INPUT: credentials (name, email, password, role)
    OUTPUT: user with email_verified=false
    
    SEQUENCE
        // Validate input
        ASSERT credentials.email != null
        ASSERT isValidEmail(credentials.email)
        ASSERT isStrongPassword(credentials.password)
        
        // Check for existing user
        existing_user ← database.findUserByEmail(credentials.email)
        IF existing_user EXISTS THEN
            RETURN Error("Email already registered")
        END IF
        
        // Create user account
        password_hash ← bcrypt.hash(credentials.password)
        user ← new User(
            name=credentials.name,
            email=credentials.email,
            password=password_hash,
            role=credentials.role,
            email_verified=false
        )
        database.save(user)
        
        // Generate verification token
        raw_token ← generateSecureRandomBytes(32)
        token_hash ← sha256(raw_token)
        
        verification_token ← new EmailVerificationToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=now() + 24 hours
        )
        database.save(verification_token)
        
        // Send verification email
        verification_link ← buildVerificationLink(raw_token)
        sendEmail(user.email, buildEmailContent(verification_link))
        
        RETURN user
    END SEQUENCE
END PROCEDURE

PROCEDURE verifyEmail(token)
    INPUT: token (unencrypted verification token)
    OUTPUT: user with email_verified=true OR error
    
    SEQUENCE
        // Hash the provided token
        token_hash ← sha256(token)
        
        // Query for token in database
        verification_token ← database.query(EmailVerificationToken)
                               .where(token_hash = token_hash)
                               .first()
        
        IF verification_token IS NULL THEN
            RETURN Error("Invalid verification token")
        END IF
        
        // Check expiration
        IF verification_token.expires_at < now() THEN
            // Delete expired token
            database.delete(verification_token)
            RETURN Error("Verification token has expired")
        END IF
        
        // Mark user as verified
        user ← database.findUserById(verification_token.user_id)
        user.email_verified ← true
        database.save(user)
        
        // Delete verification token
        database.delete(verification_token)
        
        RETURN user
    END SEQUENCE
END PROCEDURE
```

---

## Service Layer Implementation

### Password Validation Service

```python
import re
from typing import Tuple

class PasswordValidator:
    """
    Validates passwords against security requirements
    
    Requirements:
    - Minimum 12 characters
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 digit
    - At least 1 special character
    """
    
    MIN_LENGTH = 12
    UPPERCASE_PATTERN = re.compile(r'[A-Z]')
    LOWERCASE_PATTERN = re.compile(r'[a-z]')
    DIGIT_PATTERN = re.compile(r'\d')
    SPECIAL_PATTERN = re.compile(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]')
    
    @staticmethod
    def validate(password: str) -> Tuple[bool, str]:
        """
        Validate password strength
        
        Args:
            password: Password to validate
        
        Returns:
            Tuple of (is_valid: bool, message: str)
        
        Postcondition:
            - If valid: returns (True, "")
            - If invalid: returns (False, generic_message)
            - Never returns which specific requirement failed
        """
        # Check length
        if len(password) < PasswordValidator.MIN_LENGTH:
            return False, "Password does not meet requirements"
        
        # Check character types
        has_upper = PasswordValidator.UPPERCASE_PATTERN.search(password)
        has_lower = PasswordValidator.LOWERCASE_PATTERN.search(password)
        has_digit = PasswordValidator.DIGIT_PATTERN.search(password)
        has_special = PasswordValidator.SPECIAL_PATTERN.search(password)
        
        if not (has_upper and has_lower and has_digit and has_special):
            return False, "Password does not meet requirements"
        
        return True, ""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.verify(plain_password, hashed_password)
```



## File Validator Service Implementation

### MIME Type and Extension Validation

```python
import os
import mimetypes
from typing import Tuple
from pathlib import Path
import hashlib
import logging

logger = logging.getLogger(__name__)

class FileValidationException(Exception):
    """Base exception for file validation errors"""
    pass

class InvalidMimeTypeException(FileValidationException):
    """Raised when MIME type is not allowed"""
    pass

class InvalidExtensionException(FileValidationException):
    """Raised when file extension is not allowed"""
    pass

class PathTraversalException(FileValidationException):
    """Raised when path traversal attack is detected"""
    pass

class FileValidator:
    """
    Validates uploaded files for security and compliance
    
    Security measures:
    - Whitelist-based MIME type validation
    - Whitelist-based extension validation
    - Path traversal prevention
    - File size limits
    - Magic number (file signature) verification
    """
    
    # Whitelist of allowed MIME types
    ALLOWED_MIME_TYPES = {
        'image/jpeg',
        'image/png',
        'image/webp',
        'application/pdf'
    }
    
    # Whitelist of allowed file extensions
    ALLOWED_EXTENSIONS = {
        '.jpg',
        '.jpeg',
        '.png',
        '.webp',
        '.pdf'
    }
    
    # Magic numbers (file signatures) for verification
    # Format: {extension: (offset, hex_signature)}
    MAGIC_NUMBERS = {
        '.jpg': (0, b'\xff\xd8\xff'),
        '.jpeg': (0, b'\xff\xd8\xff'),
        '.png': (0, b'\x89PNG\r\n\x1a\n'),
        '.webp': (0, b'RIFF'),  # Check for WEBP at offset 8
        '.pdf': (0, b'%PDF')
    }
    
    # Maximum file sizes (in bytes)
    MAX_FILE_SIZES = {
        'image': 10 * 1024 * 1024,  # 10 MB for images
        'pdf': 50 * 1024 * 1024     # 50 MB for PDFs
    }
    
    # Forbidden characters/patterns in filenames
    FORBIDDEN_PATH_CHARS = {'/', '\\', '\0', '\n', '\r'}
    FORBIDDEN_PATTERNS = {'..', '~', '$'}
    
    @staticmethod
    def validate_filename(filename: str) -> Tuple[bool, str]:
        """
        Validate filename for security issues
        
        Args:
            filename: Original filename from upload
        
        Returns:
            Tuple of (is_valid: bool, error_message: str)
        
        Preconditions:
            - filename is not None
            - filename is a string
        
        Postconditions:
            - Returns (False, message) if path traversal detected
            - Returns (False, message) if forbidden chars detected
            - Returns (True, "") if valid
        """
        # Check for path traversal attempts
        if '..' in filename:
            logger.warning(
                "Path traversal attempt detected",
                filename=filename,
                severity="high"
            )
            raise PathTraversalException("Filename contains '..' path traversal")
        
        # Check for forbidden characters
        for char in FileValidator.FORBIDDEN_PATH_CHARS:
            if char in filename:
                logger.warning(
                    "Forbidden character in filename",
                    filename=filename,
                    forbidden_char=repr(char),
                    severity="high"
                )
                raise PathTraversalException(
                    f"Filename contains forbidden character: {repr(char)}"
                )
        
        # Check for forbidden patterns
        for pattern in FileValidator.FORBIDDEN_PATTERNS:
            if pattern in filename:
                logger.warning(
                    "Forbidden pattern in filename",
                    filename=filename,
                    pattern=pattern,
                    severity="high"
                )
                raise PathTraversalException(
                    f"Filename contains forbidden pattern: {pattern}"
                )
        
        return True, ""
    
    @staticmethod
    def validate_extension(filename: str) -> Tuple[bool, str]:
        """
        Validate file extension against whitelist
        
        Args:
            filename: Original filename from upload
        
        Returns:
            Tuple of (is_valid: bool, error_message: str)
        
        Preconditions:
            - filename contains at least one dot
        
        Postconditions:
            - Returns (False, message) if extension not in whitelist
            - Returns (True, "") if valid
        """
        # Get extension and normalize
        _, ext = os.path.splitext(filename)
        ext = ext.lower()
        
        if not ext or ext not in FileValidator.ALLOWED_EXTENSIONS:
            allowed = ', '.join(FileValidator.ALLOWED_EXTENSIONS)
            logger.warning(
                "Invalid file extension",
                filename=filename,
                extension=ext,
                allowed_extensions=allowed
            )
            raise InvalidExtensionException(
                f"File extension '{ext}' is not allowed. "
                f"Allowed extensions: {allowed}"
            )
        
        return True, ""
    
    @staticmethod
    def validate_mime_type(file_content: bytes, filename: str) -> Tuple[bool, str]:
        """
        Validate MIME type using both extension and content inspection
        
        Args:
            file_content: Binary content of uploaded file
            filename: Original filename from upload
        
        Returns:
            Tuple of (is_valid: bool, error_message: str)
        
        Preconditions:
            - file_content is not empty
            - filename is valid (validated by validate_filename)
        
        Postconditions:
            - Returns (False, message) if MIME type not in whitelist
            - Returns (True, "") if MIME type matches whitelist
        """
        # Guess MIME type from filename
        guessed_mime, _ = mimetypes.guess_type(filename)
        
        # Also check magic numbers
        _, ext = os.path.splitext(filename)
        ext = ext.lower()
        
        # Verify magic number
        if ext in FileValidator.MAGIC_NUMBERS:
            offset, signature = FileValidator.MAGIC_NUMBERS[ext]
            
            if ext == '.webp':
                # Special handling for WEBP: check for RIFF at start and WEBP at offset 8
                if not (file_content.startswith(b'RIFF') and 
                        b'WEBP' in file_content[8:12]):
                    logger.warning(
                        "Magic number mismatch",
                        filename=filename,
                        extension=ext,
                        expected_signature=signature.hex()
                    )
                    raise InvalidMimeTypeException(
                        f"File content does not match extension {ext}"
                    )
            else:
                # Check if file starts with expected signature
                if not file_content[offset:].startswith(signature):
                    logger.warning(
                        "Magic number mismatch",
                        filename=filename,
                        extension=ext,
                        expected_signature=signature.hex()
                    )
                    raise InvalidMimeTypeException(
                        f"File content does not match extension {ext}"
                    )
        
        # Verify MIME type is in whitelist
        if guessed_mime not in FileValidator.ALLOWED_MIME_TYPES:
            allowed = ', '.join(FileValidator.ALLOWED_MIME_TYPES)
            logger.warning(
                "Invalid MIME type",
                filename=filename,
                mime_type=guessed_mime,
                allowed_types=allowed
            )
            raise InvalidMimeTypeException(
                f"MIME type '{guessed_mime}' is not allowed. "
                f"Allowed types: {allowed}"
            )
        
        return True, ""
    
    @staticmethod
    def validate_file_size(file_content: bytes, filename: str) -> Tuple[bool, str]:
        """
        Validate file size against limits
        
        Args:
            file_content: Binary content of uploaded file
            filename: Original filename from upload
        
        Returns:
            Tuple of (is_valid: bool, error_message: str)
        
        Preconditions:
            - file_content is bytes object
            - filename has valid extension
        
        Postconditions:
            - Returns (False, message) if file exceeds size limit
            - Returns (True, "") if file size is acceptable
        """
        file_size = len(file_content)
        _, ext = os.path.splitext(filename)
        ext = ext.lower()
        
        # Determine file type and max size
        if ext in {'.jpg', '.jpeg', '.png', '.webp'}:
            max_size = FileValidator.MAX_FILE_SIZES['image']
            file_type = "image"
        elif ext == '.pdf':
            max_size = FileValidator.MAX_FILE_SIZES['pdf']
            file_type = "pdf"
        else:
            max_size = FileValidator.MAX_FILE_SIZES['image']  # Default
            file_type = "file"
        
        if file_size > max_size:
            max_mb = max_size / (1024 * 1024)
            actual_mb = file_size / (1024 * 1024)
            logger.warning(
                "File size exceeds limit",
                filename=filename,
                file_size_mb=actual_mb,
                max_size_mb=max_mb
            )
            raise FileValidationException(
                f"File size ({actual_mb:.1f} MB) exceeds maximum allowed size ({max_mb:.1f} MB)"
            )
        
        return True, ""
    
    @staticmethod
    def validate_and_hash(
        file_content: bytes,
        filename: str
    ) -> Tuple[str, str]:
        """
        Complete file validation and generate safe filename
        
        Args:
            file_content: Binary content of uploaded file
            filename: Original filename from upload
        
        Returns:
            Tuple of (safe_filename: str, file_hash: str)
        
        Preconditions:
            - file_content is not empty bytes
            - filename is not None or empty
        
        Postconditions:
            - All security checks passed
            - Returns UUID-based safe filename
            - Returns SHA-256 hash of file content for integrity checking
            
        Raises:
            PathTraversalException: If path traversal detected
            InvalidExtensionException: If extension not whitelisted
            InvalidMimeTypeException: If MIME type invalid or doesn't match extension
            FileValidationException: If file size exceeds limits or other errors
        """
        import uuid
        
        # Validate filename for path traversal
        FileValidator.validate_filename(filename)
        
        # Validate extension
        FileValidator.validate_extension(filename)
        
        # Validate file size
        FileValidator.validate_file_size(file_content, filename)
        
        # Validate MIME type and magic numbers
        FileValidator.validate_mime_type(file_content, filename)
        
        # Generate safe filename with UUID
        _, ext = os.path.splitext(filename)
        safe_filename = f"{uuid.uuid4()}{ext.lower()}"
        
        # Generate SHA-256 hash for integrity verification
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        logger.info(
            "File validation successful",
            original_filename=filename,
            safe_filename=safe_filename,
            file_size=len(file_content),
            file_hash=file_hash
        )
        
        return safe_filename, file_hash
```



## Token Blacklist Service Implementation

### Redis Cache Layer with Database Cleanup

```python
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import hashlib
import logging
from sqlalchemy.orm import Session
from redis import Redis
from app.models.token_blacklist import TokenBlacklist

logger = logging.getLogger(__name__)

class TokenBlacklistService:
    """
    Manages JWT token revocation with dual-layer caching:
    - Redis: Fast in-memory cache for frequent lookups
    - PostgreSQL: Persistent storage for audit trail and cleanup
    
    Caching Strategy:
    - All blacklisted tokens cached in Redis with TTL matching token expiration
    - Cache miss triggers database lookup (for cold cache or token with no expiration)
    - Periodic cleanup job removes expired entries from database
    """
    
    # Redis configuration
    REDIS_BLACKLIST_PREFIX = "token_blacklist:"
    REDIS_TTL_BUFFER_SECONDS = 300  # 5-minute buffer beyond token expiration
    
    def __init__(self, db: Session, redis_client: Redis):
        """
        Initialize service with database and Redis connections
        
        Args:
            db: SQLAlchemy database session
            redis_client: Redis client instance
        """
        self.db = db
        self.redis = redis_client
    
    @staticmethod
    def hash_token(token: str) -> str:
        """
        Hash JWT token using SHA-256 for secure storage
        
        Args:
            token: JWT token string
        
        Returns:
            SHA-256 hash of token
        
        Postcondition:
            - Always returns 64-character hex string
        """
        return hashlib.sha256(token.encode()).hexdigest()
    
    def is_blacklisted(self, token: str) -> bool:
        """
        Check if token is blacklisted (revoked)
        
        Args:
            token: JWT token to check
        
        Returns:
            True if token is blacklisted, False otherwise
        
        Preconditions:
            - token is valid JWT string
        
        Postconditions:
            - If not in Redis cache and exists in DB, caches for next lookup
            - Returns boolean indicating blacklist status
        """
        token_hash = self.hash_token(token)
        redis_key = f"{self.REDIS_BLACKLIST_PREFIX}{token_hash}"
        
        # Try Redis first (fastest)
        try:
            cached = self.redis.get(redis_key)
            if cached is not None:
                logger.debug(
                    "Token blacklist cache hit",
                    token_hash=token_hash[:8]
                )
                return True
        except Exception as e:
            # Redis error - continue to database check
            logger.warning(
                "Redis cache lookup failed",
                error=str(e),
                severity="medium"
            )
        
        # Check database if not in cache
        try:
            blacklist_entry = self.db.query(TokenBlacklist).filter(
                TokenBlacklist.token_hash == token_hash
            ).first()
            
            if blacklist_entry:
                # Token is blacklisted - cache the result
                ttl = max(
                    int((blacklist_entry.expires_at - datetime.now(timezone.utc)).total_seconds()),
                    self.REDIS_TTL_BUFFER_SECONDS
                )
                try:
                    self.redis.setex(redis_key, ttl, "revoked")
                except Exception as e:
                    logger.warning(
                        "Failed to cache blacklist entry in Redis",
                        error=str(e)
                    )
                
                logger.debug(
                    "Token found in blacklist",
                    token_hash=token_hash[:8],
                    reason=blacklist_entry.revocation_reason
                )
                return True
            
            return False
        
        except Exception as e:
            logger.error(
                "Database lookup for blacklist failed",
                error=str(e),
                severity="high"
            )
            # Fail securely - treat as blacklisted if we can't verify
            return True
    
    def revoke_token(
        self,
        token: str,
        user_id: str,
        expires_at: datetime,
        reason: str = "user_logout"
    ) -> TokenBlacklist:
        """
        Add JWT token to blacklist
        
        Args:
            token: JWT token to revoke
            user_id: User ID who owns the token
            expires_at: Token expiration time from JWT payload
            reason: Reason for revocation (logout, password_change, admin_revoke, etc.)
        
        Returns:
            Created TokenBlacklist record
        
        Preconditions:
            - token is non-empty string
            - user_id exists in users table
            - expires_at is datetime in future
            - reason is valid revocation reason
        
        Postconditions:
            - Token hash inserted into token_blacklist table
            - Entry cached in Redis with appropriate TTL
            - Audit log entry created
        """
        token_hash = self.hash_token(token)
        
        # Create database entry
        blacklist_entry = TokenBlacklist(
            token_hash=token_hash,
            user_id=user_id,
            expires_at=expires_at,
            revocation_reason=reason
        )
        
        try:
            self.db.add(blacklist_entry)
            self.db.commit()
            
            # Cache in Redis
            redis_key = f"{self.REDIS_BLACKLIST_PREFIX}{token_hash}"
            ttl = max(
                int((expires_at - datetime.now(timezone.utc)).total_seconds()),
                self.REDIS_TTL_BUFFER_SECONDS
            )
            
            try:
                self.redis.setex(redis_key, ttl, "revoked")
            except Exception as e:
                logger.warning(
                    "Failed to cache revoked token in Redis",
                    error=str(e),
                    token_hash=token_hash[:8]
                )
            
            logger.info(
                "Token revoked successfully",
                user_id=user_id,
                reason=reason,
                token_hash=token_hash[:8]
            )
            
            return blacklist_entry
        
        except Exception as e:
            self.db.rollback()
            logger.error(
                "Failed to revoke token",
                user_id=user_id,
                error=str(e),
                severity="high"
            )
            raise
    
    def revoke_user_tokens(self, user_id: str, reason: str = "password_change") -> int:
        """
        Revoke all tokens for a specific user
        
        Used when:
        - User changes password
        - Admin revokes user access
        - User account is suspended/deleted
        
        Args:
            user_id: User whose tokens should be revoked
            reason: Reason for bulk revocation
        
        Returns:
            Number of tokens revoked
        
        Postconditions:
            - All non-expired tokens for user added to blacklist
            - Redis cache invalidated for affected tokens
        """
        try:
            # Find all non-expired tokens for user
            user_tokens = self.db.query(TokenBlacklist).filter(
                TokenBlacklist.user_id == user_id,
                TokenBlacklist.expires_at > datetime.now(timezone.utc)
            ).all()
            
            count = 0
            for token_entry in user_tokens:
                token_entry.revocation_reason = reason
                redis_key = f"{self.REDIS_BLACKLIST_PREFIX}{token_entry.token_hash}"
                
                try:
                    self.redis.delete(redis_key)
                except Exception as e:
                    logger.warning(f"Failed to remove from Redis cache: {str(e)}")
                
                count += 1
            
            self.db.commit()
            
            logger.info(
                "User tokens revoked",
                user_id=user_id,
                count=count,
                reason=reason
            )
            
            return count
        
        except Exception as e:
            self.db.rollback()
            logger.error(
                "Failed to revoke user tokens",
                user_id=user_id,
                error=str(e),
                severity="high"
            )
            raise
    
    def cleanup_expired_tokens(self) -> int:
        """
        Remove expired tokens from database
        
        Should be called periodically (daily recommended) via background job
        
        Returns:
            Number of expired tokens deleted
        
        Postconditions:
            - All tokens with expires_at < now() deleted from database
            - Associated Redis cache entries removed
        """
        try:
            # Query expired tokens
            expired_tokens = self.db.query(TokenBlacklist).filter(
                TokenBlacklist.expires_at <= datetime.now(timezone.utc)
            ).all()
            
            count = 0
            for token in expired_tokens:
                # Remove from Redis cache
                redis_key = f"{self.REDIS_BLACKLIST_PREFIX}{token.token_hash}"
                try:
                    self.redis.delete(redis_key)
                except Exception as e:
                    logger.warning(
                        "Failed to remove expired token from Redis",
                        error=str(e)
                    )
                
                # Delete from database
                self.db.delete(token)
                count += 1
            
            self.db.commit()
            
            logger.info(
                "Expired tokens cleaned up",
                count=count
            )
            
            return count
        
        except Exception as e:
            self.db.rollback()
            logger.error(
                "Cleanup of expired tokens failed",
                error=str(e),
                severity="high"
            )
            raise
    
    def get_revocation_stats(self) -> dict:
        """
        Get statistics about token revocations
        
        Returns:
            Dictionary with counts and timestamps
        
        Postcondition:
            - Returns current blacklist statistics for monitoring
        """
        try:
            total_count = self.db.query(TokenBlacklist).count()
            
            active_count = self.db.query(TokenBlacklist).filter(
                TokenBlacklist.expires_at > datetime.now(timezone.utc)
            ).count()
            
            redis_count = 0
            try:
                redis_count = self.redis.dbsize()
            except Exception as e:
                logger.warning(f"Failed to get Redis DB size: {str(e)}")
            
            return {
                "total_blacklisted": total_count,
                "active_in_cache": active_count,
                "redis_keys_approximate": redis_count,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        except Exception as e:
            logger.error(
                "Failed to get revocation stats",
                error=str(e)
            )
            return {}
```



## Rate Limiter Implementation

### IP-Based Rate Limiting for Login Attempts

```python
from datetime import datetime, timedelta, timezone
from typing import Tuple, Optional
import logging
from redis import Redis
from ipaddress import ip_address, IPv4Address, IPv6Address

logger = logging.getLogger(__name__)

class RateLimitExceededException(Exception):
    """Raised when rate limit is exceeded"""
    pass

class RateLimiter:
    """
    IP-based rate limiter using Redis for distributed rate limiting
    
    Configuration:
    - Per-IP rate limits (separate buckets per IP)
    - Configurable limits and time windows
    - X-Forwarded-For header support for proxy environments
    - Automatic expiration via Redis TTL
    """
    
    # Rate limit configuration
    LOGIN_ATTEMPTS_LIMIT = 5  # Max attempts
    LOGIN_ATTEMPTS_WINDOW = 60  # Time window in seconds (60 seconds = 1 minute)
    LOGIN_LOCKOUT_DURATION = 1800  # 30 minutes
    
    # Redis configuration
    REDIS_LOGIN_PREFIX = "rate_limit:login:"
    REDIS_LOCKOUT_PREFIX = "rate_limit:lockout:"
    
    def __init__(self, redis_client: Redis):
        """
        Initialize rate limiter with Redis client
        
        Args:
            redis_client: Redis client instance
        """
        self.redis = redis_client
    
    @staticmethod
    def extract_client_ip(request) -> str:
        """
        Extract client IP from request, handling proxies
        
        Args:
            request: FastAPI/Starlette request object
        
        Returns:
            Client IP address as string
        
        Preconditions:
            - request object has headers and client attributes
        
        Postconditions:
            - Returns trusted IP from X-Forwarded-For if configured
            - Falls back to request.client.host
            - Never returns None
        """
        # Check for X-Forwarded-For header (proxy environments)
        x_forwarded_for = request.headers.get("X-Forwarded-For")
        if x_forwarded_for:
            # X-Forwarded-For can be comma-separated list of IPs
            # Use the first one (client IP)
            ips = [ip.strip() for ip in x_forwarded_for.split(",")]
            client_ip = ips[0]
        else:
            # Fall back to direct connection
            client_ip = request.client.host if request.client else "unknown"
        
        # Validate IP format
        try:
            ip_address(client_ip)
        except ValueError:
            logger.warning(
                "Invalid IP format extracted",
                ip=client_ip,
                x_forwarded_for=x_forwarded_for
            )
            client_ip = "unknown"
        
        return client_ip
    
    def is_ip_locked_out(self, client_ip: str) -> Tuple[bool, Optional[int]]:
        """
        Check if IP is currently locked out
        
        Args:
            client_ip: Client IP address
        
        Returns:
            Tuple of (is_locked_out: bool, seconds_remaining: Optional[int])
        
        Postconditions:
            - Returns (True, seconds) if locked out
            - Returns (False, None) if not locked out
        """
        lockout_key = f"{self.REDIS_LOCKOUT_PREFIX}{client_ip}"
        
        try:
            ttl = self.redis.ttl(lockout_key)
            
            if ttl > 0:
                # IP is locked out
                logger.info(
                    "Rate limit lockout active",
                    client_ip=client_ip,
                    seconds_remaining=ttl
                )
                return True, ttl
            
            return False, None
        
        except Exception as e:
            logger.error(
                "Failed to check lockout status",
                client_ip=client_ip,
                error=str(e),
                severity="high"
            )
            # Fail securely - treat as locked out
            return True, 60
    
    def check_rate_limit(self, client_ip: str) -> Tuple[bool, dict]:
        """
        Check if request is within rate limits
        
        Args:
            client_ip: Client IP address
        
        Returns:
            Tuple of (allowed: bool, details: dict)
                details contains: attempts, limit, reset_at, locked_until
        
        Preconditions:
            - client_ip is valid IP address string
        
        Postconditions:
            - If within limit: returns (True, {})
            - If limit exceeded: 
                - Increments attempt count
                - Sets lockout if consecutive attempts exceed limit
                - Returns (False, details)
            - Attempt counter auto-expires after window
        """
        # First check if IP is locked out
        is_locked, remaining = self.is_ip_locked_out(client_ip)
        if is_locked:
            return False, {
                "reason": "ip_locked_out",
                "locked_until_seconds": remaining
            }
        
        # Check current attempt count
        attempt_key = f"{self.REDIS_LOGIN_PREFIX}{client_ip}"
        
        try:
            attempts = self.redis.get(attempt_key)
            attempts = int(attempts) if attempts else 0
            
            if attempts >= self.LOGIN_ATTEMPTS_LIMIT:
                # Limit exceeded - lock out IP
                self._apply_lockout(client_ip)
                
                logger.warning(
                    "Rate limit exceeded, IP locked out",
                    client_ip=client_ip,
                    attempts=attempts,
                    limit=self.LOGIN_ATTEMPTS_LIMIT,
                    severity="medium"
                )
                
                return False, {
                    "reason": "rate_limit_exceeded",
                    "attempts": attempts,
                    "limit": self.LOGIN_ATTEMPTS_LIMIT,
                    "locked_until_seconds": self.LOGIN_LOCKOUT_DURATION
                }
            
            # Within limit - increment attempt counter
            new_attempts = attempts + 1
            self.redis.setex(
                attempt_key,
                self.LOGIN_ATTEMPTS_WINDOW,
                new_attempts
            )
            
            # Log attempt
            logger.debug(
                "Login attempt recorded",
                client_ip=client_ip,
                attempt_count=new_attempts,
                limit=self.LOGIN_ATTEMPTS_LIMIT
            )
            
            return True, {
                "attempts": new_attempts,
                "limit": self.LOGIN_ATTEMPTS_LIMIT,
                "reset_at": datetime.now(timezone.utc) + 
                           timedelta(seconds=self.LOGIN_ATTEMPTS_WINDOW)
            }
        
        except Exception as e:
            logger.error(
                "Rate limit check failed",
                client_ip=client_ip,
                error=str(e),
                severity="high"
            )
            # Fail open - allow request but log
            return True, {"warning": "rate_limit_check_failed"}
    
    def _apply_lockout(self, client_ip: str) -> None:
        """
        Apply lockout to IP address
        
        Args:
            client_ip: Client IP to lock out
        
        Postconditions:
            - IP added to lockout key with TTL
            - Attempt counter cleared
        """
        try:
            lockout_key = f"{self.REDIS_LOCKOUT_PREFIX}{client_ip}"
            attempt_key = f"{self.REDIS_LOGIN_PREFIX}{client_ip}"
            
            # Set lockout with expiration
            self.redis.setex(
                lockout_key,
                self.LOGIN_LOCKOUT_DURATION,
                "locked"
            )
            
            # Clear attempt counter
            self.redis.delete(attempt_key)
            
            logger.info(
                "IP lockout applied",
                client_ip=client_ip,
                duration_seconds=self.LOGIN_LOCKOUT_DURATION
            )
        
        except Exception as e:
            logger.error(
                "Failed to apply lockout",
                client_ip=client_ip,
                error=str(e),
                severity="high"
            )
    
    def reset_ip_attempts(self, client_ip: str) -> None:
        """
        Reset rate limit attempts for successful login
        
        Called after successful authentication to allow future attempts
        
        Args:
            client_ip: Client IP to reset
        
        Postconditions:
            - Attempt counter deleted
            - Lockout cleared if present
        """
        try:
            attempt_key = f"{self.REDIS_LOGIN_PREFIX}{client_ip}"
            lockout_key = f"{self.REDIS_LOCKOUT_PREFIX}{client_ip}"
            
            self.redis.delete(attempt_key)
            self.redis.delete(lockout_key)
            
            logger.info(
                "Rate limit reset for IP",
                client_ip=client_ip
            )
        
        except Exception as e:
            logger.warning(
                "Failed to reset rate limit",
                client_ip=client_ip,
                error=str(e)
            )
    
    def get_limit_status(self, client_ip: str) -> dict:
        """
        Get current rate limit status for an IP
        
        Returns:
            Dictionary with current status for monitoring
        """
        try:
            attempt_key = f"{self.REDIS_LOGIN_PREFIX}{client_ip}"
            lockout_key = f"{self.REDIS_LOCKOUT_PREFIX}{client_ip}"
            
            attempts = int(self.redis.get(attempt_key) or 0)
            lockout_ttl = self.redis.ttl(lockout_key)
            
            return {
                "client_ip": client_ip,
                "current_attempts": attempts,
                "limit": self.LOGIN_ATTEMPTS_LIMIT,
                "window_seconds": self.LOGIN_ATTEMPTS_WINDOW,
                "is_locked_out": lockout_ttl > 0,
                "lockout_remaining_seconds": lockout_ttl if lockout_ttl > 0 else None,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        except Exception as e:
            logger.error(f"Failed to get limit status: {str(e)}")
            return {"error": "status_check_failed"}
```



## Building Service with RBAC

### Role-Aware Building Queries

```python
from enum import Enum
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
import logging
from app.models.building import Building
from app.models.user import User

logger = logging.getLogger(__name__)

class UserRole(str, Enum):
    """User roles with hierarchical permissions"""
    ADMIN = "admin"
    WORKER = "worker"
    STUDENT = "student"
    GUEST = "guest"

class BuildingService:
    """
    Building retrieval with role-based access control
    
    Access Control:
    - ADMIN: Can see all buildings
    - WORKER: Can see assigned buildings
    - STUDENT: Can see buildings on their campus
    - GUEST: Cannot see buildings
    
    Performance Optimization:
    - Uses joinedload to prevent N+1 queries
    - Indexes on campus, role, and building_id fields
    - Efficient pagination
    """
    
    def __init__(self, db: Session):
        """
        Initialize service with database connection
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def get_buildings_for_user(
        self,
        user: User,
        limit: int = 20,
        offset: int = 0
    ) -> tuple[List[Building], int]:
        """
        Get buildings accessible to user based on role
        
        Args:
            user: User object with role and campus info
            limit: Maximum buildings to return
            offset: Pagination offset
        
        Returns:
            Tuple of (buildings_list, total_count)
        
        Preconditions:
            - user is not None
            - user has role attribute
            - limit > 0 and limit <= 100
            - offset >= 0
        
        Postconditions:
            - Returns only buildings user has access to
            - Does not execute N+1 queries
            - Returns paginated results
        """
        # Validate inputs
        if limit < 1 or limit > 100:
            limit = 20
        if offset < 0:
            offset = 0
        
        try:
            if user.role == UserRole.ADMIN:
                return self._get_all_buildings(limit, offset)
            
            elif user.role == UserRole.WORKER:
                return self._get_assigned_buildings(user, limit, offset)
            
            elif user.role == UserRole.STUDENT:
                return self._get_campus_buildings(user, limit, offset)
            
            else:  # GUEST or unknown role
                logger.warning(
                    "Unauthorized building access attempt",
                    user_id=user.id,
                    role=user.role
                )
                return [], 0
        
        except Exception as e:
            logger.error(
                "Error retrieving buildings for user",
                user_id=user.id,
                error=str(e),
                severity="high"
            )
            raise
    
    def _get_all_buildings(
        self,
        limit: int,
        offset: int
    ) -> tuple[List[Building], int]:
        """
        ADMIN: Get all buildings
        
        Preconditions:
            - Caller has ADMIN role
            - limit and offset are validated
        
        Postconditions:
            - Returns all buildings in database
            - Results are paginated
        """
        try:
            # Get total count
            total = self.db.query(Building).count()
            
            # Get paginated results with eager loading
            buildings = self.db.query(Building).offset(offset).limit(limit).all()
            
            logger.info(
                "Admin retrieved all buildings",
                total_count=total,
                page_size=limit,
                offset=offset
            )
            
            return buildings, total
        
        except Exception as e:
            logger.error(f"Failed to retrieve all buildings: {str(e)}")
            raise
    
    def _get_assigned_buildings(
        self,
        user: User,
        limit: int,
        offset: int
    ) -> tuple[List[Building], int]:
        """
        WORKER: Get buildings assigned to worker
        
        Preconditions:
            - Caller has WORKER role
            - user has building assignments
        
        Postconditions:
            - Returns only buildings assigned to worker
            - Results are paginated
        """
        try:
            # Query buildings assigned to worker
            # Assumes Building has assignment relationship
            # This structure depends on your actual model - adjust accordingly
            
            total = self.db.query(Building).filter(
                Building.assigned_workers.any(id=user.id)
            ).count()
            
            buildings = self.db.query(Building).filter(
                Building.assigned_workers.any(id=user.id)
            ).offset(offset).limit(limit).all()
            
            logger.info(
                "Worker retrieved assigned buildings",
                worker_id=user.id,
                total_count=total,
                page_size=limit
            )
            
            return buildings, total
        
        except Exception as e:
            logger.error(
                f"Failed to retrieve assigned buildings: {str(e)}",
                worker_id=user.id
            )
            raise
    
    def _get_campus_buildings(
        self,
        user: User,
        limit: int,
        offset: int
    ) -> tuple[List[Building], int]:
        """
        STUDENT: Get buildings on user's campus
        
        Preconditions:
            - Caller has STUDENT role
            - user has campus attribute
        
        Postconditions:
            - Returns only buildings on student's campus
            - Results are paginated
            - Uses index on campus column for efficiency
        """
        try:
            # Get student's campus
            if not hasattr(user, 'campus') or not user.campus:
                logger.warning(
                    "Student has no campus assigned",
                    user_id=user.id
                )
                return [], 0
            
            # Query buildings on same campus
            total = self.db.query(Building).filter(
                Building.campus == user.campus
            ).count()
            
            buildings = self.db.query(Building).filter(
                Building.campus == user.campus
            ).offset(offset).limit(limit).all()
            
            logger.info(
                "Student retrieved campus buildings",
                student_id=user.id,
                campus=user.campus,
                total_count=total
            )
            
            return buildings, total
        
        except Exception as e:
            logger.error(
                f"Failed to retrieve campus buildings: {str(e)}",
                student_id=user.id,
                campus=getattr(user, 'campus', None)
            )
            raise
    
    def get_building_by_id(
        self,
        user: User,
        building_id: str
    ) -> Optional[Building]:
        """
        Get single building with access control
        
        Args:
            user: User requesting building
            building_id: ID of building to retrieve
        
        Returns:
            Building object if user has access, None otherwise
        
        Preconditions:
            - user is authenticated
            - building_id is valid UUID
        
        Postconditions:
            - Returns building only if user has access
            - Does not leak building existence to unauthorized users
        """
        try:
            building = self.db.query(Building).filter(
                Building.id == building_id
            ).first()
            
            if not building:
                logger.debug(f"Building not found: {building_id}")
                return None
            
            # Check access
            if user.role == UserRole.ADMIN:
                return building
            
            elif user.role == UserRole.WORKER:
                # Check if building is assigned to worker
                if any(w.id == user.id for w in building.assigned_workers):
                    return building
                logger.warning(
                    "Worker access denied to building",
                    worker_id=user.id,
                    building_id=building_id
                )
                return None
            
            elif user.role == UserRole.STUDENT:
                # Check if building is on student's campus
                if building.campus == user.campus:
                    return building
                logger.warning(
                    "Student access denied to building",
                    student_id=user.id,
                    building_id=building_id,
                    requested_campus=building.campus
                )
                return None
            
            else:
                return None
        
        except Exception as e:
            logger.error(
                f"Error retrieving building by ID: {str(e)}",
                building_id=building_id,
                user_id=user.id
            )
            raise
    
    def verify_building_access(
        self,
        user: User,
        building_id: str
    ) -> bool:
        """
        Verify user has access to building
        
        Used for permission checks in other endpoints
        
        Args:
            user: User to check
            building_id: Building to verify access to
        
        Returns:
            True if user has access, False otherwise
        
        Postcondition:
            - Does not return building data (only boolean)
            - Used for authorization checks
        """
        building = self.get_building_by_id(user, building_id)
        return building is not None
```



## Complaint Service with Eager Loading

### Selectinload and Joinedload Strategies

```python
from typing import List, Optional, Tuple
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy import and_, desc
import logging
from app.models.complaint import Complaint
from app.models.user import User
from app.models.notification import Notification
from app.models.ticket_log import TicketLog

logger = logging.getLogger(__name__)

class ComplaintService:
    """
    Complaint retrieval with optimized eager loading to prevent N+1 queries
    
    N+1 Problem:
    Without eager loading, retrieving 20 complaints would require:
    - 1 query to fetch complaints
    - 20 queries to fetch created_by users
    - 20 queries to fetch assigned_worker users
    - 20 queries to fetch notifications
    - 20 queries to fetch ticket logs
    Total: 81 queries!
    
    Solution:
    - selectinload: Issues separate SELECT statements (better for relationships)
    - joinedload: Uses JOIN (better for single relationships)
    - Both strategies prevent N+1 queries
    """
    
    def __init__(self, db: Session):
        """
        Initialize service with database connection
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def get_complaints_with_eager_loading(
        self,
        user: User,
        limit: int = 20,
        offset: int = 0,
        status: Optional[str] = None
    ) -> Tuple[List[Complaint], int]:
        """
        Get complaints with all related data loaded
        
        Uses selectinload to prevent N+1 queries
        
        Args:
            user: User requesting complaints
            limit: Maximum complaints to return
            offset: Pagination offset
            status: Filter by complaint status (optional)
        
        Returns:
            Tuple of (complaints_list, total_count)
        
        Preconditions:
            - user is authenticated
            - user has permission to view complaints
            - limit > 0 and limit <= 100
            - offset >= 0
            - status is valid complaint status if provided
        
        Postconditions:
            - All complaints have related data loaded (no N+1 queries)
            - Results are paginated
            - Only returns complaints user has access to
            - Executes exactly 1 query for complaints + 5 separate queries for relationships
            - Without eager loading: would execute ~1 + (limit × 5) queries
        """
        # Validate inputs
        if limit < 1 or limit > 100:
            limit = 20
        if offset < 0:
            offset = 0
        
        try:
            # Build base query with eager loading
            # Using selectinload for one-to-many relationships
            query = self.db.query(Complaint).options(
                selectinload(Complaint.created_by),      # Load user who created complaint
                selectinload(Complaint.assigned_worker), # Load assigned worker
                selectinload(Complaint.notifications),   # Load all notifications
                selectinload(Complaint.ticket_logs)      # Load all ticket logs
            )
            
            # Apply filtering based on status if provided
            if status:
                query = query.filter(Complaint.status == status)
            
            # Apply role-based filtering
            if user.role == "admin":
                # Admin sees all complaints
                pass
            elif user.role == "worker":
                # Worker sees assigned complaints + complaints created by them
                query = query.filter(
                    or_(
                        Complaint.assigned_to == user.id,
                        Complaint.user_id == user.id
                    )
                )
            elif user.role == "student":
                # Student only sees their own complaints
                query = query.filter(Complaint.user_id == user.id)
            else:
                # Unknown role - no access
                return [], 0
            
            # Get total count before pagination
            total = query.count()
            
            # Apply pagination and sorting
            complaints = query.order_by(
                desc(Complaint.created_at)
            ).offset(offset).limit(limit).all()
            
            logger.info(
                "Complaints retrieved with eager loading",
                user_id=user.id,
                user_role=user.role,
                total_count=total,
                page_size=limit,
                offset=offset,
                status_filter=status
            )
            
            return complaints, total
        
        except Exception as e:
            logger.error(
                "Failed to retrieve complaints with eager loading",
                user_id=user.id,
                error=str(e),
                severity="high"
            )
            raise
    
    def get_single_complaint_with_eager_loading(
        self,
        user: User,
        complaint_id: str
    ) -> Optional[Complaint]:
        """
        Get single complaint with all related data
        
        Args:
            user: User requesting complaint
            complaint_id: ID of complaint to retrieve
        
        Returns:
            Complaint object with all relationships loaded, or None if not found
        
        Preconditions:
            - user is authenticated
            - complaint_id is valid UUID
        
        Postconditions:
            - Complaint has all relationships eagerly loaded
            - Executes 6 queries total (1 main + 5 for relationships)
        """
        try:
            complaint = self.db.query(Complaint).options(
                selectinload(Complaint.created_by),
                selectinload(Complaint.assigned_worker),
                selectinload(Complaint.building),
                selectinload(Complaint.notifications),
                selectinload(Complaint.ticket_logs)
            ).filter(Complaint.id == complaint_id).first()
            
            if not complaint:
                logger.debug(f"Complaint not found: {complaint_id}")
                return None
            
            # Check access
            if user.role == "admin":
                return complaint
            elif user.role == "worker":
                if complaint.assigned_to == user.id or complaint.user_id == user.id:
                    return complaint
            elif user.role == "student":
                if complaint.user_id == user.id:
                    return complaint
            
            logger.warning(
                "Unauthorized complaint access",
                user_id=user.id,
                complaint_id=complaint_id
            )
            return None
        
        except Exception as e:
            logger.error(
                f"Failed to retrieve single complaint: {str(e)}",
                complaint_id=complaint_id
            )
            raise
    
    def get_complaints_by_status(
        self,
        user: User,
        status: str,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[Complaint], int]:
        """
        Get complaints filtered by status with eager loading
        
        Uses index on status column for efficient filtering
        
        Args:
            user: User requesting complaints
            status: Complaint status to filter by
            limit: Maximum results
            offset: Pagination offset
        
        Returns:
            Tuple of (complaints_list, total_count)
        
        Postconditions:
            - Uses index on complaints.status for fast filtering
            - All relationships eagerly loaded
        """
        return self.get_complaints_with_eager_loading(
            user=user,
            limit=limit,
            offset=offset,
            status=status
        )
    
    def get_assigned_complaints(
        self,
        worker_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[Complaint], int]:
        """
        Get complaints assigned to specific worker
        
        Uses index on assigned_to column for efficient lookup
        
        Args:
            worker_id: Worker's user ID
            limit: Maximum results
            offset: Pagination offset
        
        Returns:
            Tuple of (complaints_list, total_count)
        
        Postconditions:
            - Uses index on complaints.assigned_to
            - All relationships eagerly loaded
        """
        try:
            query = self.db.query(Complaint).options(
                selectinload(Complaint.created_by),
                selectinload(Complaint.assigned_worker),
                selectinload(Complaint.building),
                selectinload(Complaint.notifications),
                selectinload(Complaint.ticket_logs)
            ).filter(
                Complaint.assigned_to == worker_id
            ).order_by(desc(Complaint.created_at))
            
            total = query.count()
            complaints = query.offset(offset).limit(limit).all()
            
            logger.info(
                "Worker complaints retrieved",
                worker_id=worker_id,
                total_count=total
            )
            
            return complaints, total
        
        except Exception as e:
            logger.error(
                f"Failed to retrieve assigned complaints: {str(e)}",
                worker_id=worker_id
            )
            raise
    
    def get_recent_complaints(
        self,
        user: User,
        days: int = 7,
        limit: int = 10
    ) -> List[Complaint]:
        """
        Get complaints created in last N days
        
        Used for dashboard displays
        
        Args:
            user: User requesting complaints
            days: Number of days to look back
            limit: Maximum results
        
        Returns:
            List of recent complaints
        
        Postcondition:
            - Returns complaints created in last N days
            - All relationships eagerly loaded
            - Ordered by most recent first
        """
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            query = self.db.query(Complaint).options(
                selectinload(Complaint.created_by),
                selectinload(Complaint.assigned_worker),
                selectinload(Complaint.building)
            ).filter(
                and_(
                    Complaint.created_at >= cutoff_date,
                    Complaint.user_id == user.id
                )
            ).order_by(desc(Complaint.created_at)).limit(limit)
            
            complaints = query.all()
            
            logger.debug(
                "Recent complaints retrieved",
                user_id=user.id,
                days=days,
                count=len(complaints)
            )
            
            return complaints
        
        except Exception as e:
            logger.error(f"Failed to retrieve recent complaints: {str(e)}")
            raise
    
    def get_complaints_statistics(self) -> dict:
        """
        Get aggregated complaint statistics
        
        Returns:
            Dictionary with status counts and metrics
        
        Postcondition:
            - Returns aggregate statistics without loading all complaints
            - Uses database aggregation functions
        """
        try:
            from sqlalchemy import func
            
            # Get counts by status
            status_counts = self.db.query(
                Complaint.status,
                func.count(Complaint.id).label('count')
            ).group_by(Complaint.status).all()
            
            # Get average resolution time
            avg_resolution = self.db.query(
                func.avg(
                    func.extract('epoch', Complaint.resolved_at - Complaint.created_at)
                ).label('avg_seconds')
            ).filter(
                Complaint.resolved_at.isnot(None)
            ).scalar()
            
            return {
                "status_breakdown": {status: count for status, count in status_counts},
                "total_complaints": self.db.query(Complaint).count(),
                "avg_resolution_time_hours": (avg_resolution / 3600) if avg_resolution else None,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        except Exception as e:
            logger.error(f"Failed to get complaint statistics: {str(e)}")
            return {"error": "statistics_unavailable"}
```



## Middleware Implementation

### Token Blacklist Checking Middleware

```python
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import logging
from datetime import datetime, timezone
import time
import jwt

logger = logging.getLogger(__name__)

class TokenBlacklistMiddleware:
    """
    Middleware to check if JWT tokens are blacklisted
    
    Execution Order:
    1. Extract token from Authorization header
    2. Check Redis cache (fast path)
    3. Fall back to database query if not cached
    4. Log all checks for security audit trail
    5. Proceed or reject based on blacklist status
    
    Performance:
    - Redis cache hit: ~1-2ms
    - Database query: ~5-10ms
    - Cache miss/hit ratio target: 95%+
    """
    
    def __init__(self, app, token_blacklist_service, jwt_secret: str):
        """
        Initialize middleware
        
        Args:
            app: FastAPI application
            token_blacklist_service: TokenBlacklistService instance
            jwt_secret: Secret key for JWT decoding
        """
        self.app = app
        self.token_blacklist_service = token_blacklist_service
        self.jwt_secret = jwt_secret
    
    async def __call__(self, request: Request, call_next):
        """
        Process request through middleware
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/route handler
        
        Returns:
            Response object or error response
        """
        # Start timing for performance monitoring
        start_time = time.time()
        
        # Check if route requires authentication
        if not self._route_requires_auth(request):
            return await call_next(request)
        
        try:
            # Extract token from Authorization header
            auth_header = request.headers.get("Authorization")
            
            if not auth_header:
                logger.warning(
                    "Missing Authorization header",
                    method=request.method,
                    path=request.url.path,
                    client_ip=request.client.host if request.client else "unknown"
                )
                return self._create_error_response(
                    status_code=401,
                    message="Authorization credentials are missing or invalid"
                )
            
            # Extract token from "Bearer <token>" format
            try:
                scheme, token = auth_header.split()
                if scheme.lower() != "bearer":
                    logger.warning(
                        "Invalid Authorization scheme",
                        scheme=scheme,
                        path=request.url.path
                    )
                    return self._create_error_response(
                        status_code=401,
                        message="Invalid Authorization scheme"
                    )
            except ValueError:
                logger.warning(
                    "Malformed Authorization header",
                    path=request.url.path
                )
                return self._create_error_response(
                    status_code=401,
                    message="Malformed Authorization header"
                )
            
            # Check token expiration
            try:
                payload = jwt.decode(
                    token,
                    self.jwt_secret,
                    algorithms=["HS256"]
                )
                
                # Check if token has expired
                if payload.get('exp'):
                    if payload['exp'] < datetime.now(timezone.utc).timestamp():
                        logger.debug(
                            "Token has expired",
                            user_id=payload.get('sub'),
                            exp=payload['exp']
                        )
                        return self._create_error_response(
                            status_code=401,
                            message="Token has expired"
                        )
            
            except jwt.InvalidTokenError as e:
                logger.warning(
                    "Invalid JWT token",
                    error=str(e),
                    path=request.url.path
                )
                return self._create_error_response(
                    status_code=401,
                    message="Invalid authentication token"
                )
            
            # Check if token is blacklisted
            is_blacklisted = self.token_blacklist_service.is_blacklisted(token)
            
            if is_blacklisted:
                logger.warning(
                    "Blacklisted token used",
                    user_id=payload.get('sub'),
                    path=request.url.path,
                    client_ip=request.client.host if request.client else "unknown"
                )
                return self._create_error_response(
                    status_code=401,
                    message="Token has been revoked"
                )
            
            # Add user info to request state for later use
            request.state.user_id = payload.get('sub')
            request.state.user_role = payload.get('role')
            request.state.token = token
            
            # Proceed to next middleware/route
            response = await call_next(request)
            
            # Log successful check
            elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
            logger.debug(
                "Token validation passed",
                user_id=payload.get('sub'),
                elapsed_ms=elapsed_time,
                path=request.url.path
            )
            
            return response
        
        except Exception as e:
            logger.error(
                "Unexpected error in token validation middleware",
                error=str(e),
                severity="high",
                path=request.url.path
            )
            # Fail securely
            return self._create_error_response(
                status_code=500,
                message="Internal server error"
            )
    
    @staticmethod
    def _route_requires_auth(request: Request) -> bool:
        """
        Determine if route requires authentication
        
        Args:
            request: FastAPI request object
        
        Returns:
            True if route requires auth, False otherwise
        
        Postcondition:
            - Public routes (login, register, health) bypass middleware
            - All other routes require authentication
        """
        path = request.url.path.lower()
        
        # Public routes that don't require authentication
        public_routes = [
            "/auth/login",
            "/auth/register",
            "/auth/verify",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/auth/resend-verification-email"
        ]
        
        # Check if path matches public routes
        for public_route in public_routes:
            if path.startswith(public_route):
                return False
        
        return True
    
    @staticmethod
    def _create_error_response(status_code: int, message: str) -> JSONResponse:
        """
        Create standardized error response
        
        Args:
            status_code: HTTP status code
            message: Error message to return
        
        Returns:
            JSONResponse with error details
        
        Postcondition:
            - Returns response in consistent format
            - Includes request_id for tracing
        """
        import uuid
        
        return JSONResponse(
            status_code=status_code,
            content={
                "success": False,
                "data": {},
                "message": message,
                "request_id": str(uuid.uuid4())[:8]
            }
        )


class RateLimitMiddleware:
    """
    Middleware to enforce rate limits on login endpoint
    """
    
    def __init__(self, app, rate_limiter):
        """
        Initialize rate limit middleware
        
        Args:
            app: FastAPI application
            rate_limiter: RateLimiter service instance
        """
        self.app = app
        self.rate_limiter = rate_limiter
    
    async def __call__(self, request: Request, call_next):
        """
        Process request through rate limit middleware
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/route handler
        
        Returns:
            Response object or rate limit error response
        """
        # Only apply rate limiting to login endpoint
        if not request.url.path.lower() == "/auth/login":
            return await call_next(request)
        
        # Only apply to POST requests
        if request.method != "POST":
            return await call_next(request)
        
        # Extract client IP
        client_ip = self.rate_limiter.extract_client_ip(request)
        
        # Check rate limit
        allowed, details = self.rate_limiter.check_rate_limit(client_ip)
        
        if not allowed:
            logger.warning(
                "Rate limit exceeded for login",
                client_ip=client_ip,
                details=details
            )
            
            return JSONResponse(
                status_code=429,
                headers={"Retry-After": str(details.get("locked_until_seconds", 60))},
                content={
                    "success": False,
                    "data": {},
                    "message": "Too many login attempts. Please try again later.",
                    "request_id": request.headers.get("X-Request-ID", "unknown")
                }
            )
        
        # Proceed to route
        response = await call_next(request)
        
        # If login was successful, reset rate limit
        if response.status_code == 200:
            self.rate_limiter.reset_ip_attempts(client_ip)
            logger.debug(
                "Rate limit reset for successful login",
                client_ip=client_ip
            )
        
        return response


class SecurityHeadersMiddleware:
    """
    Middleware to add security headers to all responses
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, request: Request, call_next):
        """
        Add security headers to response
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/route handler
        
        Returns:
            Response with security headers added
        """
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response
```



## CORS & Exception Handling Strategy

### CORS Configuration

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

logger = logging.getLogger(__name__)

def configure_cors(app: FastAPI) -> None:
    """
    Configure CORS middleware for API
    
    Security Considerations:
    - Use whitelist approach (only allow specific origins)
    - Never use "*" in production
    - Restrict credential handling
    - Limit HTTP methods
    - Validate preflight requests
    
    Args:
        app: FastAPI application instance
    
    Postcondition:
        - CORS middleware configured with secure defaults
        - Only whitelisted origins can access API
    """
    # Get allowed origins from environment
    allowed_origins = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    
    # Remove whitespace
    allowed_origins = [origin.strip() for origin in allowed_origins]
    
    # Allowed HTTP methods
    allowed_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
    
    # Allowed headers
    allowed_headers = [
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Accept",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
        "X-Request-ID"
    ]
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,      # Whitelist specific origins
        allow_credentials=True,              # Allow cookies and credentials
        allow_methods=allowed_methods,       # Whitelist HTTP methods
        allow_headers=allowed_headers,       # Whitelist headers
        expose_headers=[                     # Headers accessible to client
            "Content-Type",
            "X-Request-ID",
            "Retry-After"
        ],
        max_age=3600                         # Cache preflight for 1 hour
    )
    
    logger.info(
        "CORS configured",
        allowed_origins=allowed_origins,
        allowed_methods=allowed_methods
    )


def validate_origin(origin: str) -> bool:
    """
    Validate that origin is in whitelist
    
    Args:
        origin: Origin header value from request
    
    Returns:
        True if origin is allowed, False otherwise
    
    Postcondition:
        - Only whitelisted origins return True
        - Case-insensitive comparison
    """
    allowed_origins = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    allowed_origins = [o.strip().lower() for o in allowed_origins]
    
    return origin.lower() in allowed_origins
```

### Global Exception Handling

```python
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import traceback
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any

logger = logging.getLogger(__name__)

class APIException(Exception):
    """Base exception for API errors"""
    
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_code: str = "api_error",
        details: Dict[str, Any] = None
    ):
        """
        Initialize API exception
        
        Args:
            message: User-friendly error message
            status_code: HTTP status code
            error_code: Machine-readable error code
            details: Additional error details
        """
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(APIException):
    """Raised for validation errors"""
    def __init__(self, message: str, field: str = None, details: Dict = None):
        super().__init__(
            message=message,
            status_code=400,
            error_code="validation_error",
            details={"field": field, **(details or {})}
        )


class AuthenticationException(APIException):
    """Raised for authentication errors"""
    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=401,
            error_code="authentication_error"
        )


class AuthorizationException(APIException):
    """Raised for authorization errors"""
    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=403,
            error_code="authorization_error"
        )


class ResourceNotFoundException(APIException):
    """Raised when resource is not found"""
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            message=f"{resource_type} not found",
            status_code=404,
            error_code="not_found",
            details={"resource_type": resource_type, "resource_id": resource_id}
        )


class ConflictException(APIException):
    """Raised when resource conflict occurs"""
    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=409,
            error_code="conflict"
        )


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register global exception handlers
    
    Args:
        app: FastAPI application instance
    
    Postcondition:
        - All exceptions caught and formatted consistently
        - Error responses include request_id for tracing
        - Sensitive information not exposed to client
    """
    
    @app.exception_handler(APIException)
    async def api_exception_handler(request: Request, exc: APIException):
        """Handle custom API exceptions"""
        request_id = str(uuid.uuid4())[:8]
        
        logger.warning(
            "API exception raised",
            error_code=exc.error_code,
            status_code=exc.status_code,
            message=exc.message,
            request_id=request_id,
            path=request.url.path
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "data": exc.details,
                "message": exc.message,
                "error_code": exc.error_code,
                "request_id": request_id
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle Pydantic validation errors"""
        request_id = str(uuid.uuid4())[:8]
        
        # Extract first validation error
        errors = exc.errors()
        first_error = errors[0] if errors else {}
        field = ".".join(str(x) for x in first_error.get("loc", [1:])[:-1])
        error_msg = first_error.get("msg", "Validation failed")
        
        logger.warning(
            "Validation error",
            field=field,
            error=error_msg,
            request_id=request_id,
            path=request.url.path
        )
        
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "data": {
                    "field": field,
                    "error": "validation_error",
                    "errors": [
                        {
                            "field": ".".join(str(x) for x in e.get("loc", [])),
                            "message": e.get("msg"),
                            "type": e.get("type")
                        }
                        for e in errors[:5]  # Limit to 5 errors
                    ]
                },
                "message": error_msg,
                "request_id": request_id
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions"""
        request_id = str(uuid.uuid4())[:8]
        
        logger.error(
            "Unhandled exception",
            exception_type=type(exc).__name__,
            message=str(exc),
            request_id=request_id,
            path=request.url.path,
            traceback=traceback.format_exc(),
            severity="high"
        )
        
        # Return generic error message (don't expose stack trace)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "data": {},
                "message": "An unexpected error occurred. Please contact support.",
                "request_id": request_id
            }
        )


def setup_exception_handlers(app: FastAPI) -> None:
    """
    Setup all exception handling for application
    
    Args:
        app: FastAPI application instance
    
    Postcondition:
        - CORS configured securely
        - Global exception handlers registered
        - All errors formatted consistently
    """
    configure_cors(app)
    register_exception_handlers(app)
    
    logger.info("Exception handlers configured")
```



## Alembic Migration Strategy

### Creating New Tables and Indexes

```python
"""Add security and performance tables and indexes

Revision ID: security_hardening_001
Revises: previous_revision
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'security_hardening_001'
down_revision = 'previous_revision'  # Replace with actual previous revision
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Upgrade database schema
    
    Actions:
    1. Create token_blacklist table
    2. Create email_verification_tokens table
    3. Add email_verified column to users table
    4. Create performance indexes on complaints
    5. Create performance indexes on supporting tables
    """
    
    # Create token_blacklist table
    op.create_table(
        'token_blacklist',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('token_hash', sa.String(64), nullable=False, unique=True),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                  server_default=sa.func.now()),
        sa.Column('revocation_reason', sa.String(255), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash'),
        schema=None
    )
    
    # Create indexes on token_blacklist
    op.create_index(
        'idx_token_hash',
        'token_blacklist',
        ['token_hash'],
        unique=True
    )
    op.create_index(
        'idx_token_user_id',
        'token_blacklist',
        ['user_id']
    )
    op.create_index(
        'idx_token_expires_at',
        'token_blacklist',
        ['expires_at']
    )
    
    # Create email_verification_tokens table
    op.create_table(
        'email_verification_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False, unique=True),
        sa.Column('token_hash', sa.String(64), nullable=False, unique=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                  server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash'),
        schema=None
    )
    
    # Create indexes on email_verification_tokens
    op.create_index(
        'idx_email_token_hash',
        'email_verification_tokens',
        ['token_hash'],
        unique=True
    )
    op.create_index(
        'idx_email_expires_at',
        'email_verification_tokens',
        ['expires_at']
    )
    
    # Add email_verified column to users table
    op.add_column(
        'users',
        sa.Column('email_verified', sa.Boolean(), nullable=False, 
                  server_default=sa.true())
    )
    
    # Create performance indexes on complaints table
    op.create_index(
        'idx_complaints_status',
        'complaints',
        ['status']
    )
    op.create_index(
        'idx_complaints_assigned_to',
        'complaints',
        ['assigned_to']
    )
    op.create_index(
        'idx_complaints_created_at',
        'complaints',
        ['created_at'],
        postgresql_using='btree',
        postgresql_ops={'created_at': 'DESC'}
    )
    op.create_index(
        'idx_complaints_status_created',
        'complaints',
        ['status', 'created_at'],
        postgresql_using='btree',
        postgresql_ops={'created_at': 'DESC'}
    )
    
    # Create performance indexes on ticket_logs
    op.create_index(
        'idx_ticket_logs_complaint_id',
        'ticket_logs',
        ['complaint_id']
    )
    
    # Create performance indexes on notifications
    op.create_index(
        'idx_notifications_user_id',
        'notifications',
        ['user_id']
    )
    op.create_index(
        'idx_notifications_is_read',
        'notifications',
        ['is_read'],
        postgresql_where="is_read = false"  # Partial index for unread only
    )


def downgrade() -> None:
    """
    Downgrade database schema (rollback)
    
    Actions:
    1. Drop all created indexes
    2. Drop email_verified column from users
    3. Drop email_verification_tokens table
    4. Drop token_blacklist table
    """
    
    # Drop notification indexes
    op.drop_index('idx_notifications_is_read', table_name='notifications')
    op.drop_index('idx_notifications_user_id', table_name='notifications')
    
    # Drop ticket_logs indexes
    op.drop_index('idx_ticket_logs_complaint_id', table_name='ticket_logs')
    
    # Drop complaints indexes
    op.drop_index('idx_complaints_status_created', table_name='complaints')
    op.drop_index('idx_complaints_created_at', table_name='complaints')
    op.drop_index('idx_complaints_assigned_to', table_name='complaints')
    op.drop_index('idx_complaints_status', table_name='complaints')
    
    # Drop email_verified column
    op.drop_column('users', 'email_verified')
    
    # Drop email_verification_tokens table
    op.drop_index('idx_email_expires_at', table_name='email_verification_tokens')
    op.drop_index('idx_email_token_hash', table_name='email_verification_tokens')
    op.drop_table('email_verification_tokens')
    
    # Drop token_blacklist table
    op.drop_index('idx_token_expires_at', table_name='token_blacklist')
    op.drop_index('idx_token_user_id', table_name='token_blacklist')
    op.drop_index('idx_token_hash', table_name='token_blacklist')
    op.drop_table('token_blacklist')
```

### Migration Execution Commands

```bash
# Generate new migration (Alembic auto-generates based on model changes)
alembic revision --autogenerate -m "security_hardening_001"

# Review migration before applying
cat alembic/versions/security_hardening_001_*.py

# Apply migration to development database
alembic upgrade head

# Apply migration to specific revision
alembic upgrade security_hardening_001

# Rollback last migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade security_hardening_000

# Check current database revision
alembic current

# View migration history
alembic history --verbose

# Verify migration is valid
alembic check
```

### Pre-Migration Checks

```python
"""
Pre-migration verification script
Run before applying migrations to production
"""

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
import logging

logger = logging.getLogger(__name__)

def verify_pre_migration(database_url: str) -> bool:
    """
    Verify database is ready for migration
    
    Args:
        database_url: Database connection URL
    
    Returns:
        True if database is healthy, False otherwise
    
    Preconditions:
        - Database connection is valid
        - User has necessary permissions
    
    Checks:
        1. Database connectivity
        2. Schema integrity
        3. Backup status
        4. Active connections
    """
    engine = create_engine(database_url)
    
    try:
        # Test connectivity
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            logger.info(f"Database version: {version}")
        
        # Check for required tables
        inspector = inspect(engine)
        existing_tables = set(inspector.get_table_names())
        
        required_tables = {'users', 'complaints', 'buildings', 'notifications'}
        missing_tables = required_tables - existing_tables
        
        if missing_tables:
            logger.error(f"Missing required tables: {missing_tables}")
            return False
        
        logger.info("Pre-migration checks passed")
        return True
    
    except Exception as e:
        logger.error(f"Pre-migration check failed: {str(e)}", severity="high")
        return False


def verify_post_migration(database_url: str) -> bool:
    """
    Verify migration was successful
    
    Args:
        database_url: Database connection URL
    
    Returns:
        True if migration successful, False otherwise
    
    Checks:
        1. New tables created
        2. Indexes created
        3. Constraints applied
        4. Data integrity maintained
    """
    engine = create_engine(database_url)
    
    try:
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        
        # Verify new tables exist
        if 'token_blacklist' not in tables:
            logger.error("token_blacklist table not created")
            return False
        
        if 'email_verification_tokens' not in tables:
            logger.error("email_verification_tokens table not created")
            return False
        
        # Verify new indexes exist
        complaint_indexes = {idx['name'] for idx in inspector.get_indexes('complaints')}
        required_indexes = {
            'idx_complaints_status',
            'idx_complaints_assigned_to',
            'idx_complaints_created_at'
        }
        
        missing_indexes = required_indexes - complaint_indexes
        if missing_indexes:
            logger.error(f"Missing indexes: {missing_indexes}")
            return False
        
        # Verify email_verified column exists and has default
        users_columns = {col['name'] for col in inspector.get_columns('users')}
        if 'email_verified' not in users_columns:
            logger.error("email_verified column not added to users table")
            return False
        
        logger.info("Post-migration verification passed")
        return True
    
    except Exception as e:
        logger.error(f"Post-migration check failed: {str(e)}", severity="high")
        return False
```



## Testing Strategy

### Unit Tests

```python
"""
Unit tests for security and performance components
Using pytest framework with unittest.mock for mocking
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta, timezone
import hashlib

# Test PasswordValidator
from app.core.security import PasswordValidator


class TestPasswordValidator:
    """Unit tests for password validation"""
    
    def test_validate_strong_password_succeeds(self):
        """
        Test that strong password passes validation
        
        Precondition:
            - Password meets all requirements
        
        Postcondition:
            - Returns (True, "")
        """
        password = "MySecurePass123!@#"
        is_valid, message = PasswordValidator.validate(password)
        
        assert is_valid is True
        assert message == ""
    
    def test_validate_short_password_fails(self):
        """
        Test that password shorter than 12 characters fails
        
        Precondition:
            - Password is 11 characters
        
        Postcondition:
            - Returns (False, message)
        """
        password = "Short1!@"
        is_valid, message = PasswordValidator.validate(password)
        
        assert is_valid is False
        assert message == "Password does not meet requirements"
    
    def test_validate_no_uppercase_fails(self):
        """Test password without uppercase letter fails"""
        password = "mysecurepass123!@#"
        is_valid, _ = PasswordValidator.validate(password)
        assert is_valid is False
    
    def test_validate_no_lowercase_fails(self):
        """Test password without lowercase letter fails"""
        password = "MYSECUREPASS123!@#"
        is_valid, _ = PasswordValidator.validate(password)
        assert is_valid is False
    
    def test_validate_no_digit_fails(self):
        """Test password without digit fails"""
        password = "MySecurePass!@#"
        is_valid, _ = PasswordValidator.validate(password)
        assert is_valid is False
    
    def test_validate_no_special_char_fails(self):
        """Test password without special character fails"""
        password = "MySecurePass123"
        is_valid, _ = PasswordValidator.validate(password)
        assert is_valid is False
    
    def test_password_hashing_creates_different_hash(self):
        """
        Test that same password creates different hashes (bcrypt salt)
        
        Postcondition:
            - Two hashes of same password are different
            - Both hashes verify against original password
        """
        password = "MySecurePass123!@#"
        
        hash1 = PasswordValidator.hash_password(password)
        hash2 = PasswordValidator.hash_password(password)
        
        assert hash1 != hash2  # Different due to salt
        assert PasswordValidator.verify_password(password, hash1)
        assert PasswordValidator.verify_password(password, hash2)
    
    def test_password_verification_rejects_wrong_password(self):
        """
        Test that verification fails with wrong password
        
        Postcondition:
            - verify_password returns False for wrong password
        """
        password = "MySecurePass123!@#"
        wrong_password = "WrongPass123!@#"
        
        hashed = PasswordValidator.hash_password(password)
        
        assert not PasswordValidator.verify_password(wrong_password, hashed)


# Test FileValidator
from app.services.file_validator import (
    FileValidator,
    PathTraversalException,
    InvalidExtensionException,
    InvalidMimeTypeException
)


class TestFileValidator:
    """Unit tests for file validation"""
    
    def test_validate_filename_allows_safe_name(self):
        """
        Test that safe filename passes validation
        
        Precondition:
            - Filename contains no path traversal attempts
        
        Postcondition:
            - Returns (True, "")
        """
        is_valid, message = FileValidator.validate_filename("complaint_photo.jpg")
        assert is_valid is True
        assert message == ""
    
    def test_validate_filename_rejects_path_traversal(self):
        """
        Test that path traversal attempt is rejected
        
        Precondition:
            - Filename contains ".."
        
        Postcondition:
            - Raises PathTraversalException
        """
        with pytest.raises(PathTraversalException):
            FileValidator.validate_filename("../../../etc/passwd.jpg")
    
    def test_validate_filename_rejects_null_byte(self):
        """Test that null bytes in filename are rejected"""
        with pytest.raises(PathTraversalException):
            FileValidator.validate_filename("file\x00.jpg")
    
    def test_validate_extension_allows_whitelisted(self):
        """Test that whitelisted extensions pass validation"""
        for ext in ['.jpg', '.jpeg', '.png', '.webp', '.pdf']:
            is_valid, _ = FileValidator.validate_extension(f"file{ext}")
            assert is_valid is True
    
    def test_validate_extension_rejects_executable(self):
        """Test that executable extensions are rejected"""
        with pytest.raises(InvalidExtensionException):
            FileValidator.validate_extension("malware.exe")
    
    def test_validate_mime_type_checks_magic_numbers(self):
        """
        Test that MIME type validation checks file magic numbers
        
        Precondition:
            - File content has JPEG magic number but .png extension
        
        Postcondition:
            - Raises InvalidMimeTypeException (content doesn't match extension)
        """
        # JPEG magic number
        jpeg_content = b'\xff\xd8\xff\xe0' + b'\x00' * 100
        
        # Claim to be PNG but actually JPEG
        with pytest.raises(InvalidMimeTypeException):
            FileValidator.validate_mime_type(jpeg_content, "fake.png")
    
    def test_validate_file_size_rejects_oversized(self):
        """Test that files exceeding size limit are rejected"""
        # Create content larger than 10MB
        large_content = b'X' * (11 * 1024 * 1024)
        
        with pytest.raises(Exception):  # FileValidationException
            FileValidator.validate_file_size(large_content, "file.jpg")
    
    def test_validate_and_hash_returns_safe_filename(self):
        """
        Test that validate_and_hash returns UUID-based safe filename
        
        Postcondition:
            - Returns (safe_filename, file_hash)
            - safe_filename is UUID format
            - file_hash is SHA-256 (64 hex chars)
        """
        # Valid JPEG content
        jpeg_content = (
            b'\xff\xd8\xff\xe0\x00\x10JFIF' + b'X' * 100 + b'\xff\xd9'
        )
        
        safe_filename, file_hash = FileValidator.validate_and_hash(
            jpeg_content,
            "complaint.jpg"
        )
        
        # Verify safe_filename is UUID-based
        assert safe_filename.endswith('.jpg')
        assert len(safe_filename.replace('.jpg', '')) == 36  # UUID length
        
        # Verify hash is SHA-256
        assert len(file_hash) == 64
        assert file_hash == hashlib.sha256(jpeg_content).hexdigest()


# Test TokenBlacklistService
from app.services.token_blacklist import TokenBlacklistService


class TestTokenBlacklistService:
    """Unit tests for token blacklist service"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock()
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        return Mock()
    
    @pytest.fixture
    def service(self, mock_db, mock_redis):
        """Service instance with mocks"""
        return TokenBlacklistService(mock_db, mock_redis)
    
    def test_hash_token_returns_sha256(self, service):
        """
        Test that token hashing uses SHA-256
        
        Postcondition:
            - Returns 64-character hex string
        """
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyLTEyMyJ9.signature"
        
        token_hash = service.hash_token(token)
        
        # SHA-256 produces 64 hex characters
        assert len(token_hash) == 64
        assert all(c in '0123456789abcdef' for c in token_hash)
    
    def test_is_blacklisted_checks_redis_first(self, service, mock_redis):
        """
        Test that blacklist check tries Redis first
        
        Precondition:
            - Token is in Redis cache
        
        Postcondition:
            - Returns True without querying database
        """
        token = "test_token"
        mock_redis.get.return_value = b"revoked"
        
        result = service.is_blacklisted(token)
        
        assert result is True
        mock_redis.get.assert_called_once()
    
    def test_is_blacklisted_queries_db_on_cache_miss(self, service, mock_db, mock_redis):
        """
        Test that database is queried on Redis cache miss
        
        Precondition:
            - Token not in Redis cache
            - Token is in database
        
        Postcondition:
            - Returns True
            - Caches result in Redis
        """
        token = "test_token"
        mock_redis.get.return_value = None  # Cache miss
        
        # Mock database query
        mock_blacklist_entry = Mock()
        mock_blacklist_entry.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_blacklist_entry
        
        result = service.is_blacklisted(token)
        
        assert result is True
        mock_redis.setex.assert_called_once()  # Result cached


# Test RateLimiter
from app.core.rate_limit import RateLimiter


class TestRateLimiter:
    """Unit tests for rate limiter"""
    
    @pytest.fixture
    def mock_redis(self):
        return Mock()
    
    @pytest.fixture
    def limiter(self, mock_redis):
        return RateLimiter(mock_redis)
    
    def test_extract_client_ip_from_direct_connection(self, limiter):
        """Test extracting IP from direct connection"""
        request = Mock()
        request.headers = {}
        request.client.host = "192.168.1.100"
        
        ip = limiter.extract_client_ip(request)
        assert ip == "192.168.1.100"
    
    def test_extract_client_ip_from_x_forwarded_for(self, limiter):
        """
        Test extracting IP from X-Forwarded-For header
        
        Precondition:
            - X-Forwarded-For header present
        
        Postcondition:
            - Returns first IP in comma-separated list
        """
        request = Mock()
        request.headers = {"X-Forwarded-For": "203.0.113.100, 198.51.100.200"}
        
        ip = limiter.extract_client_ip(request)
        assert ip == "203.0.113.100"
    
    def test_check_rate_limit_allows_within_limit(self, limiter, mock_redis):
        """
        Test that requests within limit are allowed
        
        Precondition:
            - Current attempts < limit
        
        Postcondition:
            - Returns (True, details)
        """
        mock_redis.get.return_value = b"2"  # 2 attempts so far
        
        allowed, details = limiter.check_rate_limit("192.168.1.100")
        
        assert allowed is True
        assert details['attempts'] == 3  # Will be incremented
    
    def test_check_rate_limit_locks_out_on_excess(self, limiter, mock_redis):
        """
        Test that IP is locked out after exceeding limit
        
        Precondition:
            - Current attempts >= limit (5)
        
        Postcondition:
            - Returns (False, details)
            - IP is added to lockout key
        """
        mock_redis.get.return_value = b"5"  # Already at limit
        
        allowed, details = limiter.check_rate_limit("192.168.1.100")
        
        assert allowed is False
        assert details['reason'] == 'rate_limit_exceeded'
    
    def test_reset_ip_attempts_clears_counter(self, limiter, mock_redis):
        """
        Test that reset clears attempt counter and lockout
        
        Postcondition:
            - Both attempt key and lockout key are deleted
        """
        limiter.reset_ip_attempts("192.168.1.100")
        
        # Should delete attempt counter and lockout key
        assert mock_redis.delete.call_count == 2


```

### Integration Tests

```python
"""
Integration tests for security components
Uses real database and Redis instances
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta, timezone
import json


@pytest.fixture
def test_db():
    """Create test database"""
    SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    yield SessionLocal()


@pytest.fixture
def test_redis(mocker):
    """Mock Redis for integration tests"""
    return mocker.MagicMock()


@pytest.fixture
def app_with_services(test_db, test_redis):
    """FastAPI app with test services"""
    from app.main import app
    
    # Override dependencies
    app.dependency_overrides[get_db] = lambda: test_db
    app.dependency_overrides[get_redis] = lambda: test_redis
    
    return app


def test_login_with_rate_limiting(app_with_services):
    """
    Integration test: Login with rate limiting
    
    Scenario:
    1. Make 5 failed login attempts from same IP
    2. 6th attempt should be blocked with 429
    3. Verify lockout is enforced
    
    Preconditions:
        - User exists in database
        - IP can be extracted from request
    
    Postconditions:
        - First 5 requests return 401 (invalid credentials)
        - 6th request returns 429 (rate limited)
        - Lockout lasts 30 minutes
    """
    client = TestClient(app_with_services)
    
    # Make 5 failed attempts
    for i in range(5):
        response = client.post(
            "/auth/login",
            json={"email": "user@test.com", "password": "wrongpass"},
            headers={"X-Forwarded-For": "192.168.1.100"}
        )
        assert response.status_code == 401
    
    # 6th attempt should be rate limited
    response = client.post(
        "/auth/login",
        json={"email": "user@test.com", "password": "wrongpass"},
        headers={"X-Forwarded-For": "192.168.1.100"}
    )
    assert response.status_code == 429
    assert "Too many login attempts" in response.json()["message"]


def test_email_verification_flow(app_with_services, test_db):
    """
    Integration test: Email verification flow
    
    Scenario:
    1. Register new user
    2. Verify email with token
    3. Try to login before verification (should fail)
    4. After verification, login should succeed
    
    Postconditions:
        - User marked as email_verified = true
        - Unverified user cannot login
    """
    client = TestClient(app_with_services)
    
    # Register user
    register_response = client.post(
        "/auth/register",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "SecurePass123!@#",
            "role": "student"
        }
    )
    assert register_response.status_code == 201
    user_data = register_response.json()["data"]
    
    # Try to login before verification
    login_response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "SecurePass123!@#"
        }
    )
    assert login_response.status_code == 403
    assert "Email not verified" in login_response.json()["message"]


def test_token_blacklist_on_logout(app_with_services):
    """
    Integration test: Token blacklist on logout
    
    Scenario:
    1. Login and get token
    2. Use token to access protected endpoint (succeeds)
    3. Logout (token added to blacklist)
    4. Try to use same token (should fail)
    
    Postconditions:
        - Blacklisted token returns 401
        - Token is cached in Redis
    """
    client = TestClient(app_with_services)
    
    # Setup: Create verified user and login
    # ... (user creation steps) ...
    
    # Login to get token
    login_response = client.post(
        "/auth/login",
        json={"email": "user@test.com", "password": "SecurePass123!@#"}
    )
    token = login_response.json()["data"]["access_token"]
    
    # Use token successfully
    protected_response = client.get(
        "/buildings",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert protected_response.status_code == 200
    
    # Logout
    logout_response = client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert logout_response.status_code == 200
    
    # Try to use token after logout
    protected_response = client.get(
        "/buildings",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert protected_response.status_code == 401
    assert "Token has been revoked" in protected_response.json()["message"]


```

### Property-Based Tests

```python
"""
Property-based tests using Hypothesis
Tests invariants that should hold for all inputs
"""

from hypothesis import given, strategies as st
import hypothesis.strategies as st
from app.core.security import PasswordValidator
from app.services.file_validator import FileValidator


class TestPasswordValidatorProperties:
    """Property-based tests for password validation"""
    
    @given(st.text(min_size=12))
    def test_validate_never_crashes(self, password: str):
        """
        Property: validate() never crashes regardless of input
        
        Postcondition:
            - Always returns (bool, str)
        """
        try:
            is_valid, message = PasswordValidator.validate(password)
            assert isinstance(is_valid, bool)
            assert isinstance(message, str)
        except Exception as e:
            # Should not raise exceptions
            pytest.fail(f"validate() raised exception: {e}")
    
    @given(st.text())
    def test_verify_never_crashes(self, password: str):
        """
        Property: Password hashing/verification never crashes
        
        Postcondition:
            - Hashing and verification operations complete successfully
        """
        try:
            hashed = PasswordValidator.hash_password(password)
            result = PasswordValidator.verify_password(password, hashed)
            assert isinstance(result, bool)
        except Exception as e:
            pytest.fail(f"Hash/verify operation failed: {e}")


class TestFileValidatorProperties:
    """Property-based tests for file validation"""
    
    @given(st.text())
    def test_filename_validation_never_crashes(self, filename: str):
        """
        Property: Filename validation handles any string safely
        
        Postcondition:
            - Returns (bool, str) or raises known exception
        """
        try:
            is_valid, message = FileValidator.validate_filename(filename)
            assert isinstance(is_valid, bool)
            assert isinstance(message, str)
        except Exception as e:
            # Only known exceptions allowed
            from app.services.file_validator import PathTraversalException
            assert isinstance(e, PathTraversalException)
```



## Implementation Checklist & Deployment Strategy

### Pre-Implementation Requirements

- [ ] Code review of design document with security team
- [ ] Database backup of production environment
- [ ] Test environment configured with realistic data
- [ ] Redis instance deployed and tested
- [ ] Environment variables documented (see below)
- [ ] CORS allowed origins configured
- [ ] Logging infrastructure ready (structured logging)

### Environment Variables Required

```bash
# JWT Configuration
JWT_SECRET_KEY=<generate-random-256-bit-key>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Rate Limiting
LOGIN_RATE_LIMIT_ATTEMPTS=5
LOGIN_RATE_LIMIT_WINDOW_SECONDS=60
LOGIN_LOCKOUT_DURATION_SECONDS=1800

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=<if-required>
REDIS_TIMEOUT_SECONDS=5

# CORS Configuration
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://sbms.example.com

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=<your-email@gmail.com>
SMTP_PASSWORD=<app-specific-password>
SMTP_FROM_ADDRESS=noreply@sbms.example.com
EMAIL_VERIFICATION_EXPIRATION_HOURS=24

# File Upload Configuration
MAX_FILE_SIZE_IMAGES_MB=10
MAX_FILE_SIZE_PDF_MB=50
UPLOAD_DIRECTORY=/var/sbms/uploads

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Implementation Order

1. **Phase 1: Infrastructure (Week 1)**
   - [ ] Deploy Redis instance
   - [ ] Run database migrations
   - [ ] Configure environment variables
   - [ ] Set up logging infrastructure

2. **Phase 2: Core Security (Week 2)**
   - [ ] Implement PasswordValidator
   - [ ] Implement TokenBlacklistService
   - [ ] Implement RateLimiter
   - [ ] Add token blacklist middleware

3. **Phase 3: File Handling (Week 2-3)**
   - [ ] Implement FileValidator
   - [ ] Add file upload endpoint
   - [ ] Test with malicious files

4. **Phase 4: Building Service (Week 3)**
   - [ ] Implement BuildingService with RBAC
   - [ ] Update building routes
   - [ ] Test access control

5. **Phase 5: Query Optimization (Week 3-4)**
   - [ ] Implement ComplaintService with eager loading
   - [ ] Update complaint routes
   - [ ] Performance testing

6. **Phase 6: Email Verification (Week 4)**
   - [ ] Implement email verification flow
   - [ ] Update registration endpoint
   - [ ] Configure email templates

7. **Phase 7: Testing & QA (Week 4-5)**
   - [ ] Run unit tests
   - [ ] Run integration tests
   - [ ] Security testing
   - [ ] Performance testing

8. **Phase 8: Deployment (Week 5)**
   - [ ] Deploy to staging
   - [ ] Smoke testing
   - [ ] Deploy to production with rollback plan

### Performance Targets

| Component | Target | Measurement |
|-----------|--------|-------------|
| Password validation | < 50ms | bcrypt time + validation logic |
| Token blacklist check | < 5ms | Redis cache hit |
| File validation | < 100ms | Including magic number check |
| Rate limit check | < 2ms | Redis lookup |
| RBAC filtering | < 10ms | Single database query |
| Complaint eager loading | < 50ms | 20 complaints with all relationships |
| Login endpoint | < 500ms | Total time including rate limit, auth, logging |
| Building endpoint | < 200ms | Total time including RBAC, pagination, logging |

### Security Testing Checklist

#### Password Security
- [ ] Weak passwords rejected (< 12 chars, missing char types)
- [ ] Strong passwords accepted
- [ ] Hash verification works correctly
- [ ] Bcrypt salting verified (same password produces different hashes)

#### File Upload Security
- [ ] Executable files rejected (.exe, .dll, .sh, etc.)
- [ ] Path traversal attempts blocked (../, ~/, etc.)
- [ ] MIME type validation works
- [ ] Magic number verification prevents spoofing
- [ ] File size limits enforced
- [ ] Special characters in filenames blocked

#### Token Blacklist Security
- [ ] Revoked tokens rejected on protected routes
- [ ] Expired tokens auto-removed from database
- [ ] Redis cache synchronized with database
- [ ] Logout successfully blacklists token

#### Rate Limiting Security
- [ ] Failed login attempts tracked per IP
- [ ] IP locked after 5 failed attempts
- [ ] Lockout lasts 30 minutes
- [ ] Successful login resets counter
- [ ] X-Forwarded-For header respected

#### RBAC Security
- [ ] Admin sees all buildings
- [ ] Worker sees only assigned buildings
- [ ] Student sees only campus buildings
- [ ] Guest has no access
- [ ] Role escalation attempts blocked
- [ ] Unauthorized access logged

#### Email Verification Security
- [ ] Verification token hashed (not stored plaintext)
- [ ] Token expires after 24 hours
- [ ] Only one active token per user
- [ ] Token cannot be reused
- [ ] Unverified users cannot login

### Monitoring & Alerting

#### Key Metrics to Monitor

```
Rate Limiting:
- rate_limit_violations_per_minute
- avg_lockout_duration_seconds
- ip_lockout_active_count

Token Blacklist:
- blacklisted_tokens_total
- token_blacklist_cache_hit_ratio
- average_blacklist_check_time_ms

File Upload:
- rejected_files_total
- rejected_files_by_reason
- average_validation_time_ms

RBAC:
- unauthorized_access_attempts
- permission_denied_count
- avg_rbac_check_time_ms

Database:
- query_execution_time_ms
- n_plus_one_query_detection
- index_usage_statistics
```

#### Alert Thresholds

```yaml
Alerts:
  - name: high_rate_limit_violations
    condition: rate_limit_violations_per_minute > 100
    severity: warning
    
  - name: token_blacklist_check_slow
    condition: average_blacklist_check_time_ms > 50
    severity: warning
    
  - name: many_unauthorized_access_attempts
    condition: unauthorized_access_attempts_per_minute > 50
    severity: critical
    
  - name: cache_hit_ratio_low
    condition: token_blacklist_cache_hit_ratio < 0.8
    severity: warning
    
  - name: database_slow_queries
    condition: p95_query_time_ms > 100
    severity: warning
```

### Rollback Plan

**If issues occur in production:**

1. **Immediate Actions (Minutes 0-5)**
   - [ ] Alert team
   - [ ] Disable new deployments
   - [ ] Check error logs and metrics
   - [ ] Notify on-call engineer

2. **Diagnosis (Minutes 5-15)**
   - [ ] Is it rate limiting? (check redis)
   - [ ] Is it database? (check query logs)
   - [ ] Is it authentication? (check token blacklist)
   - [ ] Is it file uploads? (check validation logs)

3. **Rollback Decision (Minutes 15-25)**
   - [ ] If critical errors: rollback to previous version
   - [ ] If minor issues: apply hotfix in feature branch
   - [ ] If performance: scale resources and monitor

4. **Rollback Execution (Minutes 25-35)**
   ```bash
   # Revert to previous container image
   docker service update --image sbms-api:v1.2.0 sbms-api
   
   # Monitor health checks
   docker service ps sbms-api
   
   # Verify error rate decreases
   curl http://sbms-api:8000/health
   
   # Check logs for errors
   docker service logs sbms-api
   ```

5. **Post-Incident (Hours 1-4)**
   - [ ] Create incident report
   - [ ] Identify root cause
   - [ ] Schedule post-mortem meeting
   - [ ] Fix issue in feature branch
   - [ ] Additional testing before re-deployment

### Documentation & Training

- [ ] API documentation updated (OpenAPI/Swagger)
- [ ] Deployment runbook created
- [ ] Operations team trained on monitoring
- [ ] Security audit procedures documented
- [ ] Database maintenance scripts documented
- [ ] Troubleshooting guide created

### Sign-Off

- [ ] Security team approval
- [ ] Database team approval
- [ ] Operations team approval
- [ ] Product owner acceptance

---

## Conclusion

This technical design provides a comprehensive approach to implementing security hardening and performance optimization for the SBMS platform. The layered architecture ensures:

- **Security**: Strong authentication, rate limiting, file validation, and access control
- **Performance**: Prevented N+1 queries, optimized database indexes, Redis caching
- **Maintainability**: Clear separation of concerns, comprehensive logging, consistent error handling
- **Testability**: Unit, integration, and property-based tests for all components

The implementation should follow the phased approach outlined above, with thorough testing at each phase and careful monitoring during production deployment.

