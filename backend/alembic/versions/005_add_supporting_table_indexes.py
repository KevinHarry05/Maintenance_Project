"""add_supporting_table_indexes

Revision ID: 005_supporting_indexes
Revises: 004_complaint_indexes
Create Date: 2024-01-15 10:20:00.000000

"""
from alembic import op
from sqlalchemy.dialects import postgresql
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005_supporting_indexes'
down_revision = '004_complaint_indexes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create performance indexes on supporting tables.
    
    These indexes optimize:
    - ticket_logs: Quick lookup of logs for a specific complaint
      - Used by: GET /complaints/{id}, ticket log retrieval
      - Query pattern: SELECT * FROM ticket_logs WHERE complaint_id = ?
    - notifications: Efficient retrieval of user's notifications
      - Used by: GET /notifications, user notification listing
      - Query pattern: SELECT * FROM notifications WHERE user_id = ?
    - notifications: Finding unread notifications (partial index - PostgreSQL only)
      - Used by: GET /notifications?unread=true
      - Query pattern: SELECT * FROM notifications WHERE user_id = ? AND is_read = false
      - Note: Partial indexes reduce index size by only indexing unread notifications
    
    Performance impact:
    - ticket_logs index: Complaint log queries execute O(log n) instead of O(n)
    - user_id index: User notification queries execute O(log n) instead of O(n)
    - is_read partial index: Unread notification filtering is O(log n) with smaller index
    """
    # Index on ticket_logs.complaint_id for fast log retrieval by complaint
    # Use case: Finding all status change logs for a specific complaint
    op.create_index(
        'idx_ticket_logs_complaint_id',
        'ticket_logs',
        ['complaint_id'],
        if_not_exists=True
    )
    
    # Index on notifications.user_id for efficient per-user notification queries
    # Use case: Retrieving all notifications for a specific user
    op.create_index(
        'idx_notifications_user_id',
        'notifications',
        ['user_id'],
        if_not_exists=True
    )
    
    # Partial index on unread notifications
    # Only indexed records where is_read = false for optimal performance
    # This reduces index size compared to indexing all records
    op.create_index(
        'idx_notifications_is_read',
        'notifications',
        ['is_read'],
        if_not_exists=True,
        postgresql_where=sa.text('is_read = false')
    )


def downgrade() -> None:
    """Remove supporting table indexes."""
    op.drop_index('idx_notifications_is_read', table_name='notifications', if_exists=True)
    op.drop_index('idx_notifications_user_id', table_name='notifications', if_exists=True)
    op.drop_index('idx_ticket_logs_complaint_id', table_name='ticket_logs', if_exists=True)
