import {
  Bot,
  CheckCircle,
  ClipboardList,
  Code,
  FileSearch,
  FileText,
  Loader2,
  Terminal,
  Users,
  Wrench,
} from 'lucide-react';
import { useMemo } from 'react';
import { useAgents } from '@/hooks/useAgents';
import { useTasks } from '@/hooks/useTasks';
import { AgentStatusBadge } from '@/components/ui/agent-status-badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';
import type { TaskStatus } from '@/types/workspace';

/** V1.0-P1-2 — status precedence for "what is the Station doing right now". */
const ACTIVE_STATUS_RANK: Partial<Record<TaskStatus, number>> = {
  running: 0,
  handoff: 1,
  assigned: 2,
  ready: 3,
  pending: 4,
  waiting_approval: 5,
  revision_required: 6,
  blocked: 7,
};

const ROLE_ICON: Record<string, typeof Bot> = {
  planner: ClipboardList,
  coder: Code,
  reviewer: CheckCircle,
  research: FileSearch,
  summarizer: FileText,
  supervisor: Terminal,
  custom: Wrench,
};

/**
 * V1.0-6a — ActiveStationsSidebar.
 * V1.0-P1-2 — Sidebar row now shows the Station's current Task
 * (the one with the highest-rank active status) below the slug,
 * mirroring the Star-Office-UI visitor list behaviour.
 */
