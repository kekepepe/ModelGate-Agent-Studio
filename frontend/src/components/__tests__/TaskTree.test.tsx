import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import TaskTree from '../TaskTree'
import type { WorkspaceTask } from '../../types/workspace'

const tasks: WorkspaceTask[] = [
  { id: 't-1', goal_id: 'g-1', title: 'Task 1', status: 'running', tokens_used: 0, priority: 0, duration_ms: null },
  { id: 't-2', goal_id: 'g-1', title: 'Task 2', status: 'completed', tokens_used: 100, priority: 0, duration_ms: null },
  { id: 't-3', goal_id: 'g-1', title: 'Task 3', status: 'pending', tokens_used: 0, priority: 0, duration_ms: null },
]

describe('TaskTree', () => {
  it('renders all tasks', () => {
    render(<TaskTree tasks={tasks} />)
    expect(screen.getByText('Task 1')).toBeInTheDocument()
    expect(screen.getByText('Task 2')).toBeInTheDocument()
    expect(screen.getByText('Task 3')).toBeInTheDocument()
  })

  it('shows empty state', () => {
    render(<TaskTree tasks={[]} />)
    expect(screen.getByText('暂无任务')).toBeInTheDocument()
  })

  it('shows correct stats count', () => {
    render(<TaskTree tasks={tasks} />)
    expect(screen.getByText(/3 个 Task/)).toBeInTheDocument()
    expect(screen.getByText(/1 个进行中/)).toBeInTheDocument()
    expect(screen.getByText(/1 个已完成/)).toBeInTheDocument()
  })

  it('calls onTaskClick when task is clicked', () => {
    const onTaskClick = vi.fn()
    render(<TaskTree tasks={tasks} onTaskClick={onTaskClick} />)
    fireEvent.click(screen.getByText('Task 1'))
    expect(onTaskClick).toHaveBeenCalledWith('t-1')
  })

  it('highlights selected task', () => {
    render(<TaskTree tasks={tasks} selectedTaskId="t-2" />)
    const btn = screen.getByText('Task 2').closest('button')
    expect(btn?.className).toContain('bg-stone-100')
  })
})
