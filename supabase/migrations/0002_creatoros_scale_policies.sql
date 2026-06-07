create schema if not exists private;

create or replace function private.is_workspace_member(target_workspace_id uuid)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1
    from public.workspace_members wm
    where wm.workspace_id = target_workspace_id
      and wm.user_id = (select auth.uid())
  );
$$;

revoke all on function private.is_workspace_member(uuid) from public;
grant execute on function private.is_workspace_member(uuid) to authenticated;

alter table public.workspaces add column if not exists monthly_limit int not null default 100;
alter table public.background_jobs add column if not exists idempotency_key text unique;

create index if not exists idx_workspace_members_user on public.workspace_members(user_id);
create index if not exists idx_projects_workspace_created on public.projects(workspace_id, created_at desc);
create index if not exists idx_project_memory_project on public.project_memory(project_id);
create index if not exists idx_knowledge_sources_workspace_project on public.knowledge_sources(workspace_id, project_id, created_at desc);
create index if not exists idx_knowledge_chunks_source_index on public.knowledge_chunks(source_id, chunk_index);
create index if not exists idx_ideas_workspace_status_created on public.ideas(workspace_id, status, created_at desc);
create index if not exists idx_agent_runs_workspace_created on public.agent_runs(workspace_id, created_at desc);
create index if not exists idx_generations_workspace_created on public.generations(workspace_id, created_at desc);
create index if not exists idx_content_packs_workspace_created on public.content_packs(workspace_id, created_at desc);
create index if not exists idx_usage_ledger_workspace_created on public.usage_ledger(workspace_id, created_at desc);
create index if not exists idx_notifications_workspace_read_created on public.notifications(workspace_id, read, created_at desc);
create index if not exists idx_activity_events_workspace_created on public.activity_events(workspace_id, created_at desc);
create index if not exists idx_audit_logs_workspace_created on public.audit_logs(workspace_id, created_at desc);
create index if not exists idx_background_jobs_workspace_status_created on public.background_jobs(workspace_id, status, created_at desc);

drop policy if exists "workspace members can read workspaces" on public.workspaces;
create policy "workspace members can read workspaces"
on public.workspaces
for select
to authenticated
using (private.is_workspace_member(id));

drop policy if exists "workspace members can read membership" on public.workspace_members;
create policy "workspace members can read membership"
on public.workspace_members
for select
to authenticated
using (private.is_workspace_member(workspace_id));

drop policy if exists "workspace members can read projects" on public.projects;
create policy "workspace members can read projects"
on public.projects
for select
to authenticated
using (private.is_workspace_member(workspace_id));

drop policy if exists "workspace members can insert projects" on public.projects;
create policy "workspace members can insert projects"
on public.projects
for insert
to authenticated
with check (private.is_workspace_member(workspace_id));

drop policy if exists "workspace members can update projects" on public.projects;
create policy "workspace members can update projects"
on public.projects
for update
to authenticated
using (private.is_workspace_member(workspace_id))
with check (private.is_workspace_member(workspace_id));

drop policy if exists "workspace members can read project memory" on public.project_memory;
create policy "workspace members can read project memory"
on public.project_memory
for select
to authenticated
using (
  exists (
    select 1 from public.projects p
    where p.id = project_id
      and private.is_workspace_member(p.workspace_id)
  )
);

drop policy if exists "workspace members can mutate project memory" on public.project_memory;
create policy "workspace members can mutate project memory"
on public.project_memory
for all
to authenticated
using (
  exists (
    select 1 from public.projects p
    where p.id = project_id
      and private.is_workspace_member(p.workspace_id)
  )
)
with check (
  exists (
    select 1 from public.projects p
    where p.id = project_id
      and private.is_workspace_member(p.workspace_id)
  )
);

drop policy if exists "workspace members can use knowledge sources" on public.knowledge_sources;
create policy "workspace members can use knowledge sources"
on public.knowledge_sources
for all
to authenticated
using (private.is_workspace_member(workspace_id))
with check (private.is_workspace_member(workspace_id));

drop policy if exists "workspace members can use knowledge chunks" on public.knowledge_chunks;
create policy "workspace members can use knowledge chunks"
on public.knowledge_chunks
for all
to authenticated
using (
  exists (
    select 1 from public.knowledge_sources ks
    where ks.id = source_id
      and private.is_workspace_member(ks.workspace_id)
  )
)
with check (
  exists (
    select 1 from public.knowledge_sources ks
    where ks.id = source_id
      and private.is_workspace_member(ks.workspace_id)
  )
);

drop policy if exists "workspace members can use ideas" on public.ideas;
create policy "workspace members can use ideas"
on public.ideas
for all
to authenticated
using (private.is_workspace_member(workspace_id))
with check (private.is_workspace_member(workspace_id));

drop policy if exists "workspace members can use agent runs" on public.agent_runs;
create policy "workspace members can use agent runs"
on public.agent_runs
for all
to authenticated
using (private.is_workspace_member(workspace_id))
with check (private.is_workspace_member(workspace_id));

drop policy if exists "workspace members can use generations" on public.generations;
create policy "workspace members can use generations"
on public.generations
for all
to authenticated
using (private.is_workspace_member(workspace_id))
with check (private.is_workspace_member(workspace_id));

drop policy if exists "workspace members can use content packs" on public.content_packs;
create policy "workspace members can use content packs"
on public.content_packs
for all
to authenticated
using (private.is_workspace_member(workspace_id))
with check (private.is_workspace_member(workspace_id));

drop policy if exists "workspace members can use usage ledger" on public.usage_ledger;
create policy "workspace members can use usage ledger"
on public.usage_ledger
for select
to authenticated
using (private.is_workspace_member(workspace_id));

drop policy if exists "workspace members can use feedback" on public.generation_feedback;
create policy "workspace members can use feedback"
on public.generation_feedback
for all
to authenticated
using (
  exists (
    select 1 from public.generations g
    where g.id = generation_id
      and private.is_workspace_member(g.workspace_id)
  )
)
with check (
  exists (
    select 1 from public.generations g
    where g.id = generation_id
      and private.is_workspace_member(g.workspace_id)
  )
);

drop policy if exists "workspace members can read validations" on public.quality_validation_results;
create policy "workspace members can read validations"
on public.quality_validation_results
for select
to authenticated
using (
  exists (
    select 1 from public.generations g
    where g.id = generation_id
      and private.is_workspace_member(g.workspace_id)
  )
);

drop policy if exists "workspace members can use activity" on public.activity_events;
create policy "workspace members can use activity"
on public.activity_events
for select
to authenticated
using (private.is_workspace_member(workspace_id));

drop policy if exists "workspace members can use notifications" on public.notifications;
create policy "workspace members can use notifications"
on public.notifications
for all
to authenticated
using (private.is_workspace_member(workspace_id))
with check (private.is_workspace_member(workspace_id));

drop policy if exists "workspace members can read background jobs" on public.background_jobs;
create policy "workspace members can read background jobs"
on public.background_jobs
for select
to authenticated
using (private.is_workspace_member(workspace_id));

drop policy if exists "workspace admins can read errors" on public.error_logs;
create policy "workspace admins can read errors"
on public.error_logs
for select
to authenticated
using (workspace_id is null or private.is_workspace_member(workspace_id));

drop policy if exists "workspace members can read audit logs" on public.audit_logs;
create policy "workspace members can read audit logs"
on public.audit_logs
for select
to authenticated
using (workspace_id is null or private.is_workspace_member(workspace_id));
