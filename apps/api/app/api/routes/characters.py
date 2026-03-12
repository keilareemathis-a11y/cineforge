from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.character import Character

router = APIRouter()


class CharacterCreate(BaseModel):
    user_id: str
    name: str
    description: Optional[str] = None
    reference_image_url: Optional[str] = None
    appearance_traits: Optional[dict[str, Any]] = None
    voice_profile: Optional[str] = None


class CharacterUpdate(BaseModel):
    user_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    reference_image_url: Optional[str] = None
    appearance_traits: Optional[dict[str, Any]] = None
    voice_profile: Optional[str] = None


def _character_to_dict(character: Character) -> dict:
    return {
        "id": character.id,
        "user_id": character.user_id,
        "name": character.name,
        "description": character.description,
        "reference_image_url": character.reference_image_url,
        "appearance_traits": character.appearance_traits,
        "voice_profile": character.voice_profile,
        "created_at": character.created_at.isoformat() if character.created_at else None,
    }


@router.post("")
def create_character(data: CharacterCreate, db: Session = Depends(get_db)):
    character = Character(**data.model_dump())
    db.add(character)
    db.commit()
    db.refresh(character)
    return _character_to_dict(character)


@router.get("")
def list_characters(db: Session = Depends(get_db)):
    characters = db.query(Character).all()
    return [_character_to_dict(character) for character in characters]


@router.get("/{character_id}")
def get_character(character_id: str, db: Session = Depends(get_db)):
    character = db.query(Character).filter(Character.id == character_id).first()
    if character is None:
        raise HTTPException(status_code=404, detail="Character not found")
    return _character_to_dict(character)


@router.patch("/{character_id}")
def update_character(character_id: str, data: CharacterUpdate, db: Session = Depends(get_db)):
    character = db.query(Character).filter(Character.id == character_id).first()
    if character is None:
        raise HTTPException(status_code=404, detail="Character not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(character, field, value)

    db.commit()
    db.refresh(character)
    return _character_to_dict(character)


@router.delete("/{character_id}")
def delete_character(character_id: str, db: Session = Depends(get_db)):
    character = db.query(Character).filter(Character.id == character_id).first()
    if character is None:
        raise HTTPException(status_code=404, detail="Character not found")

    db.delete(character)
    db.commit()
    return {"message": "Character deleted"}
