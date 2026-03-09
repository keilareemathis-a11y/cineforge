import hashlib
import tempfile
from pathlib import Path

from moviepy import ColorClip, concatenate_videoclips


SHOT_VIDEO_ROOT = Path(tempfile.gettempdir()) / "cineforge" / "shot_versions"

PROVIDER_COLORS = {
    "runway": ((80, 46, 173), (35, 98, 191), (26, 164, 126)),
    "pika": ((191, 64, 112), (247, 146, 86), (255, 214, 102)),
    "stable-video-diffusion": ((46, 84, 120), (82, 120, 176), (170, 210, 255)),
}


def ensure_shot_version_video(version) -> Path:
    """Create a deterministic MP4 clip for a shot version if one does not already exist."""
    output_path = shot_version_video_path(version.id)
    if output_path.exists():
        return output_path

    provider = getattr(version, "provider", None) or "runway"
    palette = PROVIDER_COLORS.get(provider, PROVIDER_COLORS["runway"])
    duration = max(float(getattr(version, "duration_seconds", 1.0) or 1.0), 0.6)
    segment_duration = max(duration / len(palette), 0.2)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    clips = []
    try:
        for index, base_color in enumerate(palette):
            clips.append(
                ColorClip(
                    size=(1280, 720),
                    color=_variant_color(base_color, f"{version.id}:{provider}:{index}"),
                    duration=segment_duration,
                )
            )

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

    return output_path


def shot_version_video_path(version_id: str) -> Path:
    return SHOT_VIDEO_ROOT / f"{version_id}.mp4"


def shot_version_video_url(shot_id: str, version_id: str) -> str:
    return f"/api/shots/{shot_id}/versions/{version_id}/video"


def _variant_color(base_color: tuple[int, int, int], seed: str) -> tuple[int, int, int]:
    if len(base_color) != 3:
        raise ValueError("base_color must contain exactly 3 channels")
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    return (
        min(255, max(32, base_color[0] + ((digest[0] % 40) - 20))),
        min(255, max(32, base_color[1] + ((digest[1] % 40) - 20))),
        min(255, max(32, base_color[2] + ((digest[2] % 40) - 20))),
    )
