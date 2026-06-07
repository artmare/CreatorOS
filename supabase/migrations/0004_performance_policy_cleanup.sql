create index if not exists idx_agent_runs_project
  on public.agent_runs(project_id);

create index if not exists idx_calendar_items_idea
  on public.calendar_items(idea_id);

create index if not exists idx_calendar_items_script
  on public.calendar_items(script_id);

create index if not exists idx_content_packs_project
  on public.content_packs(project_id);

create index if not exists idx_error_logs_workspace
  on public.error_logs(workspace_id);

create index if not exists idx_generation_feedback_generation
  on public.generation_feedback(generation_id);

create index if not exists idx_generations_agent_run
  on public.generations(agent_run_id);

create index if not exists idx_generations_project
  on public.generations(project_id);

create index if not exists idx_ideas_project
  on public.ideas(project_id);

create index if not exists idx_knowledge_sources_project
  on public.knowledge_sources(project_id);

create index if not exists idx_quality_validation_results_generation
  on public.quality_validation_results(generation_id);

create index if not exists idx_scripts_generation
  on public.scripts(generation_id);

create index if not exists idx_scripts_idea
  on public.scripts(idea_id);

drop policy if exists "workspace members can mutate project memory" on public.project_memory;

create policy "workspace members can insert project memory"
on public.project_memory
for insert
to authenticated
with check (
  exists (
    select 1 from public.projects p
    where p.id = project_id
      and private.is_workspace_member(p.workspace_id)
  )
);

create policy "workspace members can update project memory"
on public.project_memory
for update
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

create policy "workspace members can delete project memory"
on public.project_memory
for delete
to authenticated
using (
  exists (
    select 1 from public.projects p
    where p.id = project_id
      and private.is_workspace_member(p.workspace_id)
  )
);
