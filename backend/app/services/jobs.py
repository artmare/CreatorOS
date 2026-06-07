from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from app.core.auth import CurrentUser
from app.services.events import events
from app.services.seed_store import store


class BackgroundJobService:
    def enqueue(
        self,
        user: CurrentUser,
        job_type: str,
        payload: dict[str, Any],
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        key = idempotency_key or self._key(user.workspace_id, job_type, payload)
        for job in store.background_jobs:
            if job.get("idempotency_key") == key:
                return job

        job = {
            "id": store.new_id("job"),
            "workspace_id": user.workspace_id,
            "job_type": job_type,
            "status": "queued",
            "idempotency_key": key,
            "payload": payload,
            "error": None,
            "created_at": datetime.now(timezone.utc),
        }
        store.background_jobs.insert(0, job)
        events.activity(user, "queued background job", "background_job", job["id"])
        events.audit(user, "background_job.queued", "background_job", job["id"], {"job_type": job_type})
        return job

    def mark_completed(self, user: CurrentUser, job_id: str) -> dict[str, Any]:
        job = self._get(job_id)
        job["status"] = "completed"
        events.notify(user, "Background job completed", f"{job['job_type']} finished.", "job_completed")
        return job

    def mark_failed(self, user: CurrentUser, job_id: str, error: str) -> dict[str, Any]:
        job = self._get(job_id)
        job["status"] = "failed"
        job["error"] = error
        events.error("background_job", error, job, user.workspace_id)
        events.notify(user, "Background job failed", error, "job_failed")
        return job

    def _get(self, job_id: str) -> dict[str, Any]:
        for job in store.background_jobs:
            if job["id"] == job_id:
                return job
        raise KeyError(f"Unknown job: {job_id}")

    def _key(self, workspace_id: str, job_type: str, payload: dict[str, Any]) -> str:
        digest = hashlib.sha256(f"{workspace_id}:{job_type}:{payload!r}".encode("utf-8")).hexdigest()
        return digest[:48]


jobs = BackgroundJobService()
