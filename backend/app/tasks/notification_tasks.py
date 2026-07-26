import asyncio
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from celery_worker import celery
from app.config import settings
from app.services.notification_service import create_notification, notify_admins


engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
task_loop = asyncio.new_event_loop()


@celery.task(name="app.tasks.notification_tasks.send_notification_task")
def send_notification_task(
	user_id: str,
	title: str,
	message: str,
	notification_type: str,
	complaint_id: str | None = None,
):
	task_loop.run_until_complete(
		_send_notification(
			user_id=user_id,
			title=title,
			message=message,
			notification_type=notification_type,
			complaint_id=complaint_id,
		)
	)


@celery.task(
	bind=True,
	name="app.tasks.notification_tasks.send_push_notification_task",
	max_retries=3,
	default_retry_delay=5,
)
def send_push_notification_task(
	self,
	user_id: str,
	title: str,
	message: str,
	notification_type: str,
	complaint_id: str | None = None,
):
	try:
		task_loop.run_until_complete(
			_send_notification(
				user_id=user_id,
				title=title,
				message=message,
				notification_type=notification_type,
				complaint_id=complaint_id,
			)
		)
	except Exception as exc:
		raise self.retry(exc=exc)


async def _send_notification(
	user_id: str,
	title: str,
	message: str,
	notification_type: str,
	complaint_id: str | None = None,
):
	async with AsyncSessionLocal() as session:
		await create_notification(
			db=session,
			user_id=UUID(user_id),
			title=title,
			message=message,
			notification_type=notification_type,
			complaint_id=UUID(complaint_id) if complaint_id else None,
		)


@celery.task(name="app.tasks.notification_tasks.notify_admins_task")
def notify_admins_task(
	title: str,
	message: str,
	notification_type: str,
	complaint_id: str | None = None,
):
	task_loop.run_until_complete(
		_notify_admins(
			title=title,
			message=message,
			notification_type=notification_type,
			complaint_id=complaint_id,
		)
	)


async def _notify_admins(
	title: str,
	message: str,
	notification_type: str,
	complaint_id: str | None = None,
):
	async with AsyncSessionLocal() as session:
		await notify_admins(
			db=session,
			title=title,
			message=message,
			notification_type=notification_type,
			complaint_id=UUID(complaint_id) if complaint_id else None,
		)
