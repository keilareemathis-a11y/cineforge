import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db

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
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


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
