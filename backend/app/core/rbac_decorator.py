"""RBAC Decorator - Role-Based Access Control for protected endpoints.

This module provides decorators to enforce role-based authorization on FastAPI
endpoints. It extracts the user role from the JWT token and checks against
allowed roles before the endpoint handler executes.

Security Strategy:
- Fail-closed: Deny by default, allow specific roles only
- Logged: All access attempts (granted/denied) are logged
- Defense-in-depth: Works alongside database-level permissions
"""

import logging
from functools import wraps
from typing import Callable, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthenticationCredentials
import jwt
from app.config import settings

logger = logging.getLogger(__name__)

security = HTTPBearer()


def require_role(allowed_roles: List[str]) -> Callable:
    """
    Decorator to enforce role-based access control.

    Checks that the authenticated user's role is in the allowed_roles list.
    Fails with HTTP 403 if role is not authorized.

    Args:
        allowed_roles: List of role names that are allowed (e.g., ['admin', 'worker'])

    Returns:
        Decorator function

    Usage:
        @router.get("/admin/users")
        @require_role(['admin'])
        async def list_all_users():
            return {"users": [...]}

    Postcondition:
        - Access granted only if user role in allowed_roles
        - HTTP 403 Forbidden returned if role not authorized
        - Access attempt logged with user role
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract token from request
            credentials: HTTPAuthenticationCredentials = kwargs.get('credentials')

            if not credentials:
                logger.warning(
                    "RBAC check failed: no credentials provided",
                    allowed_roles=allowed_roles
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authorization credentials are missing"
                )

            try:
                # Decode JWT
                token = credentials.credentials
                payload = jwt.decode(
                    token,
                    settings.SECRET_KEY,
                    algorithms=[settings.ALGORITHM]
                )
                user_role = payload.get("role", "student")

            except jwt.InvalidTokenError:
                logger.warning(
                    "RBAC check failed: invalid token",
                    allowed_roles=allowed_roles
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authorization credentials are invalid"
                )

            # Check role
            if user_role not in allowed_roles:
                user_id = payload.get("sub")
                logger.warning(
                    "RBAC access denied",
                    user_id=user_id,
                    user_role=user_role,
                    allowed_roles=allowed_roles
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User does not have permission to access this resource"
                )

            logger.debug(
                "RBAC access granted",
                user_id=payload.get("sub"),
                user_role=user_role,
                allowed_roles=allowed_roles
            )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def extract_user_role_from_token(credentials: HTTPAuthenticationCredentials = Depends(security)) -> str:
    """
    Extract user role from JWT token.

    Can be used as a dependency in route handlers.

    Args:
        credentials: HTTP bearer token from FastAPI security

    Returns:
        User role string (admin, worker, student)

    Raises:
        HTTPException: 401 if token is invalid or missing

    Usage:
        @router.get("/me")
        async def get_current_user(role: str = Depends(extract_user_role_from_token)):
            return {"role": role}
    """
    try:
        token = credentials.credentials
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        role = payload.get("role", "student")
        return role
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization credentials are invalid"
        )


def extract_user_id_from_token(credentials: HTTPAuthenticationCredentials = Depends(security)) -> str:
    """
    Extract user ID from JWT token.

    Args:
        credentials: HTTP bearer token from FastAPI security

    Returns:
        User ID string

    Raises:
        HTTPException: 401 if token is invalid or missing
    """
    try:
        token = credentials.credentials
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization credentials are invalid"
            )
        return user_id
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization credentials are invalid"
        )
