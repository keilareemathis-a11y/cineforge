import uuid

from sqlalchemy import Column, DateTime, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.associations import scene_characters


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
