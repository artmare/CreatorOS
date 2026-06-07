from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_usage_summary():
    response = client.get("/api/v1/usage/summary")
    assert response.status_code == 200
    assert response.json()["plan"] == "Creator Pro"


def test_content_pack_generation():
    response = client.post(
        "/api/v1/content-factory/generate-pack",
        json={"project_id": "project_youtube", "topic": "дисциплина после провала"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["titles"]) == 5
    assert len(payload["shorts"]) == 5


def test_orchestrator_routes_to_agents():
    response = client.post(
        "/api/v1/orchestrator/produce",
        json={"project_id": "project_youtube", "message": "сделай сценарий и shorts"},
    )
    assert response.status_code == 200
    agents = response.json()["agents"]
    assert "scriptwriter" in agents
    assert "repurposer" in agents
