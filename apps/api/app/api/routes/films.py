from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.film_draft import FilmDraft
from app.models.timeline_item import TimelineItem
from app.services.generated_visuals import build_shot_prompt, shot_storyboard_image, shot_version_image
from app.services.platform_service import published_film
from app.services.render_service import (
    render_film_timeline,
    render_output_path,
    rendered_video_exists,
    rendered_video_url,
)
from app.services.video_generation import ensure_shot_version_video, shot_version_video_url

router = APIRouter()


class PublishFilmRequest(BaseModel):
    draft_id: str
    description: Optional[str] = None
    tags: list[str] = []


class TimelineItemUpdate(BaseModel):
    duration_seconds: Optional[float] = None
    trim_start: Optional[float] = None
    trim_end: Optional[float] = None


class TimelineReorderRequest(BaseModel):
    item_id: str
    new_position: int


@router.post("/assemble")
def assemble_film():
    # Stub implementation for film assembly
    return {"message": "Film assembly initiated"}


@router.get("")
def list_films(
    sort: Literal["trending", "new"] = "trending", db: Session = Depends(get_db)
):
    drafts = _published_drafts_query(db).all()
    films = [published_film(draft) for draft in drafts]

    if sort == "new":
        films.sort(key=lambda film: film["published_at"] or "", reverse=True)
    else:
        films.sort(key=lambda film: (film["view_count"], film["like_count"]), reverse=True)
    return films


@router.post("/publish")
def publish_film(data: PublishFilmRequest, db: Session = Depends(get_db)):
    draft = _load_draft(db, data.draft_id)
    if not draft.timeline_items:
        raise HTTPException(status_code=400, detail="Film draft has no timeline items")

    if not rendered_video_exists(draft.id):
        render_film_timeline(draft)

    if data.description is not None:
        draft.description = data.description
    if data.tags:
        draft.tags = ",".join(data.tags)
    draft.published_at = draft.published_at or datetime.now(timezone.utc)

    db.commit()
    db.refresh(draft)
    return published_film(draft)


@router.get("/{film_draft_id}/timeline")
def get_film_timeline(film_draft_id: str, db: Session = Depends(get_db)):
    """Return the editorial timeline for a film draft with nested shots and active versions."""
    draft = _load_draft(db, film_draft_id)
    return _timeline_to_dict(draft)


