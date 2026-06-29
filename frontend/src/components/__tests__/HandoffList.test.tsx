import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import HandoffList from '../HandoffList'
import type { HandoffListItem } from '../../types/handoff'

const sample: HandoffListItem[] = [
  {
    id: 'handoff-1',
    goal_id: 'goal-1',
    task_id: 'task-1',
    task_title: 'Implement feature',
    from_agent_id: 'a-1',
    from_agent_name: 'Coder',
    from_model_id: 'claude-opus-4-7',
    to_agent_id: 'a-2',
    to_agent_name: 'Reviewer',
    to_model_id: 'claude-sonnet-4-6',
    reason: 'manual',
    status: 'ready',
    result_after_handoff: null,
    created_at: new Date().toISOString(),
  },
  {
    id: 'handoff-2',
    goal_id: 'goal-2',
    task_id: 'task-2',
    task_title: 'Review code',
    from_agent_id: 'a-2',
    from_agent_name: 'Reviewer',
    from_model_id: 'claude-sonnet-4-6',
    to_agent_id: 'a-3',
    to_agent_name: 'Summarizer',
    to_model_id: 'claude-haiku-4-5-20251001',
    reason: 'quota_exceeded',
    status: 'completed',
    result_after_handoff: 'success',
    created_at: new Date().toISOString(),
  },
]

describe('HandoffList', () => {
  it('renders rows with from/to and status', () => {
    render(<HandoffList handoffs={sample} onSelect={vi.fn()} />)
    expect(screen.getAllByText('goal-1').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Coder').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Reviewer').length).toBeGreaterThan(0)
    expect(screen.getAllByText('可接手').length).toBeGreaterThan(0)
    expect(screen.getAllByText('成功').length).toBeGreaterThan(0)
  })

  it('shows empty state with clear filter CTA when filters yield nothing', () => {
    const onClear = vi.fn()
    render(<HandoffList handoffs={[]} onSelect={vi.fn()} hasFilters onClearFilters={onClear} />)
    expect(screen.getByText('No results match your filters')).toBeInTheDocument()
    fireEvent.click(screen.getByText('Clear Filters'))
    expect(onClear).toHaveBeenCalled()
  })

  it('shows default empty state when there are no handoffs', () => {
    render(<HandoffList handoffs={[]} onSelect={vi.fn()} />)
    expect(screen.getByText('No handoff records yet')).toBeInTheDocument()
  })

  it('calls onSelect when clicking a row', () => {
    const onSelect = vi.fn()
    render(<HandoffList handoffs={sample} onSelect={onSelect} />)
    fireEvent.click(screen.getAllByText('Coder')[0])
    expect(onSelect).toHaveBeenCalledWith(sample[0])
  })
})
