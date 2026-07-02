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

  it('switches to context tab showing placeholder', () => {
    renderWithProviders(
      <TaskDetailPanel task={mockTask} onClose={vi.fn()} />
    )
    fireEvent.click(screen.getByText('Context'))
    expect(screen.getByText('上下文信息待实现')).toBeInTheDocument()
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
