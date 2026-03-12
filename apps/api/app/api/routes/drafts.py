from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.film_draft import FilmDraft
from app.models.timeline_item import TimelineItem
from app.models.shot import Shot
from app.models.shot_version import ShotVersion
from app.services.generated_visuals import build_shot_prompt, shot_storyboard_image, shot_version_image
from app.services.video_generation import ensure_shot_version_video, shot_version_video_url

router = APIRouter()


class TimelineItemCreate(BaseModel):
    shot_id: str
    position: int
    active_version_id: Optional[str] = None


def _timeline_item_to_dict(item: TimelineItem) -> dict:
    shot = item.shot
    version = item.active_version
    if version is not None:
        ensure_shot_version_video(version)
    return {
        "timeline_item_id": item.id,
        "position": item.position,
        "film_draft_id": item.film_draft_id,
        "shot_id": item.shot_id,
        "active_version_id": item.active_version_id,
        "duration_seconds": item.duration_seconds if item.duration_seconds is not None else version.duration_seconds if version else None,
        "trim_start": item.trim_start,
        "trim_end": item.trim_end,
        "shot": {
            "shot_id": shot.id,
            "shot_type": shot.shot_type,
            "description": shot.description,
            "image_prompt": shot.image_prompt,
            "prompt": build_shot_prompt(shot),
            "storyboard_image": shot_storyboard_image(shot),
            "active_version_id": shot.active_version_id,
            "created_at": shot.created_at.isoformat() if shot.created_at else None,
        }
        if shot
        else None,
        "active_version": {
            "version_id": version.id,
            "version_number": version.version_number,
            "duration_seconds": version.duration_seconds,
            "trim_start": version.trim_start,
            "trim_end": version.trim_end,
            "image_url": shot_version_image(version),
            "video_url": shot_version_video_url(version.shot_id, version.id),
            "status": version.status,
            "provider": version.provider,
            "prompt": build_shot_prompt(shot) if shot else None,
            "created_at": version.created_at.isoformat() if version.created_at else None,
        }
        if version
        else None,
    }


@router.post("/{draft_id}/timeline-items")
def create_timeline_item(
    draft_id: str, data: TimelineItemCreate, db: Session = Depends(get_db)
):
    """Add a shot to a film draft timeline."""
    draft = db.query(FilmDraft).filter(FilmDraft.id == draft_id).first()
    if draft is None:
        raise HTTPException(status_code=404, detail="Film draft not found")

    shot = db.query(Shot).filter(Shot.id == data.shot_id).first()
    if shot is None:
        raise HTTPException(status_code=404, detail="Shot not found")

    if data.active_version_id is not None:
        version = (
            db.query(ShotVersion)
            .filter(ShotVersion.id == data.active_version_id)
            .first()
        )
        if version is None:
            raise HTTPException(status_code=404, detail="ShotVersion not found")

    item = TimelineItem(
        film_draft_id=draft_id,
        shot_id=data.shot_id,
        position=data.position,
        active_version_id=data.active_version_id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return _timeline_item_to_dict(item)


@router.get("/{draft_id}/timeline")
def get_draft_timeline(draft_id: str, db: Session = Depends(get_db)):
    """Return the editorial timeline for a film draft with nested shots and active versions."""
    draft = (
        db.query(FilmDraft)
        .options(
            joinedload(FilmDraft.timeline_items).joinedload(TimelineItem.shot),
            joinedload(FilmDraft.timeline_items).joinedload(TimelineItem.active_version),
        )
        .filter(FilmDraft.id == draft_id)
        .first()
    )
    if draft is None:
        raise HTTPException(status_code=404, detail="Film draft not found")

    timeline_items = [
        _timeline_item_to_dict(item)
        for item in sorted(draft.timeline_items, key=lambda i: i.position)
    ]

    return {
        "film_draft_id": draft.id,
        "title": draft.title,
        "timeline_items": timeline_items,
    }
