from sqlalchemy import delete, func, select, update

from app.database import AsyncSessionLocal
from app.models.complaint import Complaint
from app.models.notification import Notification
from app.models.ticket_log import TicketLog
from app.models.user import User


async def cleanup_runtime_data() -> dict[str, int]:
    async with AsyncSessionLocal() as db:
        staff_to_worker_result = await db.execute(
            update(User)
            .where(User.role == "staff")
            .values(role="worker")
            .execution_options(synchronize_session=False)
        )

        await db.execute(delete(TicketLog))
        await db.execute(delete(Notification))
        await db.execute(delete(Complaint))
        await db.commit()

        user_counts_result = await db.execute(
            select(User.role, func.count(User.id)).group_by(User.role)
        )
        user_counts = {role: count for role, count in user_counts_result.all()}

    return {
        "converted_staff_to_worker": int(staff_to_worker_result.rowcount or 0),
        "students": int(user_counts.get("student", 0)),
        "workers": int(user_counts.get("worker", 0)),
        "admins": int(user_counts.get("admin", 0)),
    }


if __name__ == "__main__":
    import asyncio

    summary = asyncio.run(cleanup_runtime_data())
    print("Cleanup completed:")
    for key, value in summary.items():
        print(f"- {key}: {value}")
