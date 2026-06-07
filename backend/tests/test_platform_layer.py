from app.db.session import Base
import app.db.models  # noqa: F401
from app.main import app
from app.services.seed_store import store
from fastapi.testclient import TestClient

client = TestClient(app)


def test_admin_rejects_non_admin_bearer_user():
    response = client.get("/api/v1/admin/users", headers={"Authorization": "Bearer local-user-token"})
    assert response.status_code == 403


def test_background_jobs_are_idempotent():
    payload = {
        "job_type": "content_generation",
        "payload": {"topic": "discipline"},
        "idempotency_key": "test-job-1",
    }
    first = client.post("/api/v1/background-jobs", json=payload)
    second = client.post("/api/v1/background-jobs", json=payload)
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]


def test_idea_status_transition_creates_audit_log():
    idea_id = next(iter(store.ideas))
    response = client.patch(f"/api/v1/idea-vault/{idea_id}/status", json={"status": "promising"})
    assert response.status_code == 200
    assert response.json()["status"] == "promising"
    assert any(log["action"] == "idea.status_updated" for log in store.audit_logs)


def test_markdown_export_is_copy_ready():
    response = client.post("/api/v1/exports/markdown", json={"title": "Pack", "body": "Script"})
    assert response.status_code == 200
    assert response.json()["copy_ready"] is True
    assert response.json()["markdown"].startswith("# Pack")


def test_production_orm_contains_scale_tables():
    expected = {
        "workspaces",
        "workspace_members",
        "projects",
        "project_memory",
        "knowledge_sources",
        "knowledge_chunks",
        "content_packs",
        "ideas",
        "agent_runs",
        "generations",
        "usage_ledger",
        "generation_feedback",
        "activity_events",
        "notifications",
        "background_jobs",
        "error_logs",
        "audit_logs",
        "subscriptions",
    }
    assert expected.issubset(set(Base.metadata.tables))
