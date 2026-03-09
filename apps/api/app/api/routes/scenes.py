from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.character import Character
from app.models.scene import Scene
from app.models.shot import Shot
from app.services.generated_visuals import build_shot_prompt, shot_storyboard_image

router = APIRouter()


class SceneCreate(BaseModel):
    project_id: str
    title: str
    environment: Optional[str] = None
    lighting: Optional[str] = None
    weather: Optional[str] = None
    mood: Optional[str] = None
    character_ids: list[str] = []


def _scene_to_dict(scene: Scene) -> dict:
    return {
        "id": scene.id,
        "project_id": scene.project_id,
        "title": scene.title,
        "environment": scene.environment,
        "lighting": scene.lighting,
        "weather": scene.weather,
        "mood": scene.mood,
        "character_ids": [character.id for character in scene.characters],
        "created_at": scene.created_at.isoformat() if scene.created_at else None,
    }


def _load_characters(character_ids: list[str], db: Session) -> list[Character]:
    if not character_ids:
        return []

    characters = db.query(Character).filter(Character.id.in_(character_ids)).all()
    found_ids = {character.id for character in characters}
    missing_ids = [character_id for character_id in character_ids if character_id not in found_ids]
    if missing_ids:
        raise HTTPException(status_code=404, detail=f"Character not found: {missing_ids[0]}")
    return characters


@router.post("")
def create_scene(data: SceneCreate, db: Session = Depends(get_db)):
    scene = Scene(
        project_id=data.project_id,
        title=data.title,
        environment=data.environment,
        lighting=data.lighting,
        weather=data.weather,
        mood=data.mood,
    )
    scene.characters = _load_characters(data.character_ids, db)
    db.add(scene)
    db.commit()
    db.refresh(scene)
    return _scene_to_dict(scene)


@router.get("")
def list_scenes(db: Session = Depends(get_db)):
    scenes = db.query(Scene).all()
    return [_scene_to_dict(scene) for scene in scenes]


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


@router.get("/{scene_id}")
def get_scene(scene_id: str, db: Session = Depends(get_db)):
    scene = db.query(Scene).filter(Scene.id == scene_id).first()
    if scene is None:
        raise HTTPException(status_code=404, detail="Scene not found")
    return _scene_to_dict(scene)
