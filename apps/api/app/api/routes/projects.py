from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.Project import Project

router = APIRouter()


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None


def _project_to_dict(project: Project) -> dict:
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
    }


@router.post("")
def create_project(data: ProjectCreate, db: Session = Depends(get_db)):
    """Create a new project."""
    project = Project(name=data.name, description=data.description)
    db.add(project)
    db.commit()
    db.refresh(project)
    return _project_to_dict(project)


@router.get("/{project_id}")
def get_project(project_id: str, db: Session = Depends(get_db)):
    """Get a project by ID."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return _project_to_dict(project)
