from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from pydantic import ValidationError

from app.config import settings
from app.core.rate_limit import limiter
from app.database import get_db
from app.models.complaint import Complaint
from app.models.ticket_log import TicketLog
from app.models.user import User
from app.dependencies.role_dependency import require_role
from app.schemas.complaint_schema import (
    ComplaintCreate,
    ComplaintResponse,
    ComplaintUpdate,
    ComplaintAssign,
    ComplaintCompletion,
    ComplaintFeedback,
    ComplaintReview,
)
from app.services.complaint_service import (
    assign_worker_to_complaint,
    create_complaint_record,
    update_complaint_status_record,
)
from app.tasks.notification_tasks import send_notification_task
from app.websocket.manager import manager
from app.tasks.ai_tasks import calculate_priority_task
from app.tasks.task_dispatch import safe_dispatch_task
from app.utils.file_handler import save_complaint_file
from app.utils.cache import get_cache, set_cache, delete_cache

router = APIRouter(prefix="/complaints", tags=["Complaints"])


async def _parse_complaint_request(request: Request) -> tuple[ComplaintCreate, UploadFile | None]:
    content_type = request.headers.get("content-type", "")

    if "multipart/form-data" in content_type:
        form = await request.form()
        payload = {
            "title": form.get("title"),
            "description": form.get("description"),
            "building_id": form.get("building_id"),
            "floor_number": form.get("floor_number"),
            "room_number": form.get("room_number"),
            "category": form.get("category"),
        }
        file = form.get("file")
        try:
            validated = ComplaintCreate(**payload)
            return validated, file
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=exc.errors()) from exc

    body = await request.json()
    try:
        validated = ComplaintCreate(**body)
        return validated, None
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc


# =====================================================
# STUDENT → CREATE COMPLAINT (Async Priority via Celery)
# =====================================================
@router.post("", response_model=ComplaintResponse)
@limiter.limit("10/day")
async def create_complaint(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("student")),
):
    complaint_request, file = await _parse_complaint_request(request)
    file_path = await save_complaint_file(file, settings.COMPLAINT_UPLOAD_DIR)

    complaint = await create_complaint_record(
        db=db,
        title=complaint_request.title,
        description=complaint_request.description,
        building_id=complaint_request.building_id,

        floor_number=complaint_request.floor_number,
        room_number=complaint_request.room_number,
        user_id=current_user.id,
        category=complaint_request.category,
        file_path=file_path,
    )

    # Trigger background AI scoring
    safe_dispatch_task(calculate_priority_task, str(complaint.id))

    delete_cache("complaints:my:*")
    delete_cache("complaints:assigned:*")
    delete_cache("complaints:all")

    if complaint.assigned_to:
        safe_dispatch_task(
            send_notification_task,
            user_id=str(complaint.assigned_to),
            title="New complaint assigned",
            message=f"Complaint '{complaint.title}' has been auto-assigned to you.",
            notification_type="assigned",
            complaint_id=str(complaint.id),
        )

    # Real-time notify admin dashboard
    await manager.broadcast(
        {
            "event": "new_complaint",
            "complaint_id": str(complaint.id),
        }
    )

    return complaint


# =====================================================
# STUDENT → VIEW OWN COMPLAINTS
# =====================================================
@router.get("/my", response_model=list[ComplaintResponse])
async def get_my_complaints(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("student")),
):
    cache_key = f"complaints:my:{current_user.id}"
    cached = get_cache(cache_key)
    if cached is not None:
        return cached

    result = await db.execute(
        select(Complaint).where(Complaint.user_id == current_user.id)
    )
    complaints = result.scalars().all()
    encoded = jsonable_encoder(complaints)
    set_cache(cache_key, encoded, ttl=300)
    return complaints


