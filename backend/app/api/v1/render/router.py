from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.models import RenderJob, JobStatus, get_db
from app.database.schemas import RenderJobCreate, RenderJobUpdate, RenderJobResponse
from app.auth.dependencies import get_current_user_id
from datetime import datetime
import random

router = APIRouter(prefix="/render", tags=["Render Jobs"])


@router.post("/jobs", response_model=RenderJobResponse, status_code=status.HTTP_201_CREATED)
def create_render_job(job_data: RenderJobCreate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    """Create a new render job."""
    new_job = RenderJob(
        user_id=user_id,
        project_id=job_data.project_id,
        movie_id=job_data.movie_id,
        job_type=job_data.job_type,
        parameters=job_data.parameters,
        priority=job_data.priority,
        status=JobStatus.PENDING
    )
    
    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    from app.workers.celery_app import process_render_job
    process_render_job.delay(new_job.id)

    return new_job


@router.get("/jobs", response_model=List[RenderJobResponse])
def get_render_jobs(
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Get all render jobs for the current user."""
    query = db.query(RenderJob).filter(RenderJob.user_id == user_id)
    
    if status_filter:
        try:
            job_status = JobStatus(status_filter.lower())
            query = query.filter(RenderJob.status == job_status)
        except ValueError:
            pass
    
    jobs = query.order_by(RenderJob.created_at.desc()).offset(skip).limit(limit).all()
    return jobs


@router.get("/jobs/{job_id}", response_model=RenderJobResponse)
def get_render_job(job_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    """Get a specific render job by ID."""
    job = db.query(RenderJob).filter(
        RenderJob.id == job_id,
        RenderJob.user_id == user_id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Render job not found"
        )
    
    return job


@router.put("/jobs/{job_id}", response_model=RenderJobResponse)
def update_render_job(
    job_id: int,
    job_data: RenderJobUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Update a render job (primarily for internal use)."""
    job = db.query(RenderJob).filter(
        RenderJob.id == job_id,
        RenderJob.user_id == user_id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Render job not found"
        )
    
    update_data = job_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(job, field, value)
    
    job.updated_at = datetime.utcnow()
    
    # Set timestamps based on status
    if job_data.status == JobStatus.PREPARING and not job.started_at:
        job.started_at = datetime.utcnow()
    elif job_data.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
        job.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(job)
    
    return job


@router.post("/jobs/{job_id}/cancel", response_model=RenderJobResponse)
def cancel_render_job(job_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    """Cancel a running render job."""
    job = db.query(RenderJob).filter(
        RenderJob.id == job_id,
        RenderJob.user_id == user_id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Render job not found"
        )
    
    if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel a job that is already completed, failed, or cancelled"
        )
    
    job.status = JobStatus.CANCELLED
    job.completed_at = datetime.utcnow()
    job.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(job)
    
    return job


@router.post("/jobs/{job_id}/pause", response_model=RenderJobResponse)
def pause_render_job(job_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    """Pause a running render job (placeholder)."""
    job = db.query(RenderJob).filter(
        RenderJob.id == job_id,
        RenderJob.user_id == user_id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Render job not found"
        )
    
    if job.status not in [JobStatus.QUEUED, JobStatus.PREPARING, JobStatus.GENERATING_STORY, JobStatus.PREPARING_SCENES]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot pause a job that is not running"
        )
    
    # Placeholder: In production, this would send a signal to the worker
    job.status = JobStatus.WAITING_FOR_AI
    job.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(job)
    
    return job


@router.post("/jobs/{job_id}/resume", response_model=RenderJobResponse)
def resume_render_job(job_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    """Resume a paused render job (placeholder)."""
    job = db.query(RenderJob).filter(
        RenderJob.id == job_id,
        RenderJob.user_id == user_id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Render job not found"
        )
    
    if job.status != JobStatus.WAITING_FOR_AI:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job is not paused"
        )
    
    # Placeholder: In production, this would resume the worker
    job.status = JobStatus.PREPARING
    job.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(job)
    
    return job


@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_render_job(job_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    """Delete a render job."""
    job = db.query(RenderJob).filter(
        RenderJob.id == job_id,
        RenderJob.user_id == user_id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Render job not found"
        )
    
    db.delete(job)
    db.commit()
    
    return None


@router.get("/queue/status")
def get_queue_status(db: Session = Depends(get_db)):
    """Get the current render queue status."""
    pending = db.query(RenderJob).filter(RenderJob.status == JobStatus.PENDING).count()
    queued = db.query(RenderJob).filter(RenderJob.status == JobStatus.QUEUED).count()
    processing = db.query(RenderJob).filter(
        RenderJob.status.in_([
            JobStatus.PREPARING,
            JobStatus.GENERATING_STORY,
            JobStatus.PREPARING_SCENES,
            JobStatus.WAITING_FOR_AI,
            JobStatus.FINALIZING
        ])
    ).count()
    completed = db.query(RenderJob).filter(RenderJob.status == JobStatus.COMPLETED).count()
    failed = db.query(RenderJob).filter(RenderJob.status == JobStatus.FAILED).count()
    
    # Mock GPU usage
    gpu_usage = random.randint(0, 100) if processing > 0 else 0
    estimated_wait = processing * 5  # Mock estimate in minutes
    
    return {
        "pending": pending,
        "queued": queued,
        "processing": processing,
        "completed": completed,
        "failed": failed,
        "gpu_usage_percent": gpu_usage,
        "estimated_wait_minutes": estimated_wait
    }
