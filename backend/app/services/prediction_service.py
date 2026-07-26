from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.complaint import Complaint
from app.services.ml_prediction_service import MLPredictionSingleton


async def train_models_from_db(db: AsyncSession) -> bool:
	result = await db.execute(
		select(Complaint).where(
			Complaint.priority_level.is_not(None),
			Complaint.category.is_not(None),
		)
	)
	complaints = result.scalars().all()

	texts = [f"{complaint.title} {complaint.description}" for complaint in complaints]
	priorities = [complaint.priority_level for complaint in complaints]
	categories = [complaint.category for complaint in complaints]

	return MLPredictionSingleton.instance().train(texts, priorities, categories)


async def predict_priority_and_category(title: str, description: str) -> tuple[float, str, str]:
	model = MLPredictionSingleton.instance()
	return model.predict(title, description)
