from fastapi import APIRouter, HTTPException

router = APIRouter()

# In-memory storage for assets
assets = {}
next_id = 1


@router.post("/upload")
def upload_asset():
    global next_id
    asset_id = next_id
    assets[asset_id] = "uploaded_file"
    next_id += 1
    return {"id": asset_id, "filename": "uploaded_file"}


@router.get("/{id}")
def get_asset(id: int):
    if id in assets:
        return {"id": id, "filename": assets[id]}
    raise HTTPException(status_code=404, detail="Asset not found")


@router.delete("/{id}")
def delete_asset(id: int):
    if id in assets:
        del assets[id]
        return {"message": "Asset deleted"}
    raise HTTPException(status_code=404, detail="Asset not found")
