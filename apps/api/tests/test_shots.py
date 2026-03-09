import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.models.shot import Shot
from app.models.shot_version import ShotVersion
from app.models.timeline_item import TimelineItem

TEST_DATABASE_URL = "sqlite:///./test_shots.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_shot(scene_id="scene_1", **kwargs):
    payload = {"scene_id": scene_id, **kwargs}
    resp = client.post("/api/shots", json=payload)
    assert resp.status_code == 200
    return resp.json()


def _add_version(shot_id: str, version_number: int = 1, duration_seconds: float = 5.0,
                 trim_start: float = 0.0, trim_end: float = None) -> ShotVersion:
    """Directly insert a ShotVersion into the test DB."""
    db = TestingSessionLocal()
    try:
        v = ShotVersion(
            shot_id=shot_id,
            version_number=version_number,
            duration_seconds=duration_seconds,
            trim_start=trim_start,
            trim_end=trim_end,
        )
        db.add(v)
        db.commit()
        db.refresh(v)
        return v
    finally:
        db.close()


def _add_timeline_item(shot_id: str, active_version_id: str = None) -> TimelineItem:
    """Directly insert a minimal TimelineItem into the test DB."""
    db = TestingSessionLocal()
    try:
        # We need a film_draft_id that exists; use a stub string (no FK enforcement in SQLite)
        item = TimelineItem(
            film_draft_id="draft-1",
            shot_id=shot_id,
            active_version_id=active_version_id,
            position=0,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item
    finally:
        db.close()


def _get_timeline_item(item_id: str) -> TimelineItem:
    db = TestingSessionLocal()
    try:
        return db.query(TimelineItem).filter(TimelineItem.id == item_id).first()
    finally:
        db.close()


def _get_shot_db(shot_id: str) -> Shot:
    db = TestingSessionLocal()
    try:
        return db.query(Shot).filter(Shot.id == shot_id).first()
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Existing tests (unchanged)
# ---------------------------------------------------------------------------

class TestCreateShot:
    def test_create_shot_minimal(self):
        response = client.post("/api/shots", json={"scene_id": "scene_1"})
        assert response.status_code == 200
        data = response.json()
        assert data["scene_id"] == "scene_1"
        assert data["status"] == "planned"
        assert "id" in data

    def test_create_shot_full(self):
        payload = {
            "scene_id": "scene_12",
            "project_id": "film_88",
            "shot_number": 3,
            "title": "Over-the-shoulder dialogue",
            "description": "Camera behind protagonist facing antagonist",
            "camera_angle": "OTS",
            "lens": "50mm",
            "duration_estimate": 6.0,
            "status": "planned",
            "storyboard_image": "https://example.com/img.png",
            "notes": "Slow push-in during dialogue",
        }
        response = client.post("/api/shots", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["scene_id"] == "scene_12"
        assert data["project_id"] == "film_88"
        assert data["shot_number"] == 3
        assert data["title"] == "Over-the-shoulder dialogue"
        assert data["camera_angle"] == "OTS"
        assert data["lens"] == "50mm"
        assert data["duration_estimate"] == 6.0
        assert data["status"] == "planned"
        assert data["notes"] == "Slow push-in during dialogue"


class TestGetShot:
    def test_get_shot(self):
        create_resp = client.post("/api/shots", json={"scene_id": "scene_1", "title": "Wide establishing"})
        shot_id = create_resp.json()["id"]

        response = client.get(f"/api/shots/{shot_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == shot_id
        assert data["title"] == "Wide establishing"

    def test_get_shot_not_found(self):
        response = client.get("/api/shots/nonexistent-id")
        assert response.status_code == 404
        assert response.json()["detail"] == "Shot not found"

    def test_get_shot_includes_active_version_id(self):
        shot = _create_shot()
        shot_id = shot["id"]
        v = _add_version(shot_id, version_number=1)

        resp = client.get(f"/api/shots/{shot_id}")
        assert resp.status_code == 200
        assert "active_version_id" in resp.json()


class TestUpdateShot:
    def test_update_shot(self):
        create_resp = client.post("/api/shots", json={"scene_id": "scene_1", "camera_angle": "Wide"})
        shot_id = create_resp.json()["id"]

        response = client.patch(f"/api/shots/{shot_id}", json={"camera_angle": "Close-up", "lens": "85mm"})
        assert response.status_code == 200
        data = response.json()
        assert data["camera_angle"] == "Close-up"
        assert data["lens"] == "85mm"
        assert data["scene_id"] == "scene_1"

    def test_update_shot_not_found(self):
        response = client.patch("/api/shots/nonexistent-id", json={"title": "New Title"})
        assert response.status_code == 404
        assert response.json()["detail"] == "Shot not found"


class TestDeleteShot:
    def test_delete_shot(self):
        create_resp = client.post("/api/shots", json={"scene_id": "scene_1"})
        shot_id = create_resp.json()["id"]

        response = client.delete(f"/api/shots/{shot_id}")
        assert response.status_code == 200
        assert response.json()["message"] == "Shot deleted"

        get_resp = client.get(f"/api/shots/{shot_id}")
        assert get_resp.status_code == 404

    def test_delete_shot_not_found(self):
        response = client.delete("/api/shots/nonexistent-id")
        assert response.status_code == 404
        assert response.json()["detail"] == "Shot not found"


class TestGetShotsByScene:
    def test_get_shots_by_scene(self):
        client.post("/api/shots", json={"scene_id": "scene_99", "title": "Wide establishing"})
        client.post("/api/shots", json={"scene_id": "scene_99", "title": "Close-up reaction"})
        client.post("/api/shots", json={"scene_id": "scene_other", "title": "Other scene shot"})

        response = client.get("/api/scenes/scene_99/shots")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        titles = {s["title"] for s in data}
        assert "Wide establishing" in titles
        assert "Close-up reaction" in titles

    def test_get_shots_by_scene_empty(self):
        response = client.get("/api/scenes/scene_empty/shots")
        assert response.status_code == 200
        assert response.json() == []


# ---------------------------------------------------------------------------
# New tests: active_version_id in shot response
# ---------------------------------------------------------------------------

class TestShotActiveVersionId:
    def test_active_version_id_null_on_new_shot(self):
        shot = _create_shot()
        assert shot["active_version_id"] is None

    def test_active_version_id_present_after_setting(self):
        shot = _create_shot()
        shot_id = shot["id"]
        v = _add_version(shot_id, version_number=1)

        # Set active_version_id via regenerate
        resp = client.post(f"/api/shots/{shot_id}/regenerate")
        assert resp.status_code == 200
        shot_resp = client.get(f"/api/shots/{shot_id}")
        assert shot_resp.json()["active_version_id"] is not None


# ---------------------------------------------------------------------------
# New tests: GET /shots/{shot_id}/active-version
# ---------------------------------------------------------------------------

class TestGetActiveVersion:
    def test_returns_correct_active_version(self):
        shot = _create_shot()
        shot_id = shot["id"]
        v1 = _add_version(shot_id, version_number=1, duration_seconds=3.0)
        v2 = _add_version(shot_id, version_number=2, duration_seconds=4.5)

        # Manually set active_version_id to v1
        db = TestingSessionLocal()
        try:
            s = db.query(Shot).filter(Shot.id == shot_id).first()
            s.active_version_id = v1.id
            db.commit()
        finally:
            db.close()

        resp = client.get(f"/api/shots/{shot_id}/active-version")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == v1.id
        assert data["shot_id"] == shot_id
        assert data["version_number"] == 1
        assert data["duration_seconds"] == 3.0
        assert data["trim_start"] == 0.0
        assert "trim_end" in data
        assert "created_at" in data

    def test_normalizes_null_active_version_id(self):
        """When active_version_id is NULL, the newest version should be auto-selected."""
        shot = _create_shot()
        shot_id = shot["id"]
        v1 = _add_version(shot_id, version_number=1)
        v2 = _add_version(shot_id, version_number=2)

        resp = client.get(f"/api/shots/{shot_id}/active-version")
        assert resp.status_code == 200
        data = resp.json()
        # Should return the newest (version_number=2)
        assert data["version_number"] == 2

        # active_version_id should now be persisted on the shot
        shot_row = _get_shot_db(shot_id)
        assert shot_row.active_version_id == v2.id

    def test_does_not_modify_timeline_items(self):
        """active-version endpoint must NOT touch TimelineItem rows."""
        shot = _create_shot()
        shot_id = shot["id"]
        v1 = _add_version(shot_id, version_number=1)
        item = _add_timeline_item(shot_id, active_version_id=None)

        client.get(f"/api/shots/{shot_id}/active-version")

        refreshed = _get_timeline_item(item.id)
        assert refreshed.active_version_id is None

    def test_returns_404_when_no_versions(self):
        shot = _create_shot()
        resp = client.get(f"/api/shots/{shot['id']}/active-version")
        assert resp.status_code == 404

    def test_returns_404_when_shot_not_found(self):
        resp = client.get("/api/shots/nonexistent/active-version")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# New tests: GET /shots/{shot_id}/versions
# ---------------------------------------------------------------------------

class TestListVersions:
    def test_versions_ordered_newest_first(self):
        shot = _create_shot()
        shot_id = shot["id"]
        _add_version(shot_id, version_number=1)
        _add_version(shot_id, version_number=3)
        _add_version(shot_id, version_number=2)

        resp = client.get(f"/api/shots/{shot_id}/versions")
        assert resp.status_code == 200
        data = resp.json()
        nums = [v["version_number"] for v in data["versions"]]
        assert nums == sorted(nums, reverse=True)

    def test_is_active_flag_present(self):
        shot = _create_shot()
        shot_id = shot["id"]
        v1 = _add_version(shot_id, version_number=1)
        v2 = _add_version(shot_id, version_number=2)

        db = TestingSessionLocal()
        try:
            s = db.query(Shot).filter(Shot.id == shot_id).first()
            s.active_version_id = v1.id
            db.commit()
        finally:
            db.close()

        resp = client.get(f"/api/shots/{shot_id}/versions")
        assert resp.status_code == 200
        versions = resp.json()["versions"]
        active_flags = {v["id"]: v["is_active"] for v in versions}
        assert active_flags[v1.id] is True
        assert active_flags[v2.id] is False

    def test_normalization_auto_selects_newest_when_null(self):
        shot = _create_shot()
        shot_id = shot["id"]
        v1 = _add_version(shot_id, version_number=1)
        v2 = _add_version(shot_id, version_number=2)

        resp = client.get(f"/api/shots/{shot_id}/versions")
        assert resp.status_code == 200
        data = resp.json()
        # active_version_id points to newest
        assert data["active_version_id"] == v2.id
        active_versions = [v for v in data["versions"] if v["is_active"]]
        assert len(active_versions) == 1
        assert active_versions[0]["version_number"] == 2

    def test_normalization_does_not_modify_timeline_items(self):
        shot = _create_shot()
        shot_id = shot["id"]
        _add_version(shot_id, version_number=1)
        item = _add_timeline_item(shot_id, active_version_id=None)

        client.get(f"/api/shots/{shot_id}/versions")

        refreshed = _get_timeline_item(item.id)
        assert refreshed.active_version_id is None

    def test_returns_shot_not_found(self):
        resp = client.get("/api/shots/no-such-shot/versions")
        assert resp.status_code == 404

    def test_empty_versions_list(self):
        shot = _create_shot()
        resp = client.get(f"/api/shots/{shot['id']}/versions")
        assert resp.status_code == 200
        data = resp.json()
        assert data["versions"] == []
        assert data["active_version_id"] is None


# ---------------------------------------------------------------------------
# New tests: POST /shots/{shot_id}/regenerate
# ---------------------------------------------------------------------------

class TestRegenerateShot:
    def test_no_body_succeeds(self):
        """POST with no request body must succeed."""
        shot = _create_shot()
        resp = client.post(f"/api/shots/{shot['id']}/regenerate")
        assert resp.status_code == 200

    def test_version_number_increments(self):
        shot = _create_shot()
        shot_id = shot["id"]
        _add_version(shot_id, version_number=1)
        _add_version(shot_id, version_number=2)

        resp = client.post(f"/api/shots/{shot_id}/regenerate")
        assert resp.status_code == 200
        data = resp.json()
        version_numbers = [v["version_number"] for v in data["versions"]]
        assert max(version_numbers) == 3

    def test_version_number_starts_at_1_when_no_existing_versions(self):
        shot = _create_shot()
        resp = client.post(f"/api/shots/{shot['id']}/regenerate")
        assert resp.status_code == 200
        data = resp.json()
        assert data["versions"][0]["version_number"] == 1

    def test_shot_active_version_id_updated(self):
        shot = _create_shot()
        shot_id = shot["id"]
        _add_version(shot_id, version_number=1)

        resp = client.post(f"/api/shots/{shot_id}/regenerate")
        assert resp.status_code == 200
        data = resp.json()
        new_active_id = data["active_version_id"]

        shot_row = _get_shot_db(shot_id)
        assert shot_row.active_version_id == new_active_id

    def test_new_version_marked_active(self):
        shot = _create_shot()
        shot_id = shot["id"]
        _add_version(shot_id, version_number=1)

        resp = client.post(f"/api/shots/{shot_id}/regenerate")
        assert resp.status_code == 200
        versions = resp.json()["versions"]
        active_versions = [v for v in versions if v["is_active"]]
        assert len(active_versions) == 1
        assert active_versions[0]["version_number"] == 2

    def test_timeline_items_propagated(self):
        """All TimelineItem rows for the shot must have active_version_id updated."""
        shot = _create_shot()
        shot_id = shot["id"]
        v1 = _add_version(shot_id, version_number=1)
        item1 = _add_timeline_item(shot_id, active_version_id=v1.id)
        item2 = _add_timeline_item(shot_id, active_version_id=v1.id)

        resp = client.post(f"/api/shots/{shot_id}/regenerate")
        assert resp.status_code == 200
        new_active_id = resp.json()["active_version_id"]

        assert _get_timeline_item(item1.id).active_version_id == new_active_id
        assert _get_timeline_item(item2.id).active_version_id == new_active_id

    def test_timeline_items_across_drafts_propagated(self):
        """TimelineItems across multiple drafts for the same shot are all updated."""
        shot = _create_shot()
        shot_id = shot["id"]
        v1 = _add_version(shot_id, version_number=1)

        # Add items belonging to different film_draft_ids
        db = TestingSessionLocal()
        try:
            item_a = TimelineItem(film_draft_id="draft-A", shot_id=shot_id,
                                  active_version_id=v1.id, position=0)
            item_b = TimelineItem(film_draft_id="draft-B", shot_id=shot_id,
                                  active_version_id=v1.id, position=1)
            db.add_all([item_a, item_b])
            db.commit()
            item_a_id = item_a.id
            item_b_id = item_b.id
        finally:
            db.close()

        resp = client.post(f"/api/shots/{shot_id}/regenerate")
        assert resp.status_code == 200
        new_active_id = resp.json()["active_version_id"]

        assert _get_timeline_item(item_a_id).active_version_id == new_active_id
        assert _get_timeline_item(item_b_id).active_version_id == new_active_id

    def test_inherits_duration_from_previous_version(self):
        shot = _create_shot(duration_estimate=10.0)
        shot_id = shot["id"]
        _add_version(shot_id, version_number=1, duration_seconds=7.5, trim_start=0.5, trim_end=6.0)

        resp = client.post(f"/api/shots/{shot_id}/regenerate")
        assert resp.status_code == 200
        versions = resp.json()["versions"]
        new_version = next(v for v in versions if v["version_number"] == 2)
        assert new_version["duration_seconds"] == 7.5
        assert new_version["trim_start"] == 0.5
        assert new_version["trim_end"] == 6.0

    def test_uses_duration_estimate_when_no_previous_version(self):
        shot = _create_shot(duration_estimate=8.0)
        resp = client.post(f"/api/shots/{shot['id']}/regenerate")
        assert resp.status_code == 200
        versions = resp.json()["versions"]
        assert versions[0]["duration_seconds"] == 8.0

    def test_returns_404_when_shot_not_found(self):
        resp = client.post("/api/shots/no-such-shot/regenerate")
        assert resp.status_code == 404
