import { ArrowLeft, Download, ExternalLink, FileClock, FolderOpen, Pause, Play, Square, Users } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { Goal, MultiAgentMetrics, WorkspaceTask } from '../../types/workspace';
import type { WorkspaceViewMode } from '../../utils/workspaceViewModel';
import WorkspaceModeSwitch from '../WorkspaceModeSwitch';
import RunStatusBadge from './RunStatusBadge';

interface Props {
  runId: string;
  goal: Goal;
  tasks: WorkspaceTask[];
  teamName: string;
  mode: WorkspaceViewMode;
  onModeChange: (mode: WorkspaceViewMode) => void;
  onExecute?: () => void;
  onPause?: () => void;
  onResume?: () => void;
  onStop?: () => void;
  onExport?: () => void;
  isBusy?: boolean;
  metrics?: MultiAgentMetrics | null;
}

export default function WorkspaceRunHeader({ runId, goal, tasks, teamName, mode, onModeChange, onExecute, onPause, onResume, onStop, onExport, isBusy, metrics }: Props) {
  const totalTokens = tasks.reduce((sum, task) => sum + (task.tokens_used || 0), 0);
  const quota = Math.min(100, Math.round(totalTokens / Math.max(goal.budget_tokens || 1, 1) * 100));
  const activeAgents = metrics?.active_agent_count ?? new Set(tasks.filter((task) => ['assigned', 'running', 'handoff'].includes(task.status)).map((task) => task.assigned_agent_id).filter(Boolean)).size;
  const canPause = ['planning', 'running', 'reviewing'].includes(goal.status);
  const canResume = goal.status === 'paused';
  const canStop = !['completed', 'failed', 'cancelled'].includes(goal.status);

  const confirmStop = () => {
    if (onStop && window.confirm('停止后，当前未完成的 Task 将被取消。确定停止这个 Run 吗？')) onStop();
  };

  return (
    <section className="shrink-0 border-b border-stone-200 bg-white px-4 py-3 sm:px-6" aria-label="Workspace run header">
      <div className="mx-auto flex max-w-[1600px] flex-wrap items-start gap-x-5 gap-y-3">
        <div className="min-w-0 flex-1">
          <div className="mb-1 flex items-center gap-2 text-xs text-stone-500">
            <Link to="/workspace" className="inline-flex items-center gap-1 hover:text-stone-900"><ArrowLeft size={13} /> Workspace</Link>
            <span>/</span><Link to="/studio" className="hover:text-stone-900">Studio</Link><span>/</span>
            <span className="truncate">{teamName}</span><span>/</span><span className="font-mono">{runId.slice(0, 12)}</span>
          </div>
          <div className="flex min-w-0 items-center gap-3">
            <h1 className="truncate text-base font-semibold text-stone-900">{goal.title}</h1>
            <RunStatusBadge status={goal.status} />
          </div>
          <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-xs text-stone-500">
            <span className="inline-flex items-center gap-1"><Users size={13} />{activeAgents} Agents Active</span>
            <span>{metrics?.active_parallelism || 0}× parallel</span>
            <span>{totalTokens.toLocaleString()} / {(goal.budget_tokens || 0).toLocaleString()} tokens · Quota {quota}%</span>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Link to={`/logs?runId=${encodeURIComponent(runId)}&goalId=${encodeURIComponent(goal.id)}`} className="run-header-link"><FileClock size={13} />Logs</Link>
          <Link to={`/evolution?runId=${encodeURIComponent(runId)}&goalId=${encodeURIComponent(goal.id)}`} className="run-header-link"><ExternalLink size={13} />Evolution</Link>
          <Link to={`/assets?runId=${encodeURIComponent(runId)}`} className="run-header-link"><FolderOpen size={13} />Assets</Link>
        </div>
      </div>
      <div className="mx-auto mt-3 flex max-w-[1600px] items-center justify-between gap-4 border-t border-stone-100 pt-3">
        <WorkspaceModeSwitch mode={mode} onChange={onModeChange} />
        <div className="flex items-center gap-2">
          {goal.status === 'planning' ? <HeaderButton label="Run" onClick={onExecute} disabled={!onExecute || isBusy}><Play size={13} /></HeaderButton> : null}
          <HeaderButton label="Pause" onClick={onPause} disabled={!canPause || !onPause || isBusy}><Pause size={13} /></HeaderButton>
          <HeaderButton label="Resume" onClick={onResume} disabled={!canResume || !onResume || isBusy}><Play size={13} /></HeaderButton>
          <HeaderButton label="Stop" onClick={confirmStop} disabled={!canStop || !onStop || isBusy} danger><Square size={11} /></HeaderButton>
          <HeaderButton label="Export" onClick={onExport} disabled={!onExport}><Download size={13} /></HeaderButton>
        </div>
      </div>
    </section>
  );
}

function HeaderButton({ label, children, onClick, disabled, danger }: { label: string; children: React.ReactNode; onClick?: () => void; disabled?: boolean; danger?: boolean }) {
  return <button type="button" onClick={onClick} disabled={disabled} className={`inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1.5 text-xs font-medium disabled:cursor-not-allowed disabled:opacity-35 ${danger ? 'border-red-200 text-red-700 hover:bg-red-50' : 'border-stone-200 text-stone-700 hover:bg-stone-50'}`}>{children}{label}</button>;
}
