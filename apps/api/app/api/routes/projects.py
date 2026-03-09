from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

# Sample data structure to store projects
projects = []


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None


@router.post("")
def create_project(data: ProjectCreate):
    project_id = len(projects) + 1
    project = {"id": project_id, "name": data.name, "description": data.description}
    projects.append(project)
    return project


@router.get("")
def get_projects():
    return projects


@router.put("/{project_id}")
def update_project(project_id: int, data: ProjectCreate):
    for project in projects:
        if project["id"] == project_id:
            project["name"] = data.name if data.name is not None else project["name"]
            project["description"] = data.description if data.description is not None else project["description"]
            return project
    raise HTTPException(status_code=404, detail="Project not found")


@router.delete("/{project_id}")
def delete_project(project_id: int):
    global projects
    projects = [p for p in projects if p["id"] != project_id]
    return {"message": "Project deleted"}
