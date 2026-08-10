import json
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import SessionLocal
from app.core.job_runner import cancel_job, submit_job
from app.core.models import Job, JobEvent
from app.core.schemas import JobCreate, JobOut

router = APIRouter()

VALID_ASPECT_RATIOS = {"9:16", "16:9", "1:1"}


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@router.post("", response_model=JobOut, status_code=202)
def create_job(payload: JobCreate, session: Session = Depends(get_session)):
    if payload.aspect_ratio not in VALID_ASPECT_RATIOS:
        raise HTTPException(422, f"aspect_ratio must be one of {sorted(VALID_ASPECT_RATIOS)}")
    if not payload.clip_ids:
        raise HTTPException(422, "At least one clip_id is required")
    if payload.target_duration <= 0:
        raise HTTPException(422, "target_duration must be positive")

    job = Job(
        status="queued",
        aspect_ratio=payload.aspect_ratio,
        target_duration_s=payload.target_duration,
        style=payload.style,
        clip_ids_json=json.dumps(payload.clip_ids),
        photo_ids_json=json.dumps(payload.photo_ids),
        music_id=payload.music_id,
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    submit_job(job.id)
    return job


@router.get("", response_model=list[JobOut])
def list_jobs(session: Session = Depends(get_session)):
    """Return all jobs, newest first."""
    jobs = session.query(Job).order_by(Job.id.desc()).all()
    return jobs


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int, session: Session = Depends(get_session)):
    job = session.get(Job, job_id)
    if job is None:
        raise HTTPException(404, "job not found")
    return job


@router.get("/{job_id}/events")
def stream_job_events(job_id: int):
    """Server-Sent Events stream for real-time job progress.

    Emits a ``job_update`` event (JSON-encoded JobOut) every ~800 ms until the
    job reaches a terminal state (done | failed | cancelled).  The client should
    close the connection after receiving a terminal event.
    """
    import time

    from fastapi.responses import StreamingResponse

    _TERMINAL = {"done", "failed", "cancelled"}

    def _event_generator():
        # Each worker iteration opens its own short-lived session so we always
        # read the freshest data written by the subprocess job runner.
        while True:
            session = SessionLocal()
            try:
                job = session.get(Job, job_id)
                if job is None:
                    # Job doesn't exist — emit an error event and close.
                    payload = json.dumps({"error": "job not found"})
                    yield f"event: error\ndata: {payload}\n\n"
                    return

                out = JobOut.model_validate(job)
                yield f"event: job_update\ndata: {out.model_dump_json()}\n\n"

                if out.status in _TERMINAL:
                    return
            finally:
                session.close()

            time.sleep(0.8)

    return StreamingResponse(
        _event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable nginx buffering if proxied
        },
    )


@router.get("/{job_id}/timeline")
def get_job_timeline(job_id: int, session: Session = Depends(get_session)):
    job = session.get(Job, job_id)
    if job is None or not job.timeline_path:
        raise HTTPException(404, "timeline not available yet")
    path = Path(job.timeline_path)
    if not path.is_file():
        raise HTTPException(404, "timeline file missing")
    return json.loads(path.read_text(encoding="utf-8"))


@router.delete("/{job_id}")
def delete_job(job_id: int, session: Session = Depends(get_session)):
    job = session.get(Job, job_id)
    if job is None:
        raise HTTPException(404, "job not found")

    was_cancelled = cancel_job(job_id)
    if job.status in ("queued", "running"):
        job.status = "cancelled"
        session.add(job)
        session.commit()
    return {"future_cancelled": was_cancelled, "status": job.status}


@router.delete("/{job_id}/purge", status_code=200)
def purge_job(job_id: int, session: Session = Depends(get_session)):
    """Permanently delete a job and all of its on-disk artifacts.

    Cancels the job if it is still running, then removes:
      - storage/work/{job_id}/          (intermediate render files)
      - storage/output/job_{job_id}.mp4 (final rendered video)
      - storage/thumbnails/job_{job_id}.jpg
      - All JobEvent rows for this job
      - The Job row itself
    """
    job = session.get(Job, job_id)
    if job is None:
        raise HTTPException(404, "job not found")

    # Cancel the future if still in the pool.
    cancel_job(job_id)

    # --- Disk cleanup ---
    work_dir = settings.STORAGE_DIR / "work" / str(job_id)
    if work_dir.is_dir():
        shutil.rmtree(work_dir, ignore_errors=True)

    output_file = settings.STORAGE_DIR / "output" / f"job_{job_id}.mp4"
    if output_file.is_file():
        output_file.unlink(missing_ok=True)

    thumb_file = settings.STORAGE_DIR / "thumbnails" / f"job_{job_id}.jpg"
    if thumb_file.is_file():
        thumb_file.unlink(missing_ok=True)

    # --- DB cleanup ---
    session.query(JobEvent).filter(JobEvent.job_id == job_id).delete()
    session.delete(job)
    session.commit()

    return {"purged": True, "job_id": job_id}
