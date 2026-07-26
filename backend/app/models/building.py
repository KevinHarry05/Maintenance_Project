import uuid
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.sql import func
from app.database import Base


class Building(Base):
    __tablename__ = "buildings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    name = Column(String, nullable=False)
    block = Column(String, nullable=False)
    floor_count = Column(Integer, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())