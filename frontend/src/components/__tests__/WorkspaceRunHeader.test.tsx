import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import WorkspaceRunHeader from '../workspace/WorkspaceRunHeader';
import type { Goal } from '../../types/workspace';

const goal: Goal = {
  id: 'goal-1', title: 'Unify workspace navigation', status: 'running',
  budget_tokens: 1000,
};

function renderHeader(overrides: Partial<Goal> = {}, onStop = vi.fn()) {
  return render(<MemoryRouter><WorkspaceRunHeader
    runId="run-1234567890"
    goal={{ ...goal, ...overrides }}
    tasks={[{ id: 'task-1', goal_id: 'goal-1', title: 'Build', status: 'running', assigned_agent_id: 'agent-1', tokens_used: 250, priority: 1 }]}
    teamName="Code Delivery"
    mode="card"
    onModeChange={() => undefined}
    onPause={() => undefined}
    onResume={() => undefined}
    onStop={onStop}
    onExport={() => undefined}
  /></MemoryRouter>);
}

afterEach(() => vi.restoreAllMocks());

describe('WorkspaceRunHeader', () => {
  it('separates run context, cross-module links and controls', () => {
    renderHeader();
    expect(screen.getByRole('link', { name: /Workspace/ })).toHaveAttribute('href', '/workspace');
    expect(screen.getByRole('link', { name: 'Logs' })).toHaveAttribute('href', '/logs?runId=run-1234567890&goalId=goal-1');
    expect(screen.getByText('运行中')).toBeVisible();
    expect(screen.getByText(/250 \/ 1,000 tokens/)).toBeVisible();
    expect(screen.getByRole('button', { name: 'Pause' })).toBeEnabled();
    expect(screen.getByRole('button', { name: 'Resume' })).toBeDisabled();
  });

  it('requires confirmation before stopping', () => {
    const onStop = vi.fn();
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(false);
    renderHeader({}, onStop);
    fireEvent.click(screen.getByRole('button', { name: 'Stop' }));
    expect(confirm).toHaveBeenCalledOnce();
    expect(onStop).not.toHaveBeenCalled();
    confirm.mockReturnValue(true);
    fireEvent.click(screen.getByRole('button', { name: 'Stop' }));
    expect(onStop).toHaveBeenCalledOnce();
  });

  it('only enables resume for paused runs', () => {
    renderHeader({ status: 'paused' });
    expect(screen.getByRole('button', { name: 'Pause' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Resume' })).toBeEnabled();
  });
});
