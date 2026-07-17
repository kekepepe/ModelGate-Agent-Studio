import { Download, Pause, Play, Square } from 'lucide-react';
import type { Goal, WorkspaceTask } from '../types/workspace';
import { GOAL_STATUS_LABELS, GOAL_STATUS_COLORS } from '../types/workspace';
import type { WorkspaceViewMode } from '../utils/workspaceViewModel';
import WorkspaceModeSwitch from './WorkspaceModeSwitch';

interface TopStatusBarProps {
  goal?: Goal | null;
  tasks?: WorkspaceTask[];
  teamName?: string;
  teamVersion?: string;
  mode?: WorkspaceViewMode;
  onModeChange?: (mode: WorkspaceViewMode) => void;
  onExecute?: () => void;
  onPause?: () => void;
  onResume?: () => void;
  onStop?: () => void;
  onExport?: () => void;
  isBusy?: boolean;
}

export default function TopStatusBar({
  goal,
  tasks = [],
  teamName,
  teamVersion = 'Preset',
  mode,
  onModeChange,
  onExecute,
  onPause,
  onResume,
  onStop,
  onExport,
  isBusy = false,
}: TopStatusBarProps) {
  if (!goal) return null;

  const completedCount = tasks.filter((task) => ['completed', 'completed_verified', 'completed_unverified'].includes(task.status)).length;
  const totalCount = tasks.length;
  const runningCount = tasks.filter((t) => t.status === 'running').length;
  const handoffCount = tasks.filter((t) => t.status === 'handoff').length;
  const totalTokens = tasks.reduce((sum, t) => sum + (t.tokens_used || 0), 0);

  const statusColor = GOAL_STATUS_COLORS[goal.status] || GOAL_STATUS_COLORS.idle;
  const statusLabel = GOAL_STATUS_LABELS[goal.status] || goal.status;

  return (
    <div className="border-b border-stone-200 bg-white px-4 py-2.5 sm:px-5">
      <div className="flex max-w-full flex-wrap items-center justify-between gap-3">
        <div className="flex min-w-0 items-center gap-3">
          {teamName ? (
            <div className="hidden border-r border-stone-200 pr-3 sm:block">
              <p className="text-[10px] font-semibold uppercase tracking-wide text-stone-400">Team · {teamVersion}</p>
              <p className="max-w-40 truncate text-xs font-medium text-stone-700">{teamName}</p>
            </div>
          ) : null}
          <h1 className="max-w-md truncate text-sm font-semibold text-stone-900">
            Goal: {goal.title}
          </h1>
          <span className={`inline-flex items-center px-2 py-0.5 text-xs font-medium rounded-full border transition-colors duration-300 ${statusColor}`}>
            {statusLabel}
          </span>
        </div>
        <div className="flex shrink-0 items-center gap-3 text-xs text-stone-500">
          <span>进度: {completedCount}/{totalCount} Tasks</span>
          {runningCount > 0 && <span className="text-blue-600">{runningCount} 运行中</span>}
          {handoffCount > 0 && <span className="text-purple-600">{handoffCount} 交接中</span>}
          <span>Token: {totalTokens.toLocaleString()}</span>
          {mode && onModeChange ? <WorkspaceModeSwitch mode={mode} onChange={onModeChange} /> : null}
          <div className="flex items-center gap-1 border-l border-stone-200 pl-3">
            {goal.status === 'paused' ? (
              <ActionButton label="恢复" onClick={onResume} disabled={!onResume || isBusy}><Play size={13} fill="currentColor" /></ActionButton>
            ) : goal.status === 'planning' ? (
              <ActionButton label="执行" onClick={onExecute} disabled={isBusy || !onExecute}>
                <Play size={13} fill="currentColor" />
              </ActionButton>
            ) : goal.status === 'running' ? (
              <ActionButton label="暂停" onClick={onPause} disabled={isBusy || !onPause}><Pause size={13} /></ActionButton>
            ) : null}
            {onStop ? <ActionButton label="停止" onClick={onStop} disabled={isBusy} danger><Square size={12} fill="currentColor" /></ActionButton> : null}
            <ActionButton label="导出" onClick={onExport} disabled={!onExport}><Download size={13} /></ActionButton>
          </div>
        </div>
      </div>
    </div>
  );
}

function ActionButton({ label, children, onClick, disabled, danger = false }: { label: string; children: React.ReactNode; onClick?: () => void; disabled?: boolean; danger?: boolean }) {
  return (
    <button type="button" onClick={onClick} disabled={disabled} className={`inline-flex items-center gap-1 rounded-md border px-2 py-1.5 text-[11px] font-medium disabled:cursor-not-allowed disabled:opacity-35 ${danger ? 'border-red-200 text-red-600 hover:bg-red-50' : 'border-stone-200 text-stone-600 hover:bg-stone-50'}`}>
      {children} {label}
    </button>
  );
}
