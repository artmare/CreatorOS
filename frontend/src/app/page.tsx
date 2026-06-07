"use client";

import {
  Activity,
  BarChart3,
  Bell,
  Bot,
  CalendarDays,
  Clipboard,
  Database,
  FileText,
  Gauge,
  LayoutDashboard,
  Loader2,
  MessageSquare,
  Play,
  RefreshCcw,
  Save,
  Search,
  Settings,
  ShieldCheck,
  Sparkles,
  Wallet,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { API_BASE_URL, apiGet, apiPatch, apiPost } from "@/lib/api";

type View =
  | "dashboard"
  | "factory"
  | "scripts"
  | "calendar"
  | "memory"
  | "producer"
  | "ideas"
  | "radar"
  | "score"
  | "repurpose"
  | "analytics"
  | "settings"
  | "admin";

type AdminTab = "generations" | "feedback" | "audit";

type Workspace = {
  id: string;
  name: string;
  plan: string;
  role: string;
  monthly_limit: number;
};

type Project = {
  id: string;
  workspace_id: string;
  name: string;
  niche: string;
  platform: string;
  goal: string;
  audience: string;
  tone: string;
};

type ProjectMemory = {
  project_id: string;
  niche: string;
  audience: string;
  tone: string;
  content_rules: string[];
  preferred_formats: string[];
  rejected_ideas: string[];
  best_performing_topics: string[];
  past_successful_scripts: string[];
};

type UsageSummary = {
  workspace_id: string;
  plan: string;
  month: string;
  generations_used: number;
  generation_limit: number;
  estimated_cost: number;
  blocked: boolean;
};

type ContentPack = {
  id: string;
  project_id: string;
  topic: string;
  generation_id?: string;
  script_id?: string;
  titles?: string[];
  shorts?: string[];
  telegram_post?: string;
  youtube_script?: string;
  growth_score?: { overall?: number };
  calendar_item?: { id?: string; status?: string; title?: string };
  created_at?: string;
};

type Script = {
  id: string;
  workspace_id: string;
  project_id: string;
  idea_id?: string | null;
  generation_id?: string | null;
  title: string;
  body: string;
  status: string;
  growth_score?: Record<string, unknown>;
  export_state?: string | null;
  created_at: string;
};

type CalendarItem = {
  id: string;
  workspace_id: string;
  project_id: string;
  idea_id?: string | null;
  script_id?: string | null;
  title: string;
  platform: string;
  scheduled_for?: string | null;
  status: string;
  metadata?: Record<string, unknown>;
  created_at: string;
};

type Generation = {
  id: string;
  workspace_id: string;
  project_id: string;
  type: string;
  prompt: string;
  result: Record<string, unknown>;
  model: string;
  token_estimate: number;
  cost_estimate: number;
  validation_status: string;
  feedback_status?: string | null;
  created_at: string;
};

type FeedbackRecord = {
  id?: string;
  generation_id: string;
  user_id: string;
  action: string;
  note?: string | null;
  created_at?: string;
};

type AuditLog = {
  id: string;
  workspace_id?: string | null;
  actor_user_id?: string | null;
  action: string;
  object_type: string;
  object_id?: string | null;
  metadata?: Record<string, unknown>;
  created_at: string;
};

type ActivityEvent = {
  id: string;
  actor: string;
  verb: string;
  object_type: string;
  object_id: string;
  created_at: string;
};

type NotificationItem = {
  id: string;
  title: string;
  body: string;
  kind: string;
  read: boolean;
  created_at: string;
};

type CurrentUser = {
  id: string;
  email: string;
  role: string;
  workspace_id: string;
};

const navItems: Array<[string, LucideIcon, View]> = [
  ["Dashboard", LayoutDashboard, "dashboard"],
  ["Content Packs", Sparkles, "factory"],
  ["Scripts", FileText, "scripts"],
  ["Calendar", CalendarDays, "calendar"],
  ["Project Memory", MessageSquare, "memory"],
  ["AI Producer", Bot, "producer"],
  ["Ideas", Sparkles, "ideas"],
  ["Competitor Radar", Search, "radar"],
  ["Growth Score", Gauge, "score"],
  ["Repurpose", RefreshCcw, "repurpose"],
  ["Analytics", BarChart3, "analytics"],
  ["Settings", Settings, "settings"],
  ["Admin", ShieldCheck, "admin"],
];

const feedbackActions = ["good", "bad", "regenerate", "save_to_style", "use_in_calendar"] as const;
const scriptStatuses = ["draft", "ready", "approved", "scheduled", "published", "archived"];
const calendarStatuses = ["idea", "script_ready", "filming", "editing", "published", "analyzed", "archived"];

const emptyMemory: ProjectMemory = {
  project_id: "",
  niche: "",
  audience: "",
  tone: "",
  content_rules: [],
  preferred_formats: [],
  rejected_ideas: [],
  best_performing_topics: [],
  past_successful_scripts: [],
};

function listToText(value: string[] | undefined) {
  return (value ?? []).join("\n");
}

function textToList(value: string) {
  return value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
}

function formatDate(value?: string | null) {
  if (!value) {
    return "not scheduled";
  }
  return new Intl.DateTimeFormat("en", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

function shortId(value?: string | null) {
  if (!value) {
    return "none";
  }
  return value.slice(0, 8);
}

function StatusPill({
  children,
  kind = "neutral",
}: {
  children: React.ReactNode;
  kind?: "neutral" | "good" | "warn" | "bad";
}) {
  const color =
    kind === "good"
      ? "border-[#1f8b70] bg-[#10251f] text-[#39e4b1]"
      : kind === "warn"
        ? "border-[#766322] bg-[#28230f] text-[#ffd166]"
        : kind === "bad"
          ? "border-[#7a3232] bg-[#2a1212] text-[#ff8f8f]"
          : "border-[#2b3142] bg-[#151925] text-[#aeb7c9]";
  return <span className={`rounded-md border px-2 py-1 text-xs font-medium ${color}`}>{children}</span>;
}

function Panel({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <section className={`rounded-lg border border-[#252b38] bg-[#10131a] p-4 ${className}`}>{children}</section>;
}

function Field({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}) {
  return (
    <label className="block">
      <span className="text-xs font-medium uppercase text-[#8e96a8]">{label}</span>
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        className="mt-2 h-10 w-full rounded-md border border-[#2b3142] bg-[#0d1017] px-3 text-sm text-[#f5f7fb] outline-none focus:border-[#7c8cff]"
      />
    </label>
  );
}

function TextAreaField({
  label,
  value,
  onChange,
  minHeight = "min-h-28",
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  minHeight?: string;
}) {
  return (
    <label className="block">
      <span className="text-xs font-medium uppercase text-[#8e96a8]">{label}</span>
      <textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className={`mt-2 w-full rounded-md border border-[#2b3142] bg-[#0d1017] p-3 text-sm text-[#f5f7fb] outline-none focus:border-[#7c8cff] ${minHeight}`}
      />
    </label>
  );
}

function SelectField({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (value: string) => void;
}) {
  return (
    <label className="block">
      <span className="text-xs font-medium uppercase text-[#8e96a8]">{label}</span>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="mt-2 h-10 w-full rounded-md border border-[#2b3142] bg-[#0d1017] px-3 text-sm text-[#f5f7fb] outline-none focus:border-[#7c8cff]"
      >
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}

function MetricCard({ label, value, detail }: { label: string; value: string; detail: string }) {
  return (
    <Panel>
      <div className="text-xs font-medium uppercase text-[#8e96a8]">{label}</div>
      <div className="mt-3 text-3xl font-semibold text-[#f5f7fb]">{value}</div>
      <div className="mt-2 text-sm text-[#9aa3b2]">{detail}</div>
    </Panel>
  );
}

function FeedbackButtons({
  generationId,
  onFeedback,
}: {
  generationId?: string | null;
  onFeedback: (generationId: string, action: string) => Promise<void>;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {feedbackActions.map((action) => (
        <button
          key={action}
          disabled={!generationId}
          onClick={() => generationId && onFeedback(generationId, action)}
          className="rounded-md border border-[#2b3142] px-3 py-2 text-xs text-[#c8d0df] transition hover:border-[#7c8cff] disabled:cursor-not-allowed disabled:opacity-40"
        >
          {action.replaceAll("_", " ")}
        </button>
      ))}
    </div>
  );
}

export default function Home() {
  const [view, setView] = useState<View>("dashboard");
  const [adminTab, setAdminTab] = useState<AdminTab>("generations");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const [user, setUser] = useState<CurrentUser | null>(null);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [memory, setMemory] = useState<ProjectMemory>(emptyMemory);
  const [usage, setUsage] = useState<UsageSummary | null>(null);
  const [contentPacks, setContentPacks] = useState<ContentPack[]>([]);
  const [scripts, setScripts] = useState<Script[]>([]);
  const [calendarItems, setCalendarItems] = useState<CalendarItem[]>([]);
  const [activity, setActivity] = useState<ActivityEvent[]>([]);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [adminGenerations, setAdminGenerations] = useState<Generation[]>([]);
  const [adminFeedback, setAdminFeedback] = useState<FeedbackRecord[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);

  const [packTopic, setPackTopic] = useState("repeatable content systems");
  const [packCalendar, setPackCalendar] = useState(true);
  const [packDate, setPackDate] = useState("2026-06-15");
  const [scriptTitle, setScriptTitle] = useState("Launch review script");
  const [scriptBody, setScriptBody] = useState("Hook: show the cost of a vague launch.\n\nBody: one conflict, one proof point, one action.\n\nCTA: commit to one publishing rule.");
  const [scriptStatus, setScriptStatus] = useState("ready");
  const [editingScriptId, setEditingScriptId] = useState<string | null>(null);
  const [calendarTitle, setCalendarTitle] = useState("Publish launch review");
  const [calendarPlatform, setCalendarPlatform] = useState("YouTube");
  const [calendarStatus, setCalendarStatus] = useState("script_ready");
  const [calendarDate, setCalendarDate] = useState("2026-06-15T09:00");

  const activeProject = useMemo(
    () => projects.find((project) => project.id === selectedProjectId) ?? projects[0],
    [projects, selectedProjectId],
  );

  const pageTitle = useMemo(
    () =>
      ({
        dashboard: "Dashboard",
        factory: "Content Packs",
        scripts: "Scripts",
        calendar: "Calendar",
        memory: "Project Memory",
        producer: "AI Producer",
        ideas: "Ideas",
        radar: "Competitor Radar",
        score: "Growth Score",
        repurpose: "Repurpose",
        analytics: "Analytics",
        settings: "Settings",
        admin: "Admin",
      })[view],
    [view],
  );

  const loadPlatform = useCallback(
    async (projectOverride?: string) => {
      setError(null);
      try {
        const [nextUser, nextWorkspaces] = await Promise.all([
          apiGet<CurrentUser>("/api/v1/auth/me"),
          apiGet<Workspace[]>("/api/v1/workspaces"),
        ]);
        const [nextProjects, nextUsage, nextPacks, nextScripts, nextCalendar, nextActivity, nextNotifications] = await Promise.all([
          apiGet<Project[]>("/api/v1/projects"),
          apiGet<UsageSummary>("/api/v1/usage/summary"),
          apiGet<ContentPack[]>("/api/v1/content-factory/packs"),
          apiGet<Script[]>("/api/v1/scripts"),
          apiGet<CalendarItem[]>("/api/v1/calendar"),
          apiGet<ActivityEvent[]>("/api/v1/activity"),
          apiGet<NotificationItem[]>("/api/v1/notifications"),
        ]);

        const projectId = projectOverride || nextProjects[0]?.id || "project_youtube";
        const [nextMemory, nextGenerations, nextFeedback, nextAuditLogs] = await Promise.all([
          apiGet<ProjectMemory>(`/api/v1/project-memory?project_id=${encodeURIComponent(projectId)}`),
          apiGet<Generation[]>("/api/v1/admin/generations"),
          apiGet<FeedbackRecord[]>("/api/v1/admin/feedback"),
          apiGet<AuditLog[]>("/api/v1/admin/audit-logs"),
        ]);

        setUser(nextUser);
        setWorkspaces(nextWorkspaces);
        setProjects(nextProjects);
        setSelectedProjectId(projectId);
        setUsage(nextUsage);
        setContentPacks(nextPacks);
        setScripts(nextScripts);
        setCalendarItems(nextCalendar);
        setActivity(nextActivity);
        setNotifications(nextNotifications);
        setMemory(nextMemory);
        setAdminGenerations(nextGenerations);
        setAdminFeedback(nextFeedback);
        setAuditLogs(nextAuditLogs);
      } catch (requestError) {
        setError(requestError instanceof Error ? requestError.message : "Backend request failed");
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadPlatform();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [loadPlatform]);

  async function runAction(label: string, action: () => Promise<void>) {
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      await action();
      setNotice(label);
      await loadPlatform(selectedProjectId);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Action failed");
    } finally {
      setBusy(false);
    }
  }

  async function generateContentPack() {
    if (!activeProject) {
      setError("Create a project before generating a content pack.");
      return;
    }
    await runAction("Content pack generated and saved.", async () => {
      await apiPost<ContentPack>("/api/v1/content-factory/generate-pack", {
        project_id: activeProject.id,
        topic: packTopic,
        add_to_calendar: packCalendar,
        publish_date: packCalendar ? packDate : null,
      });
    });
  }

  async function createScript() {
    if (!activeProject) {
      setError("Create a project before creating scripts.");
      return;
    }
    await runAction("Script created.", async () => {
      await apiPost<Script>("/api/v1/scripts", {
        project_id: activeProject.id,
        title: scriptTitle,
        body: scriptBody,
        status: scriptStatus,
      });
    });
  }

  async function saveScript(script: Script) {
    await runAction("Script updated.", async () => {
      await apiPatch<Script>(`/api/v1/scripts/${script.id}`, {
        title: script.title,
        body: script.body,
        status: script.status,
      });
      setEditingScriptId(null);
    });
  }

  async function createCalendarItem() {
    if (!activeProject) {
      setError("Create a project before creating calendar items.");
      return;
    }
    await runAction("Calendar item created.", async () => {
      await apiPost<CalendarItem>("/api/v1/calendar", {
        project_id: activeProject.id,
        title: calendarTitle,
        platform: calendarPlatform,
        status: calendarStatus,
        scheduled_for: calendarDate ? new Date(calendarDate).toISOString() : null,
      });
    });
  }

  async function updateCalendarStatus(item: CalendarItem, status: string) {
    await runAction("Calendar status updated.", async () => {
      await apiPatch<CalendarItem>(`/api/v1/calendar/${item.id}`, { status });
    });
  }

  async function saveMemory() {
    await runAction("Project memory saved.", async () => {
      await apiPatch<ProjectMemory>("/api/v1/project-memory", memory);
    });
  }

  async function submitFeedback(generationId: string, action: string) {
    await runAction("Feedback saved.", async () => {
      await apiPost<FeedbackRecord>(`/api/v1/generations/${generationId}/feedback`, {
        action,
        note: `Frontend feedback: ${action}`,
      });
    });
  }

  async function markNotificationRead(notificationId: string) {
    await runAction("Notification marked read.", async () => {
      await apiPatch<NotificationItem>(`/api/v1/notifications/${notificationId}/read`, {});
    });
  }

  function updateMemoryList(key: keyof ProjectMemory, value: string) {
    setMemory((current) => ({ ...current, [key]: textToList(value) }));
  }

  function updateMemoryField(key: keyof ProjectMemory, value: string) {
    setMemory((current) => ({ ...current, [key]: value }));
  }

  function updateScriptDraft(scriptId: string, patch: Partial<Script>) {
    setScripts((current) => current.map((script) => (script.id === scriptId ? { ...script, ...patch } : script)));
  }

  return (
    <main className="min-h-screen bg-[#08090d] text-[#f5f7fb]">
      <div className="grid min-h-screen grid-cols-1 lg:grid-cols-[248px_minmax(0,1fr)_360px]">
        <aside className="border-b border-[#252b38] bg-[#0d1017] p-4 lg:border-b-0 lg:border-r">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#7c8cff] text-sm font-bold text-white">CO</div>
            <div>
              <div className="text-sm font-semibold">CreatorOS</div>
              <div className="text-xs text-[#8e96a8]">Persistent SaaS Console</div>
            </div>
          </div>

          <nav className="mt-8 grid grid-cols-2 gap-1 lg:grid-cols-1">
            {navItems.map(([label, Icon, targetView]) => (
              <button
                key={label}
                className={`flex h-9 min-w-0 items-center gap-2 rounded-md px-2 text-left text-sm transition lg:gap-3 lg:px-3 ${
                  targetView === view ? "bg-[#151925] text-white" : "text-[#9aa3b2] hover:bg-[#111722] hover:text-white"
                }`}
                onClick={() => setView(targetView)}
              >
                <Icon className="h-4 w-4" />
                <span className="truncate">{label}</span>
              </button>
            ))}
          </nav>

          <Panel className="mt-8">
            <div className="flex items-center justify-between text-xs text-[#9aa3b2]">
              <span>{usage?.plan ?? "loading"}</span>
              <span>
                {usage?.generations_used ?? 0} / {usage?.generation_limit ?? 0}
              </span>
            </div>
            <div className="mt-2 h-2 rounded-full bg-[#1b2130]">
              <div
                className="h-2 rounded-full bg-[#20d6a5]"
                style={{
                  width: `${Math.min(100, ((usage?.generations_used ?? 0) / Math.max(1, usage?.generation_limit ?? 1)) * 100)}%`,
                }}
              />
            </div>
            <div className="mt-3 text-xs text-[#8e96a8]">API: {API_BASE_URL}</div>
          </Panel>
        </aside>

        <section className="min-w-0 p-4 md:p-6">
          <header className="flex flex-col gap-4 border-b border-[#252b38] pb-5 md:flex-row md:items-center md:justify-between">
            <div>
              <div className="text-sm text-[#8e96a8]">
                Workspace: {workspaces[0]?.name ?? "loading"} / User: {user?.email ?? "loading"}
              </div>
              <h1 className="mt-1 text-2xl font-semibold">{pageTitle}</h1>
            </div>
            <div className="flex flex-wrap gap-2">
              <select
                value={selectedProjectId}
                onChange={(event) => {
                  setSelectedProjectId(event.target.value);
                  void loadPlatform(event.target.value);
                }}
                className="h-10 rounded-md border border-[#2b3142] bg-[#0d1017] px-3 text-sm text-[#dbe2f0]"
              >
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                  </option>
                ))}
              </select>
              <button
                onClick={() => void loadPlatform(selectedProjectId)}
                className="inline-flex h-10 items-center gap-2 rounded-md border border-[#2b3142] px-4 text-sm text-[#dbe2f0]"
              >
                <RefreshCcw className="h-4 w-4" />
                Refresh
              </button>
            </div>
          </header>

          {(loading || busy || error || notice) && (
            <div className="mt-4 flex flex-wrap items-center gap-3">
              {loading && (
                <StatusPill>
                  <span className="inline-flex items-center gap-2">
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    loading
                  </span>
                </StatusPill>
              )}
              {busy && <StatusPill kind="warn">saving</StatusPill>}
              {notice && <StatusPill kind="good">{notice}</StatusPill>}
              {error && <StatusPill kind="bad">{error}</StatusPill>}
            </div>
          )}

          {view === "dashboard" && (
            <div className="mt-6 space-y-6">
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                <MetricCard label="Content packs" value={String(contentPacks.length)} detail="Persisted packs from backend" />
                <MetricCard label="Scripts" value={String(scripts.length)} detail="Create and edit ready" />
                <MetricCard label="Calendar items" value={String(calendarItems.length)} detail="Scheduled workflow visible" />
                <MetricCard label="Estimated cost" value={`$${(usage?.estimated_cost ?? 0).toFixed(4)}`} detail={`${usage?.month ?? ""} usage ledger`} />
              </div>

              <div className="grid gap-4 xl:grid-cols-[1fr_0.9fr]">
                <Panel>
                  <div className="mb-4 flex items-center justify-between">
                    <h2 className="text-lg font-semibold">Recent content packs</h2>
                    <button onClick={() => setView("factory")} className="text-sm text-[#7c8cff]">
                      Open packs
                    </button>
                  </div>
                  <div className="grid gap-3">
                    {contentPacks.slice(0, 3).map((pack) => (
                      <div key={pack.id} className="rounded-md border border-[#252b38] bg-[#0d1017] p-3">
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <div className="font-semibold">{pack.topic}</div>
                            <div className="mt-1 text-xs text-[#8e96a8]">
                              script {shortId(pack.script_id)} / generation {shortId(pack.generation_id)}
                            </div>
                          </div>
                          <StatusPill kind={pack.calendar_item ? "good" : "neutral"}>{pack.calendar_item ? "calendar" : "pack"}</StatusPill>
                        </div>
                        <div className="mt-3">
                          <FeedbackButtons generationId={pack.generation_id} onFeedback={submitFeedback} />
                        </div>
                      </div>
                    ))}
                    {contentPacks.length === 0 && <div className="text-sm text-[#9aa3b2]">No content packs yet.</div>}
                  </div>
                </Panel>

                <Panel>
                  <h2 className="text-lg font-semibold">Upcoming calendar</h2>
                  <div className="mt-4 grid gap-3">
                    {calendarItems.slice(0, 4).map((item) => (
                      <div key={item.id} className="rounded-md border border-[#252b38] bg-[#0d1017] p-3">
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <div className="font-medium">{item.title}</div>
                            <div className="mt-1 text-xs text-[#8e96a8]">{formatDate(item.scheduled_for)}</div>
                          </div>
                          <StatusPill>{item.status}</StatusPill>
                        </div>
                      </div>
                    ))}
                    {calendarItems.length === 0 && <div className="text-sm text-[#9aa3b2]">No calendar items yet.</div>}
                  </div>
                </Panel>
              </div>
            </div>
          )}

          {view === "factory" && (
            <div className="mt-6 grid gap-4 xl:grid-cols-[0.75fr_1.25fr]">
              <Panel>
                <h2 className="text-lg font-semibold">Generate content pack</h2>
                <p className="mt-2 text-sm leading-6 text-[#9aa3b2]">Uses the persistent backend flow: pack, generation, script, feedback state, usage, activity, notification, and optional calendar item.</p>
                <div className="mt-5 grid gap-4">
                  <TextAreaField label="Topic" value={packTopic} onChange={setPackTopic} />
                  <label className="flex items-center gap-2 text-sm text-[#c8d0df]">
                    <input type="checkbox" checked={packCalendar} onChange={(event) => setPackCalendar(event.target.checked)} />
                    Add calendar item
                  </label>
                  <Field label="Publish date" value={packDate} onChange={setPackDate} />
                  <button onClick={generateContentPack} className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-[#7c8cff] px-4 text-sm font-semibold text-white">
                    <Play className="h-4 w-4" />
                    Generate and save
                  </button>
                </div>
              </Panel>

              <Panel>
                <h2 className="text-lg font-semibold">Content packs list</h2>
                <div className="mt-4 grid gap-3">
                  {contentPacks.map((pack) => (
                    <div key={pack.id} className="rounded-md border border-[#252b38] bg-[#0d1017] p-4">
                      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                        <div>
                          <div className="font-semibold">{pack.topic}</div>
                          <div className="mt-1 text-xs text-[#8e96a8]">
                            pack {shortId(pack.id)} / generation {shortId(pack.generation_id)} / script {shortId(pack.script_id)}
                          </div>
                        </div>
                        <StatusPill kind={pack.growth_score?.overall ? "good" : "neutral"}>score {pack.growth_score?.overall ?? "n/a"}</StatusPill>
                      </div>
                      <div className="mt-3 grid gap-2 sm:grid-cols-2">
                        {(pack.titles ?? []).slice(0, 2).map((title) => (
                          <div key={title} className="rounded border border-[#252b38] px-3 py-2 text-sm text-[#dbe2f0]">
                            {title}
                          </div>
                        ))}
                      </div>
                      <div className="mt-4">
                        <FeedbackButtons generationId={pack.generation_id} onFeedback={submitFeedback} />
                      </div>
                    </div>
                  ))}
                  {contentPacks.length === 0 && <div className="text-sm text-[#9aa3b2]">Generate the first pack from one topic.</div>}
                </div>
              </Panel>
            </div>
          )}

          {view === "scripts" && (
            <div className="mt-6 grid gap-4 xl:grid-cols-[0.8fr_1.2fr]">
              <Panel>
                <h2 className="text-lg font-semibold">Create script</h2>
                <div className="mt-4 grid gap-4">
                  <Field label="Title" value={scriptTitle} onChange={setScriptTitle} />
                  <TextAreaField label="Body" value={scriptBody} onChange={setScriptBody} minHeight="min-h-44" />
                  <SelectField label="Status" value={scriptStatus} options={scriptStatuses} onChange={setScriptStatus} />
                  <button onClick={createScript} className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-[#7c8cff] px-4 text-sm font-semibold text-white">
                    <FileText className="h-4 w-4" />
                    Create script
                  </button>
                </div>
              </Panel>

              <Panel>
                <h2 className="text-lg font-semibold">Scripts list and edit</h2>
                <div className="mt-4 grid gap-3">
                  {scripts.map((script) => {
                    const editing = editingScriptId === script.id;
                    return (
                      <div key={script.id} data-script-id={script.id} className="rounded-md border border-[#252b38] bg-[#0d1017] p-4">
                        <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                          <div className="min-w-0 flex-1">
                            {editing ? (
                              <div className="grid gap-3">
                                <Field label="Title" value={script.title} onChange={(value) => updateScriptDraft(script.id, { title: value })} />
                                <TextAreaField label="Body" value={script.body} onChange={(value) => updateScriptDraft(script.id, { body: value })} minHeight="min-h-36" />
                                <SelectField label="Status" value={script.status} options={scriptStatuses} onChange={(value) => updateScriptDraft(script.id, { status: value })} />
                              </div>
                            ) : (
                              <>
                                <div className="font-semibold">{script.title}</div>
                                <p className="mt-2 line-clamp-3 text-sm leading-6 text-[#9aa3b2]">{script.body}</p>
                              </>
                            )}
                          </div>
                          <StatusPill kind={script.status === "ready" || script.status === "approved" ? "good" : "neutral"}>{script.status}</StatusPill>
                        </div>
                        <div className="mt-4 flex flex-wrap gap-2">
                          <button
                            onClick={() => (editing ? void saveScript(script) : setEditingScriptId(script.id))}
                            className="inline-flex items-center gap-2 rounded-md border border-[#2b3142] px-3 py-2 text-xs text-[#c8d0df]"
                          >
                            {editing ? <Save className="h-3.5 w-3.5" /> : <Clipboard className="h-3.5 w-3.5" />}
                            {editing ? "Save edit" : "Edit"}
                          </button>
                          {script.generation_id && <FeedbackButtons generationId={script.generation_id} onFeedback={submitFeedback} />}
                        </div>
                      </div>
                    );
                  })}
                  {scripts.length === 0 && <div className="text-sm text-[#9aa3b2]">No scripts yet.</div>}
                </div>
              </Panel>
            </div>
          )}

          {view === "calendar" && (
            <div className="mt-6 grid gap-4 xl:grid-cols-[0.75fr_1.25fr]">
              <Panel>
                <h2 className="text-lg font-semibold">Create calendar item</h2>
                <div className="mt-4 grid gap-4">
                  <Field label="Title" value={calendarTitle} onChange={setCalendarTitle} />
                  <Field label="Platform" value={calendarPlatform} onChange={setCalendarPlatform} />
                  <SelectField label="Status" value={calendarStatus} options={calendarStatuses} onChange={setCalendarStatus} />
                  <Field label="Scheduled for" value={calendarDate} onChange={setCalendarDate} />
                  <button onClick={createCalendarItem} className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-[#7c8cff] px-4 text-sm font-semibold text-white">
                    <CalendarDays className="h-4 w-4" />
                    Add calendar item
                  </button>
                </div>
              </Panel>

              <Panel>
                <h2 className="text-lg font-semibold">Calendar list and status</h2>
                <div className="mt-4 grid gap-3">
                  {calendarItems.map((item) => (
                    <div key={item.id} data-calendar-id={item.id} className="rounded-md border border-[#252b38] bg-[#0d1017] p-4">
                      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                        <div>
                          <div className="font-semibold">{item.title}</div>
                          <div className="mt-1 text-sm text-[#9aa3b2]">
                            {item.platform} / {formatDate(item.scheduled_for)} / script {shortId(item.script_id)}
                          </div>
                        </div>
                        <StatusPill>{item.status}</StatusPill>
                      </div>
                      <div className="mt-4 flex flex-wrap gap-2">
                        {calendarStatuses.map((status) => (
                          <button
                            key={status}
                            onClick={() => void updateCalendarStatus(item, status)}
                            className={`rounded-md border px-3 py-2 text-xs ${
                              item.status === status ? "border-[#7c8cff] text-white" : "border-[#2b3142] text-[#c8d0df]"
                            }`}
                          >
                            {status}
                          </button>
                        ))}
                      </div>
                    </div>
                  ))}
                  {calendarItems.length === 0 && <div className="text-sm text-[#9aa3b2]">No calendar items yet.</div>}
                </div>
              </Panel>
            </div>
          )}

          {view === "memory" && (
            <div className="mt-6 grid gap-4 xl:grid-cols-[1fr_1fr]">
              <Panel>
                <h2 className="text-lg font-semibold">Project memory editor</h2>
                <div className="mt-4 grid gap-4">
                  <Field label="Niche" value={memory.niche} onChange={(value) => updateMemoryField("niche", value)} />
                  <Field label="Audience" value={memory.audience} onChange={(value) => updateMemoryField("audience", value)} />
                  <Field label="Tone" value={memory.tone} onChange={(value) => updateMemoryField("tone", value)} />
                  <TextAreaField label="Content rules" value={listToText(memory.content_rules)} onChange={(value) => updateMemoryList("content_rules", value)} />
                  <TextAreaField label="Preferred formats" value={listToText(memory.preferred_formats)} onChange={(value) => updateMemoryList("preferred_formats", value)} />
                  <button onClick={saveMemory} className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-[#7c8cff] px-4 text-sm font-semibold text-white">
                    <Save className="h-4 w-4" />
                    Save memory
                  </button>
                </div>
              </Panel>

              <Panel>
                <h2 className="text-lg font-semibold">Long-term context</h2>
                <div className="mt-4 grid gap-4">
                  <TextAreaField label="Rejected ideas" value={listToText(memory.rejected_ideas)} onChange={(value) => updateMemoryList("rejected_ideas", value)} />
                  <TextAreaField label="Best-performing topics" value={listToText(memory.best_performing_topics)} onChange={(value) => updateMemoryList("best_performing_topics", value)} />
                  <TextAreaField label="Past successful scripts" value={listToText(memory.past_successful_scripts)} onChange={(value) => updateMemoryList("past_successful_scripts", value)} minHeight="min-h-36" />
                </div>
              </Panel>
            </div>
          )}

          {view === "admin" && (
            <div className="mt-6 space-y-4">
              <Panel>
                <div className="flex flex-wrap items-center gap-2">
                  {(["generations", "feedback", "audit"] as AdminTab[]).map((tab) => (
                    <button
                      key={tab}
                      onClick={() => setAdminTab(tab)}
                      className={`rounded-md border px-3 py-2 text-sm ${
                        adminTab === tab ? "border-[#7c8cff] bg-[#151925] text-white" : "border-[#2b3142] text-[#c8d0df]"
                      }`}
                    >
                      {tab}
                    </button>
                  ))}
                </div>
              </Panel>

              {adminTab === "generations" && (
                <Panel>
                  <h2 className="text-lg font-semibold">Admin generations</h2>
                  <div className="mt-4 grid gap-3">
                    {adminGenerations.map((generation) => (
                      <div key={generation.id} className="rounded-md border border-[#252b38] bg-[#0d1017] p-4">
                        <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                          <div>
                            <div className="font-semibold">{generation.type}</div>
                            <div className="mt-1 text-sm text-[#9aa3b2]">
                              {generation.model} / {generation.token_estimate} tokens / ${generation.cost_estimate}
                            </div>
                          </div>
                          <StatusPill kind={generation.feedback_status ? "good" : "neutral"}>
                            {generation.feedback_status ?? generation.validation_status}
                          </StatusPill>
                        </div>
                        <div className="mt-4">
                          <FeedbackButtons generationId={generation.id} onFeedback={submitFeedback} />
                        </div>
                      </div>
                    ))}
                    {adminGenerations.length === 0 && <div className="text-sm text-[#9aa3b2]">No generations yet.</div>}
                  </div>
                </Panel>
              )}

              {adminTab === "feedback" && (
                <Panel>
                  <h2 className="text-lg font-semibold">Admin feedback</h2>
                  <div className="mt-4 overflow-hidden rounded-lg border border-[#252b38]">
                    {adminFeedback.map((record) => (
                      <div key={`${record.generation_id}-${record.action}-${record.created_at}`} className="grid gap-2 border-b border-[#252b38] p-3 text-sm last:border-b-0 md:grid-cols-[1fr_150px_1.2fr]">
                        <span className="font-mono text-[#8e96a8]">{shortId(record.generation_id)}</span>
                        <span className="text-[#e8edf7]">{record.action}</span>
                        <span className="text-[#9aa3b2]">{record.note ?? "no note"}</span>
                      </div>
                    ))}
                    {adminFeedback.length === 0 && <div className="p-3 text-sm text-[#9aa3b2]">No feedback yet.</div>}
                  </div>
                </Panel>
              )}

              {adminTab === "audit" && (
                <Panel>
                  <h2 className="text-lg font-semibold">Admin audit logs</h2>
                  <div className="mt-4 overflow-hidden rounded-lg border border-[#252b38]">
                    {auditLogs.map((log) => (
                      <div key={log.id} className="grid gap-2 border-b border-[#252b38] p-3 text-sm last:border-b-0 md:grid-cols-[1fr_1fr_100px]">
                        <span className="text-[#e8edf7]">{log.action}</span>
                        <span className="text-[#9aa3b2]">{log.object_type}</span>
                        <span className="font-mono text-[#8e96a8]">{shortId(log.object_id)}</span>
                      </div>
                    ))}
                    {auditLogs.length === 0 && <div className="p-3 text-sm text-[#9aa3b2]">No audit logs yet.</div>}
                  </div>
                </Panel>
              )}
            </div>
          )}

          {["producer", "ideas", "radar", "score", "repurpose", "analytics", "settings"].includes(view) && (
            <div className="mt-6 grid gap-4 xl:grid-cols-2">
              <Panel>
                <div className="flex items-center gap-3">
                  <Bot className="h-5 w-5 text-[#7c8cff]" />
                  <h2 className="text-lg font-semibold">Backend-connected module</h2>
                </div>
                <p className="mt-3 text-sm leading-6 text-[#9aa3b2]">
                  This phase exposes the existing backend features in the UI. Use Content Packs, Scripts, Calendar, Project Memory, Activity, Notifications, and Admin for live backend operations.
                </p>
              </Panel>
              <Panel>
                <h2 className="text-lg font-semibold">Current project</h2>
                <div className="mt-3 space-y-2 text-sm text-[#c8d0df]">
                  <div>Name: {activeProject?.name ?? "none"}</div>
                  <div>Niche: {activeProject?.niche ?? "none"}</div>
                  <div>Platform: {activeProject?.platform ?? "none"}</div>
                </div>
              </Panel>
            </div>
          )}
        </section>

        <aside className="border-t border-[#252b38] bg-[#0d1017] p-4 lg:border-l lg:border-t-0">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">Activity</h2>
            <Activity className="h-4 w-4 text-[#9aa3b2]" />
          </div>
          <div className="mt-4 grid gap-3">
            {activity.slice(0, 6).map((event) => (
              <div key={event.id} className="rounded-lg border border-[#252b38] bg-[#10131a] p-3">
                <div className="text-sm text-[#e8edf7]">{event.verb}</div>
                <div className="mt-1 text-xs text-[#8e96a8]">
                  {event.object_type} / {shortId(event.object_id)}
                </div>
              </div>
            ))}
            {activity.length === 0 && <div className="text-sm text-[#9aa3b2]">No activity events yet.</div>}
          </div>

          <div className="mt-6 flex items-center justify-between">
            <h2 className="font-semibold">Notifications</h2>
            <Bell className="h-4 w-4 text-[#9aa3b2]" />
          </div>
          <div className="mt-4 grid gap-3">
            {notifications.slice(0, 6).map((notification) => (
              <button
                key={notification.id}
                onClick={() => void markNotificationRead(notification.id)}
                className="rounded-lg border border-[#252b38] bg-[#10131a] p-3 text-left transition hover:border-[#7c8cff]"
              >
                <div className="flex items-center justify-between gap-3">
                  <span className="text-sm font-medium text-[#e8edf7]">{notification.title}</span>
                  <StatusPill kind={notification.read ? "neutral" : "good"}>{notification.read ? "read" : "new"}</StatusPill>
                </div>
                <div className="mt-2 text-xs leading-5 text-[#9aa3b2]">{notification.body}</div>
              </button>
            ))}
            {notifications.length === 0 && <div className="text-sm text-[#9aa3b2]">No notifications yet.</div>}
          </div>

          <Panel className="mt-6">
            <div className="flex items-center gap-2 font-semibold">
              <Wallet className="h-4 w-4 text-[#ffd166]" />
              Usage and cost
            </div>
            <div className="mt-4 space-y-3 text-sm text-[#c8d0df]">
              <div className="flex justify-between">
                <span>Month</span>
                <span>{usage?.month ?? "n/a"}</span>
              </div>
              <div className="flex justify-between">
                <span>Generations</span>
                <span>{usage?.generations_used ?? 0}</span>
              </div>
              <div className="flex justify-between">
                <span>Limit</span>
                <span>{usage?.generation_limit ?? 0}</span>
              </div>
              <div className="flex justify-between">
                <span>Blocked</span>
                <span>{usage?.blocked ? "yes" : "no"}</span>
              </div>
            </div>
          </Panel>

          <Panel className="mt-6">
            <div className="flex items-center gap-2 font-semibold">
              <Database className="h-4 w-4 text-[#20d6a5]" />
              Project context
            </div>
            <div className="mt-3 space-y-2 text-xs leading-5 text-[#9aa3b2]">
              <div>Memory: {memory.content_rules.length} rules</div>
              <div>Rejected ideas: {memory.rejected_ideas.length}</div>
              <div>Successful scripts: {memory.past_successful_scripts.length}</div>
            </div>
          </Panel>
        </aside>
      </div>
    </main>
  );
}
