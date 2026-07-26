"""add_complaint_performance_indexes

Requirement 6: Database Performance - Query Indexes

This migration creates performance indexes for complaint query optimization.
These indexes support the following use cases:

1. Filtering complaints by status (e.g., GET /complaints?status=OPEN)
   - Uses idx_complaints_status on complaints.status
   
2. Finding complaints assigned to a specific worker
   - Uses idx_complaints_assigned_to on complaints.assigned_to
   
3. Temporal filtering and sorting by creation date
   - Uses idx_complaints_created_at on complaints.created_at (descending)
   
4. Combined filtering by status and date (most common query pattern)
   - Uses idx_complaints_status_created composite index on (status, created_at)

Without these indexes, complaint queries would perform full table scans, resulting in
O(n) performance degradation as the complaints table grows. With indexes:
- Single-column filters: O(log n) via B-tree index
- Composite filters: O(log n) via composite B-tree index
- Sorting: Optimized by DESC index on created_at

Indexes follow naming convention: idx_{table}_{column(s)}

Revision ID: 004_complaint_indexes
Revises: 003_email_verify_tokens
Create Date: 2024-01-15 10:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004_complaint_indexes'
down_revision = '003_email_verify_tokens'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create performance indexes for complaint queries.
    
    These indexes optimize:
    - Filtering by status: GET /complaints?status=OPEN
    - Finding complaints for assigned worker: GET /complaints?assigned_to=worker-id
    - Temporal filtering and sorting: GET /complaints?created_after=2024-01-01
    - Composite queries: Most common filter combinations
    
    Indexes created:
    1. idx_complaints_status: Filters complaints by status column
    2. idx_complaints_assigned_to: Finds complaints assigned to specific worker
    3. idx_complaints_created_at: Temporal filtering and sorting by creation date
    4. idx_complaints_status_created: Composite index for common filter combinations
    """
    # Index on status for filtering complaints by state
    # Supports: WHERE status = 'OPEN' queries
    op.create_index('idx_complaints_status', 'complaints', ['status'])
    
    # Index on assigned_to (worker) for finding assigned complaints
    # Supports: WHERE assigned_to = 'worker-id' queries
    op.create_index('idx_complaints_assigned_to', 'complaints', ['assigned_to'])
    
    # Index on created_at descending for temporal queries and sorting
    # Supports: ORDER BY created_at DESC queries
    op.create_index(
        'idx_complaints_created_at',
        'complaints',
        ['created_at'],
        postgresql_using='btree',
        postgresql_ops={'created_at': 'DESC'}
    )
    
    # Composite index for common filter combinations (status + date)
    # Supports: WHERE status = 'OPEN' AND created_at > '2024-01-01' queries
    op.create_index(
        'idx_complaints_status_created',
        'complaints',
        ['status', 'created_at'],
        postgresql_using='btree'
    )


def downgrade() -> None:
    """Remove all complaint performance indexes."""
    op.drop_index('idx_complaints_status_created', table_name='complaints')
    op.drop_index('idx_complaints_created_at', table_name='complaints')
    op.drop_index('idx_complaints_assigned_to', table_name='complaints')
    op.drop_index('idx_complaints_status', table_name='complaints')
