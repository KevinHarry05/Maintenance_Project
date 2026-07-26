from celery import Celery
from app.config import settings

# Initialize Celery app
celery_app = Celery(
    'app',
    broker=settings.CELERY_BROKER_URL or settings.REDIS_URL,
    backend=settings.CELERY_RESULT_BACKEND or settings.REDIS_URL,
)

# Configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    broker_connection_retry_on_startup=True,
)

# Auto-discover tasks from app.tasks if it exists
try:
    celery_app.autodiscover_tasks(['app.tasks'], force=True)
except ImportError:
    pass


@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for Celery testing"""
    print(f'Request: {self.request!r}')
