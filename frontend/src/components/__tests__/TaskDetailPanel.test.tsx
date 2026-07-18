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

  it('shows why context was retrieved, its sources and token budget', () => {
    renderWithProviders(
      <TaskDetailPanel
        task={{
          ...mockTask,
          context: JSON.stringify({
            policy: 'approved_memory_skill_keyword_v0',
            token_count: 128,
            retrieval_reason: 'Approved project Memory matched the Task query.',
            source_references: [{ memory_id: 'm-1' }],
          }),
          context_runs: [{
            id: 'r-1', task_id: 't-1', query: 'login architecture', policy: 'hybrid_v1',
            filters: {}, latency_ms: 8, token_budget: 200, token_count: 80, status: 'completed',
            items: [
              { id: 'i-1', rank: 1, score: 0.91, used: true, citation: 'docs/login.md#chunk-0', token_count: 80, source_id: 's-1', source_name: 'Docs', content: 'Login architecture rule.' },
              { id: 'i-2', rank: 2, score: 0.7, used: false, citation: 'docs/old.md#chunk-0', token_count: 180, source_id: 's-1', source_name: 'Docs' },
            ],
          }],
        }}
        onClose={vi.fn()}
      />
    )
    fireEvent.click(screen.getByText('Context'))
    expect(screen.getByText('approved_memory_skill_keyword_v0')).toBeInTheDocument()
    expect(screen.getByText('128 tokens')).toBeInTheDocument()
    expect(screen.getByText('1 sources')).toBeInTheDocument()
    expect(screen.getByText('Approved project Memory matched the Task query.')).toBeInTheDocument()
    expect(screen.getByText(/Query: login architecture/)).toBeInTheDocument()
    expect(screen.getByText(/Injected/)).toBeInTheDocument()
    expect(screen.getByText(/Dropped/)).toBeInTheDocument()
    expect(screen.getByText('docs/login.md#chunk-0')).toBeInTheDocument()
    expect(screen.getAllByRole('button', { name: 'Disable source' })).toHaveLength(2)
  })

  it('shows Agent candidates, eliminations and the fallback entry', () => {
    renderWithProviders(<TaskDetailPanel task={{
      ...mockTask,
      selection_decision: {
        id: 'selection-1', task_id: 'plan-task-1', required_capabilities: ['code_edit'], required_tools: ['file_write'],
        selected_agent_id: 'a-1', selected_model_id: 'm-1', backup_model_ids: ['m-2'], score: .91,
        selection_reason: 'Coder covers all required capabilities and tools.',
        fallback_entry: { agent_ids: ['a-2'], model_ids: ['m-2'], handoff_allowed: true, reason: 'Handoff without replanning.' },
        candidates: [
          { agent_id: 'a-1', agent_name: 'Coder A', role: 'coder', eligible: true, elimination_reasons: [], score: .91, selected_model_id: 'm-1', selected_model_name: 'Code Model', score_breakdown: {} },
          { agent_id: 'a-2', agent_name: 'Coder B', role: 'coder', eligible: false, elimination_reasons: ['missing tools file_write'], score: .6, selected_model_id: 'm-2', selected_model_name: 'Backup Model', score_breakdown: {} },
        ],
      },
    }} onClose={vi.fn()} />)
    expect(screen.getByText('Agent / Model selection')).toBeInTheDocument()
    expect(screen.getByText(/Coder covers all required/)).toBeInTheDocument()
    expect(screen.getByText('missing tools file_write')).toBeInTheDocument()
    expect(screen.getByText(/Handoff without replanning/)).toBeInTheDocument()
  })

  it('shows the recorded router decision and recent logs in history', () => {
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
    fireEvent.click(screen.getByText('History'))
    expect(screen.getByText('GPT-4o matches the coding task.')).toBeInTheDocument()
    expect(screen.getByText(/Code capability/)).toBeInTheDocument()
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
    fireEvent.click(screen.getByText('History'))
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
