import html
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.models.building import Building
from app.models.complaint import Complaint
from app.models.ticket_log import TicketLog
from app.models.user import User
from app.services.priority_service import calculate_priority, detect_category
from app.utils.cache import delete_cache

# PERFORMANCE NOTES (Phase 6: Performance Optimization)
# =======================================================
# This service manages complaint queries with careful attention to N+1 query prevention.
#
# Query Optimization Strategy:
# 1. joinedload('created_by'): Load user via SQL JOIN (single query for one-to-one)
# 2. joinedload('assigned_worker'): Load worker via SQL JOIN
# 3. selectinload('notifications'): Load notifications in separate query (prevents N+1 for collections)
# 4. selectinload('ticket_logs'): Load ticket logs in separate query
#
# Key Methods:
# - create_complaint_record(): Creates complaint with initial relationships loaded
# - assign_worker_to_complaint(): Updates assignment
# - update_complaint_status_record(): Updates status with logging
#
# Indexed Queries (use indexes for performance):
# - Complaints by status: indexed on status column
# - Complaints by assigned_to: indexed on assigned_to column
# - Complaints by user_id: indexed on user_id column
# - Ticket logs by complaint_id: indexed on complaint_id column
# =======================================================

OPEN_STATUSES = ["pending", "assigned", "in_progress"]
WORKER_STATUS_TRANSITIONS = {"assigned": {"in_progress"}}


# Phase 6.2-6.3: Eager Loading Helper Methods for Preventing N+1 Queries
def _apply_complaint_eager_loading(query):
	"""
	Apply eager loading strategies to complaint queries.
	
	Uses:
	- joinedload for one-to-one relationships (created_by, assigned_worker)
	- selectinload for one-to-many relationships (notifications, ticket_logs)
	
	Requirement: 7.1, 7.5, 7.6
	"""
	return query.options(
		joinedload('created_by'),
		joinedload('assigned_worker'),
		selectinload('notifications'),
		selectinload('ticket_logs')
	)


async def get_complaint_by_id_with_relations(db: AsyncSession, complaint_id: str | UUID) -> Complaint | None:
	"""
	Get complaint by ID with all related data eagerly loaded.
	
	Prevents N+1 queries by eager loading:
	- created_by user (one-to-one)
	- assigned_worker user (one-to-one)
	- notifications (one-to-many)
	- ticket_logs (one-to-many)
	
	Requirements: 7.1, 7.5, 7.6
	
	Args:
		db: Async database session
		complaint_id: UUID or string ID of complaint
		
	Returns:
		Complaint with all relations loaded, or None if not found
	"""
	query = _apply_complaint_eager_loading(
		select(Complaint).where(Complaint.id == str(complaint_id))
	)
	result = await db.execute(query)
	return result.unique().scalar_one_or_none()


async def list_complaints_with_relations(
	db: AsyncSession,
	filters: dict | None = None
) -> list[Complaint]:
	"""
	List complaints with all related data eagerly loaded.
	
	Prevents N+1 queries by eager loading relationships in two additional queries
	instead of one query per complaint.
	
	Requirements: 7.2, 7.3, 7.4
	
	Args:
		db: Async database session
		filters: Optional dict with filter criteria (status, assigned_to, etc.)
		
	Returns:
		List of complaints with all relations loaded
	"""
	query = select(Complaint)
	
	if filters:
		if status := filters.get('status'):
			query = query.where(Complaint.status == status)
		if assigned_to := filters.get('assigned_to'):
			query = query.where(Complaint.assigned_to == assigned_to)
		if user_id := filters.get('user_id'):
			query = query.where(Complaint.user_id == user_id)
	
	query = _apply_complaint_eager_loading(query)
	result = await db.execute(query)
	return result.unique().scalars().all()


async def create_ticket_log(
	db: AsyncSession,
	complaint_id: UUID,
	updated_by: UUID,
	old_status: str,
	new_status: str,
) -> None:
	db.add(
		TicketLog(
			complaint_id=complaint_id,
			updated_by=updated_by,
			old_status=old_status,
			new_status=new_status,
		)
	)


