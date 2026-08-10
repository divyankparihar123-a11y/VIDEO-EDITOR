import datetime
import json

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator


class ClipOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: str
    filename: str
    stored_path: str
    duration_s: float | None = None
    width: int | None = None
    height: int | None = None
    fps: float | None = None
    created_at: datetime.datetime


class JobCreate(BaseModel):
    clip_ids: list[int] = Field(default_factory=list)
    photo_ids: list[int] = Field(default_factory=list)
    music_id: int | None = None
    aspect_ratio: str
    target_duration: float
    style: str


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    progress_pct: float
    current_stage: str | None = None
    aspect_ratio: str
    target_duration_s: float
    style: str
    output_path: str | None = None
    timeline_path: str | None = None
    error_message: str | None = None
    warnings: list[str] = Field(
        default_factory=list, validation_alias=AliasChoices("warnings", "warnings_json")
    )
    clip_ids: list[int] = Field(
        default_factory=list, validation_alias=AliasChoices("clip_ids", "clip_ids_json")
    )
    photo_ids: list[int] = Field(
        default_factory=list, validation_alias=AliasChoices("photo_ids", "photo_ids_json")
    )
    music_id: int | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    @field_validator("warnings", mode="before")
    @classmethod
    def _parse_warnings(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else []
            except json.JSONDecodeError:
                return []
        return value

    @field_validator("clip_ids", "photo_ids", mode="before")
    @classmethod
    def _parse_id_list(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else []
            except json.JSONDecodeError:
                return []
        return value
