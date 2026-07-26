from fastapi import Depends, HTTPException, status
from app.dependencies.auth_dependency import get_current_user


def require_role(*required_roles: str):
    async def role_checker(current_user=Depends(get_current_user)):
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return role_checker