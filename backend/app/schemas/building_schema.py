from pydantic import BaseModel
from uuid import UUID


class BuildingCreate(BaseModel):
    name: str
    block: str
    floor_count: int


class BuildingUpdate(BaseModel):
    name: str | None = None
    block: str | None = None
    floor_count: int | None = None


class BuildingResponse(BaseModel):
    id: UUID
    name: str
    block: str
    floor_count: int

    class Config:
        from_attributes = True