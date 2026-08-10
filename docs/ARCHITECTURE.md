# Architecture

## Overview

AI Auto-Reel Studio is a single-user, local-only application:

- **Backend**: FastAPI app (`backend/app`), SQLite database via SQLAlchemy
  2.x (`backend/app/core/db.py`, `models.py`), and Pydantic v2 schemas
  (`backend/app/core/schemas.py`) for the API surface.
- **Job execution**: jobs run in-process using a `ProcessPoolExecutor`
  (`backend/app/core/job_runner.py`) with `MAX_CONCURRENT_JOBS=1` by default,
  since rendering is GPU/CPU heavy and this is a single-user local app. No
  external queue/broker (no Redis, no Celery).
- **Rendering**: all media work (transcoding, concatenation, overlays,
  captions, transitions) is done by shelling out to ffmpeg, using NVENC
  (`h264_nvenc`) when available for faster encodes, falling back to CPU
  encoding otherwise. `backend/app/core/config.py` resolves the ffmpeg/ffprobe
  binaries and detects NVENC/libass support at runtime so the app works
  whether or not ffmpeg is on PATH.
- **Frontend**: a minimal Next.js 14 App Router + TypeScript + Tailwind app
  (`frontend/`) that talks to the backend over plain HTTP (CORS-enabled for
  `http://localhost:3000`).

## API surface (current)

- `GET /api/health` - liveness check.
- `GET /api/env-check` - reports ffmpeg/ffprobe resolution, NVENC and libass
  availability, and whether faster-whisper is importable. Backed by the same
  `get_env_report()` used by `scripts/check_env.py`.
- `/api/uploads/*`, `/api/jobs/*` - routers are wired up but empty; route
  handlers are added in later milestones.
- `/api/jobs/{id}/...` (media) - a second router mounted under the `/api/jobs`
  prefix for media sub-resources (e.g. previews), also empty for now.

## Data model (current)

- `Clip` - an uploaded video/photo/music asset with basic probed metadata
  (duration, width/height, fps).
- `Job` - a render job: status, progress, current stage, requested aspect
  ratio/duration/style, resulting output/timeline paths, and the input clip
  ids (`clip_ids_json`/`photo_ids_json`/`music_id`) it was built from.
- `JobEvent` - a log of stage/message events for a job, for progress/debug
  streaming.

## Pipeline (planned)

The actual auto-edit pipeline is not implemented yet. Future milestones will
add `backend/app/pipeline/` modules, expected to include stages such as:

1. Ingest/probe uploaded clips and photos (ffprobe metadata, scene detection
   via `scenedetect`).
2. Analyze the music track (beat/onset detection via `librosa`) to derive cut
   points.
3. Transcribe any spoken audio (`faster-whisper`, CUDA when available) for
   caption generation.
4. Select and order clips/photos to fit the target duration and style.
5. Render the final output with ffmpeg (transitions, captions via libass,
   audio mixing), writing progress back onto the `Job` row via
   `JobEvent`s.

`backend/app/core/job_runner.py` will dispatch each job's pipeline run to the
process pool once that pipeline exists.
