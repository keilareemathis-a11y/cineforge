from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.shot import Shot
from app.models.shot_version import ShotVersion

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
        "active_version_id": shot.active_version_id,
        "storyboard_image": shot.storyboard_image,
        "notes": shot.notes,
        "image_prompt": shot.image_prompt,
        "created_at": shot.created_at.isoformat() if shot.created_at else None,
        "updated_at": shot.updated_at.isoformat() if shot.updated_at else None,
    }


def _version_to_dict(version: ShotVersion) -> dict:
    return {
        "id": version.id,
        "shot_id": version.shot_id,
        "version_number": version.version_number,
        "image_url": version.image_url,
        "video_url": version.video_url,
        "status": version.status,
        "duration_seconds": version.duration_seconds,
        "trim_start": version.trim_start,
        "trim_end": version.trim_end,
        "created_at": version.created_at.isoformat() if version.created_at else None,
    }


def _versions_response(shot: Shot, versions: list) -> dict:
    return {
        "shot_id": shot.id,
        "active_version_id": shot.active_version_id,
        "versions": [_version_to_dict(v) for v in versions],
    }


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


@router.get("/{shot_id}/versions")
def get_shot_versions(shot_id: str, db: Session = Depends(get_db)):
    """Get all versions for a shot."""
    shot = db.query(Shot).filter(Shot.id == shot_id).first()
    if shot is None:
        raise HTTPException(status_code=404, detail="Shot not found")

    versions = (
        db.query(ShotVersion)
        .filter(ShotVersion.shot_id == shot_id)
        .order_by(ShotVersion.created_at.desc())
        .all()
    )
    return _versions_response(shot, versions)


@router.post("/{shot_id}/versions/{version_id}/select")
def select_shot_version(shot_id: str, version_id: str, db: Session = Depends(get_db)):
    """Select a specific version as the active version for a shot."""
    shot = db.query(Shot).filter(Shot.id == shot_id).first()
    if shot is None:
        raise HTTPException(status_code=404, detail="Shot not found")

    version = (
        db.query(ShotVersion)
        .filter(ShotVersion.id == version_id, ShotVersion.shot_id == shot_id)
        .first()
    )
    if version is None:
        raise HTTPException(status_code=404, detail="Shot version not found")

    shot.active_version_id = version_id
    db.commit()
    db.refresh(shot)

    versions = (
        db.query(ShotVersion)
        .filter(ShotVersion.shot_id == shot_id)
        .order_by(ShotVersion.created_at.desc())
        .all()
    )
    return _versions_response(shot, versions)


@router.post("/{shot_id}/regenerate")
def regenerate_shot(shot_id: str, db: Session = Depends(get_db)):
    """Create a new version of a shot (simulates regeneration)."""
    shot = db.query(Shot).filter(Shot.id == shot_id).first()
    if shot is None:
        raise HTTPException(status_code=404, detail="Shot not found")

    existing_count = db.query(ShotVersion).filter(ShotVersion.shot_id == shot_id).count()
    new_version = ShotVersion(
        shot_id=shot_id,
        version_number=existing_count + 1,
        status="pending",
    )
    db.add(new_version)
    db.commit()
    db.refresh(new_version)

    versions = (
        db.query(ShotVersion)
        .filter(ShotVersion.shot_id == shot_id)
        .order_by(ShotVersion.created_at.desc())
        .all()
    )
    return _versions_response(shot, versions)
