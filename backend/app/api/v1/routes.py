from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser, get_admin_user, get_current_user
from app.db.session import get_db
from app.schemas.platform import (
    AgentGenerateRequest,
    CalendarItemRequest,
    ContentPackRequest,
    FeedbackRequest,
    IdeaStatus,
    OrchestratorRequest,
    ScriptRequest,
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
from app.services.persistence import repository
from app.services.quality import validate_output
from app.services.seed_store import store

router = APIRouter(prefix="/api/v1")


def ensure_agent_memory(project_id: str, db: Session) -> None:
    if project_id in store.memories:
        return
    memory = repository.get_memory(db, project_id)
    if memory:
        store.memories[project_id] = memory


@router.get("/auth/me")
def auth_me(user: CurrentUser = Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "role": user.role, "workspace_id": user.workspace_id}


@router.get("/workspaces")
def workspaces(user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return repository.list_workspaces(db, user)


@router.post("/workspaces")
def create_workspace(payload: dict, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    workspace = repository.create_workspace(db, user, payload)
    events.audit(user, "workspace.created", "workspace", workspace.id, {"name": workspace.name})
    return workspace


@router.get("/projects")
def projects(user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return repository.list_projects(db, user)


@router.post("/projects")
def create_project(payload: dict, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    project = repository.create_project(db, user, payload)
    events.audit(user, "project.created", "project", project.id, {"workspace_id": project.workspace_id})
    return project


@router.get("/project-memory")
def project_memory(project_id: str = "project_youtube", user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    memory = repository.get_memory(db, project_id)
    if memory:
        return memory
    return store.memories[project_id]


@router.patch("/project-memory")
def update_project_memory(payload: dict, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    project_id = payload.get("project_id", "project_youtube")
    memory = repository.upsert_memory(db, project_id, payload)
    if memory:
        events.audit(user, "project_memory.updated", "project_memory", project_id)
        return memory
    if project_id in store.memories:
        for key in [
            "niche",
            "audience",
            "tone",
            "content_rules",
            "preferred_formats",
            "rejected_ideas",
            "best_performing_topics",
            "past_successful_scripts",
        ]:
            if key in payload:
                setattr(store.memories[project_id], key, payload[key])
        events.audit(user, "project_memory.updated", "project_memory", project_id)
        return store.memories[project_id]
    raise HTTPException(status_code=404, detail="Project memory not found")


@router.get("/knowledge-base")
def knowledge_base(user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    persisted = repository.list_knowledge(db, user)
    return persisted or list(store.knowledge_sources.values())


@router.post("/knowledge-base")
def add_knowledge(source: dict, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    persisted = repository.add_knowledge(db, user, source)
    if persisted:
        events.activity(user, "added knowledge source", "knowledge_source", persisted.id)
        events.audit(user, "knowledge_source.created", "knowledge_source", persisted.id, {"project_id": persisted.project_id})
        return persisted
    source["id"] = store.new_id("kb")
    source["created_at"] = source.get("created_at") or store.ideas[next(iter(store.ideas))].created_at
    store.knowledge_sources[source["id"]] = source
    events.activity(user, "added knowledge source", "knowledge_source", source["id"])
    events.audit(user, "knowledge_source.created", "knowledge_source", source["id"], {"project_id": source.get("project_id")})
    return source


@router.get("/idea-vault")
def idea_vault(user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    persisted = repository.list_ideas(db, user)
    return persisted or list(store.ideas.values())


@router.post("/idea-vault")
def create_idea(payload: dict, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    persisted = repository.create_idea(db, user, payload)
    if persisted:
        events.activity(user, "created idea", "idea", persisted.id)
        events.audit(user, "idea.created", "idea", persisted.id, {"status": persisted.status.value})
        return persisted
    idea = store.add_idea(
        title=payload.get("title", "Untitled idea"),
        description=payload.get("description", ""),
        format=payload.get("format", "YouTube"),
        score=int(payload.get("score", 0)),
        status=IdeaStatus(payload.get("status", "draft")),
    )
    events.activity(user, "created idea", "idea", idea.id)
    events.audit(user, "idea.created", "idea", idea.id, {"status": idea.status.value})
    return idea


@router.patch("/idea-vault/{idea_id}/status")
def update_idea_status(idea_id: str, payload: dict, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    new_status = IdeaStatus(payload["status"])
    persisted = repository.update_idea_status(db, idea_id, new_status)
    if persisted:
        events.activity(user, "updated idea status", "idea", idea_id)
        events.audit(user, "idea.status_updated", "idea", idea_id, {"status": persisted.status.value})
        return persisted
    idea = store.ideas.get(idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    idea.status = new_status
    events.activity(user, "updated idea status", "idea", idea_id)
    events.audit(user, "idea.status_updated", "idea", idea_id, {"status": idea.status.value})
    return idea


@router.post("/content-factory/generate-pack")
def content_factory(request: ContentPackRequest, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    ensure_agent_memory(request.project_id, db)
    pack = generate_content_pack(request)
    persisted = repository.record_content_pack(db, user, pack, request)
    if persisted:
        events.activity(user, "created content pack", "content_pack", persisted["id"])
        events.notify(user, "Content pack ready", f"The pack for '{request.topic}' is ready.", "generation_completed")
        events.audit(user, "content_pack.generated", "content_pack", persisted["id"], {"topic": request.topic})
        return persisted
    events.audit(user, "content_pack.generated", "content_pack", pack.id, {"topic": request.topic})
    return pack


@router.get("/content-factory/packs")
def content_packs(user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    persisted = repository.list_content_packs(db, user)
    return persisted or list(store.content_packs.values())


@router.post("/orchestrator/produce")
def produce(request: OrchestratorRequest, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    ensure_agent_memory(request.project_id, db)
    result = orchestrator.produce(request.project_id, request.message)
    for run in result["runs"]:
        repository.record_agent_run(db, user, run)
    events.audit(user, "orchestrator.produced", "agent_run", None, {"agents": result["agents"]})
    return result


@router.post("/agents/{agent_name}/generate")
def generate_agent(agent_name: str, request: AgentGenerateRequest, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    ensure_agent_memory(request.project_id, db)
    run = orchestrator.run_agent(agent_name, request.project_id, request.prompt, request.intent)
    repository.record_agent_run(db, user, run)
    events.audit(user, "agent.generated", "agent_run", run.id, {"agent_name": agent_name})
    return run


@router.get("/agent-runs")
def agent_runs(user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    persisted = repository.list_agent_runs(db, user)
    return persisted + list(store.agent_runs.values())


@router.post("/generations/{generation_id}/feedback")
def generation_feedback(generation_id: str, request: FeedbackRequest, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    persisted = repository.record_feedback(db, user, generation_id, request.action.value, request.note)
    if persisted:
        if request.action == "use_in_calendar":
            events.notify(user, "Added to calendar", "The generation was marked for the content calendar.", "calendar")
        events.audit(user, "generation.feedback", "generation", generation_id, {"action": request.action.value})
        return persisted
    record = {"generation_id": generation_id, "action": request.action, "note": request.note, "user_id": user.id}
    store.feedback.append(record)
    if request.action == "save_to_style":
        store.memories["project_youtube"].content_rules.append(request.note or "User saved this output into style memory.")
    if request.action == "use_in_calendar":
        events.notify(user, "Added to calendar", "The generation was marked for the content calendar.", "calendar")
    events.audit(user, "generation.feedback", "generation", generation_id, {"action": request.action})
    return record


@router.get("/activity")
def activity(user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    persisted = repository.list_activity(db, user)
    return persisted + store.activity


@router.get("/notifications")
def notifications(user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    persisted = repository.list_notifications(db, user)
    return persisted + store.notifications


@router.patch("/notifications/{notification_id}/read")
def mark_notification_read(notification_id: str, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    persisted = repository.mark_notification_read(db, notification_id)
    if persisted:
        events.audit(user, "notification.read", "notification", notification_id)
        return persisted
    for notification in store.notifications:
        if notification.id == notification_id:
            notification.read = True
            events.audit(user, "notification.read", "notification", notification_id)
            return notification
    raise HTTPException(status_code=404, detail="Notification not found")


@router.get("/usage/summary")
def usage(user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    persisted = repository.usage_summary(db, user)
    return persisted


@router.post("/growth-score")
def growth_score(payload: dict, user: CurrentUser = Depends(get_current_user)):
    return score_content(payload.get("title", ""), payload.get("body", ""))


@router.post("/style/analyze")
def style_analyze(request: StyleAnalyzeRequest, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    ensure_agent_memory(request.project_id, db)
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
    rule = f"Style analysis: {style['tone']}; energy={style['energy']}"
    persisted_memory = repository.append_memory_rule(db, request.project_id, rule, style["tone"])
    if persisted_memory:
        store.memories[request.project_id] = persisted_memory
    elif request.project_id in store.memories:
        store.memories[request.project_id].content_rules.append(rule)
    events.audit(user, "style.analyzed", "project_memory", request.project_id, {"energy": style["energy"]})
    return style


@router.get("/scripts")
def scripts(user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return repository.list_scripts(db, user)


@router.post("/scripts")
def create_script(request: ScriptRequest, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    persisted = repository.create_script(db, user, request.model_dump(mode="python"))
    if persisted:
        events.activity(user, "created script", "script", persisted.id)
        events.audit(user, "script.created", "script", persisted.id, {"status": persisted.status})
        return persisted
    raise HTTPException(status_code=404, detail="Project not found")


@router.patch("/scripts/{script_id}")
def update_script(script_id: str, payload: dict, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    persisted = repository.update_script(db, user, script_id, payload)
    if not persisted:
        raise HTTPException(status_code=404, detail="Script not found")
    events.audit(user, "script.updated", "script", script_id, {"status": persisted.status})
    return persisted


@router.get("/calendar")
def calendar(user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return repository.list_calendar_items(db, user)


@router.post("/calendar")
def create_calendar_item(request: CalendarItemRequest, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    persisted = repository.create_calendar_item(db, user, request.model_dump(mode="python"))
    if persisted:
        events.activity(user, "created calendar item", "calendar_item", persisted.id)
        events.audit(user, "calendar_item.created", "calendar_item", persisted.id, {"status": persisted.status})
        return persisted
    raise HTTPException(status_code=404, detail="Project not found")


@router.patch("/calendar/{item_id}")
def update_calendar_item(item_id: str, payload: dict, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    persisted = repository.update_calendar_item(db, user, item_id, payload)
    if not persisted:
        raise HTTPException(status_code=404, detail="Calendar item not found")
    events.audit(user, "calendar_item.updated", "calendar_item", item_id, {"status": persisted.status})
    return persisted


@router.post("/exports/markdown")
def export_markdown(payload: dict, user: CurrentUser = Depends(get_current_user)):
    title = payload.get("title", "CreatorOS Export")
    body = payload.get("body", "")
    markdown = f"# {title}\n\n{body}\n"
    events.audit(user, "export.markdown", "export", None, {"title": title})
    return {"markdown": markdown, "copy_ready": True}


@router.get("/background-jobs")
def background_jobs(user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    persisted = repository.list_jobs(db, user)
    return persisted or store.background_jobs


@router.post("/background-jobs")
def enqueue_job(payload: dict, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    persisted = repository.enqueue_job(db, user, payload)
    if persisted:
        return persisted
    return jobs.enqueue(user, payload.get("job_type", "content_generation"), payload.get("payload", {}), payload.get("idempotency_key"))


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
def admin_workspaces(user: CurrentUser = Depends(get_admin_user), db: Session = Depends(get_db)):
    return repository.list_workspaces(db, user)


@admin_router.get("/subscriptions")
def admin_subscriptions(user: CurrentUser = Depends(get_admin_user)):
    return [{"workspace_id": "ws_creatoros_demo", "provider": "lemon_squeezy", "status": "trialing"}]


@admin_router.get("/generations")
def admin_generations(user: CurrentUser = Depends(get_admin_user), db: Session = Depends(get_db)):
    return repository.list_generations(db, user) + list(store.generations.values())


@admin_router.get("/agent-runs")
def admin_agent_runs(user: CurrentUser = Depends(get_admin_user), db: Session = Depends(get_db)):
    return repository.list_agent_runs(db, user) + list(store.agent_runs.values())


@admin_router.get("/errors")
def admin_errors(user: CurrentUser = Depends(get_admin_user)):
    return store.errors


@admin_router.get("/feedback")
def admin_feedback(user: CurrentUser = Depends(get_admin_user), db: Session = Depends(get_db)):
    return repository.list_feedback(db) + store.feedback


@admin_router.get("/usage")
def admin_usage(user: CurrentUser = Depends(get_admin_user), db: Session = Depends(get_db)):
    return repository.usage_summary(db, user)


@admin_router.get("/audit-logs")
def admin_audit_logs(user: CurrentUser = Depends(get_admin_user), db: Session = Depends(get_db)):
    persisted = repository.admin_audit_logs(db)
    return persisted + store.audit_logs


@admin_router.get("/background-jobs")
def admin_background_jobs(user: CurrentUser = Depends(get_admin_user), db: Session = Depends(get_db)):
    persisted = repository.list_jobs(db, user)
    return persisted or store.background_jobs
