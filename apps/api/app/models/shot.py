import uuid
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Shot(Base):
    """Immutable generated shot source material."""

    __tablename__ = "shots"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scene_id = Column(String, nullable=False)
    shot_type = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    image_prompt = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    versions = relationship("ShotVersion", back_populates="shot", cascade="all, delete-orphan")
    timeline_items = relationship("TimelineItem", back_populates="shot")
