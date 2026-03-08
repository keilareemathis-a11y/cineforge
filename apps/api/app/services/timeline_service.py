from typing import List, Dict, Any

from sqlalchemy.orm import Session

from app.models.film_draft import FilmDraft
from app.models.shot import Shot
from app.models.shot_version import ShotVersion
from app.models.timeline_item import TimelineItem


def create_film_draft_from_scenes(
    project_id: str,
    title: str,
    scenes: List[Dict[str, Any]],
    db: Session,
) -> FilmDraft:
    """Convert scene generation output into a FilmDraft with TimelineItems and Shots.

    Args:
        project_id: ID of the owning project.
        title: Title for the new film draft.
        scenes: List of scene dicts, each containing a list of shot dicts.
        db: Active SQLAlchemy database session.

    Returns:
        The newly created FilmDraft (not yet committed).
    """
    draft = FilmDraft(project_id=project_id, title=title)
    db.add(draft)
    db.flush()

    position = 0
    for scene in scenes:
        scene_id = scene.get("scene_id", "")
        for shot_data in scene.get("shots", []):
            shot = Shot(
                scene_id=scene_id,
                shot_type=shot_data.get("shot_type", ""),
                description=shot_data.get("description"),
                image_prompt=shot_data.get("image_prompt"),
            )
            db.add(shot)
            db.flush()

            version = ShotVersion(
                shot_id=shot.id,
                version_number=1,
                duration_seconds=shot_data.get("duration_seconds") or 0.0,
                trim_start=0.0,
                trim_end=None,
            )
            db.add(version)
            db.flush()

            item = TimelineItem(
                film_draft_id=draft.id,
                shot_id=shot.id,
                active_version_id=version.id,
                position=position,
                duration_seconds=shot_data.get("duration_seconds"),
                trim_start=0.0,
                trim_end=None,
            )
            db.add(item)
            position += 1

    db.commit()
    db.refresh(draft)
    return draft
