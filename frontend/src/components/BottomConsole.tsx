import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ChevronDown, ChevronUp, TerminalSquare } from 'lucide-react';
import LogListItem from './LogListItem';
import LogFilters from './LogFilters';
import { getLogs } from '../api/logs';
import type { LogFilters as LogFiltersType } from '../types/log';
import type { WorkspaceHandoff, WorkspaceTask } from '../types/workspace';

interface BottomConsoleProps {
  goalId?: string | null;
  tasks?: WorkspaceTask[];
  handoffs?: WorkspaceHandoff[];
}

const COMPLETE = new Set(['completed', 'completed_verified', 'completed_unverified']);

export default function BottomConsole({ goalId, tasks = [], handoffs = [] }: BottomConsoleProps) {
  const [expanded, setExpanded] = useState(false);
  const [filters, setFilters] = useState<LogFiltersType>({ page_size: 50 });
  const allFilters = goalId ? { ...filters, goal_id: goalId } : filters;
  const { data: logsData } = useQuery({ queryKey: ['workspace-logs', allFilters], queryFn: () => getLogs(allFilters), enabled: !!goalId && expanded, refetchInterval: expanded ? 2000 : false });

  const completed = tasks.filter((task) => COMPLETE.has(task.status)).length;
  const running = tasks.filter((task) => task.status === 'running').length;
  const waiting = tasks.filter((task) => ['pending', 'ready', 'assigned', 'waiting_tool', 'waiting_approval'].includes(task.status)).length;
  const errors = tasks.filter((task) => ['failed', 'blocked'].includes(task.status)).length;
  const latestUpdate = tasks.map((task) => task.updated_at).filter(Boolean).sort().at(-1);

  return (
    <section className={`console-summary ${expanded ? 'is-expanded' : ''}`}>
      <button type="button" onClick={() => setExpanded((value) => !value)} className="console-summary-heading" aria-expanded={expanded}>
        <span><TerminalSquare size={18} />Console summary</span>{expanded ? <ChevronDown size={17} /> : <ChevronUp size={17} />}
      </button>
      <div className="console-metrics">
        <ConsoleMetric label="Tasks Completed" value={`${completed} / ${tasks.length}`} />
        <ConsoleMetric label="In Progress" value={running} />
        <ConsoleMetric label="Waiting" value={waiting} />
        <ConsoleMetric label="Handoffs" value={handoffs.length} />
        <ConsoleMetric label="Errors" value={errors} danger={errors > 0} />
        <ConsoleMetric label="Last Update" value={latestUpdate ? new Date(latestUpdate).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '—'} wide />
      </div>
      {expanded ? <div className="console-log-drawer">
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
  return <div className={`console-metric ${wide ? 'console-metric--wide' : ''}`}><span>{label}</span><strong className={danger ? 'is-danger' : ''}>{value}</strong></div>;
}
