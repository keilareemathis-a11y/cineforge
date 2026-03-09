import uuid
from sqlalchemy import Column, String, Text, DateTime, Integer, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Shot(Base):
    """Immutable generated shot source material."""

    __tablename__ = "shots"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scene_id = Column(String, nullable=False)
    project_id = Column(String, nullable=True)
    active_version_id = Column(String, nullable=True)
    shot_number = Column(Integer, nullable=True)
    title = Column(String, nullable=True)
    shot_type = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    camera_angle = Column(String, nullable=True)
    lens = Column(String, nullable=True)
    duration_estimate = Column(Float, nullable=True)
    status = Column(String, nullable=True, default="planned")
    storyboard_image = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    image_prompt = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    versions = relationship("ShotVersion", back_populates="shot", cascade="all, delete-orphan")
    timeline_items = relationship("TimelineItem", back_populates="shot")
