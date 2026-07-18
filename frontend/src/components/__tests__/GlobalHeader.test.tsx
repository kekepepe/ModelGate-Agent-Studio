import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import GlobalHeader from '../app-shell/GlobalHeader';

vi.mock('../../hooks/useDashboard', () => ({
  useDashboardStats: () => ({ data: { active_goals: 2, total_tokens_today: 420 } }),
}));
vi.mock('../../hooks/useRuns', () => ({
  useRun: () => ({ data: { goal_id: 'goal-9' } }),
}));

describe('GlobalHeader', () => {
  it('keeps Workspace active and carries run context across global navigation', () => {
    render(<MemoryRouter initialEntries={['/workspace/runs/run-9']}><GlobalHeader runId="run-9" /></MemoryRouter>);
    expect(screen.getByRole('link', { name: 'Workspace' })).toHaveAttribute('aria-current', 'page');
    expect(screen.getByRole('link', { name: 'Assets' })).toHaveAttribute('href', '/assets?runId=run-9');
    expect(screen.getByRole('link', { name: 'Evolution' })).toHaveAttribute('href', '/evolution?runId=run-9&goalId=goal-9');
    expect(screen.getByRole('link', { name: 'Logs' })).toHaveAttribute('href', '/logs?runId=run-9');
  });
});
