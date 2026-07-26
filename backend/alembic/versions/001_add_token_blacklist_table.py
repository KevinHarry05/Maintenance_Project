"""add_token_blacklist_table

Revision ID: 001_token_blacklist
Revises: f6a7b8c9d0e1
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '001_token_blacklist'
down_revision = 'f6a7b8c9d0e1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create token_blacklist table for persistent revocation storage."""
    op.create_table(
        'token_blacklist',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('token_hash', sa.String(64), nullable=False, unique=True),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('revocation_reason', sa.String(255), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash', name='uq_token_blacklist_token_hash')
    )
    
    # Create indexes for O(1) lookup performance
    op.create_index('idx_token_blacklist_token_hash', 'token_blacklist', ['token_hash'], unique=True)
    op.create_index('idx_token_blacklist_user_id', 'token_blacklist', ['user_id'])
    op.create_index('idx_token_blacklist_expires_at', 'token_blacklist', ['expires_at'])


def downgrade() -> None:
    """Drop token_blacklist table and related indexes."""
    op.drop_index('idx_token_blacklist_expires_at', table_name='token_blacklist')
    op.drop_index('idx_token_blacklist_user_id', table_name='token_blacklist')
    op.drop_index('idx_token_blacklist_token_hash', table_name='token_blacklist')
    op.drop_table('token_blacklist')
