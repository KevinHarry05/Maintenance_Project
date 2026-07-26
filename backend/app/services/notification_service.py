"""
Notification Service - Create and manage user notifications.

Performance Notes (Phase 6.4, 6.5):
- list_notifications_for_user() uses joinedload('complaint') to prevent N+1 queries
- Notifications are indexed by user_id for efficient filtering
- All queries are optimized for single execution per request
"""

from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.config import settings
from app.models.notification import Notification
from app.models.user import User
from app.websocket.manager import manager


async def create_notification(
	db: AsyncSession,
	user_id: UUID,
	title: str,
	message: str,
	notification_type: str,
	complaint_id: UUID | None = None,
) -> Notification:
	notification = Notification(
		user_id=user_id,
		complaint_id=complaint_id,
		title=title,
		message=message,
		notification_type=notification_type,
	)
	db.add(notification)
	await db.commit()
	await db.refresh(notification)

	payload = {
		"event": "notification",
		"id": str(notification.id),
		"user_id": str(notification.user_id),
		"title": title,
		"message": message,
		"notification_type": notification_type,
		"complaint_id": str(complaint_id) if complaint_id else None,
		"created_at": notification.created_at.isoformat() if notification.created_at else None,
		"is_read": notification.is_read,
	}

	await manager.send_personal_message(str(user_id), payload)
	await _send_fcm_if_enabled(str(user_id), title, message, payload)
	return notification


async def _send_fcm_if_enabled(user_id: str, title: str, message: str, data: dict) -> None:
	if not settings.FCM_SERVER_KEY:
		return

	device_token = manager.get_device_token(user_id)
	if not device_token:
		return

	headers = {
		"Authorization": f"key={settings.FCM_SERVER_KEY}",
		"Content-Type": "application/json",
	}
	body = {
		"to": device_token,
		"notification": {
			"title": title,
			"body": message,
		},
		"data": data,
	}

	async with httpx.AsyncClient(timeout=10.0) as client:
		await client.post("https://fcm.googleapis.com/fcm/send", json=body, headers=headers)


async def notify_admins(
	db: AsyncSession,
	title: str,
	message: str,
	notification_type: str,
	complaint_id: UUID | None = None,
) -> None:
	result = await db.execute(select(User).where(User.role == "admin"))
	admins = result.scalars().all()

	for admin in admins:
		await create_notification(
			db=db,
			user_id=admin.id,
			title=title,
			message=message,
			notification_type=notification_type,
			complaint_id=complaint_id,
		)


# Phase 6.4: Eager Loading for Notification Queries
async def list_notifications_for_user(
	db: AsyncSession,
	user_id: UUID
) -> list[Notification]:
	"""
	Get all notifications for a user with eager loading.
	
	Uses joinedload('complaint') to load associated complaint in same query,
	preventing N+1 queries when iterating notifications.
	
	Requirement: 7.7
	
	Args:
		db: Async database session
		user_id: ID of user whose notifications to retrieve
		
	Returns:
		List of notifications for user with complaint data loaded
	"""
	query = select(Notification).where(
		Notification.user_id == str(user_id)
	).options(
		joinedload('complaint')  # Load complaint via JOIN to prevent N+1
	).order_by(Notification.created_at.desc())
	
	result = await db.execute(query)
	return result.unique().scalars().all()
