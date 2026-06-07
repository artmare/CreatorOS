"use client";

import {
  Activity,
  AlertTriangle,
  BarChart3,
  Bell,
  Bot,
  CalendarDays,
  Check,
  ChevronRight,
  Clipboard,
  Database,
  FileText,
  Gauge,
  History,
  LayoutDashboard,
  Lock,
  MessageSquare,
  Play,
  RefreshCcw,
  Search,
  Settings,
  ShieldCheck,
  Sparkles,
  Users,
  Wallet,
} from "lucide-react";
import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";
import { useMemo, useState, useSyncExternalStore } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type View = "dashboard" | "factory" | "memory" | "admin";

const navItems = [
  ["Dashboard", LayoutDashboard],
  ["AI Producer", Bot],
  ["Scripts", FileText],
  ["Ideas", Sparkles],
  ["Content Calendar", CalendarDays],
  ["Competitor Radar", Search],
  ["Growth Score", Gauge],
  ["Repurpose", RefreshCcw],
  ["My Style", MessageSquare],
  ["Analytics", BarChart3],
  ["Settings", Settings],
] as const;

const growthData = [
  { name: "Mon", score: 72, cost: 1.2 },
  { name: "Tue", score: 76, cost: 1.7 },
  { name: "Wed", score: 84, cost: 2.4 },
  { name: "Thu", score: 81, cost: 2.2 },
  { name: "Fri", score: 89, cost: 2.9 },
  { name: "Sat", score: 86, cost: 1.4 },
  { name: "Sun", score: 92, cost: 3.1 },
];

const activity = [
  "AI Producer created a content pack",
  "Hook Doctor flagged a generic opening",
  "Usage ledger estimated 1,240 tokens",
  "Idea moved to in_script",
  "Lemon Squeezy webhook synced trialing plan",
];

const agentRuns = [
  ["Strategist", "completed", "Project memory + KB", "$0.0042"],
  ["Scriptwriter", "completed", "Long-form YouTube script", "$0.0118"],
  ["Hook Doctor", "warning", "Generic hook warning", "$0.0021"],
  ["Repurposer", "completed", "5 Shorts + Telegram", "$0.0064"],
];

const adminRows = [
  ["Users", "1", "Supabase Auth ready"],
  ["Subscriptions", "1", "Lemon Squeezy trialing"],
  ["Generations", "34", "$0.84 estimated"],
  ["Errors", "0", "No provider failures"],
  ["Feedback", "12", "8 good, 2 bad, 2 saved"],
  ["Audit logs", "19", "Admin and billing events"],
];

const safetyItems: Array<[LucideIcon, string]> = [
  [ShieldCheck, "RLS migration included"],
  [Lock, "Service role never exposed to browser"],
  [AlertTriangle, "Hallucination warning for analytics claims"],
  [Clipboard, "Markdown export and copy flow ready"],
];

const platformItems: Array<[LucideIcon, string, string]> = [
  [Users, "Workspace Layer", "Solo/team roles and project scope"],
  [History, "Agent Run History", "Inputs, memory, cost, validation"],
  [CalendarDays, "Background Jobs", "Celery + Redis/Upstash queue"],
  [ChevronRight, "Exports", "Copy and Markdown now"],
];

function MetricCard({
  label,
  value,
  detail,
  accent = "text-[#7c8cff]",
}: {
  label: string;
  value: string;
  detail: string;
  accent?: string;
}) {
  return (
    <div className="rounded-lg border border-[#252b38] bg-[#10131a] p-4">
      <div className="text-xs font-medium uppercase text-[#8e96a8]">{label}</div>
      <div className={`mt-3 text-3xl font-semibold ${accent}`}>{value}</div>
      <div className="mt-2 text-sm text-[#9aa3b2]">{detail}</div>
    </div>
  );
}

