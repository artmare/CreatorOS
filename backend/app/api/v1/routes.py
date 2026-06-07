from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import CurrentUser, get_admin_user, get_current_user
from app.schemas.platform import (
    AgentGenerateRequest,
    ContentPackRequest,
    FeedbackRequest,
    IdeaStatus,
    OrchestratorRequest,
    StyleAnalyzeRequest,
)
from app.services.agents.orchestrator import orchestrator
from app.services.content_factory import generate_content_pack
from app.services.events import events
from app.services.growth_score import score_content
from app.services.integrations.billing import create_checkout, handle_webhook
from app.services.integrations.telegram import handle_telegram_update
from app.services.integrations.youtube import competitor_summary, own_channel_summary
from app.services.jobs import jobs
from app.services.quality import validate_output
from app.services.seed_store import store

router = APIRouter(prefix="/api/v1")


@router.get("/workspaces")
def workspaces(user: CurrentUser = Depends(get_current_user)):
    return list(store.workspaces.values())


@router.get("/projects")
def projects(user: CurrentUser = Depends(get_current_user)):
    return list(store.projects.values())


@router.get("/project-memory")
def project_memory(project_id: str = "project_youtube", user: CurrentUser = Depends(get_current_user)):
    return store.memories[project_id]


@router.get("/knowledge-base")
def knowledge_base(user: CurrentUser = Depends(get_current_user)):
    return list(store.knowledge_sources.values())


@router.post("/knowledge-base")
def add_knowledge(source: dict, user: CurrentUser = Depends(get_current_user)):
    source["id"] = store.new_id("kb")
    source["created_at"] = source.get("created_at") or store.ideas[next(iter(store.ideas))].created_at
    store.knowledge_sources[source["id"]] = source
    events.activity(user, "added knowledge source", "knowledge_source", source["id"])
    events.audit(user, "knowledge_source.created", "knowledge_source", source["id"], {"project_id": source.get("project_id")})
    return source


@router.get("/idea-vault")
def idea_vault(user: CurrentUser = Depends(get_current_user)):
    return list(store.ideas.values())


