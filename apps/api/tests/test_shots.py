import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.api.routes.shots import router, _shots, _versions, _timeline_items, _seed
from app.models.shots import Shot, ShotVersion, TimelineItem

app = FastAPI()
app.include_router(router, prefix="/shots")

client = TestClient(app)


def _reset():
    """Reset in-memory stores to a clean seeded state."""
    _shots.clear()
    _versions.clear()
    _timeline_items.clear()
    _seed()


@pytest.fixture(autouse=True)
def reset_stores():
    _reset()
    yield
    _reset()


# ---------------------------------------------------------------------------
# POST /shots/{shot_id}/regenerate
# ---------------------------------------------------------------------------


class TestRegenerate:
    def test_regenerate_creates_new_version(self):
        resp = client.post(
            "/shots/shot_001/regenerate",
            json={"prompt": "Wide cityscape at sunset", "style": "cinematic"},
        )
        assert resp.status_code == 202
        data = resp.json()
        assert data["status"] == "queued"
        assert data["shot_id"] == "shot_001"
        nv = data["new_version"]
        assert nv["version_number"] == 2
        assert nv["prompt"] == "Wide cityscape at sunset"
        assert nv["style"] == "cinematic"
        assert nv["status"] == "queued"

    def test_regenerate_does_not_change_timeline(self):
        original_active = _shots["shot_001"].active_version_id
        original_timeline_version = _timeline_items[0].active_version_id

        client.post(
            "/shots/shot_001/regenerate",
            json={"prompt": "New prompt", "style": "dramatic"},
        )

        assert _shots["shot_001"].active_version_id == original_active
        assert _timeline_items[0].active_version_id == original_timeline_version

    def test_regenerate_shot_not_found_returns_404(self):
        resp = client.post(
            "/shots/nonexistent/regenerate",
            json={"prompt": "Test", "style": "test"},
        )
        assert resp.status_code == 404
        assert "nonexistent" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# POST /shots/{shot_id}/select-version
# ---------------------------------------------------------------------------


class TestSelectVersion:
    def _add_completed_version(self) -> str:
        """Helper: add a second completed version to shot_001 and return its id."""
        vid = "shotver_v2"
        _versions[vid] = ShotVersion(
            id=vid,
            shot_id="shot_001",
            version_number=2,
            prompt="Sunset shot",
            style="cinematic",
            status="completed",
            is_selected=False,
            image_url="https://example.com/img2.jpg",
            video_url="https://example.com/vid2.mp4",
        )
        _shots["shot_001"].versions.append(vid)
        return vid

    def test_select_completed_version(self):
        vid = self._add_completed_version()
        resp = client.post(
            "/shots/shot_001/select-version",
            json={"version_id": vid},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "selected"
        assert data["shot_id"] == "shot_001"
        assert data["active_version_id"] == vid

    def test_select_version_updates_shot_active_version(self):
        vid = self._add_completed_version()
        client.post(
            "/shots/shot_001/select-version",
            json={"version_id": vid},
        )
        assert _shots["shot_001"].active_version_id == vid

    def test_select_version_updates_is_selected_flag(self):
        vid = self._add_completed_version()
        client.post(
            "/shots/shot_001/select-version",
            json={"version_id": vid},
        )
        assert _versions[vid].is_selected is True
        assert _versions["shotver_v1"].is_selected is False

    def test_select_version_propagates_to_timeline_items(self):
        vid = self._add_completed_version()
        client.post(
            "/shots/shot_001/select-version",
            json={"version_id": vid},
        )
        for item in _timeline_items:
            if item.shot_id == "shot_001":
                assert item.active_version_id == vid

    def test_select_version_shot_not_found_returns_404(self):
        resp = client.post(
            "/shots/bad_shot/select-version",
            json={"version_id": "shotver_v1"},
        )
        assert resp.status_code == 404

    def test_select_version_version_not_found_returns_404(self):
        resp = client.post(
            "/shots/shot_001/select-version",
            json={"version_id": "nonexistent_version"},
        )
        assert resp.status_code == 404

    def test_select_version_version_belongs_to_different_shot_returns_404(self):
        other_shot = Shot(id="shot_002", versions=["shotver_other"])
        other_version = ShotVersion(
            id="shotver_other",
            shot_id="shot_002",
            version_number=1,
            prompt="Other",
            style="other",
            status="completed",
            is_selected=False,
            image_url="https://example.com/x.jpg",
            video_url="https://example.com/x.mp4",
        )
        _shots["shot_002"] = other_shot
        _versions["shotver_other"] = other_version

        resp = client.post(
            "/shots/shot_001/select-version",
            json={"version_id": "shotver_other"},
        )
        assert resp.status_code == 404

    def test_select_ready_version_succeeds(self):
        _versions["shotver_ready"] = ShotVersion(
            id="shotver_ready",
            shot_id="shot_001",
            version_number=2,
            prompt="test",
            style="cinematic",
            status="ready",
            is_selected=False,
            image_url="https://example.com/img_r.jpg",
            video_url="https://example.com/vid_r.mp4",
        )
        _shots["shot_001"].versions.append("shotver_ready")

        resp = client.post(
            "/shots/shot_001/select-version",
            json={"version_id": "shotver_ready"},
        )
        assert resp.status_code == 200
        assert resp.json()["active_version_id"] == "shotver_ready"

    def test_select_queued_version_returns_400(self):
        _versions["shotver_queued"] = ShotVersion(
            id="shotver_queued",
            shot_id="shot_001",
            version_number=2,
            prompt="test",
            style="test",
            status="queued",
        )
        _shots["shot_001"].versions.append("shotver_queued")

        resp = client.post(
            "/shots/shot_001/select-version",
            json={"version_id": "shotver_queued"},
        )
        assert resp.status_code == 400
        assert "queued" in resp.json()["detail"]

    def test_select_processing_version_returns_400(self):
        _versions["shotver_proc"] = ShotVersion(
            id="shotver_proc",
            shot_id="shot_001",
            version_number=2,
            prompt="test",
            style="test",
            status="processing",
        )
        _shots["shot_001"].versions.append("shotver_proc")

        resp = client.post(
            "/shots/shot_001/select-version",
            json={"version_id": "shotver_proc"},
        )
        assert resp.status_code == 400

    def test_select_failed_version_returns_400(self):
        _versions["shotver_fail"] = ShotVersion(
            id="shotver_fail",
            shot_id="shot_001",
            version_number=2,
            prompt="test",
            style="test",
            status="failed",
        )
        _shots["shot_001"].versions.append("shotver_fail")

        resp = client.post(
            "/shots/shot_001/select-version",
            json={"version_id": "shotver_fail"},
        )
        assert resp.status_code == 400
        assert "failed" in resp.json()["detail"]

    def test_select_completed_version_without_assets_returns_400(self):
        _versions["shotver_noassets"] = ShotVersion(
            id="shotver_noassets",
            shot_id="shot_001",
            version_number=2,
            prompt="test",
            style="test",
            status="completed",
        )
        _shots["shot_001"].versions.append("shotver_noassets")

        resp = client.post(
            "/shots/shot_001/select-version",
            json={"version_id": "shotver_noassets"},
        )
        assert resp.status_code == 400
        assert "assets" in resp.json()["detail"]
