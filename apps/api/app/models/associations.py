from sqlalchemy import Column, ForeignKey, String, Table

from app.core.database import Base


scene_characters = Table(
    "scene_characters",
    Base.metadata,
    Column("scene_id", String, ForeignKey("scenes.id", ondelete="CASCADE"), primary_key=True),
    Column("character_id", String, ForeignKey("characters.id", ondelete="CASCADE"), primary_key=True),
)
