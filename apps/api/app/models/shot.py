from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from apps.api.app.models.base import Base  # Adjust the import according to your project structure

class Shot(Base):
    __tablename__ = 'shots'

    # Existing fields
    # ... [other fields remain the same]
    
    active_version_id = Column(String, ForeignKey('shot_versions.id'))
    active_version = relationship('ShotVersion', foreign_keys=[active_version_id])

    versions = relationship('ShotVersion',
                            foreign_keys='ShotVersion.shot_id',
                            backref='shot')

# Any other code or classes you have will go here...