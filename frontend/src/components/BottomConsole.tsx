import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ChevronDown, ChevronUp, Radio, RadioTower, TerminalSquare } from 'lucide-react';
import LogListItem from './LogListItem';
import LogFilters from './LogFilters';
import FinalOutputPanel from './FinalOutputPanel';
import { getLogs } from '../api/logs';
import { useRuntimeEvents } from '../hooks/useWorkspace';
import { cn } from '@/lib/utils';
import type { LogFilters as LogFiltersType } from '../types/log';
import type { RuntimeStatusResponse } from '../types/runtime';
import type { WorkspaceHandoff, WorkspaceTask } from '../types/workspace';

interface BottomConsoleProps {
  goalId?: string | null;
  tasks?: WorkspaceTask[];
  handoffs?: WorkspaceHandoff[];
  runtimeStatus?: RuntimeStatusResponse;
  onOpenTask?: (taskId: string) => void;
}

const COMPLETE = new Set(['completed', 'completed_verified', 'completed_unverified']);

export default function BottomConsole({ goalId, tasks = [], handoffs = [], runtimeStatus, onOpenTask }: BottomConsoleProps) {
  const [expanded, setExpanded] = useState(false);
  const [filters, setFilters] = useState<LogFiltersType>({ page_size: 50 });
  const allFilters = goalId ? { ...filters, goal_id: goalId } : filters;
  // V1.0-P1-1: SSE drives real-time updates; polling is only a safety
  // fallback (10s) for when the SSE connection drops.
  const { isConnected: isSseConnected, lastEventAt } = useRuntimeEvents(goalId ?? null);
  const pollInterval = expanded && !isSseConnected ? 10_000 : false;
  const { data: logsData } = useQuery({ queryKey: ['workspace-logs', allFilters], queryFn: () => getLogs(allFilters), enabled: !!goalId && expanded, refetchInterval: pollInterval });

  const completed = tasks.filter((task) => COMPLETE.has(task.status)).length;
  const running = tasks.filter((task) => task.status === 'running').length;
  const waiting = tasks.filter((task) => ['pending', 'ready', 'assigned', 'waiting_tool', 'waiting_approval'].includes(task.status)).length;
  const errors = tasks.filter((task) => ['failed', 'blocked'].includes(task.status)).length;
  const latestUpdate = tasks.map((task) => task.updated_at).filter(Boolean).sort().at(-1);
  const lastUpdateLabel = (() => {
    // Prefer the most-recent event timestamp (SSE-driven) so the chip
    // updates within 1s of a backend state change. Fall back to the
    // task's own updated_at if we haven't received any SSE event yet.
    if (lastEventAt) return new Date(lastEventAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    if (latestUpdate) return new Date(latestUpdate).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    return '—';
  })();

  return (
    <section className={cn('border-t border-stone-200 bg-white', expanded ? 'shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)]' : '')}>
      <button
        type="button"
        onClick={() => setExpanded((value) => !value)}
        className="flex w-full items-center justify-between gap-3 px-4 py-2 text-left transition-colors hover:bg-stone-50"
        aria-expanded={expanded}
        aria-label={expanded ? '收起 Console summary' : '展开 Console summary'}
      >
        <span className="flex items-center gap-2 text-sm font-semibold text-stone-800">
          <TerminalSquare size={16} className="text-stone-500" />
          Console summary
          {/* V1.0-P1-1 SSE health chip */}
          {goalId ? (
            <span
              className={cn(
                'inline-flex items-center gap-1 rounded-full px-1.5 py-0.5 text-[10px] font-medium',
                isSseConnected
                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                  : 'bg-stone-100 text-stone-500 border border-stone-200',
              )}
              title={
                isSseConnected
                  ? 'SSE live: backend pushes state transitions within 1s'
                  : 'SSE disconnected: polling every 10s as fallback'
              }
              data-testid="sse-health-chip"
            >
              {isSseConnected ? <Radio size={9} className="text-emerald-600" /> : <RadioTower size={9} className="text-stone-400" />}
              {isSseConnected ? 'live' : 'poll'}
            </span>
          ) : null}
        </span>
        {expanded ? <ChevronDown size={17} className="text-stone-500" /> : <ChevronUp size={17} className="text-stone-500" />}
      </button>
      <div className="grid grid-cols-6 gap-1 border-t border-stone-200 px-2 py-1.5 text-[10px]">
        <ConsoleMetric label="Tasks Completed" value={`${completed} / ${tasks.length}`} />
        <ConsoleMetric label="In Progress" value={running} />
        <ConsoleMetric label="Waiting" value={waiting} />
        <ConsoleMetric label="Handoffs" value={handoffs.length} />
        <ConsoleMetric label="Errors" value={errors} danger={errors > 0} />
        <ConsoleMetric label="Last Update" value={lastUpdateLabel} wide />
      </div>
      {expanded ? <div className="border-t border-stone-200">
        {runtimeStatus ? <div className="border-b border-stone-200 p-3" data-testid="workspace-final-output">
          <FinalOutputPanel
            output={runtimeStatus.final_output}
            status={runtimeStatus.goal_status}
            tasksCompleted={runtimeStatus.completed_tasks}
            tasksFailed={runtimeStatus.failed_tasks}
            tasksHandoff={runtimeStatus.handoff_tasks}
            tasksTotal={runtimeStatus.total_tasks}
            totalTokens={runtimeStatus.total_tokens_used}
            logCount={runtimeStatus.log_count}
            finalSummary={runtimeStatus.final_summary}
            taskOutputs={tasks.filter((task) => task.output).map((task) => ({ id: task.id, title: task.title, output: task.output! }))}
            onOpenTask={onOpenTask}
          />
        </div> : null}
        <div className="console-log-filters"><LogFilters filters={filters} onChange={setFilters} /></div>
        <div className="console-log-list">
          {logsData?.items.map((log) => <LogListItem key={log.id} log={log} />)}
          {!goalId ? <p>启动 Goal 后此处显示实时执行日志。</p> : null}
          {goalId && logsData?.items.length === 0 ? <p>暂无日志</p> : null}
        </div>
      </div> : null}
    </section>
  );
}

function ConsoleMetric({ label, value, danger = false, wide = false }: { label: string; value: string | number; danger?: boolean; wide?: boolean }) {
  return (
    <div className={cn('flex flex-col gap-0.5 rounded px-2 py-1', wide ? 'col-span-2' : '')}>
      <span className="text-[9px] uppercase tracking-wider text-stone-500">{label}</span>
      <strong className={cn('text-sm font-semibold tabular-nums', danger ? 'text-red-600' : 'text-stone-900')}>
        {value}
      </strong>
    </div>
  );
}
