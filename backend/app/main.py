from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_jobs import router as jobs_router
from app.api.routes_media import router as media_router
from app.api.routes_upload import router as upload_router
from app.core.config import get_env_report
from app.core.db import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="AI Auto-Reel Studio", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router, prefix="/api/uploads", tags=["uploads"])
app.include_router(jobs_router, prefix="/api/jobs", tags=["jobs"])
app.include_router(media_router, prefix="/api/jobs", tags=["media"])


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/env-check")
def env_check() -> dict:
    return get_env_report()
