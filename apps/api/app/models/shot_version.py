import uuid
from sqlalchemy import Column, String, Text, Float, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class ShotVersion(Base):
    """Versioned shot content."""

    __tablename__ = "shot_versions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    shot_id = Column(String, ForeignKey("shots.id"), nullable=False)
    version_number = Column(Integer, nullable=False, default=1)
    status = Column(String, nullable=False, default="queued")
    duration_seconds = Column(Float, nullable=False, default=0.0)
    trim_start = Column(Float, nullable=False, default=0.0)
    trim_end = Column(Float, nullable=True)
    image_url = Column(String, nullable=True)
    video_url = Column(String, nullable=True)
    prompt = Column(Text, nullable=True)
    style = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    shot = relationship("Shot", back_populates="versions", foreign_keys=[shot_id])
    timeline_items = relationship("TimelineItem", back_populates="active_version")
