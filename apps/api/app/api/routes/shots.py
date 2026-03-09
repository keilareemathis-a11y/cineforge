from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.shot import Shot

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
    active_version_id: Optional[str] = None


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
