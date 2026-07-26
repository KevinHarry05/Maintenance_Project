"""Permission and Authorization Decorators - RBAC implementation.

Provides decorators for:
- verify_ownership(): Check user owns a resource
- require_permission(): Check user has required permission

Requirements: 8.5, 8.6
"""

import logging
from functools import wraps
from typing import Callable, Optional, Any
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.dependencies.auth_dependency import get_current_user
from app.database import get_db
from app.models.user import User

logger = logging.getLogger(__name__)

# Role to permissions mapping
ROLE_PERMISSIONS = {
    "admin": [
        "view_all_complaints",
        "view_all_buildings",
        "view_all_users",
        "manage_workers",
        "verify_completion",
        "force_resolve",
        "view_complaints",
        "create_complaint",
    ],
    "worker": [
        "view_assigned_complaints",
        "view_building_complaints",
        "upload_resolution",
        "view_complaints",
    ],
    "student": [
        "create_complaint",
        "view_own_complaints",
        "provide_feedback",
        "view_buildings",
        "view_complaints",
    ]
}


def verify_ownership(
    resource_type: str = "complaint",
    id_param: str = "id"
) -> Callable:
    """
    Decorator to verify user owns a resource.
    
    Requirements: 8.5
    
    Usage:
        @router.get("/complaints/{complaint_id}")
        @verify_ownership(resource_type="complaint", id_param="complaint_id")
        async def get_complaint(complaint_id: str, current_user = Depends(get_current_user)):
            ...
    
    Args:
        resource_type: Type of resource (complaint, building, etc.)
        id_param: Name of the path parameter containing resource ID
    
    Postcondition:
        - If user owns resource or is admin: handler is called
        - If user doesn't own resource: 403 Forbidden
        - If resource not found: 404 Not Found
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Extract current user and resource ID from kwargs
            current_user = kwargs.get("current_user")
            resource_id = kwargs.get(id_param)
            db = kwargs.get("db")
            
            if not current_user or not resource_id or not db:
                logger.error(
                    f"verify_ownership missing dependencies",
                    resource_type=resource_type,
                    has_user=current_user is not None,
                    has_id=resource_id is not None,
                    has_db=db is not None
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Authorization check failed"
                )
            
            # Check if user is admin (admins can access all resources)
            if current_user.role == "admin":
                return await func(*args, **kwargs)
            
            # Query resource by type
            if resource_type == "complaint":
                from app.models.complaint import Complaint
                result = await db.execute(
                    select(Complaint).where(Complaint.id == str(resource_id))
                )
                resource = result.scalar_one_or_none()
                
                if not resource:
                    logger.warning(
                        f"Resource not found during ownership check",
                        resource_type=resource_type,
                        resource_id=resource_id
                    )
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"{resource_type.capitalize()} not found"
                    )
                
                # Check ownership
                if resource.user_id != current_user.id:
                    logger.warning(
                        f"Ownership check failed",
                        resource_type=resource_type,
                        resource_id=resource_id,
                        owner_id=resource.user_id,
                        user_id=current_user.id
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="User does not have permission to access this resource"
                    )
            
            # Call the original function
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_permission(permission: str) -> Callable:
    """
    Decorator to verify user has required permission.
    
    Requirements: 8.6
    
    Usage:
        @router.post("/complaints")
        @require_permission("create_complaint")
        async def create_complaint(current_user = Depends(get_current_user)):
            ...
    
    Args:
        permission: Required permission (e.g., "create_complaint", "view_all_complaints")
    
    Postcondition:
        - If user's role has permission: handler is called
        - If user lacks permission: 403 Forbidden
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Extract current user from kwargs
            current_user = kwargs.get("current_user")
            
            if not current_user:
                logger.error(
                    f"require_permission missing user",
                    permission=permission
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Authorization check failed"
                )
            
            # Get user's role
            user_role = current_user.role
            
            # Check if role has permission
            user_permissions = ROLE_PERMISSIONS.get(user_role, [])
            
            if permission not in user_permissions:
                logger.warning(
                    f"Permission denied",
                    user_id=current_user.id,
                    role=user_role,
                    required_permission=permission,
                    user_permissions=user_permissions
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User does not have permission to perform this action"
                )
            
            # Call the original function
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def get_user_permissions(role: str) -> list[str]:
    """
    Get all permissions for a given role.
    
    Args:
        role: User role (admin, worker, student)
    
    Returns:
        List of permissions for the role
    """
    return ROLE_PERMISSIONS.get(role, [])


def user_has_permission(user: User, permission: str) -> bool:
    """
    Check if user has a specific permission.
    
    Args:
        user: User object
        permission: Permission to check
    
    Returns:
        True if user has permission, False otherwise
    """
    user_permissions = get_user_permissions(user.role)
    return permission in user_permissions
