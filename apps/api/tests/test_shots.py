import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.models.Project import Project as ProjectModel
from app.models.character import Character
from app.models.film_draft import FilmDraft

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


def create_project_and_draft(name="Test Project", title="Test Draft"):
    """Helper: create a Project and FilmDraft directly in the test database."""
    db = TestingSessionLocal()
    try:
        project = ProjectModel(name=name)
        db.add(project)
        db.flush()
        draft = FilmDraft(project_id=project.id, title=title)
        db.add(draft)
        db.commit()
        db.refresh(project)
        db.refresh(draft)
        return project.id, draft.id
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Existing tests (shots CRUD)
# ---------------------------------------------------------------------------

class TestCreateShot:
    def test_create_shot_minimal(self):
        response = client.post("/api/shots", json={"scene_id": "scene_1"})
        assert response.status_code == 200
        data = response.json()
        assert data["scene_id"] == "scene_1"
        assert data["status"] == "planned"
        assert data["storyboard_image"].startswith("data:image/")
        assert data["prompt"] == "Storyboard frame"
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


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------

class TestProjectRoutes:
    def test_create_project(self):
        response = client.post("/api/projects", json={"name": "My Film Project", "description": "Test desc"})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "My Film Project"
        assert data["description"] == "Test desc"
        assert "id" in data

    def test_create_project_minimal(self):
        response = client.post("/api/projects", json={"name": "Minimal"})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Minimal"

    def test_get_project(self):
        create_resp = client.post("/api/projects", json={"name": "Film Noir"})
        project_id = create_resp.json()["id"]

        response = client.get(f"/api/projects/{project_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project_id
        assert data["name"] == "Film Noir"

    def test_get_project_not_found(self):
        response = client.get("/api/projects/nonexistent-project")
        assert response.status_code == 404
        assert response.json()["detail"] == "Project not found"


# ---------------------------------------------------------------------------
# Characters
# ---------------------------------------------------------------------------

class TestCharacterRoutes:
    def test_create_character(self):
        response = client.post(
            "/api/characters",
            json={
                "user_id": "user_1",
                "name": "Ava",
                "description": "Lead detective",
                "reference_image_url": "https://example.com/ava.png",
                "appearance_traits": {"hair": "black", "coat": "trench"},
                "voice_profile": "calm",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "user_1"
        assert data["name"] == "Ava"
        assert data["appearance_traits"]["coat"] == "trench"
        assert "id" in data

    def test_list_characters(self):
        client.post("/api/characters", json={"user_id": "user_1", "name": "Ava"})
        client.post("/api/characters", json={"user_id": "user_2", "name": "Jon"})

        response = client.get("/api/characters")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert {character["name"] for character in data} == {"Ava", "Jon"}

    def test_get_character(self):
        create_resp = client.post("/api/characters", json={"user_id": "user_1", "name": "Ava"})
        character_id = create_resp.json()["id"]

        response = client.get(f"/api/characters/{character_id}")
        assert response.status_code == 200
        assert response.json()["id"] == character_id

    def test_get_character_not_found(self):
        response = client.get("/api/characters/nonexistent-character")
        assert response.status_code == 404
        assert response.json()["detail"] == "Character not found"

    def test_update_character(self):
        create_resp = client.post("/api/characters", json={"user_id": "user_1", "name": "Ava"})
        character_id = create_resp.json()["id"]

        response = client.patch(
            f"/api/characters/{character_id}",
            json={"description": "Updated character", "voice_profile": "confident"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated character"
        assert data["voice_profile"] == "confident"
        assert data["name"] == "Ava"

    def test_update_character_not_found(self):
        response = client.patch("/api/characters/nonexistent-character", json={"name": "Missing"})
        assert response.status_code == 404
        assert response.json()["detail"] == "Character not found"

    def test_delete_character(self):
        create_resp = client.post("/api/characters", json={"user_id": "user_1", "name": "Ava"})
        character_id = create_resp.json()["id"]

        response = client.delete(f"/api/characters/{character_id}")
        assert response.status_code == 200
        assert response.json()["message"] == "Character deleted"

        get_response = client.get(f"/api/characters/{character_id}")
        assert get_response.status_code == 404

    def test_delete_character_not_found(self):
        response = client.delete("/api/characters/nonexistent-character")
        assert response.status_code == 404
        assert response.json()["detail"] == "Character not found"


# ---------------------------------------------------------------------------
# Scenes
# ---------------------------------------------------------------------------

class TestSceneRoutes:
    def test_create_scene(self):
        db = TestingSessionLocal()
        try:
            character_one = Character(user_id="user_1", name="Ava")
            character_two = Character(user_id="user_1", name="Jon")
            db.add_all([character_one, character_two])
            db.commit()
            db.refresh(character_one)
            db.refresh(character_two)
        finally:
            db.close()

        response = client.post(
            "/api/scenes",
            json={
                "project_id": "project_1",
                "title": "Rooftop confrontation",
                "environment": "city rooftop",
                "lighting": "neon",
                "weather": "rain",
                "mood": "tense",
                "character_ids": [character_one.id, character_two.id],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == "project_1"
        assert data["title"] == "Rooftop confrontation"
        assert set(data["character_ids"]) == {character_one.id, character_two.id}
        assert "id" in data

    def test_create_scene_character_not_found(self):
        response = client.post(
            "/api/scenes",
            json={"project_id": "project_1", "title": "Missing cast", "character_ids": ["missing-character"]},
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Character not found: missing-character"

    def test_list_scenes(self):
        client.post("/api/scenes", json={"project_id": "project_1", "title": "Opening"})
        client.post("/api/scenes", json={"project_id": "project_1", "title": "Finale"})

        response = client.get("/api/scenes")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert {scene["title"] for scene in data} == {"Opening", "Finale"}

    def test_get_scene(self):
        create_resp = client.post("/api/scenes", json={"project_id": "project_1", "title": "Opening"})
        scene_id = create_resp.json()["id"]

        response = client.get(f"/api/scenes/{scene_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == scene_id
        assert data["title"] == "Opening"

    def test_get_scene_not_found(self):
        response = client.get("/api/scenes/nonexistent-scene")
        assert response.status_code == 404
        assert response.json()["detail"] == "Scene not found"


# ---------------------------------------------------------------------------
# Shot active version behavior
# ---------------------------------------------------------------------------

class TestShotActiveVersion:
    def test_shot_active_version_starts_null(self):
        resp = client.post("/api/shots", json={"scene_id": "scene_1"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["active_version_id"] is None

    def test_shot_active_version_set_after_regenerate(self):
        resp = client.post("/api/shots", json={"scene_id": "scene_1"})
        shot_id = resp.json()["id"]

        regen = client.post(f"/api/shots/{shot_id}/regenerate").json()
        new_version_id = regen["new_version"]["id"]

        shot = client.get(f"/api/shots/{shot_id}").json()
        assert shot["active_version_id"] == new_version_id

    def test_shot_active_version_updated_on_each_regenerate(self):
        resp = client.post("/api/shots", json={"scene_id": "scene_1"})
        shot_id = resp.json()["id"]

        first = client.post(f"/api/shots/{shot_id}/regenerate").json()
        second = client.post(f"/api/shots/{shot_id}/regenerate").json()

        shot = client.get(f"/api/shots/{shot_id}").json()
        assert shot["active_version_id"] == second["new_version"]["id"]
        assert shot["active_version_id"] != first["new_version"]["id"]


# ---------------------------------------------------------------------------
# Version ordering
# ---------------------------------------------------------------------------

class TestShotVersions:
    def test_get_versions_empty(self):
        resp = client.post("/api/shots", json={"scene_id": "scene_1"})
        shot_id = resp.json()["id"]
        response = client.get(f"/api/shots/{shot_id}/versions")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_versions_ordering(self):
        resp = client.post("/api/shots", json={"scene_id": "scene_1"})
        shot_id = resp.json()["id"]

        client.post(f"/api/shots/{shot_id}/regenerate")
        client.post(f"/api/shots/{shot_id}/regenerate")
        client.post(f"/api/shots/{shot_id}/regenerate")

        response = client.get(f"/api/shots/{shot_id}/versions")
        assert response.status_code == 200
        versions = response.json()
        assert len(versions) == 3

        version_numbers = [v["version_number"] for v in versions]
        assert version_numbers == sorted(version_numbers, reverse=True)
        assert version_numbers[0] == 3

    def test_get_versions_include_generated_visuals(self):
        resp = client.post("/api/shots", json={"scene_id": "scene_1", "image_prompt": "Wide sunset over a canyon"})
        shot_id = resp.json()["id"]

        client.post(f"/api/shots/{shot_id}/regenerate")
        response = client.get(f"/api/shots/{shot_id}/versions")

        assert response.status_code == 200
        version = response.json()[0]
        assert version["image_url"].startswith("data:image/")
        assert version["status"] == "ready"
        assert version["prompt"] == "Wide sunset over a canyon"

    def test_get_versions_not_found(self):
        response = client.get("/api/shots/nonexistent/versions")
        assert response.status_code == 404
        assert response.json()["detail"] == "Shot not found"

    def test_versions_do_not_modify_timeline_items(self):
        """GET /versions must not modify any TimelineItem rows."""
        _, draft_id = create_project_and_draft()
        resp = client.post("/api/shots", json={"scene_id": "scene_1"})
        shot_id = resp.json()["id"]

        regen = client.post(f"/api/shots/{shot_id}/regenerate").json()
        version_id = regen["new_version"]["id"]

        client.post(
            f"/api/drafts/{draft_id}/timeline-items",
            json={"shot_id": shot_id, "position": 1, "active_version_id": version_id},
        )

        # Call GET versions multiple times
        client.get(f"/api/shots/{shot_id}/versions")
        client.get(f"/api/shots/{shot_id}/versions")

        # Timeline item's active_version_id must be unchanged
        timeline = client.get(f"/api/drafts/{draft_id}/timeline").json()
        assert timeline["timeline_items"][0]["active_version_id"] == version_id


# ---------------------------------------------------------------------------
# Regenerate endpoint
# ---------------------------------------------------------------------------

class TestRegenerate:
    def test_regenerate_creates_version(self):
        resp = client.post("/api/shots", json={"scene_id": "scene_1"})
        shot_id = resp.json()["id"]

        response = client.post(f"/api/shots/{shot_id}/regenerate")
        assert response.status_code == 200
        data = response.json()
        assert data["shot_id"] == shot_id
        assert data["new_version"]["version_number"] == 1
        assert data["new_version"]["image_url"].startswith("data:image/")
        assert data["new_version"]["status"] == "ready"
        assert data["active_version_id"] == data["new_version"]["id"]

    def test_regenerate_increments_version_number(self):
        resp = client.post("/api/shots", json={"scene_id": "scene_1"})
        shot_id = resp.json()["id"]

        first = client.post(f"/api/shots/{shot_id}/regenerate").json()
        second = client.post(f"/api/shots/{shot_id}/regenerate").json()
        third = client.post(f"/api/shots/{shot_id}/regenerate").json()

        assert first["new_version"]["version_number"] == 1
        assert second["new_version"]["version_number"] == 2
        assert third["new_version"]["version_number"] == 3

    def test_regenerate_inherits_fields_from_previous(self):
        resp = client.post("/api/shots", json={"scene_id": "scene_1"})
        shot_id = resp.json()["id"]

        first = client.post(f"/api/shots/{shot_id}/regenerate").json()
        second = client.post(f"/api/shots/{shot_id}/regenerate").json()

        assert second["new_version"]["duration_seconds"] == first["new_version"]["duration_seconds"]
        assert second["new_version"]["trim_start"] == first["new_version"]["trim_start"]
        assert second["new_version"]["trim_end"] == first["new_version"]["trim_end"]

    def test_regenerate_propagates_to_timeline_items(self):
        _, draft_id = create_project_and_draft()

        resp = client.post("/api/shots", json={"scene_id": "scene_1"})
        shot_id = resp.json()["id"]

        first_regen = client.post(f"/api/shots/{shot_id}/regenerate").json()
        first_version_id = first_regen["new_version"]["id"]

        # Add shot to timeline with first version
        timeline_resp = client.post(
            f"/api/drafts/{draft_id}/timeline-items",
            json={"shot_id": shot_id, "position": 1, "active_version_id": first_version_id},
        )
        assert timeline_resp.status_code == 200

        # Regenerate → creates second version
        second_regen = client.post(f"/api/shots/{shot_id}/regenerate").json()
        second_version_id = second_regen["new_version"]["id"]

        # Timeline item must now reference the new version
        timeline = client.get(f"/api/drafts/{draft_id}/timeline").json()
        items = timeline["timeline_items"]
        assert len(items) == 1
        assert items[0]["active_version_id"] == second_version_id
        assert items[0]["active_version"]["version_number"] == 2

    def test_regenerate_propagates_to_multiple_timeline_items(self):
        _, draft_id = create_project_and_draft()

        resp = client.post("/api/shots", json={"scene_id": "scene_1"})
        shot_id = resp.json()["id"]
        regen = client.post(f"/api/shots/{shot_id}/regenerate").json()
        v1_id = regen["new_version"]["id"]

        # Add same shot twice at different positions
        client.post(
            f"/api/drafts/{draft_id}/timeline-items",
            json={"shot_id": shot_id, "position": 1, "active_version_id": v1_id},
        )
        client.post(
            f"/api/drafts/{draft_id}/timeline-items",
            json={"shot_id": shot_id, "position": 2, "active_version_id": v1_id},
        )

        second_regen = client.post(f"/api/shots/{shot_id}/regenerate").json()
        v2_id = second_regen["new_version"]["id"]

        timeline = client.get(f"/api/drafts/{draft_id}/timeline").json()
        for item in timeline["timeline_items"]:
            assert item["active_version_id"] == v2_id

    def test_regenerate_not_found(self):
        response = client.post("/api/shots/nonexistent/regenerate")
        assert response.status_code == 404
        assert response.json()["detail"] == "Shot not found"

    def test_regenerate_creates_provider_backed_clip(self):
        resp = client.post("/api/shots", json={"scene_id": "scene_1"})
        shot_id = resp.json()["id"]

        response = client.post(
            f"/api/shots/{shot_id}/regenerate",
            json={"provider": "pika"},
        )
        assert response.status_code == 200
        version = response.json()["new_version"]
        assert version["provider"] == "pika"
        assert version["video_url"] == f"/api/shots/{shot_id}/versions/{version['id']}/video"

        video_response = client.get(version["video_url"])
        assert video_response.status_code == 200
        assert video_response.headers["content-type"] == "video/mp4"
        assert len(video_response.content) > 0


class TestSelectVersion:
    def test_select_version_updates_shot_and_timeline(self):
        _, draft_id = create_project_and_draft()
        resp = client.post("/api/shots", json={"scene_id": "scene_1"})
        shot_id = resp.json()["id"]

        first = client.post(f"/api/shots/{shot_id}/regenerate").json()["new_version"]
        second = client.post(f"/api/shots/{shot_id}/regenerate").json()["new_version"]

        client.post(
            f"/api/drafts/{draft_id}/timeline-items",
            json={"shot_id": shot_id, "position": 1, "active_version_id": second["id"]},
        )

        response = client.post(f"/api/shots/{shot_id}/versions/{first['id']}/select")
        assert response.status_code == 200
        data = response.json()
        assert data["active_version_id"] == first["id"]
        assert data["versions"][0]["image_url"].startswith("data:image/")

        shot = client.get(f"/api/shots/{shot_id}").json()
        assert shot["active_version_id"] == first["id"]

        timeline = client.get(f"/api/drafts/{draft_id}/timeline").json()
        assert timeline["timeline_items"][0]["active_version_id"] == first["id"]

    def test_select_version_not_found(self):
        resp = client.post("/api/shots", json={"scene_id": "scene_1"})
        shot_id = resp.json()["id"]

        response = client.post(f"/api/shots/{shot_id}/versions/does-not-exist/select")
        assert response.status_code == 404
        assert response.json()["detail"] == "ShotVersion not found"


# ---------------------------------------------------------------------------
# Draft timeline endpoints
# ---------------------------------------------------------------------------

class TestDraftTimeline:
    def test_create_timeline_item(self):
        _, draft_id = create_project_and_draft()

        shot_resp = client.post("/api/shots", json={"scene_id": "scene_1"})
        shot_id = shot_resp.json()["id"]
        regen = client.post(f"/api/shots/{shot_id}/regenerate").json()
        version_id = regen["new_version"]["id"]

        response = client.post(
            f"/api/drafts/{draft_id}/timeline-items",
            json={"shot_id": shot_id, "position": 1, "active_version_id": version_id},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["shot_id"] == shot_id
        assert data["film_draft_id"] == draft_id
        assert data["active_version_id"] == version_id
        assert data["position"] == 1

    def test_create_timeline_item_without_version(self):
        _, draft_id = create_project_and_draft()
        shot_resp = client.post("/api/shots", json={"scene_id": "scene_1"})
        shot_id = shot_resp.json()["id"]

        response = client.post(
            f"/api/drafts/{draft_id}/timeline-items",
            json={"shot_id": shot_id, "position": 1},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["active_version_id"] is None

    def test_get_timeline(self):
        _, draft_id = create_project_and_draft()

        shot_resp = client.post("/api/shots", json={"scene_id": "scene_1"})
        shot_id = shot_resp.json()["id"]
        regen = client.post(f"/api/shots/{shot_id}/regenerate").json()
        version_id = regen["new_version"]["id"]

        client.post(
            f"/api/drafts/{draft_id}/timeline-items",
            json={"shot_id": shot_id, "position": 1, "active_version_id": version_id},
        )

        response = client.get(f"/api/drafts/{draft_id}/timeline")
        assert response.status_code == 200
        data = response.json()
        assert data["film_draft_id"] == draft_id
        assert len(data["timeline_items"]) == 1
        item = data["timeline_items"][0]
        assert item["position"] == 1
        assert item["shot_id"] == shot_id
        assert item["active_version"]["version_number"] == 1

    def test_get_timeline_ordered_by_position(self):
        _, draft_id = create_project_and_draft()

        shot_a = client.post("/api/shots", json={"scene_id": "s1"}).json()["id"]
        shot_b = client.post("/api/shots", json={"scene_id": "s1"}).json()["id"]
        shot_c = client.post("/api/shots", json={"scene_id": "s1"}).json()["id"]

        client.post(f"/api/drafts/{draft_id}/timeline-items", json={"shot_id": shot_c, "position": 3})
        client.post(f"/api/drafts/{draft_id}/timeline-items", json={"shot_id": shot_a, "position": 1})
        client.post(f"/api/drafts/{draft_id}/timeline-items", json={"shot_id": shot_b, "position": 2})

        response = client.get(f"/api/drafts/{draft_id}/timeline")
        assert response.status_code == 200
        items = response.json()["timeline_items"]
        positions = [i["position"] for i in items]
        assert positions == [1, 2, 3]

    def test_get_timeline_not_found(self):
        response = client.get("/api/drafts/nonexistent/timeline")
        assert response.status_code == 404
        assert response.json()["detail"] == "Film draft not found"

    def test_create_timeline_item_draft_not_found(self):
        shot_resp = client.post("/api/shots", json={"scene_id": "scene_1"})
        shot_id = shot_resp.json()["id"]
        response = client.post(
            "/api/drafts/nonexistent/timeline-items",
            json={"shot_id": shot_id, "position": 1},
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Film draft not found"

    def test_create_timeline_item_shot_not_found(self):
        _, draft_id = create_project_and_draft()
        response = client.post(
            f"/api/drafts/{draft_id}/timeline-items",
            json={"shot_id": "nonexistent", "position": 1},
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Shot not found"


class TestFilmRender:
    def test_render_film_creates_mp4(self):
        _, draft_id = create_project_and_draft()

        shot_resp = client.post("/api/shots", json={"scene_id": "scene_1", "image_prompt": "Rainy city street"})
        shot_id = shot_resp.json()["id"]
        regen = client.post(f"/api/shots/{shot_id}/regenerate").json()
        version_id = regen["new_version"]["id"]

        client.post(
            f"/api/drafts/{draft_id}/timeline-items",
            json={"shot_id": shot_id, "position": 1, "active_version_id": version_id},
        )

        render_response = client.post(f"/api/films/{draft_id}/render")
        assert render_response.status_code == 200
        render_data = render_response.json()
        assert render_data["status"] == "rendered"
        assert render_data["video_url"] == f"/api/films/{draft_id}/rendered"

        video_response = client.get(render_data["video_url"])
        assert video_response.status_code == 200
        assert video_response.headers["content-type"] == "video/mp4"
        assert len(video_response.content) > 0

    def test_timeline_reorder_and_trim_update(self):
        _, draft_id = create_project_and_draft()

        shot_a = client.post("/api/shots", json={"scene_id": "scene_1"}).json()["id"]
        shot_b = client.post("/api/shots", json={"scene_id": "scene_1"}).json()["id"]
        version_a = client.post(f"/api/shots/{shot_a}/regenerate").json()["new_version"]["id"]
        version_b = client.post(f"/api/shots/{shot_b}/regenerate").json()["new_version"]["id"]

        first = client.post(
            f"/api/drafts/{draft_id}/timeline-items",
            json={"shot_id": shot_a, "position": 0, "active_version_id": version_a},
        ).json()
        client.post(
            f"/api/drafts/{draft_id}/timeline-items",
            json={"shot_id": shot_b, "position": 1, "active_version_id": version_b},
        )

        reorder = client.post(
            f"/api/films/{draft_id}/timeline/reorder",
            json={"item_id": first["timeline_item_id"], "new_position": 1},
        )
        assert reorder.status_code == 200
        reordered_items = reorder.json()["timeline_items"]
        assert reordered_items[1]["timeline_item_id"] == first["timeline_item_id"]

        patch = client.patch(
            f"/api/films/{draft_id}/timeline/{first['timeline_item_id']}",
            json={"trim_start": 0.1, "trim_end": 0.4},
        )
        assert patch.status_code == 200
        patched_item = next(
            item for item in patch.json()["timeline_items"] if item["timeline_item_id"] == first["timeline_item_id"]
        )
        assert patched_item["trim_start"] == 0.1
        assert patched_item["trim_end"] == 0.4

    def test_publish_creates_public_film_and_creator_data(self):
        project_id, draft_id = create_project_and_draft(name="Nova Frames", title="Launch Cut")

        shot_resp = client.post("/api/shots", json={"scene_id": "scene_1", "image_prompt": "Launch sequence"})
        shot_id = shot_resp.json()["id"]
        version_id = client.post(f"/api/shots/{shot_id}/regenerate").json()["new_version"]["id"]

        client.post(
            f"/api/drafts/{draft_id}/timeline-items",
            json={"shot_id": shot_id, "position": 0, "active_version_id": version_id},
        )

        publish_response = client.post(
            "/api/films/publish",
            json={"draft_id": draft_id, "tags": ["sci-fi", "launch"]},
        )
        assert publish_response.status_code == 200
        film = publish_response.json()
        assert film["id"] == draft_id
        assert film["video_url"] == f"/api/films/{draft_id}/rendered"
        assert film["creator"]["id"] == project_id
        assert film["creator"]["handle"] == "nova-frames"
        assert film["tags"] == ["sci-fi", "launch"]

        films_response = client.get("/api/films?sort=trending")
        assert films_response.status_code == 200
        assert films_response.json()[0]["id"] == draft_id

        creator_response = client.get("/api/users/@nova-frames")
        assert creator_response.status_code == 200
        creator = creator_response.json()
        assert creator["id"] == project_id
        assert creator["films"][0]["id"] == draft_id

        like_response = client.post(f"/api/films/{draft_id}/like")
        assert like_response.status_code == 200
        assert like_response.json()["like_count"] == 1

        support_response = client.post(
            f"/api/users/{project_id}/support",
            json={"amount_cents": 500},
        )
        assert support_response.status_code == 200
        assert support_response.json()["clientSecret"] == f"support_{project_id}_500"
