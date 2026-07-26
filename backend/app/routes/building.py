from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.database import get_db
from app.models.building import Building
from app.dependencies.auth_dependency import get_current_user
from app.dependencies.role_dependency import require_role
from app.schemas.building_schema import (
    BuildingCreate,
    BuildingUpdate,
    BuildingResponse,
)
from app.utils.cache import delete_cache, get_cache, set_cache

router = APIRouter()


# Admin → Create building
@router.post("", response_model=BuildingResponse)
async def create_building(
    request: BuildingCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    building = Building(
        name=request.name,
        block=request.block,
        floor_count=request.floor_count,
    )

    db.add(building)
    await db.commit()
    await db.refresh(building)
    delete_cache("buildings:all")

    return building


# All authenticated users → View buildings
@router.get("", response_model=list[BuildingResponse])
async def get_buildings(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Retrieve all buildings.
    
    Accessible to all authenticated users (student, worker, admin).
    Returns 401 if unauthenticated.
    
    Args:
        db: Database session
        current_user: Current authenticated user (required)
    
    Returns:
        List of all buildings with their details
    """
    cache_key = "buildings:all"
    cached = get_cache(cache_key)
    if cached is not None:
        return cached

    result = await db.execute(select(Building))
    buildings = result.scalars().all()
    set_cache(cache_key, jsonable_encoder(buildings), ttl=600)
    return buildings


# Admin → Update building
@router.put("/{building_id}", response_model=BuildingResponse)
async def update_building(
    building_id: UUID,
    request: BuildingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    result = await db.execute(
        select(Building).where(Building.id == str(building_id))
    )
    building = result.scalar_one_or_none()

    if not building:
        raise HTTPException(status_code=404, detail="Building not found")

    if request.name is not None:
        building.name = request.name
    if request.block is not None:
        building.block = request.block
    if request.floor_count is not None:
        building.floor_count = request.floor_count

    await db.commit()
    await db.refresh(building)
    delete_cache("buildings:all")

    return building


# Admin → Delete building
@router.delete("/{building_id}")
async def delete_building(
    building_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    result = await db.execute(
        select(Building).where(Building.id == str(building_id))
    )
    building = result.scalar_one_or_none()

    if not building:
        raise HTTPException(status_code=404, detail="Building not found")

    await db.delete(building)
    await db.commit()
    delete_cache("buildings:all")

    return {"message": "Building deleted successfully"}
