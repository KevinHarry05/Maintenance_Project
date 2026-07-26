from app.core.logger import get_logger

logger = get_logger("sbms.tasks")


def safe_dispatch_task(task, *args, **kwargs) -> bool:
    try:
        task.delay(*args, **kwargs)
        return True
    except Exception as exc:
        logger.warning("task.dispatch_failed task=%s error=%s", getattr(task, "name", str(task)), str(exc))
        return False
