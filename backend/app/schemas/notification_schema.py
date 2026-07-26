from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class NotificationCreate(BaseModel):
    user_id: UUID
    title: str
    message: str
    notification_type: str
    complaint_id: UUID | None = None


class NotificationResponse(BaseModel):
    id: UUID
    user_id: UUID
    complaint_id: UUID | None
    title: str
    message: str
    notification_type: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
