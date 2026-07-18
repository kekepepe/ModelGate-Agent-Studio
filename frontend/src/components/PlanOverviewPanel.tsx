import { useState } from 'react';
import { Check, GitBranch, Pencil, RefreshCw, ShieldCheck, TriangleAlert } from 'lucide-react';
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
    <section className="plan-overview-panel" aria-label="Active execution plan">
      <header className="plan-overview-heading">
        <span><GitBranch size={15} /><strong>Execution plan</strong></span>
        <span className="plan-version-badge">v{activePlan.version}</span>
      </header>
      <div className="plan-mode-row">
        <span>{MODE_LABELS[activePlan.task_mode]}</span>
        <small>{activePlan.tasks.length} active tasks</small>
      </div>
      <p className="plan-activation-reason">{activePlan.activation_reason}</p>
      <div className={`plan-source ${fallback ? 'is-fallback' : 'is-model'}`}>
        {fallback ? <TriangleAlert size={12} /> : <ShieldCheck size={12} />}
        <span>{fallback ? 'Rule fallback plan' : 'Model-generated plan'}</span>
      </div>
      <div className="plan-history-row">
        <span>{versions.length} version{versions.length === 1 ? '' : 's'}</span>
        <span><RefreshCw size={10} />{replanCount} replan{replanCount === 1 ? '' : 's'}</span>
      </div>
      {awaitingConfirmation ? (
        <div className="plan-approval-box">
          <strong>Review before execution</strong>
          <span>This plan is active but cannot run until you confirm or modify it.</span>
          {editing ? (
            <div className="plan-edit-list">
              {draftObjectives.map((objective, index) => (
                <label key={activePlan.tasks[index]?.client_task_id || index}>
                  <small>{activePlan.tasks[index]?.client_task_id}</small>
                  <input
                    value={objective}
                    onChange={(event) => setDraftObjectives((current) => current.map((item, itemIndex) => itemIndex === index ? event.target.value : item))}
                  />
                </label>
              ))}
              <div className="plan-action-row">
                <button type="button" onClick={() => setEditing(false)} disabled={isMutating}>Cancel</button>
                <button type="button" className="is-primary" onClick={saveEdit} disabled={isMutating || draftObjectives.some((item) => !item.trim())}>Save & confirm</button>
              </div>
            </div>
          ) : (
            <div className="plan-action-row">
              <button type="button" onClick={beginEdit} disabled={isMutating}><Pencil size={11} />Modify</button>
              {activePlan.task_mode === 'parallel_multi_agent' && onDowngrade ? (
                <button type="button" onClick={onDowngrade} disabled={isMutating}>Use sequential</button>
              ) : null}
              <button type="button" className="is-primary" onClick={onConfirm} disabled={isMutating}><Check size={11} />Confirm</button>
            </div>
          )}
          {mutationError ? <small className="plan-action-error">{mutationError}</small> : null}
        </div>
      ) : null}
      {completionEvidence ? (
        <div className={`completion-gate completion-gate--${completionEvidence.allowed ? 'passed' : 'blocked'}`}>
          {completionEvidence.allowed ? <ShieldCheck size={12} /> : <TriangleAlert size={12} />}
          <div>
            <strong>Completion gate: {completionEvidence.status}</strong>
            <span>{completionEvidence.reason}</span>
            {completionEvidence.failed_task_ids.length > 0 ? (
              <small>{completionEvidence.failed_task_ids.length} task{completionEvidence.failed_task_ids.length === 1 ? '' : 's'} missing evidence</small>
            ) : null}
          </div>
        </div>
      ) : null}
      {latestChange ? <PlanDiff change={latestChange} /> : null}
    </section>
  );
}

function PlanDiff({ change }: { change: PlanChange }) {
  const groups = [
    { label: 'Retained', values: change.retained_task_ids, tone: 'retained' },
    { label: 'Replaced', values: change.replaced_task_ids, tone: 'replaced' },
    { label: 'Added', values: change.added_task_ids, tone: 'added' },
    { label: 'Cancelled', values: change.cancelled_task_ids, tone: 'cancelled' },
  ].filter((group) => group.values.length > 0);
  return (
    <div className="plan-diff" aria-label="Latest plan change">
      <p><strong>Latest change</strong><span>{change.reason}</span></p>
      <div className="plan-diff-groups">
        {groups.map((group) => (
          <span key={group.label} className={`plan-diff-chip plan-diff-chip--${group.tone}`}>
            {group.label} {group.values.length}
          </span>
        ))}
      </div>
    </div>
  );
}
