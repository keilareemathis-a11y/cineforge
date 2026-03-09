import tempfile
from pathlib import Path

from moviepy import VideoFileClip, concatenate_videoclips

from app.services.video_generation import ensure_shot_version_video


RENDER_ROOT = Path(tempfile.gettempdir()) / "cineforge" / "renders"


def render_film_timeline(draft) -> dict:
    """Render a film draft timeline into a single MP4 file."""
    timeline_items = sorted(draft.timeline_items, key=lambda item: item.position)
    if not timeline_items:
        raise ValueError("Film draft has no timeline items to render")

    clips = []
    output_path = render_output_path(draft.id)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        for item in timeline_items:
            version = item.active_version
            if version is None:
                raise ValueError(f"Timeline item {item.id} has no active version")

            video_path = ensure_shot_version_video(version)
            duration = _effective_duration(item, version)
            trim_start = item.trim_start if item.trim_start is not None else version.trim_start or 0.0
            source_clip = VideoFileClip(str(video_path))
            source_duration = source_clip.duration or duration
            trim_end = min(trim_start + duration, source_duration)
            if trim_end <= trim_start:
                trim_start = 0.0
                trim_end = max(source_duration, 0.2)
            clip = source_clip.subclipped(trim_start, trim_end)
            clips.append(clip)

        final_clip = concatenate_videoclips(clips, method="compose")
        final_clip.write_videofile(
            str(output_path),
            fps=24,
            codec="libx264",
            audio=False,
            preset="ultrafast",
            logger=None,
        )
    finally:
        for clip in clips:
            clip.close()
        if "final_clip" in locals():
            final_clip.close()

    return {
        "draft_id": draft.id,
        "video_url": rendered_video_url(draft.id),
        "output_path": str(output_path),
    }


def render_output_path(draft_id: str) -> Path:
    return RENDER_ROOT / f"{draft_id}.mp4"


def rendered_video_url(draft_id: str) -> str:
    return f"/api/films/{draft_id}/rendered"


def rendered_video_exists(draft_id: str) -> bool:
    return render_output_path(draft_id).exists()


def _effective_duration(item, version) -> float:
    base_duration = item.duration_seconds
    if base_duration is None:
        base_duration = version.duration_seconds or 1.0

    trim_start = item.trim_start if item.trim_start is not None else version.trim_start or 0.0
    trim_end = item.trim_end if item.trim_end is not None else version.trim_end

    if trim_end is not None:
        duration = trim_end - trim_start
    else:
        duration = base_duration - trim_start

    return max(duration, 0.2)
