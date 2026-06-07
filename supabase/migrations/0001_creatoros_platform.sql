create table if not exists public.workspaces (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  plan text not null default 'free',
  created_at timestamptz not null default now()
);

create table if not exists public.workspace_members (
  workspace_id uuid references public.workspaces(id) on delete cascade,
  user_id uuid not null,
  role text not null check (role in ('owner', 'admin', 'member')),
  created_at timestamptz not null default now(),
  primary key (workspace_id, user_id)
);

create table if not exists public.projects (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid references public.workspaces(id) on delete cascade,
  name text not null,
  niche text,
  platform text,
  goal text,
  audience text,
  tone text,
  created_at timestamptz not null default now()
);

create table if not exists public.project_memory (
  project_id uuid primary key references public.projects(id) on delete cascade,
  niche text,
  audience text,
  tone text,
  content_rules jsonb not null default '[]',
  preferred_formats jsonb not null default '[]',
  rejected_ideas jsonb not null default '[]',
  best_performing_topics jsonb not null default '[]',
  past_successful_scripts jsonb not null default '[]',
  updated_at timestamptz not null default now()
);

create table if not exists public.knowledge_sources (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid references public.workspaces(id) on delete cascade,
  project_id uuid references public.projects(id) on delete cascade,
  title text not null,
  source_type text not null,
  body text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.knowledge_chunks (
  id uuid primary key default gen_random_uuid(),
  source_id uuid references public.knowledge_sources(id) on delete cascade,
  chunk_index int not null,
  body text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.ideas (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid references public.workspaces(id) on delete cascade,
  project_id uuid references public.projects(id) on delete cascade,
  title text not null,
  description text,
  format text,
  score int not null default 0,
  status text not null default 'draft',
  created_at timestamptz not null default now()
);

create table if not exists public.agent_runs (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid references public.workspaces(id) on delete cascade,
  project_id uuid references public.projects(id) on delete cascade,
  agent_name text not null,
  intent text not null,
  input jsonb not null,
  memory_used jsonb not null,
  model text not null,
  result jsonb not null,
  token_estimate int not null default 0,
  cost_estimate numeric(12,6) not null default 0,
  validation_status text not null,
  status text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.generations (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid references public.workspaces(id) on delete cascade,
  project_id uuid references public.projects(id) on delete cascade,
  agent_run_id uuid references public.agent_runs(id) on delete set null,
  type text not null,
  prompt text not null,
  result jsonb not null,
  model text not null,
  token_estimate int not null default 0,
  cost_estimate numeric(12,6) not null default 0,
  validation_status text not null,
  feedback_status text,
  export_state text,
  created_at timestamptz not null default now()
);

create table if not exists public.content_packs (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid references public.workspaces(id) on delete cascade,
  project_id uuid references public.projects(id) on delete cascade,
  topic text not null,
  payload jsonb not null,
  created_at timestamptz not null default now()
);

create table if not exists public.generation_feedback (
  id uuid primary key default gen_random_uuid(),
  generation_id uuid references public.generations(id) on delete cascade,
  user_id uuid not null,
  action text not null,
  note text,
  created_at timestamptz not null default now()
);

create table if not exists public.usage_ledger (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid references public.workspaces(id) on delete cascade,
  user_id uuid,
  generation_type text not null,
  model text not null,
  token_estimate int not null,
  cost_estimate numeric(12,6) not null,
  blocked boolean not null default false,
  created_at timestamptz not null default now()
);

create table if not exists public.quality_validation_results (
  id uuid primary key default gen_random_uuid(),
  generation_id uuid references public.generations(id) on delete cascade,
  status text not null,
  warnings jsonb not null default '[]',
  created_at timestamptz not null default now()
);

create table if not exists public.activity_events (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid references public.workspaces(id) on delete cascade,
  actor text not null,
  verb text not null,
  object_type text not null,
  object_id uuid,
  created_at timestamptz not null default now()
);

create table if not exists public.notifications (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid references public.workspaces(id) on delete cascade,
  title text not null,
  body text not null,
  kind text not null,
  read boolean not null default false,
  created_at timestamptz not null default now()
);

create table if not exists public.background_jobs (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid references public.workspaces(id) on delete cascade,
  job_type text not null,
  status text not null,
  payload jsonb not null default '{}',
  error text,
  created_at timestamptz not null default now()
);

create table if not exists public.error_logs (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid references public.workspaces(id) on delete cascade,
  source text not null,
  message text not null,
  payload jsonb not null default '{}',
  created_at timestamptz not null default now()
);

create table if not exists public.audit_logs (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid references public.workspaces(id) on delete cascade,
  actor_user_id uuid,
  action text not null,
  object_type text not null,
  object_id uuid,
  metadata jsonb not null default '{}',
  created_at timestamptz not null default now()
);

alter table public.workspaces enable row level security;
alter table public.workspace_members enable row level security;
alter table public.projects enable row level security;
alter table public.project_memory enable row level security;
alter table public.knowledge_sources enable row level security;
alter table public.knowledge_chunks enable row level security;
alter table public.ideas enable row level security;
alter table public.agent_runs enable row level security;
alter table public.generations enable row level security;
alter table public.content_packs enable row level security;
alter table public.generation_feedback enable row level security;
alter table public.usage_ledger enable row level security;
alter table public.quality_validation_results enable row level security;
alter table public.activity_events enable row level security;
alter table public.notifications enable row level security;
alter table public.background_jobs enable row level security;
alter table public.error_logs enable row level security;
alter table public.audit_logs enable row level security;