@router.post("/{film_draft_id}/timeline/reorder")
def reorder_timeline_items(
    film_draft_id: str, data: TimelineReorderRequest, db: Session = Depends(get_db)
):
    draft = _load_draft(db, film_draft_id)
    items = list(sorted(draft.timeline_items, key=lambda item: item.position))

    item = next((entry for entry in items if entry.id == data.item_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail="Timeline item not found")

    items.remove(item)
    new_position = max(0, min(data.new_position, len(items)))
    items.insert(new_position, item)

    for index, entry in enumerate(items):
        entry.position = index

    db.commit()
    db.refresh(draft)
    return _timeline_to_dict(_load_draft(db, film_draft_id))


@router.post("/{film_draft_id}/timeline/{item_id}/move")
def move_timeline_item(
    film_draft_id: str,
    item_id: str,
    payload: dict,
    db: Session = Depends(get_db),
):
    direction = payload.get("direction")
    if direction not in {"up", "down"}:
        raise HTTPException(status_code=400, detail="Direction must be 'up' or 'down'")

    draft = _load_draft(db, film_draft_id)
    items = list(sorted(draft.timeline_items, key=lambda item: item.position))
    index = next((i for i, entry in enumerate(items) if entry.id == item_id), None)
    if index is None:
        raise HTTPException(status_code=404, detail="Timeline item not found")

    if direction == "up" and index > 0:
        items[index - 1], items[index] = items[index], items[index - 1]
    elif direction == "down" and index < len(items) - 1:
        items[index], items[index + 1] = items[index + 1], items[index]

    for position, entry in enumerate(items):
        entry.position = position

    db.commit()
    return _timeline_to_dict(_load_draft(db, film_draft_id))


@router.patch("/{film_draft_id}/timeline/{item_id}")
def update_timeline_item(
    film_draft_id: str, item_id: str, data: TimelineItemUpdate, db: Session = Depends(get_db)
):
    draft = _load_draft(db, film_draft_id)
    item = next((entry for entry in draft.timeline_items if entry.id == item_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail="Timeline item not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)

    if item.trim_end is not None and item.trim_end <= (item.trim_start or 0):
        raise HTTPException(status_code=400, detail="trim_end must be greater than trim_start")

    db.commit()
    return _timeline_to_dict(_load_draft(db, film_draft_id))


@router.get("/{id}")
def get_film(id: str, db: Session = Depends(get_db)):
    draft = _published_drafts_query(db).filter(FilmDraft.id == id).first()
    if draft is not None:
        return published_film(draft)

    if rendered_video_exists(id):
        return {
            "id": id,
            "title": f"Rendered Film {id}",
            "status": "available",
            "video_url": rendered_video_url(id),
        }
    raise HTTPException(status_code=404, detail="Film not found")


@router.post("/{film_id}/like")
def like_film(film_id: str, db: Session = Depends(get_db)):
    draft = _published_drafts_query(db).filter(FilmDraft.id == film_id).first()
    if draft is None:
        raise HTTPException(status_code=404, detail="Film not found")

    draft.like_count = (draft.like_count or 0) + 1
    db.commit()
    return {"film_id": film_id, "like_count": draft.like_count}


@router.post("/{draft_id}/render")
def render_film(draft_id: str, db: Session = Depends(get_db)):
    """Render a film draft timeline into a single MP4 file."""
    draft = _load_draft(db, draft_id)

    try:
        result = render_film_timeline(draft)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "draft_id": result["draft_id"],
        "status": "rendered",
        "video_url": result["video_url"],
    }


@router.get("/{draft_id}/rendered")
def get_rendered_film(draft_id: str):
    """Serve the rendered MP4 for a film draft."""
    output_path = render_output_path(draft_id)
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Rendered film not found")
    return FileResponse(path=str(output_path), media_type="video/mp4", filename=f"{draft_id}.mp4")


@router.get("/{id}/export")
def export_film(id: str):
    """Return the rendered film URL for export/download clients."""
    if not rendered_video_exists(id):
        raise HTTPException(status_code=404, detail="Rendered film not found")
    return {"message": "Film exported successfully", "video_url": rendered_video_url(id)}


def _load_draft(db: Session, draft_id: str) -> FilmDraft:
    draft = (
        db.query(FilmDraft)
        .options(
            joinedload(FilmDraft.project),
            joinedload(FilmDraft.timeline_items).joinedload(TimelineItem.shot),
            joinedload(FilmDraft.timeline_items).joinedload(TimelineItem.active_version),
        )
        .filter(FilmDraft.id == draft_id)
        .first()
    )
    if draft is None:
        raise HTTPException(status_code=404, detail="Film draft not found")
    return draft


def _published_drafts_query(db: Session):
    return (
        db.query(FilmDraft)
        .options(
            joinedload(FilmDraft.project),
            joinedload(FilmDraft.timeline_items).joinedload(TimelineItem.shot),
            joinedload(FilmDraft.timeline_items).joinedload(TimelineItem.active_version),
        )
        .filter(FilmDraft.published_at.isnot(None))
    )


def _timeline_to_dict(draft: FilmDraft) -> dict:
    timeline_items = []
    for item in sorted(draft.timeline_items, key=lambda i: i.position):
        shot = item.shot
        version = item.active_version
        if version is not None:
            ensure_shot_version_video(version)

        timeline_items.append(
            {
                "timeline_item_id": item.id,
                "position": item.position,
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
        )

    return {
        "film_draft_id": draft.id,
        "title": draft.title,
        "timeline_items": timeline_items,
    }
