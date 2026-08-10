import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import SessionLocal
from app.core.models import Clip
from app.core.schemas import ClipOut
from app.pipeline.ingest import probe_audio, probe_photo, probe_video

router = APIRouter()

UPLOAD_DIRS = {
    "video": settings.STORAGE_DIR / "uploads" / "clips",
    "photo": settings.STORAGE_DIR / "uploads" / "photos",
    "music": settings.STORAGE_DIR / "uploads" / "music",
}
for _dir in UPLOAD_DIRS.values():
    _dir.mkdir(parents=True, exist_ok=True)


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _save_upload(file: UploadFile, dest_dir: Path) -> Path:
    safe_name = f"{uuid.uuid4().hex}_{Path(file.filename or 'upload').name}"
    dest = dest_dir / safe_name
    with dest.open("wb") as out:
        shutil.copyfileobj(file.file, out)
    return dest


def _store_clip(file: UploadFile, kind: str, dest_dir: Path, probe, session: Session) -> Clip:
    path = _save_upload(file, dest_dir)
    meta = probe(str(path))
    clip = Clip(kind=kind, filename=file.filename or path.name, stored_path=str(path), **meta)
    session.add(clip)
    session.commit()
    session.refresh(clip)
    return clip


@router.post("/clips", response_model=list[ClipOut])
def upload_clips(files: list[UploadFile] = File(...), session: Session = Depends(get_session)):
    return [_store_clip(f, "video", UPLOAD_DIRS["video"], probe_video, session) for f in files]


@router.post("/photos", response_model=list[ClipOut])
def upload_photos(files: list[UploadFile] = File(...), session: Session = Depends(get_session)):
    return [_store_clip(f, "photo", UPLOAD_DIRS["photo"], probe_photo, session) for f in files]


@router.post("/music", response_model=ClipOut)
def upload_music(file: UploadFile = File(...), session: Session = Depends(get_session)):
    return _store_clip(file, "music", UPLOAD_DIRS["music"], probe_audio, session)
