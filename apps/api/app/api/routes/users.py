from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.Project import Project
from app.models.film_draft import FilmDraft
from app.models.timeline_item import TimelineItem
from app.services.platform_service import creator_profile, project_handle, published_film

router = APIRouter()


@router.get("")
def list_users(sort: str = "popular", db: Session = Depends(get_db)):
    projects = (
        db.query(Project)
        .options(
            joinedload(Project.film_drafts).joinedload(FilmDraft.timeline_items).joinedload(TimelineItem.shot),
            joinedload(Project.film_drafts).joinedload(FilmDraft.timeline_items).joinedload(TimelineItem.active_version),
        )
        .all()
    )

    creators = [
        creator_profile(project, project.film_drafts)
        for project in projects
        if any(draft.published_at for draft in project.film_drafts)
    ]
    creators.sort(key=lambda creator: creator["total_views"], reverse=(sort == "popular"))
    return creators


@router.get("/@{handle}")
def get_user_profile(handle: str, db: Session = Depends(get_db)):
    project = (
        db.query(Project)
        .options(
            joinedload(Project.film_drafts).joinedload(FilmDraft.timeline_items).joinedload(TimelineItem.shot),
            joinedload(Project.film_drafts).joinedload(FilmDraft.timeline_items).joinedload(TimelineItem.active_version),
        )
        .all()
    )
    matched = next((entry for entry in project if project_handle(entry) == handle), None)
    if matched is None:
        raise HTTPException(status_code=404, detail="Creator not found")

    profile = creator_profile(matched, matched.film_drafts)
    profile["films"] = [
        published_film(draft)
        for draft in matched.film_drafts
        if draft.published_at is not None
    ]
    profile["films"].sort(key=lambda film: film["published_at"] or "", reverse=True)
    return profile


@router.post("/{creator_id}/support")
def support_creator(creator_id: str, payload: dict, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == creator_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Creator not found")

    amount_cents = payload.get("amount_cents", 0)
    return {
        "clientSecret": f"support_{creator_id}_{amount_cents}",
    }
