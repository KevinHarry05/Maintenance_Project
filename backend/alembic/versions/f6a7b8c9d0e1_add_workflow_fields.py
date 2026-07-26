"""Add complaint lifecycle, location, and feedback fields.

Revision ID: f6a7b8c9d0e1
Revises: a1b2c3d4e5f6
"""

from alembic import op
import sqlalchemy as sa

revision = "f6a7b8c9d0e1"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("complaints", sa.Column("floor_number", sa.String(), nullable=False, server_default="Unknown"))
    op.add_column("complaints", sa.Column("room_number", sa.String(), nullable=False, server_default="Unknown"))
    op.add_column("complaints", sa.Column("worker_remarks", sa.Text(), nullable=True))
    op.add_column("complaints", sa.Column("admin_remarks", sa.Text(), nullable=True))
    op.add_column("complaints", sa.Column("feedback_rating", sa.Integer(), nullable=True))
    op.add_column("complaints", sa.Column("feedback_comment", sa.Text(), nullable=True))
    op.add_column("complaints", sa.Column("admin_verified", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("complaints", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("complaints", sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    for column in ("closed_at", "completed_at", "admin_verified", "feedback_comment", "feedback_rating", "admin_remarks", "worker_remarks", "room_number", "floor_number"):
        op.drop_column("complaints", column)
