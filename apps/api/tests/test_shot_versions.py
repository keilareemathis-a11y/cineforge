import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db

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
    original_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if original_override is not None:
        app.dependency_overrides[get_db] = original_override
    else:
        app.dependency_overrides.pop(get_db, None)
client = TestClient(app)


def create_shot(scene_id="scene_1", **kwargs):
    payload = {"scene_id": scene_id, **kwargs}
    resp = client.post("/api/shots", json=payload)
    assert resp.status_code == 200
    return resp.json()


class TestGetShotVersions:
    def test_get_versions_empty(self):
        shot = create_shot()
        response = client.get(f"/api/shots/{shot['id']}/versions")
        assert response.status_code == 200
        data = response.json()
        assert data["shot_id"] == shot["id"]
        assert data["active_version_id"] is None
        assert data["versions"] == []

    def test_get_versions_not_found(self):
        response = client.get("/api/shots/nonexistent-id/versions")
        assert response.status_code == 404
        assert response.json()["detail"] == "Shot not found"

    def test_get_versions_after_regenerate(self):
        shot = create_shot()
        client.post(f"/api/shots/{shot['id']}/regenerate")
        client.post(f"/api/shots/{shot['id']}/regenerate")

        response = client.get(f"/api/shots/{shot['id']}/versions")
        assert response.status_code == 200
        data = response.json()
        assert data["shot_id"] == shot["id"]
        assert len(data["versions"]) == 2
        for v in data["versions"]:
            assert v["shot_id"] == shot["id"]
            assert v["status"] == "pending"
            assert "id" in v
            assert "created_at" in v


class TestRegenerateShot:
    def test_regenerate_creates_version(self):
        shot = create_shot()
        response = client.post(f"/api/shots/{shot['id']}/regenerate")
        assert response.status_code == 200
        data = response.json()
        assert data["shot_id"] == shot["id"]
        assert len(data["versions"]) == 1
        assert data["versions"][0]["status"] == "pending"
        assert data["versions"][0]["version_number"] == 1

    def test_regenerate_increments_version_number(self):
        shot = create_shot()
        client.post(f"/api/shots/{shot['id']}/regenerate")
        response = client.post(f"/api/shots/{shot['id']}/regenerate")
        assert response.status_code == 200
        data = response.json()
        assert len(data["versions"]) == 2
        version_numbers = {v["version_number"] for v in data["versions"]}
        assert version_numbers == {1, 2}

    def test_regenerate_shot_not_found(self):
        response = client.post("/api/shots/nonexistent-id/regenerate")
        assert response.status_code == 404
        assert response.json()["detail"] == "Shot not found"


class TestSelectShotVersion:
    def test_select_version(self):
        shot = create_shot()
        regen_resp = client.post(f"/api/shots/{shot['id']}/regenerate")
        version_id = regen_resp.json()["versions"][0]["id"]

        response = client.post(f"/api/shots/{shot['id']}/versions/{version_id}/select")
        assert response.status_code == 200
        data = response.json()
        assert data["shot_id"] == shot["id"]
        assert data["active_version_id"] == version_id
        assert len(data["versions"]) == 1

    def test_select_version_updates_active(self):
        shot = create_shot()
        client.post(f"/api/shots/{shot['id']}/regenerate")
        regen_resp2 = client.post(f"/api/shots/{shot['id']}/regenerate")
        versions = regen_resp2.json()["versions"]

        older_version_id = versions[-1]["id"]
        newer_version_id = versions[0]["id"]

        client.post(f"/api/shots/{shot['id']}/versions/{older_version_id}/select")
        response = client.post(f"/api/shots/{shot['id']}/versions/{newer_version_id}/select")
        assert response.status_code == 200
        assert response.json()["active_version_id"] == newer_version_id

    def test_select_version_shot_not_found(self):
        response = client.post("/api/shots/nonexistent-id/versions/some-version/select")
        assert response.status_code == 404
        assert response.json()["detail"] == "Shot not found"

    def test_select_version_version_not_found(self):
        shot = create_shot()
        response = client.post(f"/api/shots/{shot['id']}/versions/nonexistent-version/select")
        assert response.status_code == 404
        assert response.json()["detail"] == "Shot version not found"

    def test_select_version_wrong_shot(self):
        shot1 = create_shot(scene_id="scene_1")
        shot2 = create_shot(scene_id="scene_2")
        regen_resp = client.post(f"/api/shots/{shot1['id']}/regenerate")
        version_id = regen_resp.json()["versions"][0]["id"]

        response = client.post(f"/api/shots/{shot2['id']}/versions/{version_id}/select")
        assert response.status_code == 404
        assert response.json()["detail"] == "Shot version not found"
