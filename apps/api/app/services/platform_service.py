from typing import Iterable

from app.services.generated_visuals import shot_storyboard_image
from app.services.render_service import rendered_video_exists, rendered_video_url


def project_handle(project) -> str:
    base = "".join(ch.lower() if ch.isalnum() else "-" for ch in project.name).strip("-")
    collapsed = "-".join(part for part in base.split("-") if part)
    return collapsed or project.id[:8]


def creator_profile(project, drafts: Iterable) -> dict:
    published_drafts = [draft for draft in drafts if draft.published_at]
    total_views = sum(draft.view_count or 0 for draft in published_drafts)
    total_likes = sum(draft.like_count or 0 for draft in published_drafts)

    return {
        "id": project.id,
        "handle": project_handle(project),
        "display_name": project.name,
        "avatar_url": f"https://picsum.photos/seed/{project.id}/80/80",
        "banner_url": f"https://picsum.photos/seed/banner-{project.id}/1200/300",
        "bio": project.description or "AI filmmaker publishing iterative shorts on CineForge.",
        "follower_count": max(100, total_likes * 3 + len(published_drafts) * 25),
        "total_views": total_views,
        "film_count": len(published_drafts),
    }


def published_film(draft) -> dict:
    project = draft.project
    creator = creator_profile(project, project.film_drafts if project else [draft])
    timeline_items = sorted(draft.timeline_items, key=lambda item: item.position)
    thumbnail_url = ""
    for item in timeline_items:
        if item.shot is not None:
            thumbnail_url = shot_storyboard_image(item.shot)
            if thumbnail_url:
                break

    if not thumbnail_url:
        thumbnail_url = f"https://picsum.photos/seed/film-{draft.id}/640/360"

    duration_seconds = int(sum(_timeline_item_duration(item) for item in timeline_items))

    tags = [tag.strip() for tag in (draft.tags or "").split(",") if tag.strip()]

    return {
        "id": draft.id,
        "title": draft.title,
        "description": draft.description or "Published from CineForge's versioned film editor.",
        "thumbnail_url": thumbnail_url,
        "video_url": rendered_video_url(draft.id) if rendered_video_exists(draft.id) else "",
        "duration_seconds": max(duration_seconds, 1),
        "view_count": draft.view_count or 0,
        "like_count": draft.like_count or 0,
        "created_at": draft.created_at.isoformat() if draft.created_at else None,
        "published_at": draft.published_at.isoformat() if draft.published_at else None,
        "creator": creator,
        "tags": tags or ["ai", "short-film"],
    }


def _timeline_item_duration(item) -> float:
    if item.trim_end is not None:
        return item.trim_end - (item.trim_start or 0)

    base_duration = item.duration_seconds
    if base_duration is None:
        base_duration = item.active_version.duration_seconds if item.active_version else 0

    return base_duration - (item.trim_start or 0)
