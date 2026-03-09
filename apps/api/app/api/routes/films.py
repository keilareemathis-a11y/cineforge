from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.film_draft import FilmDraft
from app.models.timeline_item import TimelineItem
from app.models.shot import Shot
from app.models.shot_version import ShotVersion

router = APIRouter()


@router.post("/assemble")
def assemble_film():
    # Stub implementation for film assembly
    return {"message": "Film assembly initiated"}


@router.get("/{film_draft_id}/timeline")
def get_film_timeline(film_draft_id: str, db: Session = Depends(get_db)):
    """Return the editorial timeline for a film draft with nested shots and active versions."""
    draft = (
        db.query(FilmDraft)
        .options(
            joinedload(FilmDraft.timeline_items).joinedload(TimelineItem.shot),
            joinedload(FilmDraft.timeline_items).joinedload(TimelineItem.active_version),
        )
        .filter(FilmDraft.id == film_draft_id)
        .first()
    )
    if draft is None:
        raise HTTPException(status_code=404, detail="Film draft not found")

    timeline_items = []
    for item in sorted(draft.timeline_items, key=lambda i: i.position):
        shot = item.shot
        version = item.active_version
        timeline_items.append(
            {
                "timeline_item_id": item.id,
                "position": item.position,
                "shot": {
                    "shot_id": shot.id,
                    "shot_type": shot.shot_type,
                    "description": shot.description,
                    "image_prompt": shot.image_prompt,
                }
                if shot
                else None,
                "active_version": {
                    "version_id": version.id,
                    "version_number": version.version_number,
                    "duration_seconds": version.duration_seconds,
                    "trim_start": version.trim_start,
                    "trim_end": version.trim_end,
                }
                if version
                else None,
            }
        )

    return {
        "film_draft_id": draft.id,
        "title": draft.title,
        "timeline_items": timeline_items,
    }


@router.get("/{id}")
def get_film(id: str):
    # Stub implementation: returning a dummy film object
    return {"id": id, "title": "Sample Film", "status": "available"}


@router.get("/{id}/export")
def export_film(id: str):
    # Stub implementation for exporting a film
    return {"message": "Film exported successfully"}