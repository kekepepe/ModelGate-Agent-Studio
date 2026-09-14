import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import TaskCard from '../TaskCard'

// TaskCard was refactored to shadcn Card + AgentStatusBadge (V1.0-P0): status
// pills use the shared English labels and there are no per-status card
// animations any more, so assertions target data attributes and badge text.

describe('TaskCard', () => {
  it('renders pending state correctly', () => {
    render(<TaskCard id="t-1" title="Test Task" status="pending" />)
    expect(screen.getByText('Test Task')).toBeInTheDocument()
    expect(screen.getByText('Pending')).toBeInTheDocument()
  })

  it('marks the card element with its task status', () => {
    render(<TaskCard id="t-1" title="Task A" status="running" />)
    expect(screen.getByRole('button')).toHaveAttribute('data-task-status', 'running')
    expect(screen.getByText('Running')).toBeInTheDocument()
  })

  it('renders completed state', () => {
    render(<TaskCard id="t-1" title="Task A" status="completed" />)
    expect(screen.getByText('Done')).toBeInTheDocument()
  })

  it('renders failed state', () => {
    render(<TaskCard id="t-1" title="Task A" status="failed" />)
    expect(screen.getByText('Failed')).toBeInTheDocument()
  })

  it('renders handoff state', () => {
    render(<TaskCard id="t-1" title="Task A" status="handoff" />)
    expect(screen.getByText('Handoff')).toBeInTheDocument()
  })

  it('calls onSelect when clicked', () => {
    const onSelect = vi.fn()
    render(<TaskCard id="t-1" title="Click" status="pending" onSelect={onSelect} />)
    fireEvent.click(screen.getByRole('button'))
    expect(onSelect).toHaveBeenCalledWith('t-1')
  })

  it('shows priority badge when > 0', () => {
    // PRIORITY_LABEL maps numeric priority 2 to the P1 badge.
    render(<TaskCard id="t-1" title="Task A" status="pending" priority={2} />)
    expect(screen.getByText('P1')).toBeInTheDocument()
  })

  it('applies selected ring style', () => {
    render(<TaskCard id="t-1" title="Sel" status="pending" isSelected />)
    expect(screen.getByRole('button').className).toContain('ring-2')
  })

  it('renders handoff indicator when provided', () => {
    const indicator = <span data-testid="handoff-indicator">Handoff indicator</span>
    render(<TaskCard id="t-1" title="H" status="handoff" handoffIndicator={indicator} />)
    expect(screen.getByTestId('handoff-indicator')).toBeInTheDocument()
  })

  it('renders agent, model and output snippet', () => {
    render(
      <TaskCard
        id="t-1"
        title="Active task"
        status="running"
        agentName="Coder"
        modelName="GPT-4o"
        outputSnippet="Implementation is in progress"
      />
    )
    expect(screen.getByText('Coder')).toBeInTheDocument()
    expect(screen.getByText('GPT-4o')).toBeInTheDocument()
    expect(screen.getByText('Implementation is in progress')).toBeInTheDocument()
  })

  it('opens the handoff detail from the handoff block without selecting the card', () => {
    const onOpenHandoff = vi.fn()
    const onSelect = vi.fn()
    render(
      <TaskCard
        id="t-1"
        title="Handoff task"
        status="handoff"
        onSelect={onSelect}
        handoff={{
          id: 'h-1', task_id: 't-1', status: 'ready', reason: 'manual',
          from_agent_id: 'a-1', from_agent_name: 'Coder', from_model_id: 'gpt',
          to_agent_id: 'a-2', to_agent_name: 'Reviewer', to_model_id: 'claude',
        }}
        onOpenHandoff={onOpenHandoff}
      />
    )
    // Explicit aria-label avoids clashing with the card's own button role.
    fireEvent.click(screen.getByRole('button', { name: 'View handoff: manual' }))
    expect(onOpenHandoff).toHaveBeenCalledWith('h-1')
    expect(onSelect).not.toHaveBeenCalled()
  })
})
