import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
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

describe('TaskDetailPanel', () => {
  it('renders null when task is null', () => {
    const { container } = render(
      <MemoryRouter>
        <TaskDetailPanel task={null} onClose={vi.fn()} />
      </MemoryRouter>
    )
    expect(container.firstChild).toBeNull()
  })

  it('shows task title', () => {
    render(
      <MemoryRouter>
        <TaskDetailPanel task={mockTask} onClose={vi.fn()} />
      </MemoryRouter>
    )
    expect(screen.getByText('Build login page')).toBeInTheDocument()
  })

  it('shows overview tab by default', () => {
    render(
      <MemoryRouter>
        <TaskDetailPanel task={mockTask} onClose={vi.fn()} />
      </MemoryRouter>
    )
    expect(screen.getByText('Coder #1')).toBeInTheDocument()
    expect(screen.getByText('1,500')).toBeInTheDocument()
  })

  it('switches to task tab and shows output', () => {
    render(
      <MemoryRouter>
        <TaskDetailPanel task={mockTask} onClose={vi.fn()} />
      </MemoryRouter>
    )
    fireEvent.click(screen.getByText('Task'))
    expect(screen.getByText('Create a login form')).toBeInTheDocument()
    expect(screen.getByText(/import React/)).toBeInTheDocument()
  })

  it('switches to context tab showing placeholder', () => {
    render(
      <MemoryRouter>
        <TaskDetailPanel task={mockTask} onClose={vi.fn()} />
      </MemoryRouter>
    )
    fireEvent.click(screen.getByText('Context'))
    expect(screen.getByText('上下文信息待实现')).toBeInTheDocument()
  })

  it('calls onClose when close button clicked', () => {
    const onClose = vi.fn()
    render(
      <MemoryRouter>
        <TaskDetailPanel task={mockTask} onClose={onClose} />
      </MemoryRouter>
    )
    const closeBtn = document.querySelector('.lucide-x')?.closest('button')
    if (closeBtn) fireEvent.click(closeBtn)
    expect(onClose).toHaveBeenCalled()
  })

  it('shows loading state', () => {
    render(
      <MemoryRouter>
        <TaskDetailPanel task={mockTask} isLoading onClose={vi.fn()} />
      </MemoryRouter>
    )
    expect(document.querySelector('.animate-pulse')).toBeTruthy()
  })
})
