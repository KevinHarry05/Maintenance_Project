from celery_worker import celery
import asyncio

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.config import settings
from app.models.complaint import Complaint
from app.services.prediction_service import predict_priority_and_category, train_models_from_db


# Async database engine
engine = create_async_engine(settings.DATABASE_URL, echo=False)
task_loop = asyncio.new_event_loop()

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@celery.task(name="app.tasks.ai_tasks.calculate_priority_task")
def calculate_priority_task(complaint_id: str):
    """
    Celery background task to calculate complaint priority
    """
    task_loop.run_until_complete(run_priority_calculation(complaint_id))


@celery.task(name="app.tasks.ai_tasks.train_ml_models_task")
def train_ml_models_task():
    task_loop.run_until_complete(run_model_training())


async def run_model_training():
    async with AsyncSessionLocal() as session:
        trained = await train_models_from_db(session)
        print(f"ML model training completed. trained={trained}")


async def run_priority_calculation(complaint_id: str):
    """
    Async function that performs the priority logic
    """

    async with AsyncSessionLocal() as session:

        result = await session.execute(
            select(Complaint).where(Complaint.id == complaint_id)
        )

        complaint = result.scalar_one_or_none()

        if complaint is None:
            print(f"Complaint {complaint_id} not found")
            return

        score, level, category = await predict_priority_and_category(complaint.title, complaint.description)

        complaint.category = category
        complaint.priority_score = score
        complaint.priority_level = level

        await session.commit()

        print(f"Complaint {complaint_id} priority updated: {level} ({score})")