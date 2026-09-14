import { useState } from 'react';
import { Check, GitBranch, Pencil, RefreshCw, ShieldCheck, TriangleAlert } from 'lucide-react';
import { Card, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { cn } from '@/lib/utils';
import type { ExecutionPlan, PlanChange, PlanVersionSummary, WorkspaceState } from '../types/workspace';

interface PlanOverviewPanelProps {
  activePlan?: ExecutionPlan | null;
  versions?: PlanVersionSummary[];
  changes?: PlanChange[];
  completionEvidence?: WorkspaceState['completion_evidence'];
  onConfirm?: () => Promise<void> | void;
  onModify?: (objectives: string[]) => Promise<void> | void;
  onDowngrade?: () => Promise<void> | void;
  isMutating?: boolean;
  mutationError?: string | null;
}

const MODE_LABELS: Record<ExecutionPlan['task_mode'], string> = {
  direct: 'Direct',
  single_agent: 'Single Agent',
  sequential_multi_agent: 'Sequential Multi-Agent',
  parallel_multi_agent: 'Parallel Multi-Agent',
};

const MODE_TONES: Record<ExecutionPlan['task_mode'], string> = {
  direct: 'border-stone-200 bg-stone-50 text-stone-700',
  single_agent: 'border-blue-200 bg-blue-50 text-blue-700',
  sequential_multi_agent: 'border-indigo-200 bg-indigo-50 text-indigo-700',
  parallel_multi_agent: 'border-violet-200 bg-violet-50 text-violet-700',
};

export default function PlanOverviewPanel({
  activePlan,
  versions = [],
  changes = [],
  completionEvidence,
  onConfirm,
  onModify,
  onDowngrade,
  isMutating = false,
  mutationError,
}: PlanOverviewPanelProps) {
  const [editing, setEditing] = useState(false);
  const [draftObjectives, setDraftObjectives] = useState<string[]>([]);
  if (!activePlan) return null;
  const latestChange = changes.at(-1);
  const replanCount = changes.filter((change) => change.change_type === 'replan').length;
  const fallback = activePlan.planner_type === 'rule_fallback';
  const awaitingConfirmation = !activePlan.confirmed_at;

  const beginEdit = () => {
    setDraftObjectives(activePlan.tasks.map((task) => task.objective));
    setEditing(true);
  };

  const saveEdit = async () => {
    await onModify?.(draftObjectives);
    setEditing(false);
  };

  return (
    <Card aria-label="Active execution plan" className="gap-0 p-0">
      <CardContent className="space-y-3 p-3">
        {/* Heading */}
        <header className="flex items-center justify-between gap-2">
          <span className="flex items-center gap-1.5 text-sm font-semibold text-stone-800">
            <GitBranch size={15} aria-hidden />
            Execution plan
          </span>
          <Badge variant="secondary" className="px-1.5 py-0 text-[10px] font-mono">
            v{activePlan.version}
          </Badge>
        </header>

        {/* Mode + task count */}
        <div className="flex items-center justify-between text-[11px]">
          <Badge
            variant="outline"
            className={cn('px-1.5 py-0 text-[10px] font-normal', MODE_TONES[activePlan.task_mode])}
          >
            {MODE_LABELS[activePlan.task_mode]}
          </Badge>
          <span className="text-stone-500">{activePlan.tasks.length} active tasks</span>
        </div>

        {/* Activation reason */}
        <p className="text-[11px] leading-snug text-stone-600">
          {activePlan.activation_reason}
        </p>

        {/* Plan source */}
        <div
          className={cn(
            'flex items-center gap-1.5 rounded border px-2 py-1 text-[11px]',
            fallback
              ? 'border-amber-200 bg-amber-50 text-amber-800'
              : 'border-emerald-200 bg-emerald-50 text-emerald-800',
          )}
        >
          {fallback ? <TriangleAlert size={12} /> : <ShieldCheck size={12} />}
          <span>{fallback ? 'Rule fallback plan' : 'Model-generated plan'}</span>
        </div>

        {/* Version history */}
        <div className="flex items-center justify-between text-[10px] text-stone-500">
          <span>
            {versions.length} version{versions.length === 1 ? '' : 's'}
          </span>
          <span className="flex items-center gap-1">
            <RefreshCw size={10} />
            {replanCount} replan{replanCount === 1 ? '' : 's'}
          </span>
        </div>

        {/* Approval / edit area */}
        {awaitingConfirmation ? (
          <div className="space-y-2 rounded-md border border-amber-200 bg-amber-50/50 p-2">
            <p className="text-[11px] font-semibold text-amber-900">Review before execution</p>
            <p className="text-[10px] text-amber-800">This plan is active but cannot run until you confirm or modify it.</p>
            {editing ? (
              <div className="space-y-1.5">
                {draftObjectives.map((objective, index) => (
                  <label key={activePlan.tasks[index]?.client_task_id || index} className="block text-[10px] text-stone-600">
                    <small className="block text-stone-500">
                      {activePlan.tasks[index]?.client_task_id}
                    </small>
                    <Input
                      value={objective}
                      onChange={(event) =>
                        setDraftObjectives((current) =>
                          current.map((item, itemIndex) =>
                            itemIndex === index ? event.target.value : item,
                          ),
                        )
                      }
                    />
                  </label>
                ))}
                <div className="flex items-center justify-end gap-2 pt-1">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => setEditing(false)}
                    disabled={isMutating}
                  >
                    Cancel
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    onClick={saveEdit}
                    disabled={isMutating || draftObjectives.some((item) => !item.trim())}
                  >
                    Save & confirm
                  </Button>
                </div>
              </div>
            ) : (
              <div className="flex flex-wrap items-center gap-1.5">
                <Button type="button" variant="outline" size="sm" onClick={beginEdit} disabled={isMutating}>
                  <Pencil size={11} /> Modify
                </Button>
                {activePlan.task_mode === 'parallel_multi_agent' && onDowngrade ? (
                  <Button type="button" variant="outline" size="sm" onClick={onDowngrade} disabled={isMutating}>
                    Use sequential
                  </Button>
                ) : null}
                <Button type="button" size="sm" onClick={onConfirm} disabled={isMutating}>
                  <Check size={11} /> Confirm
                </Button>
              </div>
            )}
            {mutationError ? <p className="text-[10px] text-red-600">{mutationError}</p> : null}
          </div>
        ) : null}

        {/* Completion gate */}
        {completionEvidence ? (
          <div
            className={cn(
              'flex items-start gap-2 rounded-md border p-2 text-[10px]',
              completionEvidence.allowed
                ? 'border-emerald-200 bg-emerald-50 text-emerald-900'
                : 'border-red-200 bg-red-50 text-red-800',
            )}
          >
            {completionEvidence.allowed ? <ShieldCheck size={12} /> : <TriangleAlert size={12} />}
            <div>
              <p className="font-semibold">
                Completion gate: {completionEvidence.status}
              </p>
              <p className="text-[10px]">{completionEvidence.reason}</p>
              {completionEvidence.failed_task_ids.length > 0 ? (
                <p className="text-[10px] font-bold">
                  {completionEvidence.failed_task_ids.length} task
                  {completionEvidence.failed_task_ids.length === 1 ? '' : 's'} missing evidence
                </p>
              ) : null}
            </div>
          </div>
        ) : null}

        {/* Plan diff */}
        {latestChange ? <PlanDiff change={latestChange} /> : null}
      </CardContent>
    </Card>
  );
}

