import { describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import ThreeZoneCardFlow from '../ThreeZoneCardFlow';
import type { WorkspaceViewModel } from '../../utils/workspaceViewModel';

const baseViewModel: WorkspaceViewModel = {
  stations: [
    {
      agent: { id: 'coder', name: 'Coder', role: 'coder', status: 'running', default_model_id: 'm-1', is_enabled: true },
      worker: null,
      tasks: [
        { id: 't-1', goal_id: 'g-1', title: 'Build login', status: 'running', assigned_agent_id: 'coder', tokens_used: 10, priority: 0 },
        { id: 't-2', goal_id: 'g-1', title: 'Review login', status: 'handoff', assigned_agent_id: 'coder', tokens_used: 5, priority: 0 },
      ],
      status: 'running',
      handoffs: [],
      order: 0,
    },
  ],
  edges: [],
  handoffs: [
    {
      id: 'h-1', task_id: 't-2', status: 'ready', reason: 'quota_exceeded',
      from_agent_id: 'coder', from_agent_name: 'Coder', from_model_id: 'm-1',
      to_agent_id: 'reviewer', to_agent_name: 'Reviewer', to_model_id: 'm-2',
    },
  ],
};

describe('ThreeZoneCardFlow', () => {
  it('renders tasks grouped into the three zones', () => {
    render(<ThreeZoneCardFlow viewModel={baseViewModel} selectedTaskId={null} onSelectTask={vi.fn()} />);
    expect(screen.getByText('Build login')).toBeInTheDocument();
    expect(screen.getByText('Review login')).toBeInTheDocument();
  });

  it('shows the handoff status bar on the task that owns an active handoff', () => {
    const onOpenHandoff = vi.fn();
    render(
      <ThreeZoneCardFlow viewModel={baseViewModel} selectedTaskId={null} onSelectTask={vi.fn()} onOpenHandoff={onOpenHandoff} />
    );
    const bar = screen.getByRole('button', { name: 'View handoff: quota_exceeded' });
    fireEvent.click(bar);
    expect(onOpenHandoff).toHaveBeenCalledWith('h-1');
  });

  it('does not render a handoff bar without an active handoff', () => {
    const empty: WorkspaceViewModel = { ...baseViewModel, handoffs: [] };
    render(<ThreeZoneCardFlow viewModel={empty} selectedTaskId={null} onSelectTask={vi.fn()} onOpenHandoff={vi.fn()} />);
    expect(screen.queryByText(/点击查看/)).not.toBeInTheDocument();
  });
});
