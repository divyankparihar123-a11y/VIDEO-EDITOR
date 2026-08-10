import subprocess
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import resolve_ffmpeg_binaries, settings
from app.core.db import SessionLocal
from app.core.models import Job

router = APIRouter()

_THUMB_DIR = settings.STORAGE_DIR / "thumbnails"
_THUMB_DIR.mkdir(parents=True, exist_ok=True)


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _get_output_path(job_id: int, session: Session) -> Path:
    job = session.get(Job, job_id)
    if job is None or not job.output_path:
        raise HTTPException(404, "output not available yet")
    path = Path(job.output_path)
    if not path.is_file():
        raise HTTPException(404, "output file missing")
    return path


@router.get("/{job_id}/preview")
def preview_job(job_id: int, session: Session = Depends(get_session)):
    path = _get_output_path(job_id, session)
    return FileResponse(path, media_type="video/mp4")


@router.get("/{job_id}/download")
def download_job(job_id: int, session: Session = Depends(get_session)):
    path = _get_output_path(job_id, session)
    return FileResponse(path, media_type="video/mp4", filename=f"reel_{job_id}.mp4")


@router.get("/{job_id}/thumbnail")
def thumbnail_job(job_id: int, session: Session = Depends(get_session)):
    """Extract a still frame at the 1-second mark and return it as a JPEG.

    The frame is generated on first request and then cached on disk so
    subsequent calls are instant (no ffmpeg re-run).
    """
    thumb_path = _THUMB_DIR / f"job_{job_id}.jpg"

    # Cache hit — return immediately.
    if thumb_path.is_file():
        return FileResponse(thumb_path, media_type="image/jpeg")

    # Need to render the frame — make sure the output exists first.
    output_path = _get_output_path(job_id, session)

    try:
        ffmpeg_path, _ = resolve_ffmpeg_binaries()
    except RuntimeError as exc:
        raise HTTPException(503, f"ffmpeg not available: {exc}") from exc

    result = subprocess.run(
        [
            ffmpeg_path, "-y",
            "-ss", "1",          # seek to 1 second
            "-i", str(output_path),
            "-frames:v", "1",    # extract exactly one frame
            "-q:v", "3",         # JPEG quality (2=best, 5=good balance)
            "-vf", "scale=480:-1",  # thumbnail width 480px, height auto
            str(thumb_path),
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0 or not thumb_path.is_file():
        raise HTTPException(500, "Thumbnail extraction failed")

    return FileResponse(thumb_path, media_type="image/jpeg")
