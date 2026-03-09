import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


scene_characters = Table(
    "scene_characters",
    Base.metadata,
    Column("scene_id", String, ForeignKey("scenes.id"), primary_key=True),
    Column("character_id", String, ForeignKey("characters.id"), primary_key=True),
)


class Scene(Base):
    __tablename__ = "scenes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    environment = Column(String, nullable=True)
    lighting = Column(String, nullable=True)
    weather = Column(String, nullable=True)
    mood = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    characters = relationship("Character", secondary=scene_characters, back_populates="scenes")
