import pytest
from fastapi.testclient import TestClient

from skill_tracker.presentation.app import create_app


@pytest.fixture()
def client(tmp_path):
    app = create_app(tmp_path / "api.db")
    with TestClient(app) as test_client:
        yield test_client


def test_health(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_dashboard_uses_camel_case(client: TestClient) -> None:
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    body = response.json()
    assert body["activeTopicsCount"] == 3
    assert body["totalModules"] == 11
    assert body["totalHoursLogged"] == pytest.approx(7.0)
    assert len(body["recentLogs"]) == 3
    assert "topicTitle" in body["recentLogs"][0]


def test_topics_are_seeded(client: TestClient) -> None:
    response = client.get("/api/topics")
    assert response.status_code == 200
    topics = response.json()
    assert len(topics) == 3
    assert topics[0]["totalModules"] == 4
    assert topics[0]["completionPercentage"] == 50
    assert topics[0]["color"] == "blue"


def test_create_update_delete_topic(client: TestClient) -> None:
    created = client.post(
        "/api/topics",
        json={
            "title": "Compilers",
            "category": "Engineering",
            "color": "cyan",
            "description": "Parsing and codegen",
            "notes": "LLVM is a rabbit hole",
        },
    )
    assert created.status_code == 201
    topic = created.json()
    assert topic["title"] == "Compilers"
    assert topic["modules"] == []

    updated = client.put(
        f"/api/topics/{topic['id']}",
        json={"title": "Compilers II", "category": "Engineering", "color": "amber"},
    )
    assert updated.status_code == 200
    assert updated.json()["color"] == "amber"

    deleted = client.delete(f"/api/topics/{topic['id']}")
    assert deleted.status_code == 204

    missing = client.delete(f"/api/topics/{topic['id']}")
    assert missing.status_code == 404


def test_blank_topic_title_returns_400(client: TestClient) -> None:
    response = client.post("/api/topics", json={"title": "   "})
    assert response.status_code == 400
    assert "cannot be empty" in response.json()["detail"]


def test_add_and_toggle_module(client: TestClient) -> None:
    topic = client.get("/api/topics").json()[0]

    added = client.post(f"/api/topics/{topic['id']}/modules", json={"title": "New module"})
    assert added.status_code == 201
    module = next(m for m in added.json()["modules"] if m["title"] == "New module")

    toggled = client.patch(f"/api/topics/{topic['id']}/modules/{module['id']}/toggle")
    assert toggled.status_code == 200
    toggled_module = next(m for m in toggled.json()["modules"] if m["id"] == module["id"])
    assert toggled_module["completed"] is True


def test_project_crud_and_tasks(client: TestClient) -> None:
    topic = client.get("/api/topics").json()[0]

    created = client.post(
        "/api/projects",
        json={
            "title": "Observability",
            "topicId": topic["id"],
            "status": "Planning",
            "targetDate": "2027-03-01",
            "techStack": ["Go", "Prometheus"],
        },
    )
    assert created.status_code == 201
    project = created.json()
    assert project["status"] == "Planning"
    assert project["techStack"] == ["Go", "Prometheus"]

    task_response = client.post(f"/api/projects/{project['id']}/tasks", json={"title": "Sketch"})
    assert task_response.status_code == 201
    task = task_response.json()["tasks"][0]

    toggled = client.patch(f"/api/projects/{project['id']}/tasks/{task['id']}/toggle")
    assert toggled.json()["tasks"][0]["completed"] is True
    assert toggled.json()["taskCompletionPercentage"] == 100


def test_project_with_unknown_topic_returns_404(client: TestClient) -> None:
    response = client.post("/api/projects", json={"title": "Ghost", "topicId": "missing"})
    assert response.status_code == 404


def test_log_session_updates_project_hours(client: TestClient) -> None:
    topic = client.get("/api/topics").json()[0]
    project = client.post(
        "/api/projects", json={"title": "Tracker", "topicId": topic["id"]}
    ).json()
    starting_hours = project["hoursSpent"]

    response = client.post(
        "/api/logs",
        json={
            "topicId": topic["id"],
            "projectId": project["id"],
            "hours": 1.5,
            "date": "2026-11-07",
            "note": "Wrote API layer",
        },
    )
    assert response.status_code == 201
    log = response.json()
    assert log["hours"] == 1.5
    assert log["topicTitle"] == topic["title"]

    refreshed = next(
        item for item in client.get("/api/projects").json() if item["id"] == project["id"]
    )
    assert refreshed["hoursSpent"] == pytest.approx(starting_hours + 1.5)


def test_invalid_log_hours_returns_400(client: TestClient) -> None:
    topic = client.get("/api/topics").json()[0]
    response = client.post(
        "/api/logs", json={"topicId": topic["id"], "hours": 0}
    )
    assert response.status_code == 400


def test_static_spa_is_served(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "SkillTrack Studio" in response.text


XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def test_export_returns_downloadable_workbook(client: TestClient) -> None:
    response = client.get("/api/export")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(XLSX)
    assert "attachment; filename=" in response.headers["content-disposition"]
    assert response.content.startswith(b"PK")


def test_import_restores_exported_workbook(client: TestClient) -> None:
    topics_before = client.get("/api/topics").json()
    projects_before = client.get("/api/projects").json()
    logs_before = client.get("/api/logs").json()
    exported = client.get("/api/export").content

    client.post("/api/topics", json={"title": "Scratch"})
    client.post("/api/projects", json={"title": "Throwaway"})
    assert len(client.get("/api/topics").json()) == len(topics_before) + 1

    response = client.post(
        "/api/import",
        files={"file": ("backup.xlsx", exported, XLSX)},
    )

    assert response.status_code == 200
    assert response.json() == {
        "topicsImported": len(topics_before),
        "projectsImported": len(projects_before),
        "logsImported": len(logs_before),
    }
    assert [topic["id"] for topic in client.get("/api/topics").json()] == [
        topic["id"] for topic in topics_before
    ]


def test_import_rejects_invalid_workbook(client: TestClient) -> None:
    response = client.post(
        "/api/import",
        files={"file": ("notes.xlsx", b"definitely not a workbook", XLSX)},
    )

    assert response.status_code == 400
    assert "valid .xlsx" in response.json()["detail"]
