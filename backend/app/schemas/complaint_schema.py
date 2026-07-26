from pydantic import BaseModel, field_validator
from uuid import UUID
from typing import Optional
from datetime import datetime


# ==============================
# CREATE COMPLAINT
# ==============================
class ComplaintCreate(BaseModel):
    title: str
    description: str
    building_id: UUID
    floor_number: str
    room_number: str
    category: str | None = None
    
    # Phase 5.7: Add field validators (Requirement 8.1)
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        """Validate title is not empty and reasonable length."""
        if not v or len(v.strip()) == 0:
            raise ValueError('Title cannot be empty')
        if len(v) < 5:
            raise ValueError('Title must be at least 5 characters')
        if len(v) > 200:
            raise ValueError('Title must not exceed 200 characters')
        return v.strip()
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        """Validate description is not empty and reasonable length."""
        if not v or len(v.strip()) == 0:
            raise ValueError('Description cannot be empty')
        if len(v) < 10:
            raise ValueError('Description must be at least 10 characters')
        if len(v) > 5000:
            raise ValueError('Description must not exceed 5000 characters')
        return v.strip()
    
    @field_validator('floor_number')
    @classmethod
    def validate_floor_number(cls, v):
        """Validate floor number is not empty."""
        if not v or len(v.strip()) == 0:
            raise ValueError('Floor number cannot be empty')
        if len(v) > 50:
            raise ValueError('Floor number must not exceed 50 characters')
        return v.strip()
    
    @field_validator('room_number')
    @classmethod
    def validate_room_number(cls, v):
        """Validate room number is not empty."""
        if not v or len(v.strip()) == 0:
            raise ValueError('Room number cannot be empty')
        if len(v) > 50:
            raise ValueError('Room number must not exceed 50 characters')
        return v.strip()


# ==============================
# ASSIGN WORKER
# ==============================
class ComplaintAssign(BaseModel):
    assignee_id: UUID


# ==============================
# UPDATE STATUS
# ==============================
class ComplaintUpdate(BaseModel):
    status: str
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """Validate status is one of allowed values."""
        allowed_statuses = {"pending", "assigned", "in_progress", "completed", "closed", "resolved"}
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of: {", ".join(allowed_statuses)}')
        return v


class ComplaintCompletion(BaseModel):
    remarks: str
    
    @field_validator('remarks')
    @classmethod
    def validate_remarks(cls, v):
        """Validate remarks are not empty and reasonable length."""
        if not v or len(v.strip()) == 0:
            raise ValueError('Remarks cannot be empty')
        if len(v) > 2000:
            raise ValueError('Remarks must not exceed 2000 characters')
        return v.strip()


class ComplaintReview(BaseModel):
    approved: bool
    remarks: str | None = None
    
    @field_validator('remarks')
    @classmethod
    def validate_remarks(cls, v):
        """Validate remarks are reasonable length if provided."""
        if v and len(v) > 2000:
            raise ValueError('Remarks must not exceed 2000 characters')
        return v.strip() if v else None


class ComplaintFeedback(BaseModel):
    rating: int
    comment: str | None = None
    
    @field_validator('rating')
    @classmethod
    def validate_rating(cls, v):
        """Validate rating is between 1 and 5."""
        if not isinstance(v, int) or not (1 <= v <= 5):
            raise ValueError('Rating must be an integer between 1 and 5')
        return v
    
    @field_validator('comment')
    @classmethod
    def validate_comment(cls, v):
        """Validate comment is reasonable length if provided."""
        if v and len(v) > 2000:
            raise ValueError('Comment must not exceed 2000 characters')
        return v.strip() if v else None


# ==============================
# RESPONSE MODEL
# ==============================
class ComplaintResponse(BaseModel):
    id: UUID
    title: str
    description: str
    category: str | None
    floor_number: str
    room_number: str
    file_path: str | None
    resolution_file_path: str | None = None
    status: str
    priority_score: float
    priority_level: str
    worker_remarks: str | None = None
    admin_remarks: str | None = None
    feedback_rating: int | None = None
    feedback_comment: str | None = None
    admin_verified: bool
    building_id: UUID
    user_id: UUID
    assigned_to: Optional[UUID]
    created_at: datetime
    completed_at: datetime | None = None
    closed_at: datetime | None = None

    class Config:
        from_attributes = True