function StatusPill({ children, kind = "neutral" }: { children: string; kind?: "neutral" | "good" | "warn" }) {
  const color =
    kind === "good"
      ? "border-[#1f8b70] bg-[#10251f] text-[#39e4b1]"
      : kind === "warn"
        ? "border-[#766322] bg-[#28230f] text-[#ffd166]"
        : "border-[#2b3142] bg-[#151925] text-[#aeb7c9]";
  return <span className={`rounded-md border px-2 py-1 text-xs font-medium ${color}`}>{children}</span>;
}

export default function Home() {
  const [view, setView] = useState<View>("dashboard");
  const [topic, setTopic] = useState("дисциплина после провала");
  const [packGenerated, setPackGenerated] = useState(false);
  const mounted = useSyncExternalStore(
    () => () => undefined,
    () => true,
    () => false,
  );

  const pageTitle = useMemo(
    () =>
      ({
        dashboard: "Dashboard",
        factory: "Content Factory",
        memory: "Project Memory",
        admin: "Admin",
      })[view],
    [view],
  );

  return (
    <main className="min-h-screen bg-[#08090d] text-[#f5f7fb]">
      <div className="grid min-h-screen grid-cols-1 lg:grid-cols-[244px_minmax(0,1fr)_360px]">
        <aside className="border-b border-[#252b38] bg-[#0d1017] p-4 lg:border-b-0 lg:border-r">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#7c8cff] text-sm font-bold text-white">
              CO
            </div>
            <div>
              <div className="text-sm font-semibold">CreatorOS</div>
              <div className="text-xs text-[#8e96a8]">AI Producer Suite</div>
            </div>
          </div>

          <nav className="mt-8 grid gap-1">
            {navItems.map(([label, Icon], index) => (
              <button
                key={label}
                className={`flex h-9 items-center gap-3 rounded-md px-3 text-left text-sm transition ${
                  index === 0 && view === "dashboard"
                    ? "bg-[#151925] text-white"
                    : "text-[#9aa3b2] hover:bg-[#111722] hover:text-white"
                }`}
                onClick={() => setView(index === 0 ? "dashboard" : label === "My Style" ? "memory" : "dashboard")}
              >
                <Icon className="h-4 w-4" />
                {label}
              </button>
            ))}
          </nav>

          <div className="mt-8 rounded-lg border border-[#252b38] bg-[#10131a] p-3">
            <div className="flex items-center justify-between text-xs text-[#9aa3b2]">
              <span>Creator Pro</span>
              <span>34 / 500</span>
            </div>
            <div className="mt-2 h-2 rounded-full bg-[#1b2130]">
              <div className="h-2 w-[7%] rounded-full bg-[#20d6a5]" />
            </div>
            <button onClick={() => setView("admin")} className="mt-3 flex items-center gap-2 text-xs text-[#7c8cff]">
              <ShieldCheck className="h-3.5 w-3.5" />
              Admin panel
            </button>
          </div>
        </aside>

        <section className="min-w-0 p-4 md:p-6">
          <header className="flex flex-col gap-4 border-b border-[#252b38] pb-5 md:flex-row md:items-center md:justify-between">
            <div>
              <div className="text-sm text-[#8e96a8]">Workspace: CreatorOS Studio</div>
              <h1 className="mt-1 text-2xl font-semibold">{pageTitle}</h1>
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setView("factory")}
                className="inline-flex h-10 items-center gap-2 rounded-md bg-[#7c8cff] px-4 text-sm font-semibold text-white"
              >
                <Sparkles className="h-4 w-4" />
                Создать идею
              </button>
              <button className="inline-flex h-10 items-center gap-2 rounded-md border border-[#2b3142] px-4 text-sm text-[#dbe2f0]">
                <FileText className="h-4 w-4" />
                Написать сценарий
              </button>
            </div>
          </header>

          {view === "dashboard" && (
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="mt-6 space-y-6">
              <div className="rounded-lg border border-[#252b38] bg-[#10131a] p-5">
                <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                  <div>
                    <h2 className="text-xl font-semibold">
                      Добро пожаловать, Артём. Сегодня твоя цель — создать 3 идеи и 1 сценарий.
                    </h2>
                    <p className="mt-2 max-w-2xl text-sm leading-6 text-[#9aa3b2]">
                      Project Memory подключена к каждому агенту: ниша, аудитория, тон, правила контента,
                      отклоненные идеи и успешные сценарии уже используются как контекст.
                    </p>
                  </div>
                  <StatusPill kind="good">Supabase-ready</StatusPill>
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                <MetricCard label="Weekly progress" value="72%" detail="3 ideas, 1 script in motion" />
                <MetricCard label="Ready scripts" value="12" detail="4 approved for production" accent="text-[#20d6a5]" />
                <MetricCard label="Growth Score" value="89" detail="Hook and clarity improved" />
                <MetricCard label="Usage cost" value="$0.84" detail="34 generations estimated" accent="text-[#ffd166]" />
              </div>

              <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
                <div className="rounded-lg border border-[#252b38] bg-[#10131a] p-4">
                  <div className="mb-4 flex items-center justify-between">
                    <h3 className="font-semibold">Growth and cost telemetry</h3>
                    <StatusPill>agent runs tracked</StatusPill>
                  </div>
                  <div className="h-64 min-h-64 min-w-0">
                    {mounted ? (
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={growthData}>
                          <defs>
                            <linearGradient id="score" x1="0" x2="0" y1="0" y2="1">
                              <stop offset="5%" stopColor="#7c8cff" stopOpacity={0.5} />
                              <stop offset="95%" stopColor="#7c8cff" stopOpacity={0} />
                            </linearGradient>
                          </defs>
                          <CartesianGrid stroke="#202637" vertical={false} />
                          <XAxis dataKey="name" stroke="#697184" fontSize={12} />
                          <YAxis stroke="#697184" fontSize={12} />
                          <Tooltip contentStyle={{ background: "#111722", border: "1px solid #252b38" }} />
                          <Area
                            type="monotone"
                            dataKey="score"
                            stroke="#7c8cff"
                            fill="url(#score)"
                            isAnimationActive={false}
                          />
                        </AreaChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="h-full rounded-md bg-[#0d1017]" />
                    )}
                  </div>
                </div>

                <div className="rounded-lg border border-[#252b38] bg-[#10131a] p-4">
                  <h3 className="font-semibold">Activity Feed</h3>
                  <div className="mt-4 space-y-3">
                    {activity.map((item) => (
                      <div key={item} className="flex gap-3 rounded-md border border-[#252b38] bg-[#0d1017] p-3">
                        <Activity className="mt-0.5 h-4 w-4 text-[#7c8cff]" />
                        <span className="text-sm text-[#c8d0df]">{item}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="grid gap-4 xl:grid-cols-3">
                {agentRuns.map(([agent, status, context, cost]) => (
                  <div key={agent} className="rounded-lg border border-[#252b38] bg-[#10131a] p-4">
                    <div className="flex items-center justify-between">
                      <h3 className="font-semibold">{agent}</h3>
                      <StatusPill kind={status === "completed" ? "good" : "warn"}>{status}</StatusPill>
                    </div>
                    <p className="mt-3 text-sm text-[#9aa3b2]">{context}</p>
                    <div className="mt-4 font-mono text-xs text-[#8e96a8]">{cost}</div>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {view === "factory" && (
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="mt-6 grid gap-4 xl:grid-cols-[0.8fr_1.2fr]">
              <div className="rounded-lg border border-[#252b38] bg-[#10131a] p-5">
                <h2 className="text-lg font-semibold">Generate Content Pack</h2>
                <p className="mt-2 text-sm leading-6 text-[#9aa3b2]">
                  One topic becomes an idea, YouTube script, five titles, five Shorts, Telegram post, Growth Score,
                  feedback actions, and optional calendar item.
                </p>
                <label className="mt-5 block text-sm text-[#c8d0df]">Topic</label>
                <textarea
                  value={topic}
                  onChange={(event) => setTopic(event.target.value)}
                  className="mt-2 min-h-28 w-full rounded-md border border-[#2b3142] bg-[#0d1017] p-3 text-sm outline-none focus:border-[#7c8cff]"
                />
                <button
                  onClick={() => setPackGenerated(true)}
                  className="mt-4 inline-flex h-10 items-center gap-2 rounded-md bg-[#7c8cff] px-4 text-sm font-semibold text-white"
                >
                  <Play className="h-4 w-4" />
                  Generate Pack
                </button>
              </div>

              <div className="rounded-lg border border-[#252b38] bg-[#10131a] p-5">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold">Pack Preview</h2>
                  <StatusPill kind={packGenerated ? "good" : "neutral"}>{packGenerated ? "generated" : "ready"}</StatusPill>
                </div>
                <div className="mt-4 grid gap-3">
                  {[
                    ["Idea", `${topic}: почему это ломает рост канала`],
                    ["YouTube script", "Hook, conflict, B-roll notes, practical steps, CTA"],
                    ["5 titles", "Why, how, conflict, mistake, rule-based title variants"],
                    ["5 Shorts", "Five direct short-form angles with punchy hooks"],
                    ["Telegram post", "A short post with thesis, observation, and evening task"],
                    ["Growth Score", "89 / 100 with criteria and improvements"],
                  ].map(([label, value]) => (
                    <div key={label} className="rounded-md border border-[#252b38] bg-[#0d1017] p-3">
                      <div className="text-xs uppercase text-[#8e96a8]">{label}</div>
                      <div className="mt-1 text-sm text-[#e8edf7]">{value}</div>
                    </div>
                  ))}
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  {["good", "bad", "regenerate", "save to style", "use in calendar"].map((item) => (
                    <button key={item} className="rounded-md border border-[#2b3142] px-3 py-2 text-xs text-[#c8d0df]">
                      {item}
                    </button>
                  ))}
                </div>
              </div>
            </motion.div>
          )}

          {view === "memory" && (
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="mt-6 grid gap-4 xl:grid-cols-2">
              <div className="rounded-lg border border-[#252b38] bg-[#10131a] p-5">
                <h2 className="text-lg font-semibold">Project Memory</h2>
                <div className="mt-4 space-y-3 text-sm">
                  {[
                    ["Niche", "мотивация и дисциплина"],
                    ["Audience", "парни 16-25 лет"],
                    ["Tone", "жесткий, честный, без воды"],
                    ["Preferred formats", "YouTube long, Shorts, Telegram"],
                    ["Rejected ideas", "утренняя рутина без нового угла"],
                    ["Best topics", "дисциплина, ответственность, деньги через навык"],
                  ].map(([label, value]) => (
                    <div key={label} className="flex items-start justify-between gap-4 border-b border-[#252b38] pb-3">
                      <span className="text-[#8e96a8]">{label}</span>
                      <span className="max-w-md text-right text-[#e8edf7]">{value}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="rounded-lg border border-[#252b38] bg-[#10131a] p-5">
                <h2 className="text-lg font-semibold">Knowledge Base</h2>
                <p className="mt-2 text-sm leading-6 text-[#9aa3b2]">
                  Stored text/chunk retrieval is the default. Embeddings can be enabled when OpenAI credentials are
                  provided.
                </p>
                <div className="mt-5 rounded-md border border-[#252b38] bg-[#0d1017] p-4">
                  <Database className="h-5 w-5 text-[#20d6a5]" />
                  <div className="mt-3 font-semibold">Reference scripts</div>
                  <div className="mt-1 text-sm text-[#9aa3b2]">4 chunks available for agent context.</div>
                </div>
              </div>
            </motion.div>
          )}

          {view === "admin" && (
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="mt-6 grid gap-4 xl:grid-cols-[1fr_0.8fr]">
              <div className="rounded-lg border border-[#252b38] bg-[#10131a] p-5">
                <h2 className="text-lg font-semibold">Minimal Admin Panel</h2>
                <div className="mt-4 overflow-hidden rounded-lg border border-[#252b38]">
                  {adminRows.map(([label, count, detail]) => (
                    <div key={label} className="grid grid-cols-[1fr_80px_1.4fr] border-b border-[#252b38] px-4 py-3 text-sm last:border-b-0">
                      <span className="text-[#e8edf7]">{label}</span>
                      <span className="font-mono text-[#7c8cff]">{count}</span>
                      <span className="text-[#9aa3b2]">{detail}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="rounded-lg border border-[#252b38] bg-[#10131a] p-5">
                <h2 className="text-lg font-semibold">Audit and Safety</h2>
                <div className="mt-4 space-y-3">
                  {safetyItems.map(([Icon, label]) => (
                    <div key={label} className="flex items-center gap-3 rounded-md border border-[#252b38] bg-[#0d1017] p-3 text-sm text-[#c8d0df]">
                      <Icon className="h-4 w-4 text-[#20d6a5]" />
                      {label}
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          )}
        </section>

        <aside className="border-t border-[#252b38] bg-[#0d1017] p-4 lg:border-l lg:border-t-0">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">AI Producer Chat</h2>
            <Bell className="h-4 w-4 text-[#9aa3b2]" />
          </div>

          <div className="mt-4 space-y-3">
            <div className="rounded-lg border border-[#252b38] bg-[#10131a] p-3 text-sm text-[#c8d0df]">
              Сделай мне контент-план на неделю.
            </div>
            <div className="rounded-lg border border-[#2b3142] bg-[#151925] p-3">
              <div className="flex items-center gap-2 text-sm font-semibold">
                <Bot className="h-4 w-4 text-[#7c8cff]" />
                Producer Orchestrator
              </div>
              <div className="mt-3 space-y-2 text-sm text-[#c8d0df]">
                <div className="flex items-start gap-2">
                  <Check className="mt-0.5 h-4 w-4 text-[#20d6a5]" />
                  Strategist chooses weekly focus.
                </div>
                <div className="flex items-start gap-2">
                  <Check className="mt-0.5 h-4 w-4 text-[#20d6a5]" />
                  Scriptwriter drafts one long video.
                </div>
                <div className="flex items-start gap-2">
                  <Check className="mt-0.5 h-4 w-4 text-[#20d6a5]" />
                  Repurposer creates Shorts and Telegram.
                </div>
              </div>
            </div>
          </div>

          <div className="mt-5 rounded-lg border border-[#252b38] bg-[#10131a] p-4">
            <div className="flex items-center gap-2 font-semibold">
              <Wallet className="h-4 w-4 text-[#ffd166]" />
              Usage and Cost Control
            </div>
            <div className="mt-4 h-40 min-h-40 min-w-0">
              {mounted ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={growthData}>
                    <XAxis dataKey="name" stroke="#697184" fontSize={10} />
                    <YAxis stroke="#697184" fontSize={10} />
                    <Bar dataKey="cost" fill="#20d6a5" radius={[4, 4, 0, 0]} isAnimationActive={false} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full rounded-md bg-[#0d1017]" />
              )}
            </div>
          </div>

          <div className="mt-5 grid gap-3">
            {platformItems.map(([Icon, title, detail]) => (
              <div key={title} className="rounded-lg border border-[#252b38] bg-[#10131a] p-3">
                <div className="flex items-center gap-2 text-sm font-semibold">
                  <Icon className="h-4 w-4 text-[#7c8cff]" />
                  {title}
                </div>
                <div className="mt-1 text-xs text-[#9aa3b2]">{detail}</div>
              </div>
            ))}
          </div>
        </aside>
      </div>
    </main>
  );
}
