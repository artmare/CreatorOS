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


def test_persistent_workspace_project_memory_and_knowledge_flow():
    workspace = client.post(
        "/api/v1/workspaces",
        json={"name": "QA Durable Workspace", "plan": "Creator Pro", "monthly_limit": 777},
    )
    assert workspace.status_code == 200
    workspace_payload = workspace.json()
    assert workspace_payload["name"] == "QA Durable Workspace"
    assert workspace_payload["monthly_limit"] == 777

    project = client.post(
        "/api/v1/projects",
        json={
            "workspace_id": workspace_payload["id"],
            "name": "QA Durable Project",
            "niche": "creator education",
            "platform": "YouTube",
            "goal": "publish weekly",
            "audience": "B2B creators",
            "tone": "clear and direct",
            "content_rules": ["No generic claims"],
            "preferred_formats": ["Long-form"],
        },
    )
    assert project.status_code == 200
    project_payload = project.json()
    assert project_payload["workspace_id"] == workspace_payload["id"]

    memory = client.patch(
        "/api/v1/project-memory",
        json={
            "project_id": project_payload["id"],
            "tone": "sharp and useful",
            "content_rules": ["Use proof", "Avoid vague advice"],
            "best_performing_topics": ["systems", "distribution"],
        },
    )
    assert memory.status_code == 200
    assert memory.json()["tone"] == "sharp and useful"
    assert "Use proof" in memory.json()["content_rules"]

    source = client.post(
        "/api/v1/knowledge-base",
        json={
            "project_id": project_payload["id"],
            "title": "Durable QA source",
            "source_type": "pasted_text",
            "text": "Creators need repeatable systems. Scripts should be specific and measurable.",
        },
    )
    assert source.status_code == 200
    assert source.json()["project_id"] == project_payload["id"]


def test_persistent_agent_run_updates_usage_ledger():
    workspace = client.post("/api/v1/workspaces", json={"name": "QA Agent Workspace"})
    project = client.post(
        "/api/v1/projects",
        json={
            "workspace_id": workspace.json()["id"],
            "name": "QA Agent Project",
            "niche": "creator ops",
            "platform": "YouTube",
            "goal": "ship systems",
            "audience": "operators",
            "tone": "direct",
        },
    )
    before = client.get("/api/v1/usage/summary").json()["generations_used"]
    response = client.post(
        "/api/v1/agents/strategist/generate",
        json={"project_id": project.json()["id"], "prompt": "build a weekly content system", "intent": "qa"},
    )
    assert response.status_code == 200
    assert response.json()["token_estimate"] > 0

    agent_runs = client.get("/api/v1/agent-runs")
    assert agent_runs.status_code == 200
    assert any(run["project_id"] == project.json()["id"] for run in agent_runs.json())

    after = client.get("/api/v1/usage/summary").json()["generations_used"]
    assert after >= before + 1


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
