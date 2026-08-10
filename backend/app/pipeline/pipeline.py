"""Orchestrates the render pipeline for a single job. Runs inside the
ProcessPoolExecutor worker (see app/core/job_runner.py) and owns its own
DB session, since SQLAlchemy sessions/engines cannot cross process
boundaries.
"""

import json
import traceback
from pathlib import Path

from app.core.config import settings
from app.core.db import SessionLocal
from app.core.models import Clip, Job
from app.pipeline import captions as captions_mod
from app.pipeline import render as render_mod
from app.pipeline import timeline as timeline_mod
from app.pipeline.render import ASPECT_RESOLUTIONS


def _build_captions_ass(tl: dict, work_dir: Path):
    """Best-effort: transcribe each unique source clip once, remap into
    timeline coordinates, chunk into cards, write an ASS file. Returns
    (ass_path_or_None, warning_or_None, cards) -- never raises; caption
    failures degrade to "no captions" rather than failing the whole job.
    """
    sources = sorted({seg["source"] for seg in tl["clips"] if seg.get("type") != "photo"})
    if not sources:
        return None, None, []

    try:
        words_by_source = {src: captions_mod.transcribe_words(src) for src in sources}
        words = captions_mod.remap_words_to_timeline(tl["clips"], words_by_source)
        if not words:
            return None, None, []

        cards = captions_mod.chunk_words(words)
        width, height = ASPECT_RESOLUTIONS[tl["aspect_ratio"]]
        ass_text = captions_mod.build_ass(cards, width, height)

        ass_path = work_dir / "captions.ass"
        ass_path.write_text(ass_text, encoding="utf-8")
        return ass_path, None, cards
    except Exception as exc:  # noqa: BLE001 - captions are optional, never fail the job for this
        return None, f"Captions could not be generated ({exc}); continuing without them.", []


def _update_job(session, job: Job, **fields) -> None:
    for key, value in fields.items():
        setattr(job, key, value)
    session.add(job)
    session.commit()


def run_job(job_id: int) -> None:
    session = SessionLocal()
    try:
        job = session.get(Job, job_id)
        if job is None:
            return

        _update_job(session, job, status="running", progress_pct=0.0, current_stage="loading clips")

        clip_ids = json.loads(job.clip_ids_json or "[]")
        photo_ids = json.loads(job.photo_ids_json or "[]")
        clips = [c for c in (session.get(Clip, cid) for cid in clip_ids) if c is not None]
        photos = [c for c in (session.get(Clip, pid) for pid in photo_ids) if c is not None]
        music_clip = session.get(Clip, job.music_id) if job.music_id else None
        if not clips:
            _update_job(session, job, status="failed", error_message="No valid clips found for this job.")
            return

        _update_job(session, job, current_stage="analyzing clip quality", progress_pct=5.0)
        tl = timeline_mod.build_full_timeline(
            clips, photos, music_clip, job.target_duration_s, job.aspect_ratio, job.style
        )

        work_dir = settings.STORAGE_DIR / "work" / str(job_id)
        work_dir.mkdir(parents=True, exist_ok=True)
        timeline_path = work_dir / "timeline.json"
        timeline_path.write_text(json.dumps(tl, indent=2), encoding="utf-8")

        output_dir = settings.STORAGE_DIR / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"job_{job_id}.mp4"

        def progress_cb(pct: float, stage: str) -> None:
            _update_job(session, job, progress_pct=round(pct * 100, 1), current_stage=stage)

        _update_job(session, job, current_stage="transcribing captions", progress_pct=10.0)
        ass_path, caption_warning, cards = _build_captions_ass(tl, work_dir)
        if caption_warning:
            tl.setdefault("warnings", []).append(caption_warning)
        tl["captions"] = cards
        timeline_path.write_text(json.dumps(tl, indent=2), encoding="utf-8")

        _update_job(session, job, current_stage="rendering", timeline_path=str(timeline_path))
        render_mod.render_full(tl, work_dir, output_path, progress_cb=progress_cb, ass_path=ass_path)

        _update_job(
            session,
            job,
            status="done",
            progress_pct=100.0,
            current_stage="done",
            output_path=str(output_path),
            warnings_json=json.dumps(tl.get("warnings", [])),
        )
    except Exception as exc:  # noqa: BLE001 - never let the worker die silently
        job = session.get(Job, job_id)
        if job is not None:
            _update_job(
                session,
                job,
                status="failed",
                error_message=f"{exc}\n{traceback.format_exc()[-2000:]}",
            )
    finally:
        session.close()
