from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.film_draft import FilmDraft
from app.models.timeline_item import TimelineItem
from app.services.generated_visuals import build_shot_prompt, shot_storyboard_image, shot_version_image
from app.services.render_service import (
    render_film_timeline,
    render_output_path,
    rendered_video_exists,
    rendered_video_url,
)

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
                    "status": "ready",
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


@router.get("/{id}")
def get_film(id: str):
    if rendered_video_exists(id):
        return {
            "id": id,
            "title": f"Rendered Film {id}",
            "status": "available",
            "video_url": rendered_video_url(id),
        }
    return {"id": id, "title": "Sample Film", "status": "available"}


@router.post("/{draft_id}/render")
def render_film(draft_id: str, db: Session = Depends(get_db)):
    """Render a film draft timeline into a single MP4 file."""
    draft = (
        db.query(FilmDraft)
        .options(
            joinedload(FilmDraft.timeline_items).joinedload(TimelineItem.active_version),
            joinedload(FilmDraft.timeline_items).joinedload(TimelineItem.shot),
        )
        .filter(FilmDraft.id == draft_id)
        .first()
    )
    if draft is None:
        raise HTTPException(status_code=404, detail="Film draft not found")

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
    # Stub implementation for exporting a film
    return {"message": "Film exported successfully"}