# =====================================================
# ADMIN → VIEW ALL COMPLAINTS
# =====================================================
@router.get("/all", response_model=list[ComplaintResponse])
async def get_all_complaints(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    cache_key = "complaints:all"
    cached = get_cache(cache_key)
    if cached is not None:
        return cached

    result = await db.execute(select(Complaint))
    complaints = result.scalars().all()
    encoded = jsonable_encoder(complaints)
    set_cache(cache_key, encoded, ttl=300)
    return complaints


# =====================================================
# ADMIN → ASSIGN WORKER
# =====================================================
@router.put("/{complaint_id}/assign")
async def assign_worker(
    complaint_id: UUID,
    request: ComplaintAssign,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    result = await db.execute(
        select(Complaint).where(Complaint.id == str(complaint_id))
    )
    complaint = result.scalar_one_or_none()

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    worker = await assign_worker_to_complaint(
        db=db,
        complaint=complaint,
        worker_id=request.assignee_id,
        admin_user_id=current_user.id,
    )

    safe_dispatch_task(
        send_notification_task,
        user_id=str(worker.id),
        title="Complaint assigned",
        message=f"Complaint '{complaint.title}' has been assigned to you.",
        notification_type="assigned",
        complaint_id=str(complaint.id),
    )

    safe_dispatch_task(
        send_notification_task,
        user_id=str(complaint.user_id),
        title="Complaint assignment update",
        message="Your complaint has been assigned to a maintenance worker.",
        notification_type="status_change",
        complaint_id=str(complaint.id),
    )

    # Real-time notify assigned worker
    await manager.send_personal_message(
        str(worker.id),
        {
            "event": "assigned_complaint",
            "complaint_id": str(complaint.id),
        },
    )

    delete_cache("complaints:assigned:*")
    delete_cache("complaints:all")
    delete_cache("complaints:my:*")

    return {"message": "Complaint assigned successfully"}


# =====================================================
# WORKER → VIEW ASSIGNED COMPLAINTS
# =====================================================
@router.get("/assigned", response_model=list[ComplaintResponse])
async def get_assigned_complaints(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("worker")),
):
    cache_key = f"complaints:assigned:{current_user.id}"
    cached = get_cache(cache_key)
    if cached is not None:
        return cached

    result = await db.execute(
        select(Complaint).where(Complaint.assigned_to == current_user.id)
    )
    complaints = result.scalars().all()
    encoded = jsonable_encoder(complaints)
    set_cache(cache_key, encoded, ttl=300)
    return complaints


# =====================================================
# WORKER → UPDATE STATUS
# =====================================================
@router.put("/{complaint_id}/status")
async def update_status(
    complaint_id: UUID,
    request: ComplaintUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("worker")),
):
    result = await db.execute(
        select(Complaint).where(Complaint.id == str(complaint_id))
    )
    complaint = result.scalar_one_or_none()

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    await update_complaint_status_record(
        db=db,
        complaint=complaint,
        new_status=request.status,
        worker_user_id=current_user.id,
    )

    safe_dispatch_task(
        send_notification_task,
        user_id=str(complaint.user_id),
        title="Complaint status updated",
        message=f"Complaint '{complaint.title}' moved to '{request.status}'.",
        notification_type="status_change",
        complaint_id=str(complaint.id),
    )

    if request.status == "resolved":
        safe_dispatch_task(
            send_notification_task,
            user_id=str(complaint.user_id),
            title="Complaint resolved",
            message=f"Complaint '{complaint.title}' has been resolved.",
            notification_type="resolved",
            complaint_id=str(complaint.id),
        )

    delete_cache("complaints:assigned:*")
    delete_cache("complaints:all")
    delete_cache("complaints:my:*")

    # Real-time notify student
    await manager.send_personal_message(
        str(complaint.user_id),
        {
            "event": "status_updated",
            "complaint_id": str(complaint.id),
            "new_status": request.status,
        },
    )

    return {"message": "Status updated successfully"}


# =====================================================
# STUDENT → ESCALATE COMPLAINT TO ADMIN
# =====================================================
@router.post("/{complaint_id}/escalate")
async def escalate_complaint(
    complaint_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("student")),
):
    result = await db.execute(select(Complaint).where(Complaint.id == str(complaint_id)))
    complaint = result.scalar_one_or_none()

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    if complaint.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only escalate your own complaints")

    if complaint.status != "resolved":
        raise HTTPException(status_code=400, detail="Only resolved complaints can be escalated")

    # Update status directly (student is not the assigned worker, skip the assigned_to guard)
    old_status = complaint.status
    complaint.status = "escalated"
    db.add(TicketLog(
        complaint_id=complaint.id,
        updated_by=current_user.id,
        old_status=old_status,
        new_status="escalated",
    ))
    await db.commit()

    # Notify all admins
    admin_result = await db.execute(select(User).where(User.role == "admin"))
    admins = admin_result.scalars().all()
    for admin in admins:
        safe_dispatch_task(
            send_notification_task,
            user_id=str(admin.id),
            title="Complaint escalated",
            message=f"Complaint '{complaint.title}' was escalated by the student for further review.",
            notification_type="escalated",
            complaint_id=str(complaint.id),
        )

    delete_cache("complaints:my:*")
    delete_cache("complaints:assigned:*")
    delete_cache("complaints:all")

    return {"message": "Complaint escalated to admin successfully"}


