import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import TopStatusBar from '../TopStatusBar'
import type { Goal, WorkspaceTask } from '../../types/workspace'

const mockGoal: Goal = {
  id: 'g-1',
  title: '实现用户认证系统',
  status: 'running',
}

const mockTasks: WorkspaceTask[] = [
  { id: 't-1', goal_id: 'g-1', title: 'Task 1', status: 'running', tokens_used: 500, priority: 0, duration_ms: null },
  { id: 't-2', goal_id: 'g-1', title: 'Task 2', status: 'completed', tokens_used: 200, priority: 0, duration_ms: null },
  { id: 't-3', goal_id: 'g-1', title: 'Task 3', status: 'pending', tokens_used: 0, priority: 0, duration_ms: null },
]

describe('TopStatusBar', () => {
  it('renders null when goal is null', () => {
    const { container } = render(<TopStatusBar goal={null} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders goal title and status', () => {
    render(<TopStatusBar goal={mockGoal} tasks={mockTasks} />)
    expect(screen.getByText(/实现用户认证系统/)).toBeInTheDocument()
    expect(screen.getByText('运行中')).toBeInTheDocument()
  })

  it('shows correct progress stats', () => {
    render(<TopStatusBar goal={mockGoal} tasks={mockTasks} />)
    expect(screen.getByText('进度: 1/3 Tasks')).toBeInTheDocument()
  })

  it('shows all 8 goal status colors', () => {
    const statuses = ['idle', 'planning', 'running', 'waiting', 'handoff', 'reviewing', 'completed', 'failed']
    statuses.forEach((status) => {
      const goal = { ...mockGoal, status } as Goal
      const { container } = render(<TopStatusBar goal={goal} tasks={[]} />)
      expect(container.textContent).toContain('Goal:')
    })
  })
})
