from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.schemas.platform import (
    ActivityEvent,
    AgentRun,
    Generation,
    Idea,
    IdeaStatus,
    KnowledgeSource,
    Notification,
    Project,
    ProjectMemory,
    UsageSummary,
    Workspace,
)


def now() -> datetime:
    return datetime.now(timezone.utc)


class SeedStore:
    def __init__(self) -> None:
        self.workspaces: dict[str, Workspace] = {
            "ws_creatoros_demo": Workspace(
                id="ws_creatoros_demo",
                name="CreatorOS Studio",
                plan="Creator Pro",
                role="owner",
                monthly_limit=500,
            )
        }
        self.projects: dict[str, Project] = {
            "project_youtube": Project(
                id="project_youtube",
                workspace_id="ws_creatoros_demo",
                name="Motivation YouTube",
                niche="мотивация и дисциплина",
                platform="YouTube + Shorts + Telegram",
                goal="рост канала и регулярный выпуск сильных сценариев",
                audience="парни 16-25 лет, которые хотят собраться и перестать сливать время",
                tone="жесткий, честный, без воды",
            )
        }
        self.memories: dict[str, ProjectMemory] = {
            "project_youtube": ProjectMemory(
                project_id="project_youtube",
                niche="мотивация и дисциплина",
                audience="парни 16-25 лет",
                tone="жесткий, честный, без воды",
                content_rules=[
                    "Не писать общие мотивационные фразы.",
                    "Каждая идея должна иметь конфликт и боль.",
                    "Давать конкретные действия в конце.",
                ],
                preferred_formats=["YouTube long", "Shorts", "Telegram"],
                rejected_ideas=["утренняя рутина без нового угла", "топ-10 привычек без истории"],
                best_performing_topics=["дисциплина", "мужская ответственность", "деньги через навык"],
                past_successful_scripts=[
                    "Ты не ленивый. Ты каждый день тренируешь слабую версию себя."
                ],
            )
        }
        self.knowledge_sources: dict[str, KnowledgeSource] = {}
        self.ideas: dict[str, Idea] = {}
        self.generations: dict[str, Generation] = {}
        self.agent_runs: dict[str, AgentRun] = {}
        self.feedback: list[dict[str, Any]] = []
        self.notifications: list[Notification] = []
        self.activity: list[ActivityEvent] = []
        self.audit_logs: list[dict[str, Any]] = []
        self.errors: list[dict[str, Any]] = []

        self.add_idea(
            "Почему дисциплина не работает, пока ты защищаешь слабые привычки",
            "Разобрать конфликт между желанием измениться и привычкой искать оправдания.",
            "YouTube long",
            88,
            IdeaStatus.approved,
        )

    def new_id(self, prefix: str) -> str:
        return f"{prefix}_{uuid4().hex[:10]}"

    def add_activity(self, verb: str, object_type: str, object_id: str, actor: str = "AI Producer") -> None:
        self.activity.insert(
            0,
            ActivityEvent(
                id=self.new_id("activity"),
                workspace_id="ws_creatoros_demo",
                actor=actor,
                verb=verb,
                object_type=object_type,
                object_id=object_id,
                created_at=now(),
            ),
        )

    def add_notification(self, title: str, body: str, kind: str) -> None:
        self.notifications.insert(
            0,
            Notification(
                id=self.new_id("notification"),
                workspace_id="ws_creatoros_demo",
                title=title,
                body=body,
                kind=kind,
                read=False,
                created_at=now(),
            ),
        )

    def add_idea(self, title: str, description: str, format: str, score: int, status: IdeaStatus) -> Idea:
        idea = Idea(
            id=self.new_id("idea"),
            project_id="project_youtube",
            title=title,
            description=description,
            format=format,
            score=score,
            status=status,
            created_at=now(),
        )
        self.ideas[idea.id] = idea
        self.add_activity("создал идею", "idea", idea.id)
        return idea

    def usage_summary(self) -> UsageSummary:
        workspace = self.workspaces["ws_creatoros_demo"]
        estimated_cost = sum(g.cost_estimate for g in self.generations.values())
        return UsageSummary(
            workspace_id=workspace.id,
            plan=workspace.plan,
            month=now().strftime("%Y-%m"),
            generations_used=len(self.generations),
            generation_limit=workspace.monthly_limit,
            estimated_cost=round(estimated_cost, 4),
            blocked=len(self.generations) >= workspace.monthly_limit,
        )


store = SeedStore()