async def validate_building_exists(db: AsyncSession, building_id: UUID) -> None:
	# IDs are stored in VARCHAR columns.  Bind UUID inputs as their canonical
	# hyphenated string representation; SQLite otherwise removes hyphens while
	# adapting a UUID and cannot find the stored record.
	result = await db.execute(select(Building).where(Building.id == str(building_id)))
	building = result.scalar_one_or_none()
	if not building:
		raise HTTPException(status_code=404, detail="Building not found")


async def get_lowest_workload_worker_id(db: AsyncSession) -> UUID | None:
	worker_result = await db.execute(
		select(User).where(User.role == "worker").order_by(User.created_at.desc())
	)
	workers = worker_result.scalars().all()
	if not workers:
		return None

	selected_worker_id = None
	min_workload = None

	for worker in workers:
		workload_result = await db.execute(
			select(func.count(Complaint.id)).where(
				Complaint.assigned_to == worker.id,
				Complaint.status.in_(OPEN_STATUSES),
			)
		)
		workload = workload_result.scalar_one()

		if min_workload is None or workload < min_workload:
			min_workload = workload
			selected_worker_id = worker.id

	return selected_worker_id


async def create_complaint_record(
	db: AsyncSession,
	title: str,
	description: str,
	building_id: UUID,
	floor_number: str,
	room_number: str,
	user_id: UUID,
	category: str | None = None,
	file_path: str | None = None,
) -> Complaint:
	await validate_building_exists(db, building_id)

	safe_title = html.escape(title or "", quote=True)
	safe_description = html.escape(description or "", quote=True)

	final_category = category or detect_category(safe_title, safe_description)
	priority_score, priority_level = calculate_priority(safe_title, safe_description, final_category)
	# Assignment is an explicit administrator decision so that expertise,
	# availability, and the AI recommendation can be reviewed first.
	auto_worker_id = None
	initial_status = "pending"

	complaint = Complaint(
		title=safe_title,
		description=safe_description,
		category=final_category,
		file_path=file_path,
		building_id=str(building_id),
		floor_number=floor_number.strip(),
		room_number=room_number.strip(),
		user_id=user_id,
		assigned_to=auto_worker_id,
		status=initial_status,
		priority_score=priority_score,
		priority_level=priority_level,
	)

	db.add(complaint)
	await db.flush()

	await create_ticket_log(
		db=db,
		complaint_id=complaint.id,
		updated_by=user_id,
		old_status="none",
		new_status="created",
	)

	if auto_worker_id:
		await create_ticket_log(
			db=db,
			complaint_id=complaint.id,
			updated_by=user_id,
			old_status="pending",
			new_status="assigned",
		)

	await db.commit()
	await db.refresh(complaint)
	delete_cache("complaints:my:*")
	delete_cache("complaints:assigned:*")
	delete_cache("complaints:all")
	return complaint


async def assign_worker_to_complaint(
	db: AsyncSession,
	complaint: Complaint,
	worker_id: UUID,
	admin_user_id: UUID,
) -> User:
	result = await db.execute(select(User).where(User.id == str(worker_id)))
	worker = result.scalar_one_or_none()

	if not worker or worker.role != "worker":
		raise HTTPException(status_code=400, detail="Invalid worker")

	old_status = complaint.status
	complaint.assigned_to = worker.id
	complaint.status = "assigned"

	await create_ticket_log(
		db=db,
		complaint_id=complaint.id,
		updated_by=admin_user_id,
		old_status=old_status,
		new_status="assigned",
	)

	await db.commit()
	delete_cache("complaints:my:*")
	delete_cache("complaints:assigned:*")
	delete_cache("complaints:all")
	return worker


async def update_complaint_status_record(
	db: AsyncSession,
	complaint: Complaint,
	new_status: str,
	worker_user_id: UUID,
) -> None:
	if complaint.assigned_to != worker_user_id:
		raise HTTPException(status_code=403, detail="Not assigned to you")
	if new_status not in WORKER_STATUS_TRANSITIONS.get(complaint.status, set()):
		raise HTTPException(
			status_code=400,
			detail=f"Cannot change status from '{complaint.status}' to '{new_status}'",
		)

	old_status = complaint.status
	complaint.status = new_status

	await create_ticket_log(
		db=db,
		complaint_id=complaint.id,
		updated_by=worker_user_id,
		old_status=old_status,
		new_status=new_status,
	)

	await db.commit()
	delete_cache("complaints:my:*")
	delete_cache("complaints:assigned:*")
	delete_cache("complaints:all")