# =====================================================
# STUDENT → CANCEL ESCALATION (revert to resolved)
# =====================================================
@router.post("/{complaint_id}/cancel-escalation")
async def cancel_escalation(
    complaint_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("student")),
):
    result = await db.execute(select(Complaint).where(Complaint.id == str(complaint_id)))
    complaint = result.scalar_one_or_none()

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    if complaint.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only cancel escalation on your own complaints")

    if complaint.status != "escalated":
        raise HTTPException(status_code=400, detail="Complaint is not currently escalated")

    old_status = complaint.status
    complaint.status = "resolved"
    db.add(TicketLog(
        complaint_id=complaint.id,
        updated_by=current_user.id,
        old_status=old_status,
        new_status="resolved",
    ))
    await db.commit()

    delete_cache("complaints:my:*")
    delete_cache("complaints:assigned:*")
    delete_cache("complaints:all")

    return {"message": "Escalation cancelled. Complaint marked as resolved."}


# =====================================================
# WORKER → RESOLVE WITH OPTIONAL IMAGE
# =====================================================
# WORKER → RESOLVE WITH OPTIONAL IMAGE (Phase 4.1: File Upload Security)
# =====================================================
@router.post("/{complaint_id}/upload-resolution")
async def upload_resolution(
    complaint_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("worker")),
):
    """
    Upload resolution proof for a complaint.
    
    Security Requirements: 3.1-3.9
    - Validates file extension, MIME type, size, and magic numbers
    - Generates secure filename
    - Prevents path traversal attacks
    """
    from app.services.file_validator import FileValidator
    from app.core.logger import get_logger
    import os
    
    logger = get_logger("sbms.complaints")
    
    # Parse completion remarks and optional proof image from multipart.
    file = None
    remarks = ""
    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" in content_type:
        form = await request.form()
        file = form.get("file") or None
        remarks = str(form.get("remarks") or "").strip()

    result = await db.execute(select(Complaint).where(Complaint.id == str(complaint_id)))
    complaint = result.scalar_one_or_none()

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    if complaint.assigned_to != current_user.id:
        raise HTTPException(status_code=403, detail="Not assigned to you")
    if complaint.status != "in_progress":
        raise HTTPException(status_code=400, detail="Only in-progress complaints can be completed")
    if not remarks:
        raise HTTPException(status_code=422, detail="Completion remarks are required")

    # Phase 4.1: Validate and securely store uploaded file
    resolution_path = None
    if file:
        try:
            # 1. Validate filename (Phase 4.1)
            FileValidator.validate_filename(file.filename)
            
            # 2. Validate extension (Phase 4.1)
            FileValidator.validate_extension(file.filename)
            
            # 3. Validate MIME type (Phase 4.1)
            FileValidator.validate_mime_type(file.content_type, os.path.splitext(file.filename)[1].lower())
            
            # 4. Read file content for size and magic number checks
            file_content = await file.read()
            
            # 5. Validate file size (Phase 4.1)
            FileValidator.validate_file_size(len(file_content))
            
            # 6. Validate magic numbers (Phase 4.1)
            FileValidator.validate_magic_numbers(file_content, os.path.splitext(file.filename)[1].lower())
            
            # Generate secure filename
            secure_filename = FileValidator.generate_secure_filename(file.filename)
            
            # Save file to disk
            os.makedirs(settings.COMPLAINT_UPLOAD_DIR, exist_ok=True)
            file_path = os.path.join(settings.COMPLAINT_UPLOAD_DIR, secure_filename)
            
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            resolution_path = file_path
            
            logger.info(
                "File uploaded successfully",
                complaint_id=str(complaint_id),
                original_filename=file.filename,
                secure_filename=secure_filename,
                file_size=len(file_content)
            )
            
        except Exception as e:
            error_msg = str(e)
            logger.warning(
                "File upload rejected",
                complaint_id=str(complaint_id),
                filename=file.filename,
                error=error_msg
            )
            raise HTTPException(status_code=400, detail=f"File upload failed: {error_msg}")
    
    # Save completion proof before updating the lifecycle state.
    if resolution_path:
        complaint.resolution_file_path = resolution_path

    old_status = complaint.status
    complaint.worker_remarks = remarks
    complaint.status = "completed"
    complaint.completed_at = datetime.now(timezone.utc)
    db.add(TicketLog(
        complaint_id=complaint.id,
        updated_by=current_user.id,
        old_status=old_status,
        new_status="completed",
    ))
    await db.commit()

    safe_dispatch_task(
        send_notification_task,
        user_id=str(complaint.user_id),
        title="Complaint completed",
        message=f"Work on '{complaint.title}' is complete and awaiting administrator verification.",
        notification_type="completed",
        complaint_id=str(complaint.id),
    )

    await manager.send_personal_message(
        str(complaint.user_id),
        {
            "event": "status_updated",
            "complaint_id": str(complaint.id),
            "new_status": "completed",
        },
    )

    delete_cache("complaints:assigned:*")
    delete_cache("complaints:all")
    delete_cache("complaints:my:*")

    return {"message": "Complaint completed and submitted for administrator verification"}


