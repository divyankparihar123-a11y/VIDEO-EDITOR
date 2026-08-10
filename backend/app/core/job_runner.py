from concurrent.futures import Future, ProcessPoolExecutor

from app.core.config import settings

executor = ProcessPoolExecutor(max_workers=settings.MAX_CONCURRENT_JOBS)
_futures: dict[int, Future] = {}


def _run_job_entrypoint(job_id: int) -> None:
    # Imported inside the worker process (spawned fresh on Windows) rather
    # than at module scope, so the parent process doesn't need every
    # pipeline dependency (opencv, faster-whisper, ...) importable just to
    # submit jobs.
    from app.pipeline.pipeline import run_job

    run_job(job_id)


def submit_job(job_id: int) -> None:
    future = executor.submit(_run_job_entrypoint, job_id)
    _futures[job_id] = future
    future.add_done_callback(lambda f: _on_job_done(job_id, f))


def _on_job_done(job_id: int, future: Future) -> None:
    _futures.pop(job_id, None)
    if future.cancelled():
        return
    exc = future.exception()
    if exc is None:
        return

    from app.core.db import SessionLocal
    from app.core.models import Job

    session = SessionLocal()
    try:
        job = session.get(Job, job_id)
        if job is not None and job.status not in ("done", "failed"):
            job.status = "failed"
            job.error_message = f"Worker process crashed: {exc}"
            session.add(job)
            session.commit()
    finally:
        session.close()


def cancel_job(job_id: int) -> bool:
    future = _futures.get(job_id)
    if future is None:
        return False
    return future.cancel()
