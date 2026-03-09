from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.models.shot import Shot
from app.models.shot_version import ShotVersion
from app.models.timeline_item import TimelineItem

router = APIRouter()


class ShotCreate(BaseModel):
    scene_id: str
    project_id: Optional[str] = None
    shot_number: Optional[int] = None
    title: Optional[str] = None
    shot_type: Optional[str] = ""
    description: Optional[str] = None
    camera_angle: Optional[str] = None
    lens: Optional[str] = None
    duration_estimate: Optional[float] = None
    status: Optional[str] = "planned"
    storyboard_image: Optional[str] = None
    notes: Optional[str] = None
    image_prompt: Optional[str] = None


class ShotUpdate(BaseModel):
    project_id: Optional[str] = None
    shot_number: Optional[int] = None
    title: Optional[str] = None
    shot_type: Optional[str] = None
    description: Optional[str] = None
    camera_angle: Optional[str] = None
    lens: Optional[str] = None
    duration_estimate: Optional[float] = None
    status: Optional[str] = None
    storyboard_image: Optional[str] = None
    notes: Optional[str] = None
    image_prompt: Optional[str] = None


def _shot_to_dict(shot: Shot) -> dict:
    return {
        "id": shot.id,
        "scene_id": shot.scene_id,
        "project_id": shot.project_id,
        "shot_number": shot.shot_number,
        "title": shot.title,
        "shot_type": shot.shot_type,
        "description": shot.description,
        "camera_angle": shot.camera_angle,
        "lens": shot.lens,
        "duration_estimate": shot.duration_estimate,
        "status": shot.status,
        "storyboard_image": shot.storyboard_image,
        "notes": shot.notes,
        "image_prompt": shot.image_prompt,
        "active_version_id": shot.active_version_id,
        "created_at": shot.created_at.isoformat() if shot.created_at else None,
        "updated_at": shot.updated_at.isoformat() if shot.updated_at else None,
    }


def _version_to_dict(version: ShotVersion) -> dict:
    return {
        "id": version.id,
        "shot_id": version.shot_id,
        "version_number": version.version_number,
        "duration_seconds": version.duration_seconds,
        "trim_start": version.trim_start,
        "trim_end": version.trim_end,
        "created_at": version.created_at.isoformat() if version.created_at else None,
    }


def _ordered_versions(shot_id: str, db: Session):
    """Return ShotVersion rows ordered by version_number DESC, created_at DESC, id DESC."""
    return (
        db.query(ShotVersion)
        .filter(ShotVersion.shot_id == shot_id)
        .order_by(desc(ShotVersion.version_number), desc(ShotVersion.created_at), desc(ShotVersion.id))
        .all()
    )


def _normalize_active_version(shot: Shot, db: Session) -> Optional[ShotVersion]:
    """If active_version_id is NULL, auto-select newest version and persist.

    Does NOT touch TimelineItem rows.
    Returns the active ShotVersion, or None if no versions exist.
    """
    if shot.active_version_id is not None:
        return db.query(ShotVersion).filter(ShotVersion.id == shot.active_version_id).first()

    versions = _ordered_versions(shot.id, db)
    if not versions:
        return None

    newest = versions[0]
    shot.active_version_id = newest.id
    db.commit()
    db.refresh(shot)
    return newest


@router.post("")
def create_shot(data: ShotCreate, db: Session = Depends(get_db)):
    """Create a new shot."""
    shot = Shot(
        scene_id=data.scene_id,
        project_id=data.project_id,
        shot_number=data.shot_number,
        title=data.title,
        shot_type=data.shot_type or "",
        description=data.description,
        camera_angle=data.camera_angle,
        lens=data.lens,
        duration_estimate=data.duration_estimate,
        status=data.status or "planned",
        storyboard_image=data.storyboard_image,
        notes=data.notes,
        image_prompt=data.image_prompt,
    )
    db.add(shot)
    db.commit()
    db.refresh(shot)
    return _shot_to_dict(shot)


