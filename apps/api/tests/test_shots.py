import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.models.Project import Project
from app.models.film_draft import FilmDraft
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
# Test helpers
# ---------------------------------------------------------------------------


def _create_project_and_drafts(n_drafts=2):
    """Create a project and *n_drafts* film drafts; return (project_id, [draft_id, ...])."""
    db = TestingSessionLocal()
    try:
        project = Project(name="Test Project")
        db.add(project)
        db.flush()
        draft_ids = []
        for i in range(n_drafts):
            draft = FilmDraft(project_id=project.id, title=f"Draft {i + 1}")
            db.add(draft)
            db.flush()
            draft_ids.append(draft.id)
        db.commit()
        return project.id, draft_ids
    finally:
        db.close()


def _create_timeline_items(shot_id, draft_ids, version_id=None):
    """Create one TimelineItem per draft for the given shot; return item ids."""
    db = TestingSessionLocal()
    try:
        item_ids = []
        for i, draft_id in enumerate(draft_ids):
            item = TimelineItem(
                film_draft_id=draft_id,
                shot_id=shot_id,
                active_version_id=version_id,
                position=i,
                duration_seconds=5.0,
                trim_start=0.0,
            )
            db.add(item)
            db.flush()
            item_ids.append(item.id)
        db.commit()
        return item_ids
    finally:
        db.close()


def _create_version(shot_id, version_number=1, duration_seconds=5.0):
    """Create a ShotVersion directly in the DB; return the new version id."""
    db = TestingSessionLocal()
    try:
        v = ShotVersion(
            shot_id=shot_id,
            version_number=version_number,
            duration_seconds=duration_seconds,
            trim_start=0.0,
        )
        db.add(v)
        db.commit()
        db.refresh(v)
        return v.id
    finally:
        db.close()


def _get_timeline_item_version(item_id):
    """Return the active_version_id stored for a TimelineItem (raises if not found)."""
    db = TestingSessionLocal()
    try:
        item = db.query(TimelineItem).filter(TimelineItem.id == item_id).first()
        assert item is not None, f"TimelineItem {item_id!r} not found in test database"
        return item.active_version_id
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Existing CRUD tests
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

    def test_get_shot_includes_active_version_id(self):
        create_resp = client.post("/api/shots", json={"scene_id": "scene_1"})
        shot_id = create_resp.json()["id"]

        response = client.get(f"/api/shots/{shot_id}")
        assert response.status_code == 200
        assert "active_version_id" in response.json()

    def test_get_shot_not_found(self):
        response = client.get("/api/shots/nonexistent-id")
        assert response.status_code == 404
        assert response.json()["detail"] == "Shot not found"


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
# GET /versions tests
# ---------------------------------------------------------------------------


class TestGetShotVersions:
    def test_get_versions_empty(self):
        create_resp = client.post("/api/shots", json={"scene_id": "scene_1"})
        shot_id = create_resp.json()["id"]

        response = client.get(f"/api/shots/{shot_id}/versions")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_versions_ordered(self):
        create_resp = client.post("/api/shots", json={"scene_id": "scene_1"})
        shot_id = create_resp.json()["id"]

        _create_version(shot_id, version_number=1, duration_seconds=3.0)
        _create_version(shot_id, version_number=2, duration_seconds=4.0)
        _create_version(shot_id, version_number=3, duration_seconds=5.0)

        response = client.get(f"/api/shots/{shot_id}/versions")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["version_number"] == 3
        assert data[1]["version_number"] == 2
        assert data[2]["version_number"] == 1

    def test_normalization_sets_active_version_id(self):
        """GET /versions normalizes shot.active_version_id to the most recent version."""
        create_resp = client.post("/api/shots", json={"scene_id": "scene_1"})
        shot_id = create_resp.json()["id"]
        assert create_resp.json()["active_version_id"] is None

        _create_version(shot_id, version_number=1, duration_seconds=3.0)
        v2_id = _create_version(shot_id, version_number=2, duration_seconds=4.0)

        response = client.get(f"/api/shots/{shot_id}/versions")
        assert response.status_code == 200
        assert response.json()[0]["version_number"] == 2

        shot_resp = client.get(f"/api/shots/{shot_id}")
        assert shot_resp.json()["active_version_id"] == v2_id

    def test_no_timeline_mutation_on_get(self):
        """GET /versions normalizes only the shot; timeline items are NOT touched."""
        _, draft_ids = _create_project_and_drafts(n_drafts=1)

        create_resp = client.post("/api/shots", json={"scene_id": "scene_1"})
        shot_id = create_resp.json()["id"]

        v1_id = _create_version(shot_id, version_number=1, duration_seconds=3.0)
        v2_id = _create_version(shot_id, version_number=2, duration_seconds=4.0)
        item_ids = _create_timeline_items(shot_id, draft_ids, version_id=v1_id)

        client.get(f"/api/shots/{shot_id}/versions")

        shot_resp = client.get(f"/api/shots/{shot_id}")
        assert shot_resp.json()["active_version_id"] == v2_id

        assert _get_timeline_item_version(item_ids[0]) == v1_id

    def test_get_versions_not_found(self):
        response = client.get("/api/shots/nonexistent-id/versions")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /versions/{version_id}/select tests
