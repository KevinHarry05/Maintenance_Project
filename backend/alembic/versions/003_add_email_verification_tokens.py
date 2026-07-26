"""add_email_verification_tokens

Revision ID: 003_email_verify_tokens
Revises: 002_user_email_verify
Create Date: 2024-01-15 10:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_email_verify_tokens'
down_revision = '002_user_email_verify'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create email_verification_tokens table for temporary token storage."""
    op.create_table(
        'email_verification_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False, unique=True),
        sa.Column('token_hash', sa.String(64), nullable=False, unique=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_email_verify_user_id'),
        sa.UniqueConstraint('token_hash', name='uq_email_verify_token_hash')
    )
    
    # Create indexes for efficient lookup
    op.create_index('idx_email_verify_token_hash', 'email_verification_tokens', ['token_hash'], unique=True)
    op.create_index('idx_email_verify_expires_at', 'email_verification_tokens', ['expires_at'])


def downgrade() -> None:
    """Drop email_verification_tokens table and related indexes."""
    op.drop_index('idx_email_verify_expires_at', table_name='email_verification_tokens')
    op.drop_index('idx_email_verify_token_hash', table_name='email_verification_tokens')
    op.drop_table('email_verification_tokens')
