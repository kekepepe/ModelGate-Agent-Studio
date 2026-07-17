import { Box, ChevronDown, Download, Pause, Play, Square, Users } from 'lucide-react';
import type { Goal, WorkspaceTask } from '../types/workspace';
import { GOAL_STATUS_LABELS } from '../types/workspace';
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
  showWhenEmpty?: boolean;
}

export default function TopStatusBar({
  goal,
  tasks = [],
  teamName = 'Team Acme',
  teamVersion = 'v1.2.3',
  mode,
  onModeChange,
  onExecute,
  onPause,
  onResume,
  onStop,
  onExport,
  isBusy = false,
  showWhenEmpty = false,
}: TopStatusBarProps) {
  if (!goal && !showWhenEmpty) return null;
  const completedCount = tasks.filter((task) => ['completed', 'completed_verified', 'completed_unverified'].includes(task.status)).length;
  const totalTokens = tasks.reduce((sum, task) => sum + (task.tokens_used || 0), 0);
  const tokenLimit = goal?.budget_tokens || 100_000;
  const usagePercent = Math.min(100, Math.round((totalTokens / Math.max(1, tokenLimit)) * 100));
  const activeAgents = new Set(tasks.filter((task) => task.assigned_agent_id).map((task) => task.assigned_agent_id)).size;
  const statusLabel = goal ? (GOAL_STATUS_LABELS[goal.status] || goal.status) : 'Ready';
  const isRunning = goal?.status === 'running';

  return (
    <header className="workspace-header shrink-0 bg-white">
      <span className="sr-only">进度: {completedCount}/{tasks.length} Tasks</span>
      <div className="workspace-brand-row">
        <div className="workspace-brand">
          <span className="workspace-logo"><Box size={18} strokeWidth={2.2} /></span>
          <span>ModelGate</span>
        </div>
        <div className="workspace-header-divider" />
        <button type="button" className="workspace-team-button">
          <span>{teamName}</span><span className="workspace-version">{teamVersion}</span><ChevronDown size={12} />
        </button>
        <div className="workspace-header-divider" />
        <p className="workspace-goal-title"><strong>Goal:</strong> {goal?.title || 'Create a goal to start the workspace'}</p>
        <span className={`workspace-run-status workspace-run-status--${goal?.status || 'idle'}`}><i />{statusLabel}</span>
        <div className="workspace-header-divider workspace-header-divider--desktop" />
        <div className="workspace-active-agents"><Users size={15} /><span>{activeAgents || 0} Agents Active</span></div>
        <div className="workspace-header-divider workspace-header-divider--desktop" />
        <div className="workspace-quota">
          <div className="workspace-quota-copy"><span>Quota</span><strong>{usagePercent}%</strong></div>
          <div className="workspace-quota-track"><span style={{ width: `${usagePercent}%` }} /></div>
          <small>{totalTokens.toLocaleString()} / {tokenLimit.toLocaleString()} tokens</small>
        </div>
      </div>

      <div className="workspace-control-row">
        {mode && onModeChange ? <WorkspaceModeSwitch mode={mode} onChange={onModeChange} /> : <span />}
        <div className="workspace-run-controls">
          {goal?.status === 'planning' ? <ActionButton label="Run" onClick={onExecute} disabled={!onExecute || isBusy}><Play size={13} fill="currentColor" /></ActionButton> : null}
          <ActionButton label="Pause" onClick={onPause} disabled={!isRunning || !onPause || isBusy}><Pause size={13} fill="currentColor" /></ActionButton>
          <ActionButton label="Resume" onClick={onResume} disabled={goal?.status !== 'paused' || !onResume || isBusy} primary><Play size={13} fill="currentColor" /></ActionButton>
          <ActionButton label="Stop" onClick={onStop} disabled={!onStop || isBusy} danger><Square size={11} fill="currentColor" /></ActionButton>
          <ActionButton label="Export" onClick={onExport} disabled={!onExport}><Download size={13} /></ActionButton>
        </div>
      </div>
    </header>
  );
}

function ActionButton({ label, children, onClick, disabled, danger = false, primary = false }: { label: string; children: React.ReactNode; onClick?: () => void; disabled?: boolean; danger?: boolean; primary?: boolean }) {
  const variant = danger ? 'workspace-action--danger' : primary ? 'workspace-action--primary' : '';
  return <button type="button" onClick={onClick} disabled={disabled} className={`workspace-action ${variant}`}>{children}<span>{label}</span></button>;
}
