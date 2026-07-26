from celery_worker import celery
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from datetime import datetime, timedelta

from app.models.complaint import Complaint
from app.config import settings
from app.tasks.task_dispatch import safe_dispatch_task


engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
task_loop = asyncio.new_event_loop()


@celery.task(name="app.tasks.sla_tasks.check_sla_violations")
def check_sla_violations():
    task_loop.run_until_complete(run_sla_check())


async def run_sla_check():
    from app.tasks.notification_tasks import notify_admins_task, send_notification_task

    async with AsyncSessionLocal() as session:

        result = await session.execute(
            select(Complaint).where(Complaint.status == "pending")
        )

        complaints = result.scalars().all()

        now = datetime.utcnow()

        escalated_24h = 0
        escalated_72h = 0

        for complaint in complaints:
            complaint_age = now - complaint.created_at.replace(tzinfo=None)

            if complaint_age >= timedelta(hours=24):
                complaint.priority_level = "High"
                complaint.priority_score = max(float(complaint.priority_score or 0), 0.75)
                escalated_24h += 1

            if complaint_age >= timedelta(hours=48):
                safe_dispatch_task(
                    notify_admins_task,
                    title="SLA warning (48h)",
                    message=f"Complaint {complaint.id} has been pending for over 48 hours.",
                    notification_type="sla_warning",
                    complaint_id=str(complaint.id),
                )

            if complaint_age >= timedelta(hours=72):
                complaint.status = "escalated"
                complaint.priority_level = "Critical"
                complaint.priority_score = 1.0
                escalated_72h += 1

                safe_dispatch_task(
                    send_notification_task,
                    user_id=str(complaint.user_id),
                    title="Complaint auto-escalated",
                    message="Your complaint has been auto-escalated due to SLA breach.",
                    notification_type="sla_critical",
                    complaint_id=str(complaint.id),
                )

        await session.commit()

        print(
            "SLA check completed. "
            f"24h adjusted: {escalated_24h}, 72h auto-escalated: {escalated_72h}"
        )