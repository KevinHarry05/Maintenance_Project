from celery import Celery
from app.config import settings

broker_url = settings.CELERY_BROKER_URL or settings.REDIS_URL
backend_url = settings.CELERY_RESULT_BACKEND or settings.REDIS_URL

celery = Celery(
    "sbms",
    broker=broker_url,
    backend=backend_url,
    include=[
        "app.tasks.ai_tasks",
        "app.tasks.sla_tasks",
        "app.tasks.notification_tasks",
    ]
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
)

# Optional periodic task scheduler (for SLA checks)
celery.conf.beat_schedule = {
    "check-sla-every-minute": {
        "task": "app.tasks.sla_tasks.check_sla_violations",
        "schedule": 60.0
    },
    "train-ml-models-hourly": {
        "task": "app.tasks.ai_tasks.train_ml_models_task",
        "schedule": 3600.0,
    }
}