import { ArrowRight, CircleDot, GitBranch, Wrench } from 'lucide-react';
import type { WorkspaceAgent, WorkspaceHandoff, WorkspaceWorker } from '../types/workspace';
import { TASK_STATUS_LABELS } from '../types/workspace';
import WorkerBadge from './WorkerBadge';

const ROLE_COLORS: Record<string, string> = {
  planner: 'bg-purple-100 text-purple-700',
  coder: 'bg-blue-100 text-blue-700',
  reviewer: 'bg-amber-100 text-amber-700',
  research: 'bg-green-100 text-green-700',
  summarizer: 'bg-sky-100 text-sky-700',
  supervisor: 'bg-red-100 text-red-700',
};

interface AgentStationCardProps {
  agent: WorkspaceAgent;
  worker?: WorkspaceWorker | null;
  tasks: Array<{
    id: string;
    title: string;
    status: string;
    agent_id?: string | null;
    assigned_agent_id?: string | null;
    output?: string | null;
    tokens_used?: number;
    quota?: { quota_status: string; usage_percent?: number | null } | null;
    latest_tool_call?: { tool_name: string; status: string } | null;
    next_action?: string | null;
    dependencies?: string[];
  }>;
  status?: string;
  handoffs?: WorkspaceHandoff[];
  isSelected?: boolean;
  onStationClick?: (agentId: string, taskId?: string) => void;
  onTaskClick?: (taskId: string) => void;
}

const STATUS_STYLES: Record<string, { label: string; dot: string; border: string; surface: string }> = {
  idle: { label: 'Idle', dot: 'bg-stone-300', border: 'border-stone-200', surface: 'bg-white' },
  waiting: { label: 'Waiting', dot: 'bg-amber-500', border: 'border-amber-300', surface: 'bg-amber-50/40' },
  running: { label: 'Running', dot: 'bg-blue-500 animate-breathe-dot', border: 'border-blue-400', surface: 'bg-blue-50/30' },
  handoff: { label: 'Handoff', dot: 'bg-purple-500 animate-breathe-dot', border: 'border-purple-400', surface: 'bg-purple-50/30' },
  done: { label: 'Done', dot: 'bg-emerald-500', border: 'border-emerald-400', surface: 'bg-emerald-50/30' },
  completed: { label: 'Done', dot: 'bg-emerald-500', border: 'border-emerald-400', surface: 'bg-emerald-50/30' },
  error: { label: 'Error', dot: 'bg-red-500', border: 'border-red-400', surface: 'bg-red-50/30' },
  failed: { label: 'Error', dot: 'bg-red-500', border: 'border-red-400', surface: 'bg-red-50/30' },
};

