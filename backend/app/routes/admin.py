from fastapi import APIRouter, Depends
from app.dependencies.role_dependency import require_role

router = APIRouter()


@router.get("/test")
async def admin_test(current_user=Depends(require_role("admin"))):
    return {"message": "Admin access granted"}