@router.patch("/idea-vault/{idea_id}/status")
def update_idea_status(idea_id: str, payload: dict, user: CurrentUser = Depends(get_current_user)):
    idea = store.ideas.get(idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    idea.status = IdeaStatus(payload["status"])
    events.activity(user, "updated idea status", "idea", idea_id)
    events.audit(user, "idea.status_updated", "idea", idea_id, {"status": idea.status.value})
    return idea


@router.post("/content-factory/generate-pack")
def content_factory(request: ContentPackRequest, user: CurrentUser = Depends(get_current_user)):
    pack = generate_content_pack(request)
    events.audit(user, "content_pack.generated", "content_pack", pack.id, {"topic": request.topic})
    return pack


@router.post("/orchestrator/produce")
def produce(request: OrchestratorRequest, user: CurrentUser = Depends(get_current_user)):
    result = orchestrator.produce(request.project_id, request.message)
    events.audit(user, "orchestrator.produced", "agent_run", None, {"agents": result["agents"]})
    return result


@router.post("/agents/{agent_name}/generate")
def generate_agent(agent_name: str, request: AgentGenerateRequest, user: CurrentUser = Depends(get_current_user)):
    run = orchestrator.run_agent(agent_name, request.project_id, request.prompt, request.intent)
    events.audit(user, "agent.generated", "agent_run", run.id, {"agent_name": agent_name})
    return run


@router.get("/agent-runs")
def agent_runs(user: CurrentUser = Depends(get_current_user)):
    return list(store.agent_runs.values())


@router.post("/generations/{generation_id}/feedback")
def generation_feedback(generation_id: str, request: FeedbackRequest, user: CurrentUser = Depends(get_current_user)):
    record = {"generation_id": generation_id, "action": request.action, "note": request.note, "user_id": user.id}
    store.feedback.append(record)
    if request.action == "save_to_style":
        store.memories["project_youtube"].content_rules.append(request.note or "User saved this output into style memory.")
    if request.action == "use_in_calendar":
        events.notify(user, "Added to calendar", "The generation was marked for the content calendar.", "calendar")
    events.audit(user, "generation.feedback", "generation", generation_id, {"action": request.action})
    return record


@router.get("/activity")
def activity(user: CurrentUser = Depends(get_current_user)):
    return store.activity


@router.get("/notifications")
def notifications(user: CurrentUser = Depends(get_current_user)):
    return store.notifications


@router.patch("/notifications/{notification_id}/read")
def mark_notification_read(notification_id: str, user: CurrentUser = Depends(get_current_user)):
    for notification in store.notifications:
        if notification.id == notification_id:
            notification.read = True
            events.audit(user, "notification.read", "notification", notification_id)
            return notification
    raise HTTPException(status_code=404, detail="Notification not found")


@router.get("/usage/summary")
def usage(user: CurrentUser = Depends(get_current_user)):
    return store.usage_summary()


@router.post("/growth-score")
def growth_score(payload: dict, user: CurrentUser = Depends(get_current_user)):
    return score_content(payload.get("title", ""), payload.get("body", ""))


@router.post("/style/analyze")
def style_analyze(request: StyleAnalyzeRequest, user: CurrentUser = Depends(get_current_user)):
    text = request.text
    normalized = text.lower()
    direct_markers = ["weak", "discipline", "\u0441\u043b\u0430\u0431", "\u0434\u0438\u0441\u0446\u0438\u043f\u043b\u0438\u043d"]
    style = {
        "tone": "direct, high-energy" if any(word in normalized for word in direct_markers) else "calm, explanatory",
        "vocabulary": ["discipline", "rule", "weak version", "responsibility", "\u0434\u0438\u0441\u0446\u0438\u043f\u043b\u0438\u043d\u0430"],
        "phrases": [sentence.strip() for sentence in text.split(".") if sentence.strip()][:5],
        "energy": "high" if len(text) > 500 else "medium",
        "quality": validate_output(text),
    }
    store.memories[request.project_id].content_rules.append(f"Style analysis: {style['tone']}")
    events.audit(user, "style.analyzed", "project_memory", request.project_id, {"energy": style["energy"]})
    return style


@router.post("/exports/markdown")
def export_markdown(payload: dict, user: CurrentUser = Depends(get_current_user)):
    title = payload.get("title", "CreatorOS Export")
    body = payload.get("body", "")
    markdown = f"# {title}\n\n{body}\n"
    events.audit(user, "export.markdown", "export", None, {"title": title})
    return {"markdown": markdown, "copy_ready": True}


@router.get("/background-jobs")
def background_jobs(user: CurrentUser = Depends(get_current_user)):
    return store.background_jobs


@router.post("/background-jobs")
def enqueue_job(payload: dict, user: CurrentUser = Depends(get_current_user)):
    return jobs.enqueue(
        user,
        payload.get("job_type", "content_generation"),
        payload.get("payload", {}),
        payload.get("idempotency_key"),
    )


@router.post("/telegram/webhook")
def telegram_webhook(payload: dict):
    return handle_telegram_update(payload)


@router.post("/youtube/competitors")
def youtube_competitors(payload: dict, user: CurrentUser = Depends(get_current_user)):
    return competitor_summary(payload.get("channel_url", ""))


@router.post("/youtube/channel-summary")
def youtube_channel(payload: dict, user: CurrentUser = Depends(get_current_user)):
    return own_channel_summary(payload.get("channel_id", ""))


@router.post("/billing/checkout")
def billing_checkout(payload: dict, user: CurrentUser = Depends(get_current_user)):
    return create_checkout(payload.get("plan", "creator_pro"))


@router.post("/billing/webhook")
def billing_webhook(payload: dict):
    return handle_webhook(payload)


admin_router = APIRouter(prefix="/api/v1/admin")


@admin_router.get("/users")
def admin_users(user: CurrentUser = Depends(get_admin_user)):
    return [{"id": "user_artem", "email": "artem@example.com", "role": "owner"}]


@admin_router.get("/workspaces")
def admin_workspaces(user: CurrentUser = Depends(get_admin_user)):
    return list(store.workspaces.values())


@admin_router.get("/subscriptions")
def admin_subscriptions(user: CurrentUser = Depends(get_admin_user)):
    return [{"workspace_id": "ws_creatoros_demo", "provider": "lemon_squeezy", "status": "trialing"}]


@admin_router.get("/generations")
def admin_generations(user: CurrentUser = Depends(get_admin_user)):
    return list(store.generations.values())


@admin_router.get("/agent-runs")
def admin_agent_runs(user: CurrentUser = Depends(get_admin_user)):
    return list(store.agent_runs.values())


@admin_router.get("/errors")
def admin_errors(user: CurrentUser = Depends(get_admin_user)):
    return store.errors


@admin_router.get("/feedback")
def admin_feedback(user: CurrentUser = Depends(get_admin_user)):
    return store.feedback


@admin_router.get("/usage")
def admin_usage(user: CurrentUser = Depends(get_admin_user)):
    return store.usage_summary()


@admin_router.get("/audit-logs")
def admin_audit_logs(user: CurrentUser = Depends(get_admin_user)):
    return store.audit_logs


@admin_router.get("/background-jobs")
def admin_background_jobs(user: CurrentUser = Depends(get_admin_user)):
    return store.background_jobs
