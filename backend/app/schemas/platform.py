from datetime import date, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class IdeaStatus(StrEnum):
    draft = "draft"
    promising = "promising"
    approved = "approved"
    in_script = "in_script"
    scheduled = "scheduled"
    published = "published"
    rejected = "rejected"
    archived = "archived"


class FeedbackAction(StrEnum):
    good = "good"
    bad = "bad"
    regenerate = "regenerate"
    save_to_style = "save_to_style"
    use_in_calendar = "use_in_calendar"


class Workspace(BaseModel):
    id: str
    name: str
    plan: str
    role: str
    monthly_limit: int


class Project(BaseModel):
    id: str
    workspace_id: str
    name: str
    niche: str
    platform: str
    goal: str
    audience: str
    tone: str


class ProjectMemory(BaseModel):
    project_id: str
    niche: str
    audience: str
    tone: str
    content_rules: list[str] = Field(default_factory=list)
    preferred_formats: list[str] = Field(default_factory=list)
    rejected_ideas: list[str] = Field(default_factory=list)
    best_performing_topics: list[str] = Field(default_factory=list)
    past_successful_scripts: list[str] = Field(default_factory=list)


class KnowledgeSource(BaseModel):
    id: str
    project_id: str
    title: str
    source_type: str
    text: str
    created_at: datetime


class Idea(BaseModel):
    id: str
    project_id: str
    title: str
    description: str
    format: str
    score: int
    status: IdeaStatus
    created_at: datetime


class Generation(BaseModel):
    id: str
    workspace_id: str
    project_id: str
    type: str
    prompt: str
    result: dict[str, Any]
    model: str
    token_estimate: int
    cost_estimate: float
    validation_status: str
    feedback_status: str | None = None
    created_at: datetime


class Script(BaseModel):
    id: str
    workspace_id: str
    project_id: str
    idea_id: str | None = None
    generation_id: str | None = None
    title: str
    body: str
    status: str
    growth_score: dict[str, Any] = Field(default_factory=dict)
    export_state: str | None = None
    created_at: datetime


class CalendarItem(BaseModel):
    id: str
    workspace_id: str
    project_id: str
    idea_id: str | None = None
    script_id: str | None = None
    title: str
    platform: str
    scheduled_for: datetime | None = None
    status: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class AgentRun(BaseModel):
    id: str
    workspace_id: str
    project_id: str
    agent_name: str
    intent: str
    input: dict[str, Any]
    memory_used: ProjectMemory
    model: str
    result: dict[str, Any]
    token_estimate: int = 0
    cost_estimate: float
    validation_status: str
    status: str
    created_at: datetime


class GrowthScore(BaseModel):
    hook: int
    title: int
    retention: int
    emotion: int
    virality: int
    clarity: int
    overall: int
    criteria: dict[str, str]
    improvements: list[str]


class ContentPackRequest(BaseModel):
    project_id: str = "project_youtube"
    topic: str
    add_to_calendar: bool = False
    publish_date: date | None = None


class ContentPack(BaseModel):
    id: str
    project_id: str
    topic: str
    idea: Idea
    youtube_script: str
    titles: list[str]
    shorts: list[str]
    telegram_post: str
    growth_score: GrowthScore
    calendar_item: dict[str, Any] | None = None
    created_at: datetime


class AgentGenerateRequest(BaseModel):
    project_id: str = "project_youtube"
    prompt: str
    intent: str = "generate"


class OrchestratorRequest(BaseModel):
    project_id: str = "project_youtube"
    message: str


class FeedbackRequest(BaseModel):
    action: FeedbackAction
    note: str | None = None


class StyleAnalyzeRequest(BaseModel):
    project_id: str = "project_youtube"
    text: str


class ScriptRequest(BaseModel):
    project_id: str = "project_youtube"
    title: str
    body: str
    status: str = "draft"
    idea_id: str | None = None
    generation_id: str | None = None
    growth_score: dict[str, Any] = Field(default_factory=dict)


class CalendarItemRequest(BaseModel):
    project_id: str = "project_youtube"
    title: str
    platform: str = "YouTube"
    scheduled_for: datetime | None = None
    status: str = "idea"
    idea_id: str | None = None
    script_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Notification(BaseModel):
    id: str
    workspace_id: str
    title: str
    body: str
    kind: str
    read: bool
    created_at: datetime


class ActivityEvent(BaseModel):
    id: str
    workspace_id: str
    actor: str
    verb: str
    object_type: str
    object_id: str
    created_at: datetime


class UsageSummary(BaseModel):
    workspace_id: str
    plan: str
    month: str
    generations_used: int
    generation_limit: int
    estimated_cost: float
    blocked: bool


class AdminOverview(BaseModel):
    users: int
    workspaces: int
    subscriptions: int
    generations: int
    agent_runs: int
    errors: int
    feedback: int
    estimated_cost: float
