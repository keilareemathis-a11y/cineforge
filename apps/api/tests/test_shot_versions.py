import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.models.shot import Shot
from app.models.shot_version import ShotVersion
from app.models.film_draft import FilmDraft
from app.models.timeline_item import TimelineItem
from app.models.Project import Project

TEST_DATABASE_URL = "sqlite:///./test_shot_versions.db"

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
    # Save and replace the get_db override for the duration of each test so
    # this file doesn't conflict with test_shots.py's module-level override.
    previous_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if previous_override is not None:
        app.dependency_overrides[get_db] = previous_override
    else:
        app.dependency_overrides.pop(get_db, None)


client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_shot(scene_id: str = "scene_1") -> dict:
    resp = client.post("/api/shots", json={"scene_id": scene_id})
    assert resp.status_code == 200
    return resp.json()


def _create_ready_version(db, shot_id: str, image_url: str = "https://example.com/img.png") -> ShotVersion:
    """Insert a ready ShotVersion directly into the test DB."""
    v = ShotVersion(
        shot_id=shot_id,
        version_number=1,
        status="ready",
        image_url=image_url,
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


def _create_timeline_item(db, shot_id: str, version_id: str | None = None) -> TimelineItem:
    """Create a Project, FilmDraft, and TimelineItem for timeline propagation tests."""
    project = Project(name="Test Project")
    db.add(project)
    db.commit()
    db.refresh(project)

    film = FilmDraft(project_id=project.id, title="Test Film")
    db.add(film)
    db.commit()
    db.refresh(film)

    item = TimelineItem(
        film_draft_id=film.id,
        shot_id=shot_id,
        active_version_id=version_id,
        position=1,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


# ---------------------------------------------------------------------------
# GET /api/shots/{shot_id}/versions
# ---------------------------------------------------------------------------

class TestGetShotVersions:
    def test_returns_empty_list_when_no_versions(self):
        shot = _create_shot()
        resp = client.get(f"/api/shots/{shot['id']}/versions")
        assert resp.status_code == 200
        data = resp.json()
        assert data["shot_id"] == shot["id"]
        assert data["active_version_id"] is None
        assert data["versions"] == []

    def test_returns_versions_with_active_version_id(self):
        shot = _create_shot()
        db = TestingSessionLocal()
        try:
            version = _create_ready_version(db, shot["id"])
            version_id = version.id
            shot_obj = db.query(Shot).filter(Shot.id == shot["id"]).first()
            shot_obj.active_version_id = version_id
            db.commit()
        finally:
            db.close()

        resp = client.get(f"/api/shots/{shot['id']}/versions")
        assert resp.status_code == 200
        data = resp.json()
        assert data["shot_id"] == shot["id"]
        assert data["active_version_id"] == version_id
        assert len(data["versions"]) == 1
        assert data["versions"][0]["id"] == version_id
        assert data["versions"][0]["status"] == "ready"
        assert data["versions"][0]["image_url"] == "https://example.com/img.png"

    def test_returns_all_versions(self):
        shot = _create_shot()
        db = TestingSessionLocal()
        try:
            for n in range(1, 4):
                v = ShotVersion(shot_id=shot["id"], version_number=n, status="ready")
                db.add(v)
            db.commit()
        finally:
            db.close()

        resp = client.get(f"/api/shots/{shot['id']}/versions")
        assert resp.status_code == 200
        assert len(resp.json()["versions"]) == 3

    def test_shot_not_found(self):
        resp = client.get("/api/shots/nonexistent/versions")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Shot not found"


# ---------------------------------------------------------------------------
# POST /api/shots/{shot_id}/regenerate
# ---------------------------------------------------------------------------

class TestRegenerateShot:
    def test_creates_queued_version(self):
        shot = _create_shot()
        resp = client.post(f"/api/shots/{shot['id']}/regenerate", json={})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "queued"
        assert data["shot_id"] == shot["id"]
        assert data["new_version"]["status"] == "queued"
        assert data["new_version"]["shot_id"] == shot["id"]
        assert "id" in data["new_version"]

    def test_version_number_increments(self):
        shot = _create_shot()
        resp1 = client.post(f"/api/shots/{shot['id']}/regenerate", json={})
        resp2 = client.post(f"/api/shots/{shot['id']}/regenerate", json={})
        assert resp1.json()["new_version"]["version_number"] == 1
        assert resp2.json()["new_version"]["version_number"] == 2

    def test_stores_prompt_and_style(self):
        shot = _create_shot()
        resp = client.post(
            f"/api/shots/{shot['id']}/regenerate",
            json={"prompt": "Wide cityscape at sunset", "style": "cinematic"},
        )
        assert resp.status_code == 200
        v = resp.json()["new_version"]
        assert v["prompt"] == "Wide cityscape at sunset"
        assert v["style"] == "cinematic"

    def test_no_body_is_accepted(self):
        shot = _create_shot()
        resp = client.post(f"/api/shots/{shot['id']}/regenerate")
        assert resp.status_code == 200
        assert resp.json()["new_version"]["status"] == "queued"

    def test_version_appears_in_get_versions(self):
        shot = _create_shot()
        client.post(f"/api/shots/{shot['id']}/regenerate", json={})
        resp = client.get(f"/api/shots/{shot['id']}/versions")
        assert len(resp.json()["versions"]) == 1

    def test_shot_not_found(self):
        resp = client.post("/api/shots/nonexistent/regenerate", json={})
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Shot not found"


# ---------------------------------------------------------------------------
# POST /api/shots/{shot_id}/versions/{version_id}/select
# ---------------------------------------------------------------------------

class TestSelectShotVersion:
    def test_selects_ready_version(self):
        shot = _create_shot()
        db = TestingSessionLocal()
        try:
            version = _create_ready_version(db, shot["id"])
            version_id = version.id
        finally:
            db.close()

        resp = client.post(f"/api/shots/{shot['id']}/versions/{version_id}/select")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "selected"
        assert data["shot_id"] == shot["id"]
        assert data["active_version_id"] == version_id

    def test_updates_shot_active_version_id(self):
        shot = _create_shot()
        db = TestingSessionLocal()
        try:
            version = _create_ready_version(db, shot["id"])
            version_id = version.id
        finally:
            db.close()

        client.post(f"/api/shots/{shot['id']}/versions/{version_id}/select")

        shot_resp = client.get(f"/api/shots/{shot['id']}")
        assert shot_resp.json()["active_version_id"] == version_id

    def test_propagates_to_timeline_items(self):
        shot = _create_shot()
        db = TestingSessionLocal()
        try:
            version = _create_ready_version(db, shot["id"])
            version_id = version.id
            item1 = _create_timeline_item(db, shot["id"])
            item2 = _create_timeline_item(db, shot["id"])
            item1_id = item1.id
            item2_id = item2.id
        finally:
            db.close()

        client.post(f"/api/shots/{shot['id']}/versions/{version_id}/select")

        db2 = TestingSessionLocal()
        try:
            updated1 = db2.query(TimelineItem).filter(TimelineItem.id == item1_id).first()
            updated2 = db2.query(TimelineItem).filter(TimelineItem.id == item2_id).first()
            assert updated1.active_version_id == version_id
            assert updated2.active_version_id == version_id
        finally:
            db2.close()

    def test_does_not_affect_other_shots_timeline_items(self):
        shot_a = _create_shot("scene_1")
        shot_b = _create_shot("scene_2")
        db = TestingSessionLocal()
        try:
            version_a = _create_ready_version(db, shot_a["id"])
            version_b = _create_ready_version(db, shot_b["id"])
            item_b = _create_timeline_item(db, shot_b["id"])
            version_a_id = version_a.id
            item_b_id = item_b.id
        finally:
            db.close()

        client.post(f"/api/shots/{shot_a['id']}/versions/{version_a_id}/select")

        db2 = TestingSessionLocal()
        try:
            item_b_obj = db2.query(TimelineItem).filter(TimelineItem.id == item_b_id).first()
            assert item_b_obj.active_version_id != version_a_id
        finally:
            db2.close()

    def test_shot_not_found(self):
        resp = client.post("/api/shots/nonexistent/versions/some-version/select")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Shot not found"

    def test_version_not_found(self):
        shot = _create_shot()
        resp = client.post(f"/api/shots/{shot['id']}/versions/nonexistent/select")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Version not found"

    def test_version_from_different_shot_is_not_found(self):
        shot_a = _create_shot("scene_1")
        shot_b = _create_shot("scene_2")
        db = TestingSessionLocal()
        try:
            version_b = _create_ready_version(db, shot_b["id"])
            version_b_id = version_b.id
        finally:
            db.close()

        # Try to select shot_b's version on shot_a
        resp = client.post(f"/api/shots/{shot_a['id']}/versions/{version_b_id}/select")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Version not found"

    def test_cannot_select_queued_version(self):
        shot = _create_shot()
        db = TestingSessionLocal()
        try:
            version = ShotVersion(shot_id=shot["id"], version_number=1, status="queued")
            db.add(version)
            db.commit()
            db.refresh(version)
            version_id = version.id
        finally:
            db.close()

        resp = client.post(f"/api/shots/{shot['id']}/versions/{version_id}/select")
        assert resp.status_code == 400
        assert "not ready" in resp.json()["detail"]
        assert "queued" in resp.json()["detail"]

    def test_cannot_select_processing_version(self):
        shot = _create_shot()
        db = TestingSessionLocal()
        try:
            version = ShotVersion(shot_id=shot["id"], version_number=1, status="processing")
            db.add(version)
            db.commit()
            db.refresh(version)
            version_id = version.id
        finally:
            db.close()

        resp = client.post(f"/api/shots/{shot['id']}/versions/{version_id}/select")
        assert resp.status_code == 400
        assert "not ready" in resp.json()["detail"]
        assert "processing" in resp.json()["detail"]

    def test_cannot_select_failed_version(self):
        shot = _create_shot()
        db = TestingSessionLocal()
        try:
            version = ShotVersion(shot_id=shot["id"], version_number=1, status="failed")
            db.add(version)
            db.commit()
            db.refresh(version)
            version_id = version.id
        finally:
            db.close()

        resp = client.post(f"/api/shots/{shot['id']}/versions/{version_id}/select")
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Cannot select a failed version"

    def test_cannot_select_version_without_rendered_assets(self):
        shot = _create_shot()
        db = TestingSessionLocal()
        try:
            version = ShotVersion(
                shot_id=shot["id"], version_number=1, status="ready", image_url=None
            )
            db.add(version)
            db.commit()
            db.refresh(version)
            version_id = version.id
        finally:
            db.close()

        resp = client.post(f"/api/shots/{shot['id']}/versions/{version_id}/select")
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Version has no rendered assets"
