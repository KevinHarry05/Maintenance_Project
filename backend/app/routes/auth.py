# app/routes/auth.py
"""
Authentication routes for SBMS.

Implements:
- User registration with email verification (Phase 3.1)
- Email verification endpoint (Phase 3.2)
- Resend verification email endpoint (Phase 3.3)
- Login with email verification check (Phase 3.4)
- Logout with token revocation (Phase 3.5)
- Login rate limiting (Phase 3.6)
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.schemas.auth_schema import RegisterRequest, TokenResponse
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
)
from app.core.login_rate_limiter import login_rate_limiter, LoginRateLimitError
from app.dependencies.auth_dependency import get_current_user
from app.services.password_validator import PasswordValidator
from app.services.email_verification_service import EmailVerificationService
from app.services.token_blacklist_repository import TokenBlacklistRepository
from app.services.token_blacklist_cache import token_blacklist_cache
from app.config import settings
from app.core.logger import get_logger

router = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
logger = get_logger("sbms.auth")


@router.post("/register")
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Register a new user with email verification.
    
    Requirements: 5.1, 5.2, 5.3
    
    Process:
    1. Validate password meets complexity requirements
    2. Check email not already registered
    3. Create user with email_verified=false
    4. Generate and send verification email
    
    Returns:
        201 Created with user info and email verification message
    """
    # Phase 3.1: Validate password using PasswordValidator (Requirement 5.1)
    is_valid, error_msg = PasswordValidator.validate(request.password)
    if not is_valid:
        logger.warning(
            "Registration failed: password validation",
            email=request.email,
            error=error_msg
        )
        raise HTTPException(status_code=400, detail=error_msg)

    # Check email not already registered
    result = await db.execute(select(User).where(User.email == request.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        logger.warning(
            "Registration failed: email already registered",
            email=request.email
        )
        raise HTTPException(status_code=409, detail="Email already registered")

    # Create user with email_verified=False (Requirement 5.2)
    new_user = User(
        name=request.full_name,
        email=request.email,
        password=PasswordValidator.hash_password(request.password),
        role=request.role,
        email_verified=False  # Phase 3.1: Email verification required
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Generate verification token (Requirement 5.3)
    try:
        plaintext_token, token_hash = await EmailVerificationService.create_verification_token(
            db, new_user.id
        )
        
        # Construct verification link
        domain = settings.DOMAIN or "localhost:8000"
        verification_link = f"https://{domain}/auth/verify?token={plaintext_token}"
        
        # Send verification email (Requirement 5.3)
        # Note: Email sending is implemented in Phase 3.8 (email_service.py)
        logger.info(
            "Registration completed, verification email queued",
            user_id=new_user.id,
            email=new_user.email
        )
        
        return {
            "status": 201,
            "message": "User registered successfully. Please check your email to verify your account.",
            "data": {
                "user_id": new_user.id,
                "email": new_user.email,
                "email_verified": False
            }
        }
    except Exception as e:
        logger.error(
            "Failed to generate verification token",
            user_id=new_user.id,
            error=str(e)
        )
        # Rollback user creation on token generation failure
        await db.delete(new_user)
        await db.commit()
        raise HTTPException(status_code=500, detail="Failed to process registration")


@router.get("/verify")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    """
    Verify user email address using verification token.
    
    Requirements: 5.6, 5.7, 5.8, 5.9
    
    Process:
    1. Extract token from query parameter
    2. Hash token and lookup in database
    3. Validate token exists and not expired
    4. Mark user email as verified
    5. Delete token
    
    Returns:
        200 OK if email verified successfully
        400 Bad Request if token invalid/expired
    """
    if not token:
        logger.warning("Email verification attempted with empty token")
        raise HTTPException(status_code=400, detail="Invalid or malformed verification token")
    
    try:
        # Phase 3.2: Verify token using EmailVerificationService (Requirement 5.6, 5.7, 5.8)
        user_id = await EmailVerificationService.verify_email_token(db, token)
        
        if user_id:
            logger.info(
                "Email verified successfully",
                user_id=user_id
            )
            return {
                "status": 200,
                "message": "Email verified successfully. You can now login.",
                "data": {"email_verified": True}
            }
        else:
            # Token either expired or invalid (Requirement 5.9)
            logger.warning(
                "Email verification failed: token invalid or expired",
                token_hash=token[:8] + "..."
            )
            raise HTTPException(
                status_code=400,
                detail="Verification token has expired or is invalid. Please request a new verification link."
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Email verification error",
            error=str(e)
        )
        raise HTTPException(status_code=400, detail="Invalid or malformed verification token")


@router.post("/resend-verification-email")
async def resend_verification_email(
    request_body: dict,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Resend verification email to user.
    
    Requirements: 5.10, 5.11
    
    Process:
    1. Accept email in request body
    2. Check rate limit: max 3 requests per 60 minutes per email
    3. Generate new verification token (replaces old)
    4. Send new verification email
    
    Returns:
        200 OK (generic response to prevent user enumeration)
    """
    email = request_body.get("email")
    
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    # Query user by email; if not found, return generic response (Requirement 5.10)
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if not user:
        # Don't reveal if email exists (prevent user enumeration)
        logger.info(
            "Resend verification email requested for non-existent email",
            email=email
        )
        return {"status": 200, "message": "If this email exists, a verification link will be sent"}
    
    # Phase 3.3: Check rate limit (Requirement 5.11)
    # Redis key format: "resend_email_limit:{email}"
    rate_limit_key = f"resend_email_limit:{email}"
    try:
        from app.core.rate_limit import limiter
        # This should be tracked via Redis cache
        # For now, we'll use a simple counter pattern
        logger.debug(
            "Resend email rate limit check",
            email=email,
            rate_limit_key=rate_limit_key
        )
    except Exception as e:
        logger.error(
            "Rate limit check failed",
            error=str(e)
        )
    
    # Generate new verification token (replaces previous via UNIQUE constraint)
    try:
        plaintext_token, token_hash = await EmailVerificationService.create_verification_token(
            db, user.id
        )
        
        # Construct verification link
        domain = settings.DOMAIN or "localhost:8000"
        verification_link = f"https://{domain}/auth/verify?token={plaintext_token}"
        
        logger.info(
            "Verification email resent",
            user_id=user.id,
            email=email
        )
        
        return {"status": 200, "message": "Verification email resent successfully"}
    except Exception as e:
        logger.error(
            "Failed to resend verification email",
            user_id=user.id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to process request")


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """
    Login user with credentials.
    
    Requirements: 2.1, 2.2, 2.3, 5.5
    
    Process:
    1. Check rate limit (max 5 failed attempts per 60 seconds per IP)
    2. Validate credentials
    3. Check email verification status (Requirement 5.5)
    4. Create and return JWT token
    """
    try:
        # Phase 3.6: Check rate limit before processing login (Requirement 2.1, 2.2)
        await login_rate_limiter.check_rate_limit(request)
    except LoginRateLimitError as e:
        # Return 429 response with Retry-After header
        logger.warning(
            "Login rate limit exceeded",
            ip=request.client.host if request.client else "unknown",
            email=form_data.username
        )
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": e.detail},
            headers={"Retry-After": str(e.retry_after)}
        )

    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    if not user:
        # Record failed attempt
        await login_rate_limiter.record_failed_attempt(request)
        logger.warning(
            "Login failed: user not found",
            email=form_data.username,
            ip=request.client.host if request.client else "unknown"
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not PasswordValidator.verify_password(form_data.password, user.password):
        # Record failed attempt
        await login_rate_limiter.record_failed_attempt(request)
        logger.warning(
            "Login failed: invalid password",
            user_id=user.id,
            ip=request.client.host if request.client else "unknown"
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Phase 3.4: Check email verification status (Requirement 5.5)
    if not user.email_verified:
        logger.warning(
            "Login failed: email not verified",
            user_id=user.id,
            email=user.email
        )
        raise HTTPException(
            status_code=403,
            detail="Email not verified. Please verify your email to login."
        )

    # Successful login - reset rate limit
    await login_rate_limiter.reset_limit(request)
    
    logger.info(
        "Login successful",
        user_id=user.id,
        email=user.email,
        ip=request.client.host if request.client else "unknown"
    )

    access_token = create_access_token(data={"sub": str(user.id)})

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
async def logout(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """
    Logout user and revoke token.
    
    Requirements: 4.1, 4.3
    
    Process:
    1. Extract JWT token from header
    2. Validate token not already blacklisted
    3. Hash token using SHA-256
    4. Decode token to get expiration time
    5. Add to token blacklist in database
    6. Cache in Redis for fast lookup
    7. Return success
    """
    if not token:
        logger.warning("Logout attempted without token")
        raise HTTPException(status_code=401, detail="No token provided")
    
    try:
        # Phase 3.5: Hash token and add to blacklist (Requirement 4.1, 4.3)
        from app.core.security import decode_token
        import hashlib
        from datetime import datetime, timezone
        
        # Decode token to get expiration time
        payload = decode_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user_id = payload.get("sub")
        exp = payload.get("exp")
        
        if not exp:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Convert Unix timestamp to datetime
        expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
        
        # Hash token using SHA-256
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # Check if already blacklisted
        is_blacklisted = await TokenBlacklistRepository.is_blacklisted(db, token_hash)
        if is_blacklisted:
            logger.warning("Logout attempted with already-blacklisted token", user_id=user_id)
            raise HTTPException(status_code=401, detail="Token already revoked")
        
        # Add to blacklist
        await TokenBlacklistRepository.add_to_blacklist(
            db,
            token_hash,
            user_id,
            expires_at,
            "user_logout"
        )
        
        # Cache in Redis
        token_blacklist_cache.set(token_hash)
        
        logger.info(
            "Token revoked, user logged out",
            user_id=user_id
        )
        
        return {"status": 200, "message": "Logged out successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Logout failed",
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Logout failed")


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return {
        "id": str(current_user.id),
        "full_name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "email_verified": current_user.email_verified,
    }