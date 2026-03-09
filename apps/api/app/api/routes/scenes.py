from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.shot import Shot
from app.services.generated_visuals import build_shot_prompt, shot_storyboard_image

router = APIRouter()


@router.post("/generate")
def generate_scene():
    # Stub response for scene generation
    return {"message": "Scene generation initiated", "status": "success"}


@router.get("/{scene_id}/shots")
def get_shots_by_scene(scene_id: str, db: Session = Depends(get_db)):
    """Get all shots belonging to a scene."""
    shots = db.query(Shot).filter(Shot.scene_id == scene_id).all()
    return [
        {
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
            "created_at": shot.created_at.isoformat() if shot.created_at else None,
            "updated_at": shot.updated_at.isoformat() if shot.updated_at else None,
        }
        for shot in shots
    ]


@router.get("/{id}")
def get_scene(id: str):
    # Stub response for retrieving scene by ID
    return {"id": id, "message": "Scene details", "status": "success"}
