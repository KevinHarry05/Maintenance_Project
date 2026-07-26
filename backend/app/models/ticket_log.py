import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class TicketLog(Base):
    __tablename__ = "ticket_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    complaint_id = Column(String(36), ForeignKey("complaints.id"))
    updated_by = Column(String(36), ForeignKey("users.id"))

    old_status = Column(String)
    new_status = Column(String)

    updated_at = Column(DateTime(timezone=True), server_default=func.now())