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
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def _create_shot(scene_id="scene_1"):
    resp = client.post("/api/shots", json={"scene_id": scene_id})
    assert resp.status_code == 200
    return resp.json()["id"]


class TestListShotVersions:
    def test_list_versions_empty(self):
        shot_id = _create_shot()
        response = client.get(f"/api/shots/{shot_id}/versions")
        assert response.status_code == 200
        data = response.json()
        assert data["shot_id"] == shot_id
        assert data["versions"] == []
        assert data["active_version_id"] == ""

    def test_list_versions_not_found(self):
        response = client.get("/api/shots/nonexistent-id/versions")
        assert response.status_code == 404
        assert response.json()["detail"] == "Shot not found"

    def test_list_versions_after_regenerate(self):
        shot_id = _create_shot()
        client.post(f"/api/shots/{shot_id}/regenerate")
        response = client.get(f"/api/shots/{shot_id}/versions")
        assert response.status_code == 200
        data = response.json()
        assert data["shot_id"] == shot_id
        assert len(data["versions"]) == 1
        assert data["versions"][0]["status"] == "pending"
        assert data["versions"][0]["shot_id"] == shot_id
        assert data["versions"][0]["version_number"] == 1


class TestSelectShotVersion:
    def test_select_version(self):
        shot_id = _create_shot()
        regen = client.post(f"/api/shots/{shot_id}/regenerate")
        version_id = regen.json()["versions"][0]["id"]

        response = client.post(f"/api/shots/{shot_id}/versions/{version_id}/select")
        assert response.status_code == 200
        data = response.json()
        assert data["shot_id"] == shot_id
        assert data["active_version_id"] == version_id

    def test_select_version_shot_not_found(self):
        response = client.post("/api/shots/nonexistent/versions/v1/select")
        assert response.status_code == 404
        assert response.json()["detail"] == "Shot not found"

    def test_select_version_version_not_found(self):
        shot_id = _create_shot()
        response = client.post(f"/api/shots/{shot_id}/versions/nonexistent-version/select")
        assert response.status_code == 404
        assert response.json()["detail"] == "Version not found"

    def test_select_version_wrong_shot(self):
        shot_id_a = _create_shot("scene_a")
        shot_id_b = _create_shot("scene_b")
        regen = client.post(f"/api/shots/{shot_id_a}/regenerate")
        version_id_a = regen.json()["versions"][0]["id"]

        # Try to select a version belonging to shot A on shot B
        response = client.post(f"/api/shots/{shot_id_b}/versions/{version_id_a}/select")
        assert response.status_code == 404
        assert response.json()["detail"] == "Version not found"


class TestRegenerateShot:
    def test_regenerate_creates_pending_version(self):
        shot_id = _create_shot()
        response = client.post(f"/api/shots/{shot_id}/regenerate")
        assert response.status_code == 200
        data = response.json()
        assert data["shot_id"] == shot_id
        assert len(data["versions"]) == 1
        v = data["versions"][0]
        assert v["status"] == "pending"
        assert v["shot_id"] == shot_id
        assert v["version_number"] == 1

    def test_regenerate_increments_version_number(self):
        shot_id = _create_shot()
        client.post(f"/api/shots/{shot_id}/regenerate")
        response = client.post(f"/api/shots/{shot_id}/regenerate")
        assert response.status_code == 200
        data = response.json()
        assert len(data["versions"]) == 2
        numbers = {v["version_number"] for v in data["versions"]}
        assert numbers == {1, 2}

    def test_regenerate_shot_not_found(self):
        response = client.post("/api/shots/nonexistent-id/regenerate")
        assert response.status_code == 404
        assert response.json()["detail"] == "Shot not found"

    def test_versions_ordered_newest_first(self):
        shot_id = _create_shot()
        client.post(f"/api/shots/{shot_id}/regenerate")
        response = client.post(f"/api/shots/{shot_id}/regenerate")
        data = response.json()
        version_numbers = [v["version_number"] for v in data["versions"]]
        assert version_numbers == sorted(version_numbers, reverse=True)
