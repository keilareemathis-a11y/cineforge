import uuid
from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class TimelineItem(Base):
    """Editorial decision for a shot within a film draft timeline."""

    __tablename__ = "timeline_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    film_draft_id = Column(String, ForeignKey("film_drafts.id"), nullable=False)
    shot_id = Column(String, ForeignKey("shots.id"), nullable=False)
    active_version_id = Column(String, ForeignKey("shot_versions.id"), nullable=True)
    position = Column(Integer, nullable=False)
    duration_seconds = Column(Float, nullable=True)
    trim_start = Column(Float, nullable=False, default=0.0)
    trim_end = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    film_draft = relationship("FilmDraft", back_populates="timeline_items")
    shot = relationship("Shot", back_populates="timeline_items")
    active_version = relationship("ShotVersion", back_populates="timeline_items")
