from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser
from app.db.models import (
    ActivityEventORM,
    AgentRunORM,
    AuditLogORM,
    BackgroundJobORM,
    GenerationFeedbackORM,
    IdeaORM,
    KnowledgeChunkORM,
    KnowledgeSourceORM,
    NotificationORM,
    ProjectMemoryORM,
    ProjectORM,
    UsageLedgerORM,
    WorkspaceMemberORM,
    WorkspaceORM,
)
from app.schemas.platform import ActivityEvent, AgentRun, Idea, IdeaStatus, KnowledgeSource, Notification, Project, ProjectMemory, UsageSummary, Workspace


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
        db.add(
            IdeaORM(
                workspace_id=workspace.id,
                project_id=project.id,
                title="Why discipline fails when your environment protects weak habits",
                description="Show the conflict between wanting growth and defending comfort.",
                format="YouTube long",
                score=88,
                status=IdeaStatus.approved.value,
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

    def update_idea_status(self, db: Session, idea_id: str, status: IdeaStatus) -> Idea | None:
        parsed = as_uuid(idea_id)
        if parsed is None:
            return None
        row = db.get(IdeaORM, parsed)
        if row is None:
            return None
        row.status = status.value
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

    def record_feedback(self, db: Session, user: CurrentUser, generation_id: str, action: str, note: str | None) -> dict[str, Any] | None:
        parsed_generation = as_uuid(generation_id)
        if parsed_generation is None:
            return None
        row = GenerationFeedbackORM(
            generation_id=parsed_generation,
            user_id=stable_user_uuid(user.id),
            action=action,
            note=note,
        )
        db.add(row)
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


repository = PlatformRepository()
