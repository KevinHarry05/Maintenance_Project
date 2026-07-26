"""extend_user_email_verification

Revision ID: 002_user_email_verify
Revises: 001_token_blacklist
Create Date: 2024-01-15 10:05:00.000000

"""
# Migration runs in context where 'op' is injected by Alembic
# See alembic/env.py for how context is established
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_user_email_verify'
down_revision = '001_token_blacklist'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Extend User model with email verification support.
    
    Changes:
    - Add email_verified column (BOOLEAN, DEFAULT FALSE)
      - New users created with email_verified=FALSE
      - Cannot login until verified
      - Existing users treated as verified (backward compatibility)
    - Add created_at column if missing (for audit trail)
    
    Postconditions:
    - users.email_verified column exists with NOT NULL constraint
    - Existing users have email_verified=TRUE (backward compatible)
    - users.created_at column exists with default=now()
    
    Requirements: 5.4 (Email verification), 4.2 (Token blacklist)
    """
    # Add email_verified column for new user registration flow
    # New registrations will have email_verified=FALSE until verified
    # Existing users are set to TRUE (backward compatibility)
    op.add_column(
        'users',
        sa.Column('email_verified', sa.Boolean(), nullable=False, server_default=sa.literal(False))
    )
    
    # Update existing users to be treated as verified (backward compatibility)
    # This allows the system to function immediately without forcing all users to reverify
    op.execute('UPDATE users SET email_verified = true WHERE email_verified = false')
    
    # Add created_at timestamp column for audit trail if missing
    # Using server_default=func.now() to capture creation time
    try:
        op.add_column(
            'users',
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
        )
    except Exception:
        # Column may already exist from previous migrations
        # This is safe to ignore - the column will be in place either way
        pass


def downgrade() -> None:
    """
    Remove email_verified and created_at columns from users table.
    
    Preconditions:
    - users table exists with email_verified column
    
    Postconditions:
    - email_verified column removed from users table
    - created_at column removed if it exists
    """
    op.drop_column('users', 'email_verified')
    try:
        op.drop_column('users', 'created_at')
    except Exception:
        # Column may not exist, safe to ignore
        # This can happen if created_at was added in a different migration
        pass
