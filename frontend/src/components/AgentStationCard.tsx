import {
  ArrowRight,
  BrainCircuit,
  CheckCircle2,
  Code2,
  FileSearch,
  FileText,
  LoaderCircle,
  Terminal,
  Wrench,
} from 'lucide-react';
import { Card, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { Avatar, AvatarFallback } from './ui/avatar';
import { AgentStatusBadge } from './ui/agent-status-badge';
import { cn } from '@/lib/utils';
import type { WorkspaceAgent, WorkspaceHandoff, WorkspaceWorker } from '../types/workspace';

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
    model_name?: string | null;
    quota?: {
      quota_status: string;
      usage_percent?: number | null;
      token_limit?: number | null;
    } | null;
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

const ROLE_ICON: Record<string, typeof Code2> = {
  coder: Code2,
  reviewer: FileSearch,
  planner: BrainCircuit,
  research: FileSearch,
  summarizer: FileText,
  supervisor: Terminal,
};

function ModelIcon({ role }: { role: string }) {
  const Icon = ROLE_ICON[role] ?? BrainCircuit;
  return <Icon aria-hidden />;
}

function TaskStateIcon({ status }: { status: string }) {
  if (['done', 'completed', 'completed_verified', 'completed_unverified'].includes(status)) {
    return <CheckCircle2 size={14} className="text-emerald-600" aria-hidden />;
  }
  if (status === 'running') {
    return <LoaderCircle size={14} className="animate-spin text-blue-600" aria-hidden />;
  }
  return <span aria-hidden>⌛</span>;
}

function shortModelName(value: string): string {
  if (/^[0-9a-f]{8}-[0-9a-f-]{27,}$/i.test(value)) return 'Configured Model';
  const parts = value.split(/[/:]/);
  return parts.at(-1) || value;
}

function defaultTools(role: string): string[] {
  if (role === 'coder') return ['VS Code', 'Terminal'];
  if (role === 'reviewer') return ['Code Review', 'Files'];
  return ['Web Search', 'File Reader'];
}

function waitingMessage(taskStatus?: string, stationStatus?: string): string {
  if (taskStatus === 'running') return 'Execution in progress. Waiting for the next verified output.';
  if (stationStatus === 'waiting') return 'Waiting for upstream task completion.';
  if (stationStatus === 'done') return 'Task completed and ready for the next station.';
  return 'No output yet.';
}

export default function AgentStationCard({
  agent,
  worker,
  tasks,
  status,
  handoffs = [],
  isSelected = false,
  onStationClick,
  onTaskClick,
}: AgentStationCardProps) {
  const agentTasks = tasks.filter(
    (task) => !task.assigned_agent_id || task.assigned_agent_id === agent.id,
  );
  const currentTask =
    agentTasks.find((task) => ['running', 'handoff'].includes(task.status)) || agentTasks.at(-1);

  const stationStatus = status || agent.status;
  const modelName =
    worker?.model_name ||
    currentTask?.model_name ||
    worker?.model_id ||
    agent.default_model_id ||
    'Unassigned';
  const usage = currentTask?.tokens_used || worker?.total_tokens_used || 0;
  const tokenLimit = currentTask?.quota?.token_limit || Math.max(20_000, usage);
  const usagePercent =
    currentTask?.quota?.usage_percent ?? Math.min(100, Math.round((usage / tokenLimit) * 100));
  const latestHandoff = handoffs.at(-1);
  const outgoing = latestHandoff?.from_agent_id === agent.id;

  const tools = currentTask?.latest_tool_call
    ? [currentTask.latest_tool_call.tool_name, defaultTools(agent.role)[1]]
    : defaultTools(agent.role);

  return (
    <Card
      data-station-id={agent.id}
      data-station-status={stationStatus}
      className={cn(
        'gap-0 p-0 transition-shadow',
        isSelected && 'ring-2 ring-blue-400',
        currentTask?.status === 'running' && 'shadow-sm',
      )}
    >
      <CardContent className="space-y-3 p-3">
        {/* Header */}
        <button
          type="button"
          className="flex w-full items-center justify-between gap-2 rounded text-left transition-colors hover:bg-stone-50"
          onClick={() => {
            if (currentTask) onTaskClick?.(currentTask.id);
            onStationClick?.(agent.id, currentTask?.id);
          }}
        >
          <div className="flex min-w-0 items-center gap-2">
            <Avatar className="h-8 w-8 shrink-0">
              <AvatarFallback className="bg-blue-50 text-blue-700">
                <ModelIcon role={agent.role} />
              </AvatarFallback>
            </Avatar>
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-stone-900" title={agent.name}>
                {agent.name}
              </p>
              <p className="text-[10px] uppercase tracking-wider text-stone-500">{agent.role}</p>
            </div>
          </div>
          <AgentStatusBadge state={stationStatus} dot className="shrink-0 text-[10px]" />
        </button>

        {/* Model */}
        <section className="rounded-md border border-stone-200 bg-stone-50 p-2">
          <p className="text-[10px] uppercase tracking-wider text-stone-500">Model</p>
          <p className="mt-0.5 truncate font-mono text-xs text-stone-800" title={modelName}>
            {shortModelName(modelName)}
          </p>
        </section>

        {/* Current task */}
        <section>
          <p className="text-[10px] uppercase tracking-wider text-stone-500">Current task</p>
          <p className="mt-0.5 flex items-center gap-1 truncate text-xs text-stone-700">
            <TaskStateIcon status={currentTask?.status || stationStatus} />
            <span title={currentTask?.title || 'Awaiting task'}>
              {currentTask?.title || 'Awaiting task'}
            </span>
          </p>
        </section>

        {/* Latest output */}
        <section>
          <p className="text-[10px] uppercase tracking-wider text-stone-500">Latest output</p>
          <p className="mt-0.5 line-clamp-3 text-[11px] text-stone-600">
            {currentTask?.output || currentTask?.next_action || waitingMessage(currentTask?.status, stationStatus)}
          </p>
        </section>

        {/* Usage */}
        <section>
          <div className="flex items-baseline justify-between text-[10px] text-stone-500">
            <span className="uppercase tracking-wider">Usage (this run)</span>
            <span className="font-mono text-stone-700">
              {usage.toLocaleString()} / {tokenLimit.toLocaleString()} ({Math.round(usagePercent)}%)
            </span>
          </div>
          <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-stone-200">
            <div
              className="h-full rounded-full bg-blue-500 transition-all"
              style={{ width: `${Math.min(100, usagePercent)}%` }}
              aria-hidden
            />
          </div>
        </section>

        {/* Tools */}
        <section>
          <p className="text-[10px] uppercase tracking-wider text-stone-500">
            {currentTask?.latest_tool_call ? 'Tools in use' : 'Tools'}
          </p>
          <div className="mt-1 flex flex-wrap gap-1">
            {tools.map((t) => (
              <Badge
                key={t}
                variant="secondary"
                className="gap-1 px-1.5 py-0 text-[10px] font-normal"
              >
                {t === 'Terminal' ? <Terminal size={10} /> : <Wrench size={10} />}
                {t}
              </Badge>
            ))}
          </div>
        </section>

        {/* Handoff */}
        <section
          className={cn(
            'rounded-md border p-2',
            latestHandoff ? 'border-violet-200 bg-violet-50' : 'border-stone-200 bg-stone-50',
          )}
        >
          <p className="text-[10px] uppercase tracking-wider text-stone-500">
            Handoff {latestHandoff ? (outgoing ? '(outgoing)' : '(incoming)') : ''}
          </p>
          {latestHandoff ? (
            <div className="mt-0.5 space-y-0.5 text-[11px] text-stone-700">
              <p>
                {outgoing ? 'To' : 'From'}: <strong>{outgoing ? latestHandoff.to_agent_name || 'Target' : latestHandoff.from_agent_name || 'Source'}</strong>
              </p>
              <p>Reason: {latestHandoff.reason_description || latestHandoff.reason}</p>
            </div>
          ) : (
            <p className="mt-0.5 flex items-center gap-1 text-[11px] italic text-stone-500">
              {currentTask
                ? `Will ${stationStatus === 'done' ? 'handoff' : 'receive'} when ready`
                : 'No handoff planned'}{' '}
              <ArrowRight size={10} aria-hidden />
            </p>
          )}
        </section>
      </CardContent>
    </Card>
  );
}
