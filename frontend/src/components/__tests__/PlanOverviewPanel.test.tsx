import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import PlanOverviewPanel from '../PlanOverviewPanel';
import type { ExecutionPlan, PlanChange } from '../../types/workspace';

const plan: ExecutionPlan = {
  id: 'plan-v2',
  plan_id: 'plan',
  goal_id: 'goal',
  version: 2,
  status: 'active',
  task_mode: 'sequential_multi_agent',
  goal_summary: 'Repair the build',
  assumptions: [],
  required_context: [],
  activation_reason: 'Verification evidence invalidated one task.',
  final_acceptance_criteria: [],
  human_approval_points: [],
  estimated_cost: {},
  planner_type: 'runtime_replan',
  tasks: [
    {
      id: 'pt-1', client_task_id: 'build', objective: 'Revise build', task_type: 'coding',
      required_capabilities: ['code_edit'], required_tools: [], dependencies: [],
      acceptance_criteria: [{ type: 'diff_exists' }], risk_level: 'medium', parallel_safe: false,
      context_query: '', approval_required: false, runtime_task_id: 'task-new', source: 'replaced',
    },
  ],
};

const change: PlanChange = {
  id: 'change', goal_id: 'goal', from_plan_version_id: 'plan-v1', to_plan_version_id: 'plan-v2',
  change_type: 'replan', reason: 'Verification failed', evidence: [],
  retained_task_ids: ['research'], replaced_task_ids: ['build'], added_task_ids: [], cancelled_task_ids: ['old-review'],
};

describe('PlanOverviewPanel', () => {
  it('shows active mode, version, source and latest plan diff', () => {
    render(<PlanOverviewPanel activePlan={plan} versions={[{ ...plan, created_at: null }, { ...plan, id: 'v1', version: 1, created_at: null }]} changes={[change]} />);
    expect(screen.getByText('Sequential Multi-Agent')).toBeInTheDocument();
    expect(screen.getByText('v2')).toBeInTheDocument();
    expect(screen.getByText('Model-generated plan')).toBeInTheDocument();
    expect(screen.getByText('Retained 1')).toBeInTheDocument();
    expect(screen.getByText('Replaced 1')).toBeInTheDocument();
    expect(screen.getByText('Cancelled 1')).toBeInTheDocument();
  });

  it('labels an explicit rule fallback', () => {
    render(<PlanOverviewPanel activePlan={{ ...plan, planner_type: 'rule_fallback' }} />);
    expect(screen.getByText('Rule fallback plan')).toBeInTheDocument();
  });

  it('shows failed completion evidence instead of implying success', () => {
    render(<PlanOverviewPanel
      activePlan={plan}
      completionEvidence={{
        allowed: false,
        status: 'failed',
        goal_status: 'revision_required',
        reason: 'Completion evidence is missing or failed.',
        failed_task_ids: ['task-new'],
        tasks: [],
      }}
    />);
    expect(screen.getByText('Completion gate: failed')).toBeInTheDocument();
    expect(screen.getByText('1 task missing evidence')).toBeInTheDocument();
  });

  it('requires explicit confirmation and supports preflight task edits', async () => {
    const onConfirm = vi.fn();
    const onModify = vi.fn().mockResolvedValue(undefined);
    render(<PlanOverviewPanel activePlan={{ ...plan, confirmed_at: null }} onConfirm={onConfirm} onModify={onModify} />);

    expect(screen.getByText('Review before execution')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Confirm' }));
    expect(onConfirm).toHaveBeenCalledOnce();

    fireEvent.click(screen.getByRole('button', { name: 'Modify' }));
    fireEvent.change(screen.getByDisplayValue('Revise build'), { target: { value: 'Revise and document build' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save & confirm' }));
    await waitFor(() => expect(onModify).toHaveBeenCalledWith(['Revise and document build']));
  });
});
