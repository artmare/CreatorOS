create table if not exists public.scripts (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid references public.workspaces(id) on delete cascade,
  project_id uuid references public.projects(id) on delete cascade,
  idea_id uuid references public.ideas(id) on delete set null,
  generation_id uuid references public.generations(id) on delete set null,
  title text not null,
  body text not null,
  status text not null default 'draft'
    check (status in ('draft','ready','approved','scheduled','published','archived')),
  growth_score jsonb not null default '{}',
  export_state text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.calendar_items (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid references public.workspaces(id) on delete cascade,
  project_id uuid references public.projects(id) on delete cascade,
  idea_id uuid references public.ideas(id) on delete set null,
  script_id uuid references public.scripts(id) on delete set null,
  title text not null,
  platform text not null,
  scheduled_for timestamptz,
  status text not null default 'idea'
    check (status in ('idea','script_ready','filming','editing','published','analyzed','archived')),
  metadata jsonb not null default '{}',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.scripts enable row level security;
alter table public.calendar_items enable row level security;

grant select, insert, update, delete on public.scripts to authenticated;
grant select, insert, update, delete on public.calendar_items to authenticated;

create index if not exists idx_scripts_workspace_status_created
  on public.scripts(workspace_id, status, created_at desc);

create index if not exists idx_scripts_project_created
  on public.scripts(project_id, created_at desc);

create index if not exists idx_calendar_items_workspace_status_scheduled
  on public.calendar_items(workspace_id, status, scheduled_for);

create index if not exists idx_calendar_items_project_scheduled
  on public.calendar_items(project_id, scheduled_for);

drop policy if exists "workspace members can use scripts" on public.scripts;
create policy "workspace members can use scripts"
on public.scripts
for all
to authenticated
using (private.is_workspace_member(workspace_id))
with check (private.is_workspace_member(workspace_id));

drop policy if exists "workspace members can use calendar items" on public.calendar_items;
create policy "workspace members can use calendar items"
on public.calendar_items
for all
to authenticated
using (private.is_workspace_member(workspace_id))
with check (private.is_workspace_member(workspace_id));
