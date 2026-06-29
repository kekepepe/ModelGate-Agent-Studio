import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import HandoffDetailDrawer from '../HandoffDetailDrawer'
import type { HandoffRecord } from '../../types/handoff'

const summary = {
  original_goal: 'Goal 1',
  current_task: 'Task 1',
  completed_work: ['完成 A'],
  unfinished_work: ['完成 B'],
  important_constraints: ['保持顺序'],
  key_decisions: ['拆分阶段'],
  errors_and_risks: ['上下文受限'],
  next_suggested_steps: ['继续实现 B'],
  context_needed: ['原始 goal'],
}

const handoff: HandoffRecord = {
  id: 'handoff-1',
  goal_id: 'goal-1',
  task_id: 'task-1',
  from_agent_id: 'a-1',
  from_model_id: 'claude-opus-4-7',
  to_agent_id: 'a-2',
  to_model_id: 'claude-sonnet-4-6',
  reason: 'manual',
  reason_description: 'user',
  handoff_summary: summary,
  status: 'ready',
  result_after_handoff: null,
  result_note: null,
  tokens_before_handoff: 0,
  tokens_after_handoff: 0,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  from_agent_name: 'Coder',
  to_agent_name: 'Reviewer',
  task: {
    id: 'task-1',
    goal_id: 'goal-1',
    title: 'Task 1',
    description: 'Task 1',
    status: 'running',
    assigned_agent_id: 'a-1',
    assigned_model_id: 'claude-opus-4-7',
  },
}

describe('HandoffDetailDrawer', () => {
  it('renders all 9 summary fields and accept action for ready status', () => {
    const onAccept = vi.fn()
    render(
      <HandoffDetailDrawer handoff={handoff} onClose={vi.fn()} onAccept={onAccept} />
    )
    expect(screen.getByText('Original Goal')).toBeInTheDocument()
    expect(screen.getByText('Current Task')).toBeInTheDocument()
    expect(screen.getByText('Completed Work')).toBeInTheDocument()
    expect(screen.getByText('Unfinished Work')).toBeInTheDocument()
    expect(screen.getByText('Important Constraints')).toBeInTheDocument()
    expect(screen.getByText('Key Decisions')).toBeInTheDocument()
    expect(screen.getByText('Errors and Risks')).toBeInTheDocument()
    expect(screen.getByText('Next Suggested Steps')).toBeInTheDocument()
    expect(screen.getByText('Context Needed')).toBeInTheDocument()
    expect(screen.getByText('Coder')).toBeInTheDocument()
    expect(screen.getByText('Reviewer')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Accept Handoff' }))
    expect(onAccept).toHaveBeenCalled()
  })

  it('shows fallback hint when status is failed', () => {
    render(
      <HandoffDetailDrawer handoff={{ ...handoff, status: 'failed' }} onClose={vi.fn()} />
    )
    expect(screen.getByText(/Summary generation failed/)).toBeInTheDocument()
  })

  it('shows generating hint when status is generating_summary', () => {
    render(
      <HandoffDetailDrawer handoff={{ ...handoff, status: 'generating_summary' }} onClose={vi.fn()} />
    )
    expect(screen.getByText(/Generating summary/)).toBeInTheDocument()
  })

  it('renders result note when result is recorded', () => {
    render(
      <HandoffDetailDrawer
        handoff={{
          ...handoff,
          status: 'completed',
          result_after_handoff: 'success',
          result_note: 'looks good',
        }}
        onClose={vi.fn()}
      />
    )
    expect(screen.getByText('looks good')).toBeInTheDocument()
  })

  it('calls onClose when clicking the close button', () => {
    const onClose = vi.fn()
    render(<HandoffDetailDrawer handoff={handoff} onClose={onClose} />)
    fireEvent.click(screen.getByRole('button', { name: 'close drawer' }))
    expect(onClose).toHaveBeenCalled()
  })
})
