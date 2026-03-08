import uuid
from typing import Dict, List
from fastapi import APIRouter, HTTPException

from app.models.shots import (
    Shot,
    ShotVersion,
    TimelineItem,
    RegenerateRequest,
    RegenerateResponse,
    SelectVersionRequest,
    SelectVersionResponse,
)

router = APIRouter()

# In-memory stores (replace with DB in production)
_shots: Dict[str, Shot] = {}
_versions: Dict[str, ShotVersion] = {}
_timeline_items: List[TimelineItem] = []

# Seed data so the endpoints work out of the box in tests and demos
def _seed() -> None:
    shot = Shot(id="shot_001", active_version_id="shotver_v1", versions=["shotver_v1"])
    version = ShotVersion(
        id="shotver_v1",
        shot_id="shot_001",
        version_number=1,
        prompt="Wide cityscape at dawn",
        style="cinematic",
        status="completed",
        is_selected=True,
        image_url="https://example.com/image.jpg",
        video_url="https://example.com/video.mp4",
    )
    timeline_item = TimelineItem(
        id="ti_001", shot_id="shot_001", active_version_id="shotver_v1"
    )
    _shots[shot.id] = shot
    _versions[version.id] = version
    _timeline_items.append(timeline_item)


_seed()


@router.post(
    "/{shot_id}/regenerate",
    response_model=RegenerateResponse,
    status_code=202,
)
async def regenerate_shot(shot_id: str, body: RegenerateRequest) -> RegenerateResponse:
    """Create a new version of a shot for regeneration without affecting the timeline."""
    shot = _shots.get(shot_id)
    if shot is None:
        raise HTTPException(status_code=404, detail=f"Shot '{shot_id}' not found")

    next_version_number = len(shot.versions) + 1
    new_version_id = f"shotver_{uuid.uuid4().hex[:8]}"

    new_version = ShotVersion(
        id=new_version_id,
        shot_id=shot_id,
        version_number=next_version_number,
        prompt=body.prompt,
        style=body.style,
        status="queued",
        is_selected=False,
    )

    _versions[new_version_id] = new_version
    shot.versions.append(new_version_id)

    return RegenerateResponse(
        status="queued",
        shot_id=shot_id,
        new_version=new_version,
    )


@router.post(
    "/{shot_id}/select-version",
    response_model=SelectVersionResponse,
)
async def select_version(
    shot_id: str, body: SelectVersionRequest
) -> SelectVersionResponse:
    """Select an existing version as the active version and propagate to all timeline items."""
    shot = _shots.get(shot_id)
    if shot is None:
        raise HTTPException(status_code=404, detail=f"Shot '{shot_id}' not found")

    version = _versions.get(body.version_id)
    if version is None or version.shot_id != shot_id:
        raise HTTPException(
            status_code=404,
            detail=f"Version '{body.version_id}' not found for shot '{shot_id}'",
        )

    if version.status == "failed":
        raise HTTPException(
            status_code=400,
            detail=f"Version '{body.version_id}' failed to generate and cannot be selected",
        )

    if version.status in ("queued", "processing"):
        raise HTTPException(
            status_code=400,
            detail=f"Version '{body.version_id}' is still being generated (status: {version.status})",
        )

    if version.status not in ("completed", "ready"):
        raise HTTPException(
            status_code=400,
            detail=f"Version '{body.version_id}' is not ready for selection (status: {version.status})",
        )

    if not version.image_url and not version.video_url:
        raise HTTPException(
            status_code=400,
            detail=f"Version '{body.version_id}' has no rendered assets",
        )

    # Atomic update: Shot, ShotVersion flags, and all TimelineItems
    for vid in shot.versions:
        v = _versions.get(vid)
        if v is not None:
            v.is_selected = vid == body.version_id

    shot.active_version_id = body.version_id

    for item in _timeline_items:
        if item.shot_id == shot_id:
            item.active_version_id = body.version_id

    return SelectVersionResponse(
        status="selected",
        shot_id=shot_id,
        active_version_id=body.version_id,
    )
