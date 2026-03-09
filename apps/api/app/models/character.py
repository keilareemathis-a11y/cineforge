import uuid

from sqlalchemy import JSON, Column, DateTime, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.scene import scene_characters


class Character(Base):
    __tablename__ = "characters"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    reference_image_url = Column(String, nullable=True)
    appearance_traits = Column(JSON, nullable=True)
    voice_profile = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    scenes = relationship("Scene", secondary=scene_characters, back_populates="characters")
