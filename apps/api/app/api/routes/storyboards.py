from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Any

router = APIRouter()


class StoryboardUpdate(BaseModel):
    content: Optional[Any] = None


@router.post("/generate")
def generate_storyboard():
    # Stub response
    return {
        "message": "Storyboard generated",
        "frames": [
            {"frame_id": 1, "content": "Frame 1 content"},
            {"frame_id": 2, "content": "Frame 2 content"},
        ],
    }


@router.get("/{id}")
def get_storyboard(id: int):
    # Stub response for a specific storyboard
    return {
        "id": id,
        "frames": [{"frame_id": id, "content": f"Storyboard frame content for id {id}"}],
    }


@router.put("/{id}")
def update_storyboard(id: int, data: StoryboardUpdate):
    # Stub response for updating a specific storyboard
    return {"message": "Storyboard updated", "id": id, "updated_data": data}