from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, text

from app.core.database import get_db
from app.models.shot import Shot
from app.models.shot_version import ShotVersion
from app.models.timeline_item import TimelineItem
from app.services.generated_visuals import (
    build_shot_prompt,
    shot_storyboard_image,
    shot_version_image,
)
from app.services.video_generation import ensure_shot_version_video, shot_version_video_path, shot_version_video_url

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


class ShotRegenerateRequest(BaseModel):
    provider: Optional[str] = "runway"


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
        "storyboard_image": shot_storyboard_image(shot),
        "notes": shot.notes,
        "image_prompt": shot.image_prompt,
        "prompt": build_shot_prompt(shot),
        "active_version_id": shot.active_version_id,
        "created_at": shot.created_at.isoformat() if shot.created_at else None,
        "updated_at": shot.updated_at.isoformat() if shot.updated_at else None,
    }


def _version_to_dict(version: ShotVersion) -> dict:
    ensure_shot_version_video(version)
    return {
        "id": version.id,
        "shot_id": version.shot_id,
        "version_number": version.version_number,
        "duration_seconds": version.duration_seconds,
        "trim_start": version.trim_start,
        "trim_end": version.trim_end,
        "image_url": shot_version_image(version),
        "video_url": shot_version_video_url(version.shot_id, version.id),
        "status": version.status,
        "provider": version.provider,
        "prompt": build_shot_prompt(version.shot) if version.shot is not None else None,
        "created_at": version.created_at.isoformat() if version.created_at else None,
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
    db.flush()
    if not shot.storyboard_image:
        shot.storyboard_image = shot_storyboard_image(shot)
    db.commit()
    db.refresh(shot)
    return _shot_to_dict(shot)


@router.get("/{shot_id}/versions")
def get_shot_versions(shot_id: str, db: Session = Depends(get_db)):
    """List all versions for a shot, ordered by version_number DESC, created_at DESC, id DESC."""
    shot = db.query(Shot).filter(Shot.id == shot_id).first()
    if shot is None:
        raise HTTPException(status_code=404, detail="Shot not found")

    versions = (
        db.query(ShotVersion)
        .filter(ShotVersion.shot_id == shot_id)
        .order_by(
            desc(ShotVersion.version_number),
            desc(ShotVersion.created_at),
            desc(ShotVersion.id),
        )
        .all()
    )
    return [_version_to_dict(v) for v in versions]


@router.post("/{shot_id}/versions/{version_id}/select")
def select_shot_version(shot_id: str, version_id: str, db: Session = Depends(get_db)):
    """Set a specific ShotVersion as active and propagate it to timeline items."""
    shot = db.query(Shot).filter(Shot.id == shot_id).first()
    if shot is None:
        raise HTTPException(status_code=404, detail="Shot not found")

    version = (
        db.query(ShotVersion)
        .filter(ShotVersion.id == version_id, ShotVersion.shot_id == shot_id)
        .first()
    )
    if version is None:
        raise HTTPException(status_code=404, detail="ShotVersion not found")

    shot.active_version_id = version.id

    timeline_items = db.query(TimelineItem).filter(TimelineItem.shot_id == shot_id).all()
    for item in timeline_items:
        item.active_version_id = version.id

    db.commit()

    versions = (
        db.query(ShotVersion)
        .filter(ShotVersion.shot_id == shot_id)
        .order_by(
            desc(ShotVersion.version_number),
            desc(ShotVersion.created_at),
            desc(ShotVersion.id),
        )
        .all()
    )
    return {
        "shot_id": shot.id,
        "active_version_id": shot.active_version_id,
        "versions": [_version_to_dict(v) for v in versions],
    }


@router.post("/{shot_id}/regenerate")
def regenerate_shot(
    shot_id: str, data: Optional[ShotRegenerateRequest] = None, db: Session = Depends(get_db)
):
    """Create a new ShotVersion, increment version_number, propagate active_version_id to timeline items."""
    shot = db.query(Shot).filter(Shot.id == shot_id).first()
    if shot is None:
        raise HTTPException(status_code=404, detail="Shot not found")

    # Find the previous version to inherit fields from
    prev_version = (
        db.query(ShotVersion)
        .filter(ShotVersion.shot_id == shot_id)
        .order_by(desc(ShotVersion.version_number))
        .first()
    )

    if prev_version is not None:
        new_version_number = prev_version.version_number + 1
        duration_seconds = prev_version.duration_seconds
        trim_start = prev_version.trim_start
        trim_end = prev_version.trim_end
    else:
        new_version_number = 1
        duration_seconds = 1.0
        trim_start = 0.0
        trim_end = None

    new_version = ShotVersion(
        shot_id=shot_id,
        version_number=new_version_number,
        duration_seconds=duration_seconds,
        trim_start=trim_start,
        trim_end=trim_end,
        provider=(data.provider if data and data.provider else "runway"),
        status="ready",
    )
    db.add(new_version)
    db.flush()
    ensure_shot_version_video(new_version)

    # Set Shot.active_version_id to the new version
    shot.active_version_id = new_version.id

    # Propagate new active_version_id to all TimelineItem rows referencing this shot
    timeline_items = db.query(TimelineItem).filter(TimelineItem.shot_id == shot_id).all()
    for item in timeline_items:
        item.active_version_id = new_version.id

    db.commit()
    db.refresh(new_version)
    db.refresh(shot)

    return {
        "shot_id": shot.id,
        "active_version_id": shot.active_version_id,
        "new_version": _version_to_dict(new_version),
    }


@router.get("/{shot_id}/versions/{version_id}/video")
def get_shot_version_video(shot_id: str, version_id: str, db: Session = Depends(get_db)):
    """Serve the generated MP4 clip for a shot version."""
    version = (
        db.query(ShotVersion)
        .filter(ShotVersion.id == version_id, ShotVersion.shot_id == shot_id)
        .first()
    )
    if version is None:
        raise HTTPException(status_code=404, detail="ShotVersion not found")

    video_path = shot_version_video_path(version.id)
    if not video_path.exists():
        ensure_shot_version_video(version)

    return FileResponse(path=str(video_path), media_type="video/mp4", filename=f"{version_id}.mp4")


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

    visual_fields = {"title", "shot_type", "description", "camera_angle", "lens", "image_prompt"}
    if "storyboard_image" not in update_data and visual_fields.intersection(update_data):
        if not shot.storyboard_image or shot.storyboard_image.startswith("data:image/"):
            shot.storyboard_image = shot_storyboard_image(shot)

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
