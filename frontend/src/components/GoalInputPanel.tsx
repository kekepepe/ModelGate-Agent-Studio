import { Check, CheckSquare2, FileText, Pencil, Settings2 } from 'lucide-react';
import { useState } from 'react';
import { useCreateGoal, useStartGoal } from '../hooks/useWorkspace';
import type { TeamPreset } from '../types/team';
import type { Goal } from '../types/workspace';

interface GoalInputPanelProps {
  onGoalCreated: (goalId: string) => void;
  activeGoalId?: string | null;
  goalTitle?: string | null;
  goal?: Goal | null;
  preset?: TeamPreset;
}

export default function GoalInputPanel({ onGoalCreated, activeGoalId, goalTitle, goal, preset }: GoalInputPanelProps) {
  const [title, setTitle] = useState(preset?.defaultGoal || '');
  const [description, setDescription] = useState('');
  const [executionMode, setExecutionMode] = useState<'live' | 'sandbox' | 'dry_run' | 'mock'>('live');
  const [budgetTokens, setBudgetTokens] = useState(100000);
  const [maxDurationSeconds, setMaxDurationSeconds] = useState(3600);
  const [error, setError] = useState<string | null>(null);
  const [showRunConfig, setShowRunConfig] = useState(false);
  const [autoHandoff, setAutoHandoff] = useState(true);
  const [autoModelSwitch, setAutoModelSwitch] = useState(true);
  const createGoal = useCreateGoal();
  const startGoal = useStartGoal();

  const isSubmitting = createGoal.isPending || startGoal.isPending;
  const isValid = title.trim().length > 0;
  const handleStart = async () => {
    if (!isValid) return;
    setError(null);
    try {
      const result = await createGoal.mutateAsync({ title: title.trim(), description: description.trim() || undefined, executionMode, budgetTokens, maxDurationSeconds, teamPreset: preset?.id });
      const startResult = await startGoal.mutateAsync(result.goal_id);
      onGoalCreated(startResult.goal_id);
    } catch {
      setError('创建失败，请重试');
    }
  };

  if (activeGoalId) {
    return (
      <div className="workspace-sidebar-sections">
        <SidebarSection icon={<FileText size={16} />} title="Goal" action={<Pencil size={13} />}>
          <p className="sidebar-goal-copy">{goalTitle || 'Untitled'}</p>
          <span className="sr-only">{activeGoalId}</span>
        </SidebarSection>
        <SidebarSection icon={<CheckSquare2 size={16} />} title="Completion criteria">
          <ul className="sidebar-criteria">
            {(preset?.defaultCriteria || ['完成目标要求', '输出可验证', '审查通过']).map((criterion) => <li key={criterion}><Check size={12} />{criterion}</li>)}
          </ul>
        </SidebarSection>
        <SidebarSection icon={<Settings2 size={17} />} title="Run config">
          <dl className="sidebar-config-grid">
            <dt>Mode</dt><dd>Auto · smallest safe path</dd>
            <dt>Max Parallel Agents</dt><dd>{preset?.executionPolicy.maxParallel || 3}</dd>
            <dt>Model Routing</dt><dd>Auto</dd>
            <dt>Max Tokens (Run)</dt><dd>{(goal?.budget_tokens || 100000).toLocaleString()}</dd>
            <dt>Temperature</dt><dd>0.3</dd>
            <dt>Retry Policy</dt><dd>2 retries</dd>
          </dl>
          <button type="button" className="sidebar-text-link">View all config</button>
        </SidebarSection>
      </div>
    );
  }

  return (
    <div className="workspace-setup-panel">
      <div className="workspace-setup-heading"><FileText size={16} /><span>Goal</span></div>
      {preset ? <p className="workspace-setup-team">{preset.name} · capability pool: {preset.capabilities.join(', ')}</p> : null}
      <textarea value={title} onChange={(event) => setTitle(event.target.value)} placeholder="描述你的目标..." rows={3} disabled={isSubmitting} />
      <input type="text" value={description} onChange={(event) => setDescription(event.target.value)} placeholder="补充说明（可选）" disabled={isSubmitting} />
      {preset?.defaultCriteria?.length ? <ul className="sidebar-criteria workspace-setup-criteria">{preset.defaultCriteria.map((criterion) => <li key={criterion}><Check size={12} />{criterion}</li>)}</ul> : null}
      <button type="button" onClick={() => setShowRunConfig((value) => !value)} className="workspace-config-toggle"><Settings2 size={14} />Run Config<span>{showRunConfig ? '收起' : '展开'}</span></button>
      {showRunConfig ? <div className="workspace-config-form">
        <select value={executionMode} onChange={(event) => setExecutionMode(event.target.value as typeof executionMode)} disabled={isSubmitting}>
          <option value="live">Live · 真实模型与工具</option><option value="sandbox">Sandbox · 受控工作区</option><option value="dry_run">Dry Run · 禁止写入</option><option value="mock">Mock · 演示/测试</option>
        </select>
        <RunToggle label="Auto Handoff" value={autoHandoff} onChange={setAutoHandoff} />
        <RunToggle label="Auto Model Switch" value={autoModelSwitch} onChange={setAutoModelSwitch} />
        <label>Token 预算<input type="number" min={1} value={budgetTokens} onChange={(event) => setBudgetTokens(Math.max(1, Number(event.target.value) || 1))} /></label>
        <label>最长时长（秒）<input type="number" min={1} value={maxDurationSeconds} onChange={(event) => setMaxDurationSeconds(Math.max(1, Number(event.target.value) || 1))} /></label>
      </div> : null}
      <button type="button" aria-label="开始" onClick={handleStart} disabled={!isValid || isSubmitting} className="workspace-start-button">{isSubmitting ? '创建中...' : '创建并规划'}</button>
      {error ? <p className="workspace-error">{error}</p> : null}
    </div>
  );
}

function SidebarSection({ icon, title, action, children }: { icon: React.ReactNode; title: string; action?: React.ReactNode; children: React.ReactNode }) {
  return <section className="sidebar-section"><header><span className="sidebar-section-icon">{icon}</span><h3>{title}</h3>{action ? <button type="button" aria-label={`Edit ${title}`}>{action}</button> : null}</header>{children}</section>;
}

function RunToggle({ label, value, onChange }: { label: string; value: boolean; onChange: (value: boolean) => void }) {
  return <label className="workspace-run-toggle"><span>{label}</span><input type="checkbox" checked={value} onChange={(event) => onChange(event.target.checked)} /></label>;
}
