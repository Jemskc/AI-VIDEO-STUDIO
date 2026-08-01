from celery import Celery
from app.core.config import settings

# Create Celery application
celery_app = Celery(
    "ai_movie_studio",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    worker_prefetch_multiplier=1,
)


@celery_app.task(bind=True, max_retries=3)
def process_render_job(self, job_id: int):
    """
    Process a render job: build the production blueprint for the job's story,
    adapt it into an orchestrator execution plan, run mock workers/providers
    to completion, and stitch the resulting scene clips into a final video.

    Providers are mocked (placeholder outputs) for now; the orchestration,
    worker, and FFmpeg wiring here is real and unchanged when real AI
    providers are swapped in later.
    """
    import asyncio
    from datetime import datetime
    from app.database.models import RenderJob, JobStatus, get_db
    from app.services.movie_planning import MoviePlanningService
    from app.services.blueprint_adapter import to_orchestrator_blueprint
    from app.orchestrator.engine import get_orchestrator, TaskType
    from app.workers.base import (
        LLMWorker, ImageWorker, VideoWorker, VoiceWorker, MusicWorker, RenderWorker,
    )

    db = next(get_db())
    job = None

    try:
        job = db.query(RenderJob).filter(RenderJob.id == job_id).first()
        if not job:
            raise ValueError(f"Render job {job_id} not found")

        story_id = (job.parameters or {}).get("story_id")
        if not story_id:
            raise ValueError("Render job parameters must include 'story_id'")

        job.status = JobStatus.PREPARING
        job.progress = 5
        job.started_at = datetime.utcnow()
        db.commit()

        planner = MoviePlanningService(db)
        blueprint = planner.get_production_blueprint(story_id)
        adapted = to_orchestrator_blueprint(blueprint)

        job.status = JobStatus.GENERATING_STORY
        job.progress = 15
        db.commit()

        async def run_pipeline():
            orchestrator = get_orchestrator()
            plan = await orchestrator.create_execution_plan(
                project_id=adapted["project_id"],
                blueprint_id=str(adapted["id"]),
                blueprint_data=adapted,
            )

            workers = [
                LLMWorker(), ImageWorker(), VideoWorker(),
                VoiceWorker(), MusicWorker(), RenderWorker(),
            ]
            for worker in workers:
                await worker.initialize()

            return await orchestrator.run_plan_to_completion(plan.plan_id, workers)

        job.status = JobStatus.WAITING_FOR_AI
        job.progress = 40
        db.commit()

        completed_plan = asyncio.run(run_pipeline())

        job.status = JobStatus.FINALIZING
        job.progress = 90
        db.commit()

        if completed_plan.status != "completed":
            raise RuntimeError(
                f"Render plan did not complete: {completed_plan.completed_tasks}/"
                f"{completed_plan.total_tasks} tasks done, {completed_plan.failed_tasks} failed"
            )

        render_task = next(
            (t for t in completed_plan.tasks if t.task_type == TaskType.RENDER), None
        )
        if not render_task or not render_task.result:
            raise RuntimeError("Render task did not produce an output")

        job.status = JobStatus.COMPLETED
        job.progress = 100
        job.completed_at = datetime.utcnow()
        job.output_url = render_task.result["output_path"]
        db.commit()

        return {
            "job_id": job_id,
            "status": "completed",
            "output_url": job.output_url
        }

    except Exception as exc:
        if job:
            job.status = JobStatus.FAILED
            job.error_message = str(exc)
            job.completed_at = datetime.utcnow()
            db.commit()

        retry_delay = 60 * (self.request.retries + 1)
        raise self.retry(exc=exc, countdown=retry_delay)

    finally:
        db.close()


@celery_app.task
def send_notification_task(user_id: int, title: str, message: str):
    """Send a notification to a user (mock implementation)."""
    from sqlalchemy.orm import Session
    from app.database.models import Notification, get_db
    
    db = next(get_db())
    
    try:
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type="info"
        )
        db.add(notification)
        db.commit()
        
        return {"notification_id": notification.id, "status": "sent"}
    finally:
        db.close()


@celery_app.task
def cleanup_old_files():
    """Clean up old temporary files (scheduled task)."""
    # Placeholder for file cleanup logic
    return {"status": "cleanup_completed"}


@celery_app.task
def generate_thumbnail(asset_id: int):
    """Generate a thumbnail for an asset (placeholder)."""
    # Placeholder for thumbnail generation
    return {"asset_id": asset_id, "thumbnail_url": "/mock/thumbnail.jpg"}
