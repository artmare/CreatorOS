# CreatorOS Production Deployment

## Architecture

- Frontend: Vercel, rooted at `frontend/`
- Backend API: Render Web Service running FastAPI
- Worker: Render Background Worker running Celery
- Database/Auth: Supabase Auth + Supabase Postgres
- Queue: Upstash Redis or Render Redis
- Billing: Lemon Squeezy
- AI: OpenAI API
- Integrations: Telegram bot webhook and YouTube Data API

## Frontend on Vercel

1. Create a Vercel project from this repository.
2. Set root directory to `frontend`.
3. Add env vars:
   - `NEXT_PUBLIC_API_BASE_URL`
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`
4. Deploy with the default Next.js build command.

## Backend on Render

Use the included root-level `render.yaml` blueprint for the API and worker, or create services manually. Render reads the service `buildCommand`, `startCommand`, `healthCheckPath`, and `envVars` from this file.

The repo includes `.python-version` with `3.13` so Render does not fall back to its current default Python 3.14 runtime. The backend normalizes Supabase `postgres://` and `postgresql://` URLs to SQLAlchemy's `postgresql+psycopg://` driver and installs `psycopg[binary]`.

Create a Web Service manually:

```bash
pip install --upgrade pip && pip install -r backend/requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port $PORT --app-dir backend
```

Required API env vars:

- `APP_ENV=production`
- `FRONTEND_ORIGIN=https://your-vercel-domain`
- `DATABASE_URL`
- `SUPABASE_URL`
- `SUPABASE_JWT_AUDIENCE=authenticated`
- `SUPABASE_JWT_SECRET`
- `SUPABASE_SERVICE_ROLE_KEY`
- `OPENAI_API_KEY`
- `OPENAI_MODEL=gpt-5-mini`
- `OPENAI_TIMEOUT_SECONDS=45`
- `OPENAI_MAX_RETRIES=2`
- `REDIS_URL`
- `ADMIN_EMAIL_ALLOWLIST`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_WEBHOOK_SECRET`
- `YOUTUBE_API_KEY`
- `YOUTUBE_OAUTH_CLIENT_ID`
- `YOUTUBE_OAUTH_CLIENT_SECRET`
- `LEMONSQUEEZY_API_KEY`
- `LEMONSQUEEZY_STORE_ID`
- `LEMONSQUEEZY_WEBHOOK_SECRET`
- `LEMONSQUEEZY_STARTER_VARIANT_ID`
- `LEMONSQUEEZY_PRO_VARIANT_ID`
- `LEMONSQUEEZY_AGENCY_VARIANT_ID`

## Celery Worker on Render

Create a Background Worker:

```bash
pip install --upgrade pip && pip install -r backend/requirements.txt
celery --workdir backend -A app.workers.celery_app.celery_app worker --loglevel=info
```

Use the same backend env vars that affect jobs and providers, especially `DATABASE_URL`, `REDIS_URL`, `SUPABASE_*`, `OPENAI_*`, `TELEGRAM_*`, `YOUTUBE_API_KEY`, and Lemon Squeezy webhook/API settings.

## Supabase Setup

1. Create a Supabase project.
2. Open the Supabase SQL editor or use `psql` against the Supabase Postgres connection string.
3. Run `supabase/migrations/0001_creatoros_platform.sql`.
4. Run `supabase/migrations/0002_creatoros_scale_policies.sql`.
5. Run `supabase/migrations/0003_scripts_calendar_layer.sql`.
6. Keep RLS enabled for all exposed tables.
7. Grant Data API access only to the roles and tables you intend to expose.
8. Use publishable keys in the frontend and secret/service-role keys only on the backend.

Migration verification query:

```sql
select table_name
from information_schema.tables
where table_schema = 'public'
  and table_name in (
    'workspaces',
    'projects',
    'project_memory',
    'content_packs',
    'generations',
    'scripts',
    'calendar_items',
    'generation_feedback',
    'audit_logs'
  )
order by table_name;
```

Expected result: all listed tables exist, and RLS is enabled for `scripts` and `calendar_items`.

Supabase docs used for the implementation recommend SSR clients with cookies and `@supabase/ssr`, and stress that Data API grants and RLS policies must be configured together.

## Telegram

Set the bot webhook to:

```text
https://your-api-domain/api/v1/telegram/webhook
```

Keep `TELEGRAM_BOT_TOKEN` and `TELEGRAM_WEBHOOK_SECRET` backend-only.

## YouTube Data API

Create a Google Cloud project, enable YouTube Data API v3, and set `YOUTUBE_API_KEY`. OAuth credentials can be added later for private channel analytics.

## Lemon Squeezy

1. Create Starter, Creator Pro, and Agency variants.
2. Add variant IDs to backend env.
3. Configure webhook URL:

```text
https://your-api-domain/api/v1/billing/webhook
```

4. Set `LEMONSQUEEZY_WEBHOOK_SECRET`.

## OpenAI

Set `OPENAI_API_KEY` on the backend only. Live AI calls remain disabled locally and in production until this variable exists.
