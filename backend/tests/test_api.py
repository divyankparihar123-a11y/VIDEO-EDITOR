from fastapi.testclient import TestClient
from app.main import app
from app.core.db import SessionLocal
from app.core.models import Job

client = TestClient(app)


def test_list_jobs():
    response = client.get("/api/jobs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_thumbnail_not_found():
    response = client.get("/api/jobs/99999/thumbnail")
    assert response.status_code == 404


def test_purge_job_not_found():
    response = client.delete("/api/jobs/99999/purge")
    assert response.status_code == 404


def test_purge_existing_job():
    session = SessionLocal()
    try:
        job = Job(
            status="done",
            aspect_ratio="9:16",
            target_duration_s=15.0,
            style="cinematic",
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        job_id = job.id
    finally:
        session.close()

    response = client.delete(f"/api/jobs/{job_id}/purge")
    assert response.status_code == 200
    assert response.json()["purged"] is True

    # Verify job is gone from DB
    session = SessionLocal()
    try:
        assert session.get(Job, job_id) is None
    finally:
        session.close()
