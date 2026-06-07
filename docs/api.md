# CreatorOS API Map

## Core

- `GET /health`
- `GET /api/v1/auth/me`
- `GET /api/v1/workspaces`
- `POST /api/v1/workspaces`
- `GET /api/v1/projects`
- `POST /api/v1/projects`
- `GET /api/v1/project-memory`
- `PATCH /api/v1/project-memory`
- `GET|POST /api/v1/knowledge-base`
- `GET|POST /api/v1/idea-vault`
- `PATCH /api/v1/idea-vault/{idea_id}/status`
- `POST /api/v1/content-factory/generate-pack`
- `GET /api/v1/content-factory/packs`
- `POST /api/v1/orchestrator/produce`
- `POST /api/v1/agents/{agent_name}/generate`
- `GET /api/v1/agent-runs`
- `POST /api/v1/generations/{generation_id}/feedback`
- `GET|POST /api/v1/scripts`
- `PATCH /api/v1/scripts/{script_id}`
- `GET|POST /api/v1/calendar`
- `PATCH /api/v1/calendar/{item_id}`
- `GET /api/v1/activity`
- `GET /api/v1/notifications`
- `PATCH /api/v1/notifications/{notification_id}/read`
- `GET /api/v1/usage/summary`
- `POST /api/v1/growth-score`
- `POST /api/v1/style/analyze`
- `POST /api/v1/exports/markdown`
- `GET|POST /api/v1/background-jobs`

## Integrations

- `POST /api/v1/telegram/webhook`
- `POST /api/v1/youtube/competitors`
- `POST /api/v1/youtube/channel-summary`
- `POST /api/v1/billing/checkout`
- `POST /api/v1/billing/webhook`

## Admin

- `GET /api/v1/admin/users`
- `GET /api/v1/admin/workspaces`
- `GET /api/v1/admin/subscriptions`
- `GET /api/v1/admin/generations`
- `GET /api/v1/admin/agent-runs`
- `GET /api/v1/admin/errors`
- `GET /api/v1/admin/feedback`
- `GET /api/v1/admin/usage`
- `GET /api/v1/admin/audit-logs`
- `GET /api/v1/admin/background-jobs`

## Persistence

Workspace, project, project memory, knowledge base, idea vault, content packs, generations, scripts, calendar items, feedback, agent runs, usage ledger, activity, notification, audit, and background job routes use the SQLAlchemy repository. Local development auto-creates SQLite tables; production uses the Supabase Postgres `DATABASE_URL` with committed migrations.
