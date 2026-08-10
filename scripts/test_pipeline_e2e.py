"""End-to-End Pipeline Integration Test.
Creates DB entries for sample clips, submits a job, executes run_job(),
and verifies that the final rendered video (job_X.mp4) is produced.
"""

import sys
from pathlib import Path

# Add backend directory to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import json
from app.core.db import SessionLocal, init_db
from app.core.models import Clip, Job
from app.pipeline.ingest import probe_audio, probe_photo, probe_video
from app.pipeline.pipeline import run_job


def main():
    print("=== Initializing DB ===")
    init_db()

    sample_dir = BACKEND_DIR / "tests" / "sample_clips"
    sharp_path = sample_dir / "sharp.mp4"
    blurry_path = sample_dir / "blurry.mp4"
    photo_path = sample_dir / "photo1.jpg"
    music_path = sample_dir / "beat_music.mp3"

    session = SessionLocal()
    try:
        print("=== Registering sample clips ===")
        sharp_meta = probe_video(str(sharp_path))
        sharp_clip = Clip(
            kind="video",
            filename="sharp.mp4",
            stored_path=str(sharp_path),
            **sharp_meta,
        )
        session.add(sharp_clip)

        blurry_meta = probe_video(str(blurry_path))
        blurry_clip = Clip(
            kind="video",
            filename="blurry.mp4",
            stored_path=str(blurry_path),
            **blurry_meta,
        )
        session.add(blurry_clip)

        photo_meta = probe_photo(str(photo_path))
        photo_clip = Clip(
            kind="photo",
            filename="photo1.jpg",
            stored_path=str(photo_path),
            **photo_meta,
        )
        session.add(photo_clip)

        music_meta = probe_audio(str(music_path))
        music_clip = Clip(
            kind="music",
            filename="beat_music.mp3",
            stored_path=str(music_path),
            **music_meta,
        )
        session.add(music_clip)

        session.commit()
        session.refresh(sharp_clip)
        session.refresh(blurry_clip)
        session.refresh(photo_clip)
        session.refresh(music_clip)

        print(f"Clips created: video IDs={[sharp_clip.id, blurry_clip.id]}, photo ID={photo_clip.id}, music ID={music_clip.id}")

        print("=== Creating Job ===")
        job = Job(
            status="queued",
            aspect_ratio="9:16",
            target_duration_s=15.0,
            style="cinematic",
            clip_ids_json=json.dumps([sharp_clip.id, blurry_clip.id]),
            photo_ids_json=json.dumps([photo_clip.id]),
            music_id=music_clip.id,
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        job_id = job.id
        print(f"Job created with ID: {job_id}")

    finally:
        session.close()

    print(f"=== Running Job #{job_id} synchronously ===")
    run_job(job_id)

    # Verification
    session = SessionLocal()
    try:
        job = session.get(Job, job_id)
        print(f"Final Job Status: {job.status}")
        print(f"Current Stage: {job.current_stage}")
        print(f"Progress Pct: {job.progress_pct}%")
        print(f"Output Path: {job.output_path}")

        if job.status == "done" and job.output_path:
            out_file = Path(job.output_path)
            if out_file.is_file() and out_file.stat().st_size > 0:
                print(f"SUCCESS: Rendered reel saved at {out_file} ({out_file.stat().st_size / 1024 / 1024:.2f} MB)")
            else:
                print(f"FAILURE: Output file missing or 0 bytes: {out_file}")
                sys.exit(1)
        else:
            print(f"FAILURE: Job failed with error:\n{job.error_message}")
            sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    main()