export default function ActiveStationsSidebar() {
  const { data, isLoading, isError } = useAgents({
    is_enabled: true,
    page_size: 50,
  });
  const stations = data?.items ?? [];

  // Single query for all stations' current tasks. We pass the station
  // id list, default no status filter (so the Sidebar still shows
  // recent-but-paused / blocked work). Backend ordering puts 'running'
  // first, so the first match per agent_id is the most relevant task.
  const { data: tasksResp, isLoading: isTasksLoading } = useTasks({
    agentIds: stations.map((s) => s.id),
    statuses: [
      'running',
      'handoff',
      'assigned',
      'ready',
      'pending',
      'waiting_approval',
      'revision_required',
      'blocked',
    ],
    pageSize: 100,
  });

  // Per-Station current task. Group by agent_id, take the task with
  // the highest rank (lowest ACTIVE_STATUS_RANK value).
  const currentTaskByAgent = useMemo(() => {
    const map: Record<string, { title: string; status: TaskStatus }> = {};
    const rank = (s: TaskStatus) => ACTIVE_STATUS_RANK[s] ?? 99;
    for (const t of tasksResp?.items ?? []) {
      if (!t.assigned_agent_id) continue;
      const cur = map[t.assigned_agent_id];
      if (!cur || rank(t.status) < rank(cur.status)) {
        map[t.assigned_agent_id] = { title: t.title, status: t.status };
      }
    }
    return map;
  }, [tasksResp]);

  // State distribution chip (per Star-Office-UI's status bar idea)
  const distribution = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const s of stations) {
      counts[s.status] = (counts[s.status] ?? 0) + 1;
    }
    return counts;
  }, [stations]);

  return (
    <aside
      aria-label="Active stations"
      className="hidden w-72 shrink-0 flex-col border-r border-stone-200 bg-white lg:flex"
    >
      <header className="border-b border-stone-200 px-4 py-3">
        <h2 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-stone-700">
          <Users size={12} aria-hidden />
          活跃 Station
        </h2>
        <p className="mt-0.5 text-[10px] text-stone-400">
          {isLoading
            ? "Loading…"
            : `${stations.length} stations · 仿 Star-Office-UI 访客列表`}
        </p>
      </header>

      <ScrollArea className="flex-1">
        <div className="space-y-1 p-2">
          {isLoading &&
            Array.from({ length: 6 }).map((_, i) => (
              <div
                key={i}
                className="h-16 animate-pulse rounded-md bg-stone-100"
                aria-hidden
              />
            ))}

          {isError && (
            <div className="px-2 py-4 text-xs text-stone-500">
              加载 Station 失败
            </div>
          )}

          {!isLoading && !isError && stations.length === 0 && (
            <div className="px-2 py-4 text-xs text-stone-500">
              暂无活跃 Station
            </div>
          )}

          {stations.map((station) => {
            const Icon = ROLE_ICON[station.role] ?? Bot;
            const task = currentTaskByAgent[station.id];
            return (
              <button
                key={station.id}
                type="button"
                className={cn(
                  "group flex w-full items-start gap-3 rounded-md px-2 py-2 text-left",
                  "transition-colors hover:bg-stone-50 focus:bg-stone-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-stone-300"
                )}
                aria-label={`Station ${station.name} (${station.role})${task ? ` — ${task.title}` : ''}`}
              >
                <Avatar className="h-9 w-9 shrink-0">
                  <AvatarFallback
                    className={cn(
                      station.is_builtin
                        ? "bg-blue-50 text-blue-700 border-blue-200"
                        : "bg-stone-100 text-stone-700 border-stone-200",
                      "border"
                    )}
                  >
                    <Icon size={15} aria-hidden />
                  </AvatarFallback>
                </Avatar>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <span className="truncate text-sm font-medium text-stone-900">
                      {station.name}
                    </span>
                    {station.is_builtin && (
                      <span className="shrink-0 rounded bg-stone-100 px-1 py-px text-[9px] uppercase tracking-wider text-stone-500">
                        built-in
                      </span>
                    )}
                  </div>
                  <div className="mt-0.5 flex items-center gap-1.5 text-[10px] text-stone-500">
                    <span className="lowercase">{station.role}</span>
                    {station.slug && (
                      <>
                        <span aria-hidden>·</span>
                        <span className="truncate font-mono">{station.slug}</span>
                      </>
                    )}
                  </div>
                  <div className="mt-1.5">
                    <AgentStatusBadge
                      state={station.status}
                      label={statusToZh(station.status)}
                      className="px-1.5 py-0 text-[10px]"
                    />
                  </div>
                  {/* V1.0-P1-2: per-Station "current task" line */}
                  <div
                    className="mt-1 flex min-w-0 items-center gap-1 text-[11px] text-stone-600"
                    title={task ? task.title : undefined}
                  >
                    {task ? (
                      <>
                        <span className="text-stone-400" aria-hidden>→</span>
                        <span className="truncate">{task.title}</span>
                      </>
                    ) : isTasksLoading ? (
                      <>
                        <Loader2 size={10} className="animate-spin text-stone-400" aria-hidden />
                        <span className="italic text-stone-400">查找任务…</span>
                      </>
                    ) : (
                      <span className="italic text-stone-400">→ (空闲)</span>
                    )}
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </ScrollArea>

      <footer className="border-t border-stone-200 px-4 py-2">
        <p className="text-[10px] uppercase tracking-wider text-stone-400">
          状态分布
        </p>
        <div className="mt-1 flex flex-wrap gap-1">
          {Object.entries(distribution)
            .sort((a, b) => b[1] - a[1])
            .map(([state, n]) => (
              <AgentStatusBadge
                key={state}
                state={state}
                label={`${statusToZh(state)} ${n}`}
                dot={false}
                className="px-1.5 py-0 text-[10px]"
              />
            ))}
          {Object.keys(distribution).length === 0 && (
            <span className="text-[10px] italic text-stone-400">—</span>
          )}
        </div>
      </footer>
    </aside>
  );
}

const ZH: Record<string, string> = {
  idle: "空闲",
  running: "运行中",
  busy: "忙碌",
  blocked: "阻塞",
  error: "出错",
  disabled: "禁用",
  pending: "待命",
  paused: "已暂停",
  waiting: "等待中",
  completed: "已完成",
  done: "已完成",
  handoff: "交接中",
  handoff_required: "需交接",
  failed: "失败",
  reviewing: "审查中",
  planning: "规划中",
  ready: "就绪",
  started: "已启动",
  executing: "执行中",
  writing: "写作中",
  researching: "调研中",
  syncing: "同步中",
};
function statusToZh(s: string): string {
  return ZH[s] ?? s;
}
