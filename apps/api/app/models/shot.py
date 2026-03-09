import uuid
from sqlalchemy import Column, String, Text, DateTime, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.models.shot_version import ShotVersion


class Shot(Base):
    """Immutable generated shot source material."""

    __tablename__ = "shots"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scene_id = Column(String, nullable=False)
    project_id = Column(String, nullable=True)
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
    active_version_id = Column(String, ForeignKey("shot_versions.id", use_alter=True, name="fk_shot_active_version"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    versions = relationship(
        "ShotVersion",
        foreign_keys=[ShotVersion.shot_id],
        back_populates="shot",
        cascade="all, delete-orphan",
    )
    active_version = relationship(
        "ShotVersion",
        foreign_keys=[active_version_id],
        post_update=True,
    )
    timeline_items = relationship("TimelineItem", back_populates="shot")
