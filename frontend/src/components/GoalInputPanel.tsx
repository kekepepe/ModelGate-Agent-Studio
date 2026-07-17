import { useState } from 'react';
import { useCreateGoal, useStartGoal } from '../hooks/useWorkspace';
import type { TeamPreset } from '../types/team';

interface GoalInputPanelProps {
  onGoalCreated: (goalId: string) => void;
  activeGoalId?: string | null;
  goalTitle?: string | null;
  preset?: TeamPreset;
}

export default function GoalInputPanel({ onGoalCreated, activeGoalId, goalTitle, preset }: GoalInputPanelProps) {
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
      const result = await createGoal.mutateAsync({
        title: title.trim(), description: description.trim() || undefined, executionMode,
        budgetTokens, maxDurationSeconds, teamPreset: preset?.id,
      });
      const startResult = await startGoal.mutateAsync(result.goal_id);
      onGoalCreated(startResult.goal_id);
    } catch {
      setError('创建失败，请重试');
    }
  };

  if (activeGoalId) {
    return (
      <div className="p-4 border-b border-stone-200">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-stone-400 mb-2">当前 Goal</h3>
        <p className="text-sm font-medium text-stone-800 mb-1 truncate">{goalTitle || 'Untitled'}</p>
        <p className="text-xs text-stone-400 font-mono truncate">{activeGoalId}</p>
      </div>
    );
  }

  return (
    <div className="p-4 border-b border-stone-200">
      {preset ? (
        <div className="mb-4 rounded-lg border border-blue-100 bg-blue-50/60 px-3 py-2">
          <p className="text-[10px] font-semibold uppercase tracking-wide text-blue-600">Team preset</p>
          <p className="mt-0.5 text-sm font-semibold text-stone-800">{preset.name}</p>
          <p className="mt-1 line-clamp-2 text-[11px] leading-4 text-stone-500">{preset.roles.map((role) => role.label).join(' → ')}</p>
        </div>
      ) : null}
      <h3 className="text-xs font-semibold uppercase tracking-wide text-stone-400 mb-3">Goal</h3>
      <textarea
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="描述你的目标..."
        rows={4}
        className="w-full px-3 py-2 text-sm border border-stone-200 rounded-lg resize-none focus:outline-none focus:ring-1 focus:ring-stone-400 mb-2"
        disabled={isSubmitting}
      />
      <input
        type="text"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        placeholder="补充说明（可选）"
        className="w-full px-3 py-1.5 text-sm border border-stone-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-stone-400 mb-3"
        disabled={isSubmitting}
      />
      {preset?.defaultCriteria?.length ? (
        <div className="mb-3 rounded-lg border border-stone-200 bg-stone-50 px-3 py-2">
          <p className="text-[10px] font-semibold uppercase tracking-wide text-stone-400">Completion criteria</p>
          <ul className="mt-1.5 space-y-1 text-[11px] text-stone-600">{preset.defaultCriteria.map((criterion) => <li key={criterion}>✓ {criterion}</li>)}</ul>
        </div>
      ) : null}
      <button type="button" onClick={() => setShowRunConfig((value) => !value)} className="mb-3 flex w-full items-center justify-between rounded-lg border border-stone-200 bg-white px-3 py-2 text-xs font-medium text-stone-600 hover:bg-stone-50">
        Run Config <span className="text-stone-400">{showRunConfig ? '收起' : '展开'}</span>
      </button>
      {showRunConfig ? <div className="mb-3 space-y-3 rounded-lg border border-stone-200 bg-stone-50 p-3">
        <select value={executionMode} onChange={(e) => setExecutionMode(e.target.value as typeof executionMode)} disabled={isSubmitting}
          className="w-full rounded-lg border border-stone-200 bg-white px-3 py-1.5 text-xs">
          <option value="live">Live · 真实模型与工具</option>
          <option value="sandbox">Sandbox · 受控工作区</option>
          <option value="dry_run">Dry Run · 禁止写入</option>
          <option value="mock">Mock · 仅演示/测试</option>
        </select>
        <RunToggle label="Auto Handoff" value={autoHandoff} onChange={setAutoHandoff} />
        <RunToggle label="Auto Model Switch" value={autoModelSwitch} onChange={setAutoModelSwitch} />
      <div className="grid grid-cols-2 gap-2">
        <label className="text-xs text-stone-500">Run Token 预算
          <input type="number" min={1} value={budgetTokens} onChange={(e) => setBudgetTokens(Math.max(1, Number(e.target.value) || 1))}
            disabled={isSubmitting} className="mt-1 w-full px-2 py-1.5 text-sm border border-stone-200 rounded-lg" />
        </label>
        <label className="text-xs text-stone-500">最长时长（秒）
          <input type="number" min={1} value={maxDurationSeconds} onChange={(e) => setMaxDurationSeconds(Math.max(1, Number(e.target.value) || 1))}
            disabled={isSubmitting} className="mt-1 w-full px-2 py-1.5 text-sm border border-stone-200 rounded-lg" />
        </label>
      </div>
      </div> : null}
      <button
        onClick={handleStart}
        disabled={!isValid || isSubmitting}
        className="w-full py-2 text-sm font-medium bg-stone-800 text-white rounded-lg hover:bg-stone-900 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
      >
        {isSubmitting ? '创建中...' : '开始'}
      </button>
      {error && <p className="text-xs text-red-600 mt-2">{error}</p>}
    </div>
  );
}

function RunToggle({ label, value, onChange }: { label: string; value: boolean; onChange: (value: boolean) => void }) {
  return (
    <label className="flex items-center justify-between text-xs text-stone-600">
      {label}
      <input type="checkbox" checked={value} onChange={(event) => onChange(event.target.checked)} className="rounded border-stone-300" />
    </label>
  );
}
