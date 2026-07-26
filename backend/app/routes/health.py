from fastapi import APIRouter
from sqlalchemy import text

from app.config import settings
from app.database import AsyncSessionLocal
from celery_worker import celery

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
	database_status = "disconnected"
	redis_status = "disconnected"
	celery_status = "unreachable"

	try:
		async with AsyncSessionLocal() as session:
			await session.execute(text("SELECT 1"))
		database_status = "connected"
	except Exception:
		database_status = "disconnected"

	try:
		redis_client = celery.backend.client
		redis_client.ping()
		redis_status = "connected"
	except Exception:
		try:
			broker_connection = celery.connection_for_read(connect_timeout=1.0)
			with broker_connection as connection:
				connection.ensure_connection(max_retries=0)
			redis_status = "connected"
		except Exception:
			redis_status = "disconnected"

	if settings.ENABLE_CELERY_HEALTH_CHECK:
		try:
			inspect = celery.control.inspect(timeout=0.5)
			ping_result = inspect.ping() if inspect else None
			if ping_result:
				celery_status = "online"
			else:
				celery_status = "offline"
		except Exception:
			celery_status = "offline"
	else:
		celery_status = "skipped"

	overall_status = "healthy" if database_status == "connected" and redis_status == "connected" else "degraded"

	return {
		"status": overall_status,
		"database": database_status,
		"redis": redis_status,
		"celery": celery_status,
		"redis_url": settings.REDIS_URL,
	}
