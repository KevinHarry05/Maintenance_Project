import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Float, Integer, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String, nullable=True)
    floor_number = Column(String, nullable=False)
    room_number = Column(String, nullable=False)
    file_path = Column(String, nullable=True)
    resolution_file_path = Column(String, nullable=True)

    status = Column(String, default="pending", nullable=False)

    # NEW PRIORITY FIELDS
    priority_score = Column(Float, default=0.0)
    priority_level = Column(String, default="Low")
    worker_remarks = Column(Text, nullable=True)
    admin_remarks = Column(Text, nullable=True)
    feedback_rating = Column(Integer, nullable=True)
    feedback_comment = Column(Text, nullable=True)
    admin_verified = Column(Boolean, default=False, nullable=False)

    user_id = Column(String(36), ForeignKey("users.id"))
    building_id = Column(String(36), ForeignKey("buildings.id"))
    assigned_to = Column(String(36), ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships with eager loading strategy for performance optimization
    # These use lazy="select" to defer loading by default, then selectinload/joinedload
    # are applied in service layer for batch efficiency. This prevents N+1 queries.
    
    created_by = relationship(
        "User",
        foreign_keys=[user_id],
        lazy="select",
        backref="created_complaints",
        # Eager loading strategy: Use joinedload in service layer for single complaint queries,
        # selectinload for complaint lists. Prevents N+1 queries when accessing complaint creator.
    )
    
    assigned_worker = relationship(
        "User",
        foreign_keys=[assigned_to],
        lazy="select",
        backref="assigned_complaints",
        # Eager loading strategy: Use joinedload in service layer for single complaint queries,
        # selectinload for complaint lists. Prevents N+1 queries when accessing assigned worker.
    )
    
    building = relationship(
        "Building",
        foreign_keys=[building_id],
        lazy="select",
        backref="complaints"
        # Eager loading strategy: Use joinedload in service layer. Prevents additional query
        # when accessing complaint's building reference.
    )
    
    # Collection relationships for eager loading via selectinload in service layer
    notifications = relationship(
        "Notification",
        back_populates="complaint",
        lazy="select",
        cascade="all, delete-orphan",
        # Eager loading strategy: Use selectinload in service layer to batch-load all notifications
        # for a set of complaints in a single query. Prevents N+1 queries during iteration.
    )
    
    ticket_logs = relationship(
        "TicketLog",
        back_populates="complaint",
        lazy="select",
        cascade="all, delete-orphan",
        # Eager loading strategy: Use selectinload in service layer to batch-load all ticket logs
        # for a set of complaints in a single query. Prevents N+1 queries during iteration.
    )

    # PERFORMANCE NOTES:
    # Pattern: lazy="select" at model level + selectinload/joinedload at service layer
    # Benefits:
    #   - Default lazy loading defers relationship loading
    #   - Service layer applies appropriate eager loading strategy per query
    #   - Prevents N+1 queries: created_by, assigned_worker, notifications, ticket_logs
    #   - For single complaint: use joinedload for many-to-one (created_by, assigned_worker)
    #   - For single complaint: use selectinload for one-to-many (notifications, ticket_logs)
    #   - For complaint lists: use selectinload for all relationships
    # See complaint_service.py for implementation examples