# =====================================================
# ADMIN → FORCE RESOLVE / CLOSE ESCALATION
# =====================================================
@router.put("/{complaint_id}/review")
async def review_completed_complaint(
    complaint_id: UUID,
    request: ComplaintReview,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    result = await db.execute(select(Complaint).where(Complaint.id == str(complaint_id)))
    complaint = result.scalar_one_or_none()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    if complaint.status != "completed":
        raise HTTPException(status_code=400, detail="Only completed complaints can be reviewed")

    complaint.admin_remarks = request.remarks.strip() if request.remarks else None
    old_status = complaint.status
    if request.approved:
        complaint.admin_verified = True
        message = "Completion approved. The student can now provide feedback and close the complaint."
    else:
        complaint.admin_verified = False
        complaint.status = "assigned"
        message = "Complaint reopened and reassigned for further work."
    db.add(TicketLog(
        complaint_id=complaint.id,
        updated_by=current_user.id,
        old_status=old_status,
        new_status="verified" if request.approved else "assigned",
    ))
    await db.commit()
    delete_cache("complaints:my:*")
    delete_cache("complaints:assigned:*")
    delete_cache("complaints:all")
    safe_dispatch_task(
        send_notification_task,
        user_id=str(complaint.user_id),
        title="Repair verified" if request.approved else "Additional work required",
        message=message,
        notification_type="verified" if request.approved else "reopened",
        complaint_id=str(complaint.id),
    )
    return {"message": message}


@router.put("/{complaint_id}/feedback")
async def submit_feedback(
    complaint_id: UUID,
    request: ComplaintFeedback,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("student")),
):
    if not 1 <= request.rating <= 5:
        raise HTTPException(status_code=422, detail="Rating must be between 1 and 5")
    result = await db.execute(select(Complaint).where(Complaint.id == str(complaint_id)))
    complaint = result.scalar_one_or_none()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    if complaint.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only provide feedback for your own complaint")
    if complaint.status != "completed" or not complaint.admin_verified:
        raise HTTPException(status_code=400, detail="Feedback is available after administrator verification")

    complaint.feedback_rating = request.rating
    complaint.feedback_comment = request.comment.strip() if request.comment else None
    complaint.status = "closed"
    complaint.closed_at = datetime.now(timezone.utc)
    db.add(TicketLog(
        complaint_id=complaint.id,
        updated_by=current_user.id,
        old_status="completed",
        new_status="closed",
    ))
    await db.commit()
    delete_cache("complaints:my:*")
    delete_cache("complaints:assigned:*")
    delete_cache("complaints:all")
    return {"message": "Feedback recorded and complaint closed"}


@router.post("/{complaint_id}/admin-resolve")
async def admin_resolve_complaint(
    complaint_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    result = await db.execute(select(Complaint).where(Complaint.id == str(complaint_id)))
    complaint = result.scalar_one_or_none()

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    if complaint.status == "resolved":
        raise HTTPException(status_code=400, detail="Complaint is already resolved")

    old_status = complaint.status
    complaint.status = "resolved"
    db.add(TicketLog(
        complaint_id=complaint.id,
        updated_by=current_user.id,
        old_status=old_status,
        new_status="resolved",
    ))
    await db.commit()

    safe_dispatch_task(
        send_notification_task,
        user_id=str(complaint.user_id),
        title="Complaint resolved by admin",
        message=f"Your complaint '{complaint.title}' has been resolved by an administrator.",
        notification_type="resolved",
        complaint_id=str(complaint.id),
    )

    await manager.send_personal_message(
        str(complaint.user_id),
        {
            "event": "status_updated",
            "complaint_id": str(complaint.id),
            "new_status": "resolved",
        },
    )

    delete_cache("complaints:my:*")
    delete_cache("complaints:assigned:*")
    delete_cache("complaints:all")

    return {"message": "Complaint resolved by admin"}
