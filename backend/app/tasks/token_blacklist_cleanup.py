"""Token Blacklist Cleanup Task - Scheduled daily removal of expired tokens.

This task runs daily (default 02:00 UTC, configurable via TOKEN_BLACKLIST_CLEANUP_HOUR)
to remove expired entries from the token_blacklist table. This prevents the table
from growing unbounded and maintains performance.

Scheduling:
- Uses APScheduler for reliable task scheduling
- Runs in background without blocking API requests
- Automatically restarts with application
- Logs all executions for audit trail
"""

import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from app.services.token_blacklist_repository import TokenBlacklistRepository

logger = logging.getLogger(__name__)


async def cleanup_expired_tokens_task() -> None:
    """
    Clean up expired tokens from the blacklist table.

    This task is scheduled to run daily at configured time (default 02:00 UTC).
    It removes all TokenBlacklist entries where the original JWT has expired.

    Precondition:
        - Database is accessible and responsive
        - AsyncSessionLocal is properly configured

    Postcondition:
        - All expired TokenBlacklist entries are deleted from database
        - Cleanup time and count are logged
        - Task execution is recorded in logs for audit trail

    Raises:
        No exceptions are raised; errors are logged and handled gracefully
    """
    try:
        logger.info("Starting token blacklist cleanup task")

        async with AsyncSessionLocal() as db:
            # Execute cleanup
            deleted_count = await TokenBlacklistRepository.cleanup_expired_tokens(db)

            logger.info(
                "Token blacklist cleanup completed",
                deleted_count=deleted_count,
                execution_time=datetime.now(timezone.utc).isoformat()
            )

    except Exception as e:
        logger.error(
            "Token blacklist cleanup failed",
            error=str(e),
            execution_time=datetime.now(timezone.utc).isoformat()
        )
        # Don't raise - allow application to continue even if cleanup fails


def schedule_token_cleanup_task(scheduler) -> None:
    """
    Schedule the token cleanup task to run daily.

    Args:
        scheduler: APScheduler scheduler instance (from app startup)

    Postcondition:
        - Task is scheduled to run daily at TOKEN_BLACKLIST_CLEANUP_HOUR (UTC)
        - Task runs indefinitely until application shutdown
    """
    from app.config import settings

    cleanup_hour = settings.TOKEN_BLACKLIST_CLEANUP_HOUR

    try:
        # Schedule daily cleanup at configured hour
        scheduler.add_job(
            cleanup_expired_tokens_task,
            'cron',
            hour=cleanup_hour,
            minute=0,
            second=0,
            timezone='UTC',
            id='token_blacklist_cleanup',
            name='Token Blacklist Cleanup',
            replace_existing=True,
            misfire_grace_time=60  # Allow 60 second grace period if missed
        )

        logger.info(
            "Token blacklist cleanup scheduled",
            cleanup_hour=cleanup_hour,
            timezone="UTC"
        )
    except Exception as e:
        logger.error(
            "Failed to schedule token blacklist cleanup",
            error=str(e)
        )
        # Don't raise - allow application to start even if scheduling fails


# Sync wrapper for use with standard APScheduler
def cleanup_expired_tokens_sync() -> None:
    """Synchronous wrapper for async cleanup task (for APScheduler compatibility)."""
    import asyncio

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    loop.run_until_complete(cleanup_expired_tokens_task())
