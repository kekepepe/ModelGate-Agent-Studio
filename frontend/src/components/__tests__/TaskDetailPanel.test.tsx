import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import TaskDetailPanel from '../TaskDetailPanel'
import type { WorkspaceTask } from '../../types/workspace'

const mockTask: WorkspaceTask = {
  id: 't-1',
  goal_id: 'g-1',
  title: 'Build login page',
  description: 'Create a login form',
  status: 'running',
  assigned_agent_id: 'a-1',
  agent_name: 'Coder #1',
  agent_role: 'coder',
  model_name: 'GPT-4o',
  tokens_used: 1500,
  duration_ms: 3500,
  output: '```tsx\nimport React\n// code here\n```',
  priority: 1,
}

function renderWithProviders(ui: React.ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>
  )
}

describe('TaskDetailPanel', () => {
  it('renders null when task is null', () => {
    const { container } = renderWithProviders(
      <TaskDetailPanel task={null} onClose={vi.fn()} />
    )
    expect(container.firstChild).toBeNull()
  })

  it('shows task title', () => {
    renderWithProviders(
      <TaskDetailPanel task={mockTask} onClose={vi.fn()} />
    )
    expect(screen.getByText('Build login page')).toBeInTheDocument()
  })

  it('shows overview tab by default', () => {
    renderWithProviders(
      <TaskDetailPanel task={mockTask} onClose={vi.fn()} />
    )
    expect(screen.getByText('Coder #1')).toBeInTheDocument()
    expect(screen.getByText('1,500')).toBeInTheDocument()
  })

  it('switches to task tab and shows output', () => {
    renderWithProviders(
      <TaskDetailPanel task={mockTask} onClose={vi.fn()} />
    )
    fireEvent.click(screen.getByText('Task'))
    expect(screen.getByText('Create a login form')).toBeInTheDocument()
    expect(screen.getByText(/import React/)).toBeInTheDocument()
  })

  it('switches to context tab with an empty-state message', () => {
    renderWithProviders(
      <TaskDetailPanel task={mockTask} onClose={vi.fn()} />
    )
    fireEvent.click(screen.getByText('Context'))
    expect(screen.getByText('当前 Task 尚未建立可继承上下文。')).toBeInTheDocument()
  })

  it('shows the recorded router decision and recent logs', () => {
    renderWithProviders(
      <TaskDetailPanel
        task={{
          ...mockTask,
          context: '{"handoff":"context"}',
          quota: { model_id: 'gpt', quota_status: 'warning', usage_percent: 0.8, total_tokens: 800, request_count: 4 },
          routing_decision: {
            confidence: 0.88,
            routing_reason: { summary: 'GPT-4o matches the coding task.', primary_factors: ['Code capability'], tradeoffs: ['Higher cost'] },
            backup_model_ids: ['deepseek-coder'],
          },
          recent_logs: [{ id: 'l-1', event_type: 'model_call', event_status: 'completed', output_summary: 'Model completed a step.' }],
        }}
        onClose={vi.fn()}
      />
    )
    fireEvent.click(screen.getByText('Router'))
    expect(screen.getByText('GPT-4o matches the coding task.')).toBeInTheDocument()
    expect(screen.getByText(/Code capability/)).toBeInTheDocument()
    fireEvent.click(screen.getByText('Logs'))
    expect(screen.getByText('Model completed a step.')).toBeInTheDocument()
    fireEvent.click(screen.getByText('Context'))
    expect(screen.getByText(/"handoff": "context"/)).toBeInTheDocument()
  })

  it('shows the handoff timeline in the selected task context', () => {
    const onOpenHandoff = vi.fn()
    renderWithProviders(
      <TaskDetailPanel
        task={mockTask}
        onClose={vi.fn()}
        onOpenHandoff={onOpenHandoff}
        handoffs={[{
          id: 'h-1', task_id: 't-1', status: 'ready', reason: 'manual',
          from_agent_id: 'a-1', from_agent_name: 'Coder #1', from_model_id: 'gpt',
          to_agent_id: 'a-2', to_agent_name: 'Reviewer #1', to_model_id: 'claude',
          reason_description: 'Need a review',
        }]}
      />
    )
    fireEvent.click(screen.getByText('Handoff'))
    expect(screen.getByText('Coder #1 → Reviewer #1')).toBeInTheDocument()
    fireEvent.click(screen.getByText('Need a review'))
    expect(onOpenHandoff).toHaveBeenCalledWith('h-1')
  })

  it('calls onClose when close button clicked', () => {
    const onClose = vi.fn()
    renderWithProviders(
      <TaskDetailPanel task={mockTask} onClose={onClose} />
    )
    const closeBtn = document.querySelector('.lucide-x')?.closest('button')
    if (closeBtn) fireEvent.click(closeBtn)
    expect(onClose).toHaveBeenCalled()
  })

  it('shows loading state', () => {
    renderWithProviders(
      <TaskDetailPanel task={mockTask} isLoading onClose={vi.fn()} />
    )
    expect(document.querySelector('.animate-pulse')).toBeTruthy()
  })
})