# ---------------------------------------------------------------------------


class TestSelectVersion:
    def test_select_version_updates_shot(self):
        create_resp = client.post("/api/shots", json={"scene_id": "scene_1"})
        shot_id = create_resp.json()["id"]

        v1_id = _create_version(shot_id, version_number=1, duration_seconds=3.0)
        _create_version(shot_id, version_number=2, duration_seconds=4.0)

        response = client.post(f"/api/shots/{shot_id}/versions/{v1_id}/select")
        assert response.status_code == 200
        assert response.json()["active_version_id"] == v1_id

    def test_select_propagates_to_all_drafts(self):
        """POST /versions/{version_id}/select propagates to timeline items across all drafts."""
        _, draft_ids = _create_project_and_drafts(n_drafts=2)

        create_resp = client.post("/api/shots", json={"scene_id": "scene_1"})
        shot_id = create_resp.json()["id"]

        v1_id = _create_version(shot_id, version_number=1, duration_seconds=3.0)
        v2_id = _create_version(shot_id, version_number=2, duration_seconds=4.0)
        item_ids = _create_timeline_items(shot_id, draft_ids, version_id=v1_id)

        response = client.post(f"/api/shots/{shot_id}/versions/{v2_id}/select")
        assert response.status_code == 200
        assert response.json()["active_version_id"] == v2_id

        for item_id in item_ids:
            assert _get_timeline_item_version(item_id) == v2_id

    def test_select_version_shot_not_found(self):
        response = client.post("/api/shots/nonexistent-id/versions/some-version/select")
        assert response.status_code == 404
        assert response.json()["detail"] == "Shot not found"

    def test_select_version_not_found(self):
        create_resp = client.post("/api/shots", json={"scene_id": "scene_1"})
        shot_id = create_resp.json()["id"]

        response = client.post(f"/api/shots/{shot_id}/versions/nonexistent-version/select")
        assert response.status_code == 404
        assert response.json()["detail"] == "Version not found"


# ---------------------------------------------------------------------------
# POST /regenerate tests
# ---------------------------------------------------------------------------


class TestRegenerateShot:
    def test_regenerate_creates_next_version(self):
        create_resp = client.post("/api/shots", json={"scene_id": "scene_1", "duration_estimate": 5.0})
        shot_id = create_resp.json()["id"]

        v1_id = _create_version(shot_id, version_number=1, duration_seconds=5.0)
        client.post(f"/api/shots/{shot_id}/versions/{v1_id}/select")

        response = client.post(f"/api/shots/{shot_id}/regenerate")
        assert response.status_code == 200
        new_version_id = response.json()["active_version_id"]
        assert new_version_id != v1_id

        versions_resp = client.get(f"/api/shots/{shot_id}/versions")
        versions = versions_resp.json()
        assert len(versions) == 2
        assert versions[0]["version_number"] == 2

    def test_regenerate_increments_version_number(self):
        """POST /regenerate increments past the highest existing version_number."""
        create_resp = client.post("/api/shots", json={"scene_id": "scene_1", "duration_estimate": 5.0})
        shot_id = create_resp.json()["id"]

        _create_version(shot_id, version_number=1, duration_seconds=5.0)
        _create_version(shot_id, version_number=2, duration_seconds=5.0)

        response = client.post(f"/api/shots/{shot_id}/regenerate")
        assert response.status_code == 200

        versions_resp = client.get(f"/api/shots/{shot_id}/versions")
        version_numbers = [v["version_number"] for v in versions_resp.json()]
        assert 3 in version_numbers

    def test_regenerate_propagates_to_all_drafts(self):
        """POST /regenerate propagates the new version to timeline items across all drafts."""
        _, draft_ids = _create_project_and_drafts(n_drafts=2)

        create_resp = client.post("/api/shots", json={"scene_id": "scene_1", "duration_estimate": 5.0})
        shot_id = create_resp.json()["id"]

        v1_id = _create_version(shot_id, version_number=1, duration_seconds=5.0)
        item_ids = _create_timeline_items(shot_id, draft_ids, version_id=v1_id)
        client.post(f"/api/shots/{shot_id}/versions/{v1_id}/select")

        response = client.post(f"/api/shots/{shot_id}/regenerate")
        assert response.status_code == 200
        new_version_id = response.json()["active_version_id"]

        for item_id in item_ids:
            assert _get_timeline_item_version(item_id) == new_version_id

    def test_regenerate_shot_not_found(self):
        response = client.post("/api/shots/nonexistent-id/regenerate")
        assert response.status_code == 404
        assert response.json()["detail"] == "Shot not found"

    def test_regenerate_accepts_no_body(self):
        """POST /regenerate must succeed with no JSON body at all."""
        create_resp = client.post("/api/shots", json={"scene_id": "scene_1", "duration_estimate": 3.0})
        shot_id = create_resp.json()["id"]

        response = client.post(f"/api/shots/{shot_id}/regenerate")
        assert response.status_code == 200
        assert response.json()["active_version_id"] is not None
