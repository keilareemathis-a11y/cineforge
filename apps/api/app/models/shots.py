from typing import Optional, List
from pydantic import BaseModel


class ShotVersion(BaseModel):
    id: str
    shot_id: str
    version_number: int
    prompt: str
    style: str
    status: str  # queued, processing, completed, ready, failed
    is_selected: bool = False
    image_url: Optional[str] = None
    video_url: Optional[str] = None


class Shot(BaseModel):
    id: str
    active_version_id: Optional[str] = None
    versions: List[str] = []  # list of ShotVersion ids


class TimelineItem(BaseModel):
    id: str
    shot_id: str
    active_version_id: Optional[str] = None


class RegenerateRequest(BaseModel):
    prompt: str
    style: str


class RegenerateResponse(BaseModel):
    status: str
    shot_id: str
    new_version: ShotVersion


class SelectVersionRequest(BaseModel):
    version_id: str


class SelectVersionResponse(BaseModel):
    status: str
    shot_id: str
    active_version_id: str
