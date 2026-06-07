from __future__ import annotations

import uuid
from datetime import datetime, time, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.core.auth import CurrentUser
from app.db.models import (
    ActivityEventORM,
    AgentRunORM,
    AuditLogORM,
    BackgroundJobORM,
    CalendarItemORM,
    ContentPackORM,
    GenerationFeedbackORM,
    GenerationORM,
    IdeaORM,
    KnowledgeChunkORM,
    KnowledgeSourceORM,
    NotificationORM,
    ProjectMemoryORM,
    ProjectORM,
    ScriptORM,
    UsageLedgerORM,
    WorkspaceMemberORM,
    WorkspaceORM,
)
from app.schemas.platform import (
    ActivityEvent,
    AgentRun,
    CalendarItem,
    ContentPack,
    ContentPackRequest,
    Generation,
    Idea,
    IdeaStatus,
    KnowledgeSource,
    Notification,
    Project,
    ProjectMemory,
    Script,
    UsageSummary,
    Workspace,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def as_uuid(value: str | uuid.UUID | None) -> uuid.UUID | None:
    if value is None:
        return None
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except ValueError:
        return None


def stable_user_uuid(user_id: str) -> uuid.UUID:
    parsed = as_uuid(user_id)
    return parsed or uuid.uuid5(uuid.NAMESPACE_URL, f"creatoros:user:{user_id}")


def estimate_tokens(*values: object) -> int:
    text = " ".join(str(value) for value in values if value is not None)
    return max(1, len(text) // 4)


class PlatformRepository:
    def ensure_demo_workspace(self, db: Session, user: CurrentUser) -> WorkspaceORM:
        workspace = db.scalars(select(WorkspaceORM).limit(1)).first()
        if workspace:
            return workspace

        workspace = WorkspaceORM(name="CreatorOS Studio", plan="Creator Pro", monthly_limit=500)
        db.add(workspace)
        db.flush()
        db.add(WorkspaceMemberORM(workspace_id=workspace.id, user_id=stable_user_uuid(user.id), role="owner"))

        project = ProjectORM(
            workspace_id=workspace.id,
            name="Motivation YouTube",
            niche="motivation and discipline",
            platform="YouTube + Shorts + Telegram",
            goal="grow the channel and publish strong scripts consistently",
            audience="men 16-25 who want discipline and concrete action",
            tone="direct, honest, no fluff",
        )
        db.add(project)
        db.flush()
        db.add(
            ProjectMemoryORM(
                project_id=project.id,
                niche=project.niche,
                audience=project.audience,
                tone=project.tone,
                content_rules=[
                    "Do not write generic motivational phrases.",
                    "Every idea needs conflict, pain, and one concrete action.",
                ],
                preferred_formats=["YouTube long", "Shorts", "Telegram"],
                rejected_ideas=["routine without a fresh angle"],
                best_performing_topics=["discipline", "responsibility", "money through skills"],
                past_successful_scripts=["You are not lazy. You repeat a weak version of yourself."],
            )
        )
        idea = IdeaORM(
            workspace_id=workspace.id,
            project_id=project.id,
            title="Why discipline fails when your environment protects weak habits",
            description="Show the conflict between wanting growth and defending comfort.",
            format="YouTube long",
            score=88,
            status=IdeaStatus.approved.value,
        )
        db.add(idea)
        db.flush()
        script = ScriptORM(
            workspace_id=workspace.id,
            project_id=project.id,
            idea_id=idea.id,
            title="Discipline fails when comfort owns your environment",
            body="Hook: You do not need more motivation. You need fewer exits.\n\nBuild the video around one clear rule, one visible consequence, and one action the viewer can do today.",
            status="ready",
            growth_score={"overall": 84, "hook": 88, "clarity": 90},
            export_state="markdown_ready",
        )
        db.add(script)
        db.flush()
        db.add(
            CalendarItemORM(
                workspace_id=workspace.id,
                project_id=project.id,
                idea_id=idea.id,
                script_id=script.id,
                title=script.title,
                platform="YouTube",
                status="script_ready",
                metadata_json={"source": "demo_seed"},
            )
        )
        db.commit()
        db.refresh(workspace)
        return workspace

    def list_workspaces(self, db: Session, user: CurrentUser) -> list[Workspace]:
        self.ensure_demo_workspace(db, user)
        rows = db.scalars(select(WorkspaceORM).order_by(WorkspaceORM.created_at.desc())).all()
        return [
            Workspace(
                id=str(row.id),
                name=row.name,
                plan=row.plan,
                role="owner",
                monthly_limit=row.monthly_limit,
            )
            for row in rows
        ]

    def create_workspace(self, db: Session, user: CurrentUser, payload: dict[str, Any]) -> Workspace:
        row = WorkspaceORM(
            name=payload.get("name") or "Untitled Workspace",
            plan=payload.get("plan") or "Creator Pro",
            monthly_limit=int(payload.get("monthly_limit") or 500),
        )
        db.add(row)
        db.flush()
        db.add(WorkspaceMemberORM(workspace_id=row.id, user_id=stable_user_uuid(user.id), role=payload.get("role") or "owner"))
        db.commit()
        db.refresh(row)
        return Workspace(id=str(row.id), name=row.name, plan=row.plan, role="owner", monthly_limit=row.monthly_limit)

    def list_projects(self, db: Session, user: CurrentUser) -> list[Project]:
        self.ensure_demo_workspace(db, user)
        rows = db.scalars(select(ProjectORM).order_by(ProjectORM.created_at.desc())).all()
        return [self._project(row) for row in rows]

    def create_project(self, db: Session, user: CurrentUser, payload: dict[str, Any]) -> Project:
        workspace_id = as_uuid(payload.get("workspace_id"))
        if workspace_id is None:
            workspace_id = self.ensure_demo_workspace(db, user).id

        row = ProjectORM(
            workspace_id=workspace_id,
            name=payload.get("name") or "Untitled Project",
            niche=payload.get("niche") or "",
            platform=payload.get("platform") or "",
            goal=payload.get("goal") or "",
            audience=payload.get("audience") or "",
            tone=payload.get("tone") or "",
        )
        db.add(row)
        db.flush()
        db.add(
            ProjectMemoryORM(
                project_id=row.id,
                niche=row.niche,
                audience=row.audience,
                tone=row.tone,
                content_rules=payload.get("content_rules") or [],
                preferred_formats=payload.get("preferred_formats") or [],
                rejected_ideas=[],
                best_performing_topics=[],
                past_successful_scripts=[],
            )
        )
        db.commit()
        db.refresh(row)
        return self._project(row)

    def get_memory(self, db: Session, project_id: str) -> ProjectMemory | None:
        parsed = as_uuid(project_id)
        if parsed is None:
            return None
        row = db.get(ProjectMemoryORM, parsed)
        if row is None:
            return None
        return self._memory(row)

    def upsert_memory(self, db: Session, project_id: str, payload: dict[str, Any]) -> ProjectMemory | None:
        parsed = as_uuid(project_id)
        if parsed is None:
            return None
        row = db.get(ProjectMemoryORM, parsed)
        if row is None:
            project = db.get(ProjectORM, parsed)
            if project is None:
                return None
            row = ProjectMemoryORM(project_id=parsed)
            db.add(row)
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
                setattr(row, key, payload[key])
        row.updated_at = _now()
        db.commit()
        db.refresh(row)
        return self._memory(row)

    def append_memory_rule(self, db: Session, project_id: str, rule: str, tone: str | None = None) -> ProjectMemory | None:
        parsed = as_uuid(project_id)
        if parsed is None:
            return None
        row = db.get(ProjectMemoryORM, parsed)
        if row is None:
            return None
        rules = list(row.content_rules or [])
        rules.append(rule)
        row.content_rules = rules
        if tone:
            row.tone = tone
        row.updated_at = _now()
        db.commit()
        db.refresh(row)
        return self._memory(row)

    def list_knowledge(self, db: Session, user: CurrentUser) -> list[KnowledgeSource]:
        self.ensure_demo_workspace(db, user)
        rows = db.scalars(select(KnowledgeSourceORM).order_by(KnowledgeSourceORM.created_at.desc())).all()
        return [
            KnowledgeSource(
                id=str(row.id),
                project_id=str(row.project_id),
                title=row.title,
                source_type=row.source_type,
                text=row.body,
                created_at=row.created_at,
            )
            for row in rows
        ]

    def add_knowledge(self, db: Session, user: CurrentUser, payload: dict[str, Any]) -> KnowledgeSource | None:
        project_id = as_uuid(payload.get("project_id"))
        if project_id is None:
            return None
        project = db.get(ProjectORM, project_id)
        if project is None:
            return None
        text = payload.get("text") or payload.get("body") or ""
        source = KnowledgeSourceORM(
            workspace_id=project.workspace_id,
            project_id=project.id,
            title=payload.get("title") or "Untitled source",
            source_type=payload.get("source_type") or "pasted_text",
            body=text,
        )
        db.add(source)
        db.flush()
        for index, chunk in enumerate(self.chunk_text(text)):
            db.add(KnowledgeChunkORM(source_id=source.id, chunk_index=index, body=chunk))
        db.commit()
        db.refresh(source)
        return KnowledgeSource(
            id=str(source.id),
            project_id=str(source.project_id),
            title=source.title,
            source_type=source.source_type,
            text=source.body,
            created_at=source.created_at,
        )

    def list_ideas(self, db: Session, user: CurrentUser) -> list[Idea]:
        self.ensure_demo_workspace(db, user)
        rows = db.scalars(select(IdeaORM).order_by(IdeaORM.created_at.desc())).all()
        return [self._idea(row) for row in rows]

    def create_idea(self, db: Session, user: CurrentUser, payload: dict[str, Any]) -> Idea | None:
        project_id = as_uuid(payload.get("project_id"))
        if project_id is None:
            return None
        project = db.get(ProjectORM, project_id)
        if project is None:
            return None
        status = IdeaStatus(payload.get("status") or IdeaStatus.draft.value)
        row = IdeaORM(
            workspace_id=project.workspace_id,
            project_id=project.id,
            title=payload.get("title") or "Untitled idea",
            description=payload.get("description") or "",
            format=payload.get("format") or "YouTube",
            score=int(payload.get("score") or 0),
            status=status.value,
        )
        db.add(row)
        db.flush()
        self._add_activity(db, project.workspace_id, user.email, "created idea", "idea", row.id)
        self._add_audit(db, project.workspace_id, user, "idea.created", "idea", row.id, {"status": status.value})
        db.commit()
        db.refresh(row)
        return self._idea(row)

    def update_idea_status(self, db: Session, idea_id: str, status: IdeaStatus) -> Idea | None:
        parsed = as_uuid(idea_id)
        if parsed is None:
            return None
        row = db.get(IdeaORM, parsed)
        if row is None:
            return None
        row.status = status.value
        if status == IdeaStatus.rejected:
            memory = db.get(ProjectMemoryORM, row.project_id)
            if memory:
                rejected = list(memory.rejected_ideas or [])
                if row.title not in rejected:
                    rejected.append(row.title)
                memory.rejected_ideas = rejected
                memory.updated_at = _now()
        db.commit()
        db.refresh(row)
        return self._idea(row)

    def list_activity(self, db: Session, user: CurrentUser) -> list[ActivityEvent]:
        self.ensure_demo_workspace(db, user)
        rows = db.scalars(select(ActivityEventORM).order_by(ActivityEventORM.created_at.desc()).limit(100)).all()
        return [
            ActivityEvent(
                id=str(row.id),
                workspace_id=str(row.workspace_id),
                actor=row.actor,
                verb=row.verb,
                object_type=row.object_type,
                object_id=str(row.object_id) if row.object_id else "",
                created_at=row.created_at,
            )
            for row in rows
        ]

    def list_notifications(self, db: Session, user: CurrentUser) -> list[Notification]:
        self.ensure_demo_workspace(db, user)
        rows = db.scalars(select(NotificationORM).order_by(NotificationORM.created_at.desc()).limit(100)).all()
        return [
            Notification(
                id=str(row.id),
                workspace_id=str(row.workspace_id),
                title=row.title,
                body=row.body,
                kind=row.kind,
                read=row.read,
                created_at=row.created_at,
            )
            for row in rows
        ]

    def mark_notification_read(self, db: Session, notification_id: str) -> Notification | None:
        parsed = as_uuid(notification_id)
        if parsed is None:
            return None
        row = db.get(NotificationORM, parsed)
        if row is None:
            return None
        row.read = True
        db.commit()
        db.refresh(row)
        return Notification(
            id=str(row.id),
            workspace_id=str(row.workspace_id),
            title=row.title,
            body=row.body,
            kind=row.kind,
            read=row.read,
            created_at=row.created_at,
        )

    def usage_summary(self, db: Session, user: CurrentUser) -> UsageSummary:
        workspace = self.ensure_demo_workspace(db, user)
        used = db.scalar(select(func.count(UsageLedgerORM.id))) or 0
        cost = db.scalar(select(func.coalesce(func.sum(UsageLedgerORM.cost_estimate), 0))) or 0
        return UsageSummary(
            workspace_id=str(workspace.id),
            plan=workspace.plan,
            month=_now().strftime("%Y-%m"),
            generations_used=int(used),
            generation_limit=workspace.monthly_limit,
            estimated_cost=round(float(cost), 4),
            blocked=int(used) >= workspace.monthly_limit,
        )

    def list_agent_runs(self, db: Session, user: CurrentUser) -> list[dict[str, Any]]:
        self.ensure_demo_workspace(db, user)
        rows = db.scalars(select(AgentRunORM).order_by(AgentRunORM.created_at.desc()).limit(100)).all()
        return [
            {
                "id": str(row.id),
                "workspace_id": str(row.workspace_id),
                "project_id": str(row.project_id),
                "agent_name": row.agent_name,
                "intent": row.intent,
                "input": row.input,
                "memory_used": row.memory_used,
                "model": row.model,
                "result": row.result,
                "token_estimate": row.token_estimate,
                "cost_estimate": float(row.cost_estimate),
                "validation_status": row.validation_status,
                "status": row.status,
                "created_at": row.created_at,
            }
            for row in rows
        ]

    def record_agent_run(self, db: Session, user: CurrentUser, run: AgentRun) -> dict[str, Any] | None:
        project_id = as_uuid(run.project_id)
        if project_id is None:
            return None
        project = db.get(ProjectORM, project_id)
        if project is None:
            return None
        row = AgentRunORM(
            workspace_id=project.workspace_id,
            project_id=project.id,
            agent_name=run.agent_name,
            intent=run.intent,
            input=run.input,
            memory_used=run.memory_used.model_dump(),
            model=run.model,
            result=run.result,
            token_estimate=run.token_estimate,
            cost_estimate=run.cost_estimate,
            validation_status=run.validation_status,
            status=run.status,
            created_at=run.created_at,
        )
        db.add(row)
        db.flush()
        db.add(
            GenerationORM(
                workspace_id=project.workspace_id,
                project_id=project.id,
                agent_run_id=row.id,
                type=f"agent:{run.agent_name}",
                prompt=str(run.input.get("prompt") or run.input.get("message") or ""),
                result=run.result,
                model=run.model,
                token_estimate=run.token_estimate,
                cost_estimate=run.cost_estimate,
                validation_status=run.validation_status,
                feedback_status=None,
                export_state="markdown_ready",
                created_at=run.created_at,
            )
        )
        db.add(
            UsageLedgerORM(
                workspace_id=project.workspace_id,
                user_id=stable_user_uuid(user.id),
                generation_type=f"agent:{run.agent_name}",
                model=run.model,
                token_estimate=run.token_estimate,
                cost_estimate=run.cost_estimate,
                blocked=False,
            )
        )
        db.commit()
        db.refresh(row)
        return {
            "id": str(row.id),
            "workspace_id": str(row.workspace_id),
            "project_id": str(row.project_id),
            "agent_name": row.agent_name,
            "intent": row.intent,
            "model": row.model,
            "token_estimate": row.token_estimate,
            "cost_estimate": float(row.cost_estimate),
            "status": row.status,
        }

    def record_content_pack(
        self,
        db: Session,
        user: CurrentUser,
        pack: ContentPack,
        request: ContentPackRequest,
    ) -> dict[str, Any] | None:
        project_id = as_uuid(request.project_id)
        if project_id is None:
            return None
        project = db.get(ProjectORM, project_id)
        if project is None:
            return None

        idea = IdeaORM(
            workspace_id=project.workspace_id,
            project_id=project.id,
            title=pack.idea.title,
            description=pack.idea.description,
            format=pack.idea.format,
            score=pack.idea.score,
            status=pack.idea.status.value,
        )
        db.add(idea)
        db.flush()

        payload = pack.model_dump(mode="json")
        payload["project_id"] = str(project.id)
        payload["idea"]["id"] = str(idea.id)
        payload["idea"]["project_id"] = str(project.id)

        content_pack = ContentPackORM(
            workspace_id=project.workspace_id,
            project_id=project.id,
            topic=request.topic,
            payload=payload,
        )
        db.add(content_pack)
        db.flush()
        payload["id"] = str(content_pack.id)

        token_count = estimate_tokens(request.topic, payload)
        cost = round(token_count * 0.000002, 6)
        generation = GenerationORM(
            workspace_id=project.workspace_id,
            project_id=project.id,
            agent_run_id=None,
            type="content_pack",
            prompt=request.topic,
            result=payload,
            model="creatoros-orchestrator-local",
            token_estimate=token_count,
            cost_estimate=cost,
            validation_status="pass",
            feedback_status=None,
            export_state="markdown_ready",
            created_at=pack.created_at,
        )
        db.add(generation)
        db.flush()
        payload["generation_id"] = str(generation.id)

        script = ScriptORM(
            workspace_id=project.workspace_id,
            project_id=project.id,
            idea_id=idea.id,
            generation_id=generation.id,
            title=pack.titles[0] if pack.titles else request.topic,
            body=pack.youtube_script,
            status="ready",
            growth_score=pack.growth_score.model_dump(mode="json"),
            export_state="markdown_ready",
        )
        db.add(script)
        db.flush()
        payload["script_id"] = str(script.id)

        if request.add_to_calendar:
            scheduled_for = None
            if request.publish_date:
                scheduled_for = datetime.combine(request.publish_date, time(hour=9), tzinfo=timezone.utc)
            calendar = CalendarItemORM(
                workspace_id=project.workspace_id,
                project_id=project.id,
                idea_id=idea.id,
                script_id=script.id,
                title=script.title,
                platform="YouTube",
                scheduled_for=scheduled_for,
                status="script_ready",
                metadata_json={"content_pack_id": str(content_pack.id), "generation_id": str(generation.id)},
            )
            db.add(calendar)
            db.flush()
            payload["calendar_item"] = {
                "id": str(calendar.id),
                "workspace_id": str(project.workspace_id),
                "project_id": str(project.id),
                "idea_id": str(idea.id),
                "script_id": str(script.id),
                "title": script.title,
                "platform": "YouTube",
                "scheduled_for": scheduled_for.isoformat() if scheduled_for else None,
                "status": "script_ready",
                "metadata": {"content_pack_id": str(content_pack.id), "generation_id": str(generation.id)},
                "created_at": _now().isoformat(),
            }

        content_pack.payload = dict(payload)
        generation.result = dict(payload)
        flag_modified(content_pack, "payload")
        flag_modified(generation, "result")
        db.add(
            UsageLedgerORM(
                workspace_id=project.workspace_id,
                user_id=stable_user_uuid(user.id),
                generation_type="content_pack",
                model="creatoros-orchestrator-local",
                token_estimate=token_count,
                cost_estimate=cost,
                blocked=False,
            )
        )
        self._add_activity(db, project.workspace_id, user.email, "created content pack", "content_pack", content_pack.id)
        self._add_notification(
            db,
            project.workspace_id,
            "Content pack ready",
            f"The pack for '{request.topic}' is ready.",
            "generation_completed",
        )
        self._add_audit(db, project.workspace_id, user, "content_pack.generated", "content_pack", content_pack.id, {"topic": request.topic})
        db.commit()
        return payload

    def list_content_packs(self, db: Session, user: CurrentUser) -> list[dict[str, Any]]:
        self.ensure_demo_workspace(db, user)
        rows = db.scalars(select(ContentPackORM).order_by(ContentPackORM.created_at.desc()).limit(100)).all()
        return [
            {
                **row.payload,
                "id": str(row.id),
                "workspace_id": str(row.workspace_id),
                "project_id": str(row.project_id),
                "topic": row.topic,
                "created_at": row.created_at,
            }
            for row in rows
        ]

    def list_generations(self, db: Session, user: CurrentUser) -> list[Generation]:
        self.ensure_demo_workspace(db, user)
        rows = db.scalars(select(GenerationORM).order_by(GenerationORM.created_at.desc()).limit(100)).all()
        return [
            Generation(
                id=str(row.id),
                workspace_id=str(row.workspace_id),
                project_id=str(row.project_id),
                type=row.type,
                prompt=row.prompt,
                result=row.result,
                model=row.model,
                token_estimate=row.token_estimate,
                cost_estimate=float(row.cost_estimate),
                validation_status=row.validation_status,
                feedback_status=row.feedback_status,
                created_at=row.created_at,
            )
            for row in rows
        ]

    def list_scripts(self, db: Session, user: CurrentUser) -> list[Script]:
        self.ensure_demo_workspace(db, user)
        rows = db.scalars(select(ScriptORM).order_by(ScriptORM.created_at.desc()).limit(100)).all()
        return [self._script(row) for row in rows]

    def create_script(self, db: Session, user: CurrentUser, payload: dict[str, Any]) -> Script | None:
        project_id = as_uuid(payload.get("project_id"))
        if project_id is None:
            return None
        project = db.get(ProjectORM, project_id)
        if project is None:
            return None
        row = ScriptORM(
            workspace_id=project.workspace_id,
            project_id=project.id,
            idea_id=as_uuid(payload.get("idea_id")),
            generation_id=as_uuid(payload.get("generation_id")),
            title=payload.get("title") or "Untitled script",
            body=payload.get("body") or "",
            status=payload.get("status") or "draft",
            growth_score=payload.get("growth_score") or {},
            export_state="markdown_ready",
        )
        db.add(row)
        db.flush()
        self._add_activity(db, project.workspace_id, user.email, "created script", "script", row.id)
        self._add_audit(db, project.workspace_id, user, "script.created", "script", row.id, {"status": row.status})
        db.commit()
        db.refresh(row)
        return self._script(row)

    def update_script(self, db: Session, user: CurrentUser, script_id: str, payload: dict[str, Any]) -> Script | None:
        row_id = as_uuid(script_id)
        if row_id is None:
            return None
        row = db.get(ScriptORM, row_id)
        if row is None:
            return None
        for key in ["title", "body", "status", "growth_score", "export_state"]:
            if key in payload:
                setattr(row, key, payload[key])
        row.updated_at = _now()
        self._add_audit(db, row.workspace_id, user, "script.updated", "script", row.id, {"status": row.status})
        db.commit()
        db.refresh(row)
        return self._script(row)

    def list_calendar_items(self, db: Session, user: CurrentUser) -> list[CalendarItem]:
        self.ensure_demo_workspace(db, user)
        rows = db.scalars(select(CalendarItemORM).order_by(CalendarItemORM.created_at.desc()).limit(100)).all()
        return [self._calendar_item(row) for row in rows]

    def create_calendar_item(self, db: Session, user: CurrentUser, payload: dict[str, Any]) -> CalendarItem | None:
        project_id = as_uuid(payload.get("project_id"))
        if project_id is None:
            return None
        project = db.get(ProjectORM, project_id)
        if project is None:
            return None
        row = CalendarItemORM(
            workspace_id=project.workspace_id,
            project_id=project.id,
            idea_id=as_uuid(payload.get("idea_id")),
            script_id=as_uuid(payload.get("script_id")),
            title=payload.get("title") or "Untitled calendar item",
            platform=payload.get("platform") or "YouTube",
            scheduled_for=payload.get("scheduled_for"),
            status=payload.get("status") or "idea",
            metadata_json=payload.get("metadata") or {},
        )
        db.add(row)
        db.flush()
        self._add_activity(db, project.workspace_id, user.email, "created calendar item", "calendar_item", row.id)
        self._add_audit(db, project.workspace_id, user, "calendar_item.created", "calendar_item", row.id, {"status": row.status})
        db.commit()
        db.refresh(row)
        return self._calendar_item(row)

    def update_calendar_item(self, db: Session, user: CurrentUser, item_id: str, payload: dict[str, Any]) -> CalendarItem | None:
        row_id = as_uuid(item_id)
        if row_id is None:
            return None
        row = db.get(CalendarItemORM, row_id)
        if row is None:
            return None
        for key, attr in [
            ("title", "title"),
            ("platform", "platform"),
            ("scheduled_for", "scheduled_for"),
            ("status", "status"),
            ("metadata", "metadata_json"),
        ]:
            if key in payload:
                setattr(row, attr, payload[key])
        row.updated_at = _now()
        self._add_audit(db, row.workspace_id, user, "calendar_item.updated", "calendar_item", row.id, {"status": row.status})
        db.commit()
        db.refresh(row)
        return self._calendar_item(row)

    def record_feedback(self, db: Session, user: CurrentUser, generation_id: str, action: str, note: str | None) -> dict[str, Any] | None:
        parsed_generation = as_uuid(generation_id)
        if parsed_generation is None:
            return None
        generation = db.get(GenerationORM, parsed_generation)
        if generation is None:
            return None
        row = GenerationFeedbackORM(
            generation_id=parsed_generation,
            user_id=stable_user_uuid(user.id),
            action=action,
            note=note,
        )
        db.add(row)
        generation.feedback_status = action
        if action == "save_to_style":
            memory = db.get(ProjectMemoryORM, generation.project_id)
            if memory:
                rules = list(memory.content_rules or [])
                rules.append(note or "User marked this output as part of the creator style.")
                memory.content_rules = rules
                memory.updated_at = _now()
        if action == "use_in_calendar":
            title = str(generation.result.get("topic") or generation.prompt or "Generation follow-up")
            db.add(
                CalendarItemORM(
                    workspace_id=generation.workspace_id,
                    project_id=generation.project_id,
                    title=title,
                    platform="YouTube",
                    status="script_ready",
                    metadata_json={"generation_id": str(generation.id), "source": "feedback"},
                )
            )
        if action == "regenerate":
            self._add_notification(db, generation.workspace_id, "Regeneration requested", "A new version can be queued from this feedback.", "feedback")
        self._add_activity(db, generation.workspace_id, user.email, "added generation feedback", "generation", generation.id)
        self._add_audit(db, generation.workspace_id, user, "generation.feedback", "generation", generation.id, {"action": action})
        db.commit()
        db.refresh(row)
        return {
            "id": str(row.id),
            "generation_id": str(row.generation_id),
            "action": row.action,
            "note": row.note,
            "user_id": str(row.user_id),
            "created_at": row.created_at,
        }

    def list_feedback(self, db: Session) -> list[dict[str, Any]]:
        rows = db.scalars(select(GenerationFeedbackORM).order_by(GenerationFeedbackORM.created_at.desc()).limit(100)).all()
        return [
            {
                "id": str(row.id),
                "generation_id": str(row.generation_id),
                "user_id": str(row.user_id),
                "action": row.action,
                "note": row.note,
                "created_at": row.created_at,
            }
            for row in rows
        ]

    def list_jobs(self, db: Session, user: CurrentUser) -> list[dict[str, Any]]:
        self.ensure_demo_workspace(db, user)
        rows = db.scalars(select(BackgroundJobORM).order_by(BackgroundJobORM.created_at.desc()).limit(100)).all()
        return [self._job(row) for row in rows]

    def enqueue_job(self, db: Session, user: CurrentUser, payload: dict[str, Any]) -> dict[str, Any]:
        workspace = self.ensure_demo_workspace(db, user)
        key = payload.get("idempotency_key")
        if key:
            existing = db.scalars(select(BackgroundJobORM).where(BackgroundJobORM.idempotency_key == key)).first()
            if existing:
                return self._job(existing)
        row = BackgroundJobORM(
            workspace_id=workspace.id,
            job_type=payload.get("job_type") or "content_generation",
            status="queued",
            idempotency_key=key,
            payload=payload.get("payload") or {},
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return self._job(row)

    def admin_audit_logs(self, db: Session) -> list[dict[str, Any]]:
        rows = db.scalars(select(AuditLogORM).order_by(AuditLogORM.created_at.desc()).limit(100)).all()
        return [
            {
                "id": str(row.id),
                "workspace_id": str(row.workspace_id) if row.workspace_id else None,
                "actor_user_id": str(row.actor_user_id) if row.actor_user_id else None,
                "action": row.action,
                "object_type": row.object_type,
                "object_id": str(row.object_id) if row.object_id else None,
                "metadata": row.metadata_json,
                "created_at": row.created_at,
            }
            for row in rows
        ]

    def chunk_text(self, text: str, chunk_size: int = 900) -> list[str]:
        clean = " ".join(text.split())
        if not clean:
            return []
        return [clean[index : index + chunk_size] for index in range(0, len(clean), chunk_size)]

    def _project(self, row: ProjectORM) -> Project:
        return Project(
            id=str(row.id),
            workspace_id=str(row.workspace_id),
            name=row.name,
            niche=row.niche or "",
            platform=row.platform or "",
            goal=row.goal or "",
            audience=row.audience or "",
            tone=row.tone or "",
        )

    def _memory(self, row: ProjectMemoryORM) -> ProjectMemory:
        return ProjectMemory(
            project_id=str(row.project_id),
            niche=row.niche or "",
            audience=row.audience or "",
            tone=row.tone or "",
            content_rules=row.content_rules or [],
            preferred_formats=row.preferred_formats or [],
            rejected_ideas=row.rejected_ideas or [],
            best_performing_topics=row.best_performing_topics or [],
            past_successful_scripts=row.past_successful_scripts or [],
        )

    def _idea(self, row: IdeaORM) -> Idea:
        return Idea(
            id=str(row.id),
            project_id=str(row.project_id),
            title=row.title,
            description=row.description or "",
            format=row.format or "",
            score=row.score,
            status=IdeaStatus(row.status),
            created_at=row.created_at,
        )

    def _script(self, row: ScriptORM) -> Script:
        return Script(
            id=str(row.id),
            workspace_id=str(row.workspace_id),
            project_id=str(row.project_id),
            idea_id=str(row.idea_id) if row.idea_id else None,
            generation_id=str(row.generation_id) if row.generation_id else None,
            title=row.title,
            body=row.body,
            status=row.status,
            growth_score=row.growth_score or {},
            export_state=row.export_state,
            created_at=row.created_at,
        )

    def _calendar_item(self, row: CalendarItemORM) -> CalendarItem:
        return CalendarItem(
            id=str(row.id),
            workspace_id=str(row.workspace_id),
            project_id=str(row.project_id),
            idea_id=str(row.idea_id) if row.idea_id else None,
            script_id=str(row.script_id) if row.script_id else None,
            title=row.title,
            platform=row.platform,
            scheduled_for=row.scheduled_for,
            status=row.status,
            metadata=row.metadata_json or {},
            created_at=row.created_at,
        )

    def _job(self, row: BackgroundJobORM) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "workspace_id": str(row.workspace_id),
            "job_type": row.job_type,
            "status": row.status,
            "idempotency_key": row.idempotency_key,
            "payload": row.payload,
            "error": row.error,
            "created_at": row.created_at,
        }

    def _add_activity(
        self,
        db: Session,
        workspace_id: uuid.UUID,
        actor: str,
        verb: str,
        object_type: str,
        object_id: uuid.UUID | None,
    ) -> None:
        db.add(
            ActivityEventORM(
                workspace_id=workspace_id,
                actor=actor,
                verb=verb,
                object_type=object_type,
                object_id=object_id,
            )
        )

    def _add_notification(self, db: Session, workspace_id: uuid.UUID, title: str, body: str, kind: str) -> None:
        db.add(
            NotificationORM(
                workspace_id=workspace_id,
                title=title,
                body=body,
                kind=kind,
                read=False,
            )
        )

    def _add_audit(
        self,
        db: Session,
        workspace_id: uuid.UUID | None,
        user: CurrentUser,
        action: str,
        object_type: str,
        object_id: uuid.UUID | None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        db.add(
            AuditLogORM(
                workspace_id=workspace_id,
                actor_user_id=stable_user_uuid(user.id),
                action=action,
                object_type=object_type,
                object_id=object_id,
                metadata_json=metadata or {},
            )
        )


repository = PlatformRepository()
