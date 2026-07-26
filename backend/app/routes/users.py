from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.role_dependency import require_role
from app.models.user import User
from app.dependencies.auth_dependency import get_current_user

router = APIRouter()


@router.get("/me")
async def get_me(current_user=Depends(get_current_user)):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
    }


@router.get("/workers")
async def get_workers(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    result = await db.execute(select(User).where(User.role == "worker"))
    workers = result.scalars().all()

    return [
        {
            "id": str(worker.id),
            "name": worker.name,
            "email": worker.email,
            "role": worker.role,
        }
        for worker in workers
    ]