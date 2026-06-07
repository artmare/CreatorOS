from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.core.auth import CurrentUser
from app.schemas.platform import ActivityEvent, Notification
from app.services.seed_store import store


def _now() -> datetime:
    return datetime.now(timezone.utc)


class EventRecorder:
    def activity(
        self,
        user: CurrentUser,
        verb: str,
        object_type: str,
        object_id: str,
        workspace_id: str | None = None,
    ) -> ActivityEvent:
        event = ActivityEvent(
            id=store.new_id("activity"),
            workspace_id=workspace_id or user.workspace_id,
            actor=user.email,
            verb=verb,
            object_type=object_type,
            object_id=object_id,
            created_at=_now(),
        )
        store.activity.insert(0, event)
        return event

    def notify(
        self,
        user: CurrentUser,
        title: str,
        body: str,
        kind: str,
        workspace_id: str | None = None,
    ) -> Notification:
        notification = Notification(
            id=store.new_id("notification"),
            workspace_id=workspace_id or user.workspace_id,
            title=title,
            body=body,
            kind=kind,
            read=False,
            created_at=_now(),
        )
        store.notifications.insert(0, notification)
        return notification

    def audit(
        self,
        user: CurrentUser,
        action: str,
        object_type: str,
        object_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        workspace_id: str | None = None,
    ) -> dict[str, Any]:
        record = {
            "id": store.new_id("audit"),
            "workspace_id": workspace_id or user.workspace_id,
            "actor_user_id": user.id,
            "actor_email": user.email,
            "action": action,
            "object_type": object_type,
            "object_id": object_id,
            "metadata": metadata or {},
            "created_at": _now(),
        }
        store.audit_logs.insert(0, record)
        return record

    def error(
        self,
        source: str,
        message: str,
        payload: dict[str, Any] | None = None,
        workspace_id: str | None = None,
    ) -> dict[str, Any]:
        record = {
            "id": store.new_id("error"),
            "workspace_id": workspace_id,
            "source": source,
            "message": message,
            "payload": payload or {},
            "created_at": _now(),
        }
        store.errors.insert(0, record)
        return record


events = EventRecorder()