@router.get("/{shot_id}")
def get_shot(shot_id: str, db: Session = Depends(get_db)):
    """Get a single shot by ID."""
    shot = db.query(Shot).filter(Shot.id == shot_id).first()
    if shot is None:
        raise HTTPException(status_code=404, detail="Shot not found")
    return _shot_to_dict(shot)


@router.patch("/{shot_id}")
def update_shot(shot_id: str, data: ShotUpdate, db: Session = Depends(get_db)):
    """Update a shot by ID."""
    shot = db.query(Shot).filter(Shot.id == shot_id).first()
    if shot is None:
        raise HTTPException(status_code=404, detail="Shot not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(shot, field, value)

    db.commit()
    db.refresh(shot)
    return _shot_to_dict(shot)


@router.delete("/{shot_id}")
def delete_shot(shot_id: str, db: Session = Depends(get_db)):
    """Delete a shot by ID."""
    shot = db.query(Shot).filter(Shot.id == shot_id).first()
    if shot is None:
        raise HTTPException(status_code=404, detail="Shot not found")

    db.delete(shot)
    db.commit()
    return {"message": "Shot deleted"}


@router.get("/{shot_id}/active-version")
def get_active_version(shot_id: str, db: Session = Depends(get_db)):
    """Return the active ShotVersion for a shot.

    If active_version_id is NULL, the newest version is auto-selected and
    persisted on the Shot row. TimelineItem rows are never touched.
    """
    shot = db.query(Shot).filter(Shot.id == shot_id).first()
    if shot is None:
        raise HTTPException(status_code=404, detail="Shot not found")

    active = _normalize_active_version(shot, db)
    if active is None:
        raise HTTPException(status_code=404, detail="No versions found for this shot")

    return _version_to_dict(active)


@router.get("/{shot_id}/versions")
def list_versions(shot_id: str, db: Session = Depends(get_db)):
    """List all versions for a shot, ordered newest-first, with is_active flag.

    If active_version_id is NULL, the newest version is auto-selected and
    persisted on the Shot row. TimelineItem rows are never touched.
    """
    shot = db.query(Shot).filter(Shot.id == shot_id).first()
    if shot is None:
        raise HTTPException(status_code=404, detail="Shot not found")

    _normalize_active_version(shot, db)

    versions = _ordered_versions(shot_id, db)
    active_id = shot.active_version_id

    return {
        "shot_id": shot_id,
        "active_version_id": active_id,
        "versions": [
            {**_version_to_dict(v), "is_active": v.id == active_id}
            for v in versions
        ],
    }


@router.post("/{shot_id}/regenerate")
def regenerate_shot(shot_id: str, db: Session = Depends(get_db)):
    """Create a new ShotVersion, set it active, and propagate to all TimelineItems."""
    shot = db.query(Shot).filter(Shot.id == shot_id).first()
    if shot is None:
        raise HTTPException(status_code=404, detail="Shot not found")

    existing = _ordered_versions(shot_id, db)

    if existing:
        prev = existing[0]
        max_version_number = prev.version_number
        new_duration = prev.duration_seconds
        new_trim_start = prev.trim_start
        new_trim_end = prev.trim_end
    else:
        max_version_number = 0
        new_duration = shot.duration_estimate or 0.0
        new_trim_start = 0.0
        new_trim_end = None

    new_version = ShotVersion(
        shot_id=shot_id,
        version_number=max_version_number + 1,
        duration_seconds=new_duration,
        trim_start=new_trim_start,
        trim_end=new_trim_end,
    )
    db.add(new_version)
    db.flush()  # get new_version.id before commit

    shot.active_version_id = new_version.id

    # Propagate to all TimelineItem rows for this shot
    db.query(TimelineItem).filter(TimelineItem.shot_id == shot_id).update(
        {"active_version_id": new_version.id}, synchronize_session=False
    )

    db.commit()
    db.refresh(shot)

    versions = _ordered_versions(shot_id, db)
    active_id = shot.active_version_id

    return {
        "shot_id": shot_id,
        "active_version_id": active_id,
        "versions": [
            {**_version_to_dict(v), "is_active": v.id == active_id}
            for v in versions
        ],
    }