export default function AgentStationCard({ agent, worker, tasks, status, handoffs = [], isSelected = false, onStationClick, onTaskClick }: AgentStationCardProps) {
  const agentTasks = tasks.filter((task) => (task.agent_id || task.assigned_agent_id) === agent.id);
  const roleColor = ROLE_COLORS[agent.role] || 'bg-stone-100 text-stone-600';
  const currentTask = agentTasks.find((task) => task.status === 'running' || task.status === 'handoff') || agentTasks.at(-1);
  const stationStatus = status || agent.status;
  const statusStyle = STATUS_STYLES[stationStatus] || STATUS_STYLES.idle;
  const latestHandoff = handoffs.at(-1);
  const modelName = worker?.model_name || worker?.model_id || agent.default_model_id || 'Unassigned model';

  return (
    <article className={`w-[286px] shrink-0 overflow-hidden rounded-xl border ${statusStyle.border} ${statusStyle.surface} shadow-sm transition-all duration-300 ${isSelected ? 'ring-2 ring-blue-300 ring-offset-2' : ''}`}>
      <button
        type="button"
        onClick={() => onStationClick?.(agent.id, currentTask?.id)}
        className="w-full border-b border-stone-100 bg-white/85 px-4 py-3 text-left hover:bg-white"
      >
        <div className="flex items-center justify-between gap-3">
          <div className="flex min-w-0 items-center gap-2">
            <span className={`h-2.5 w-2.5 shrink-0 rounded-full ${statusStyle.dot}`} />
            <span className="truncate text-sm font-semibold text-stone-900">{agent.name}</span>
          </div>
          <span className="text-[10px] font-semibold uppercase tracking-wide text-stone-500">{statusStyle.label}</span>
        </div>
        <div className="mt-2 flex items-center justify-between gap-2">
          <span className={`inline-block rounded px-1.5 py-0.5 text-[10px] font-medium ${roleColor}`}>{agent.role}</span>
          <span className="text-[10px] font-medium uppercase tracking-wide text-stone-400">Worker model</span>
        </div>
      </button>

      <div className="space-y-3 px-4 py-3">
        <div className="flex items-center gap-2 min-w-0">
          <WorkerBadge modelName={modelName} status={worker?.status || stationStatus} totalTokensUsed={worker?.total_tokens_used} />
        </div>
        {agentTasks.length === 0 && (
          <div className="rounded-lg border border-dashed border-stone-200 bg-white/70 px-3 py-5 text-center text-xs text-stone-400">暂无任务</div>
        )}
        {currentTask ? (
          <button key={currentTask.id} onClick={() => onTaskClick?.(currentTask.id)} className="w-full rounded-lg border border-stone-200 bg-white p-3 text-left hover:border-stone-300">
            <div className="flex items-center justify-between gap-2">
              <span className="text-[10px] font-semibold uppercase tracking-wide text-stone-400">Current task</span>
              <span className="text-[10px] text-stone-500">{TASK_STATUS_LABELS[currentTask.status] || currentTask.status}</span>
            </div>
            <p className="mt-1 truncate text-sm font-medium text-stone-800">{currentTask.title}</p>
            <p className="mt-2 line-clamp-2 text-xs leading-5 text-stone-500">
              {currentTask.output || currentTask.next_action || waitingMessage(currentTask, stationStatus)}
            </p>
          </button>
        ) : null}

        <div className="grid grid-cols-2 gap-2 text-[10px] text-stone-500">
          <div className="rounded-md bg-white/75 px-2 py-1.5">
            <span className="block text-stone-400">Usage</span>
            <span className="mt-0.5 block font-medium text-stone-700">{(currentTask?.tokens_used || worker?.total_tokens_used || 0).toLocaleString()} tokens</span>
          </div>
          <div className="rounded-md bg-white/75 px-2 py-1.5">
            <span className="block text-stone-400">Quota</span>
            <span className="mt-0.5 block font-medium text-stone-700">{currentTask?.quota?.quota_status || worker?.quota_status || 'normal'}</span>
          </div>
        </div>

        {currentTask?.latest_tool_call ? (
          <div className="flex items-center gap-2 text-[11px] text-stone-500"><Wrench size={12} /> {currentTask.latest_tool_call.tool_name} · {currentTask.latest_tool_call.status}</div>
        ) : (
          <div className="flex items-center gap-2 text-[11px] text-stone-400"><CircleDot size={12} /> No active tool call</div>
        )}

        {latestHandoff ? (
          <div className="rounded-lg border border-purple-200 bg-purple-50 px-3 py-2 text-[11px] text-purple-800">
            <div className="flex items-center gap-1.5 font-semibold"><GitBranch size={12} /> Handoff · {latestHandoff.status}</div>
            <p className="mt-1 flex items-center gap-1">{latestHandoff.from_agent_name || 'Source'} <ArrowRight size={11} /> {latestHandoff.to_agent_name || 'Target'}</p>
          </div>
        ) : null}
      </div>
    </article>
  );
}

function waitingMessage(task: { status: string; dependencies?: string[] }, stationStatus: string): string {
  if (task.status === 'pending' && (task.dependencies?.length || 0) === 0) return '已就绪，等待运行开始。';
  if (stationStatus === 'waiting') return '等待上游工位完成后接手。';
  return '等待 Worker 输出。';
}
