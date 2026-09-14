import { Check, CheckSquare2, FileText, Pencil, Settings2 } from 'lucide-react';
import { useState } from 'react';
import { useCreateGoal, useStartGoal } from '../hooks/useWorkspace';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { Button } from './ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select';
import type { TeamPreset } from '../types/team';
import type { Goal } from '../types/workspace';

interface GoalInputPanelProps {
  onGoalCreated: (goalId: string, runId: string) => void;
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
      onGoalCreated(startResult.goal_id, startResult.run_id || result.run_id);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : '创建失败，请重试');
    }
  };

  if (activeGoalId) {
    return (
      <div className="divide-y divide-stone-200">
        <SidebarSection icon={<FileText size={16} />} title="Goal" action={<Pencil size={13} />}>
          <p className="truncate text-sm text-stone-700">{goalTitle || 'Untitled'}</p>
          <span className="sr-only">{activeGoalId}</span>
        </SidebarSection>
        <SidebarSection icon={<CheckSquare2 size={16} />} title="Completion criteria">
          <ul className="space-y-1 text-[11px] text-stone-600">
            {(preset?.defaultCriteria || ['完成目标要求', '输出可验证', '审查通过']).map((criterion) => (
              <li key={criterion} className="flex items-center gap-1.5">
                <Check size={12} className="text-emerald-600" />
                {criterion}
              </li>
            ))}
          </ul>
        </SidebarSection>
        <SidebarSection icon={<Settings2 size={17} />} title="Run config">
          <dl className="grid grid-cols-[max-content_1fr] gap-x-2 gap-y-0.5 text-[10px] text-stone-500">
            <dt className="font-medium text-stone-600">Mode</dt><dd>Auto · smallest safe path</dd>
            <dt className="font-medium text-stone-600">Max Parallel Agents</dt><dd>{preset?.executionPolicy.maxParallel || 3}</dd>
            <dt className="font-medium text-stone-600">Model Routing</dt><dd>Auto</dd>
            <dt className="font-medium text-stone-600">Max Tokens (Run)</dt><dd>{(goal?.budget_tokens || 100000).toLocaleString()}</dd>
            <dt className="font-medium text-stone-600">Temperature</dt><dd>0.3</dd>
            <dt className="font-medium text-stone-600">Retry Policy</dt><dd>2 retries</dd>
          </dl>
          <Button variant="link" size="sm" className="h-auto p-0 text-[11px]">View all config</Button>
        </SidebarSection>
      </div>
    );
  }

  return (
    <div className="space-y-3 p-3">
      <div className="flex items-center gap-2 text-sm font-semibold text-stone-800">
        <FileText size={15} aria-hidden />
        <span>Goal</span>
      </div>
      {preset ? (
        <p className="text-[11px] text-stone-500">
          {preset.name} · capability pool: {preset.capabilities.join(', ')}
        </p>
      ) : null}
      <Textarea
        value={title}
        onChange={(event) => setTitle(event.target.value)}
        placeholder="描述你的目标..."
        rows={3}
        disabled={isSubmitting}
        className="resize-none"
      />
      <Input
        type="text"
        value={description}
        onChange={(event) => setDescription(event.target.value)}
        placeholder="补充说明（可选）"
        disabled={isSubmitting}
      />
      {preset?.defaultCriteria?.length ? (
        <ul className="space-y-1 text-[11px] text-stone-600">
          {preset.defaultCriteria.map((criterion) => (
            <li key={criterion} className="flex items-center gap-1.5">
              <Check size={12} className="text-emerald-600" />
              {criterion}
            </li>
          ))}
        </ul>
      ) : null}
      <Button
        type="button"
        onClick={() => setShowRunConfig((value) => !value)}
        variant="outline"
        size="sm"
        className="w-full justify-between"
      >
        <span className="flex items-center gap-1.5">
          <Settings2 size={14} />Run Config
        </span>
        <span>{showRunConfig ? '收起' : '展开'}</span>
      </Button>
      {showRunConfig ? (
        <div className="space-y-2">
          <Select
            value={executionMode}
            onValueChange={(v) => setExecutionMode(v as typeof executionMode)}
            disabled={isSubmitting}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="live">Live · 真实模型与工具</SelectItem>
              <SelectItem value="sandbox">Sandbox · 受控工作区</SelectItem>
              <SelectItem value="dry_run">Dry Run · 禁止写入</SelectItem>
              <SelectItem value="mock">Mock · 演示/测试</SelectItem>
            </SelectContent>
          </Select>
          <RunToggle label="Auto Handoff" value={autoHandoff} onChange={setAutoHandoff} />
          <RunToggle label="Auto Model Switch" value={autoModelSwitch} onChange={setAutoModelSwitch} />
          <label className="flex flex-col gap-1 text-[11px] text-stone-600">
            Token 预算
            <Input
              type="number"
              min={1}
              value={budgetTokens}
              onChange={(event) => setBudgetTokens(Math.max(1, Number(event.target.value) || 1))}
            />
          </label>
          <label className="flex flex-col gap-1 text-[11px] text-stone-600">
            最长时长（秒）
            <Input
              type="number"
              min={1}
              value={maxDurationSeconds}
              onChange={(event) => setMaxDurationSeconds(Math.max(1, Number(event.target.value) || 1))}
            />
          </label>
        </div>
      ) : null}
      <Button
        type="button"
        aria-label="开始"
        onClick={handleStart}
        disabled={!isValid || isSubmitting}
        className="w-full"
      >
        {isSubmitting ? '创建中...' : '创建并规划'}
      </Button>
      {error ? <p className="text-xs text-red-600">{error}</p> : null}
    </div>
  );
}

function SidebarSection({ icon, title, action, children }: { icon: React.ReactNode; title: string; action?: React.ReactNode; children: React.ReactNode }) {
  return (
    <section className="p-3">
      <header className="mb-2 flex items-center justify-between gap-2">
        <span className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-stone-700">
          {icon}
          <h3>{title}</h3>
        </span>
        {action ? (
          <button
            type="button"
            aria-label={`Edit ${title}`}
            className="rounded p-1 text-stone-400 hover:bg-stone-100 hover:text-stone-700"
          >
            {action}
          </button>
        ) : null}
      </header>
      {children}
    </section>
  );
}

function RunToggle({ label, value, onChange }: { label: string; value: boolean; onChange: (value: boolean) => void }) {
  return (
    <label className="flex items-center justify-between gap-2 rounded border border-stone-200 bg-white px-2 py-1 text-[11px] text-stone-700">
      <span>{label}</span>
      <input
        type="checkbox"
        checked={value}
        onChange={(event) => onChange(event.target.checked)}
        className="h-3.5 w-3.5 accent-blue-600"
      />
    </label>
  );
}