const DIFF_TONES: Record<string, string> = {
  retained: 'border-stone-200 bg-stone-50 text-stone-700',
  replaced: 'border-amber-200 bg-amber-50 text-amber-700',
  added: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  cancelled: 'border-red-200 bg-red-50 text-red-700',
};

function PlanDiff({ change }: { change: PlanChange }) {
  const groups = [
    { label: 'Retained', values: change.retained_task_ids, tone: 'retained' },
    { label: 'Replaced', values: change.replaced_task_ids, tone: 'replaced' },
    { label: 'Added', values: change.added_task_ids, tone: 'added' },
    { label: 'Cancelled', values: change.cancelled_task_ids, tone: 'cancelled' },
  ].filter((group) => group.values.length > 0);
  return (
    <div className="space-y-1.5 rounded-md border border-stone-200 bg-stone-50 p-2 text-[10px]" aria-label="Latest plan change">
      <p className="text-stone-700">
        <strong>Latest change</strong> · <span className="text-stone-500">{change.reason}</span>
      </p>
      <div className="flex flex-wrap gap-1">
        {groups.map((group) => (
          <Badge
            key={group.label}
            variant="outline"
            className={cn('px-1.5 py-0 text-[10px] font-normal', DIFF_TONES[group.tone])}
          >
            {group.label} {group.values.length}
          </Badge>
        ))}
      </div>
    </div>
  );
}
