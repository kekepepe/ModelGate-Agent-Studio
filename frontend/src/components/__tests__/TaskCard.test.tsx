import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import TaskCard from '../TaskCard'

describe('TaskCard', () => {
  it('renders pending state correctly', () => {
    render(<TaskCard id="t-1" title="Test Task" status="pending" />)
    expect(screen.getByText('Test Task')).toBeInTheDocument()
    expect(screen.getByText('待处理')).toBeInTheDocument()
  })

  it('renders running state with animation class', () => {
    const { container } = render(<TaskCard id="t-1" title="Running" status="running" />)
    const card = container.firstChild as HTMLElement
    expect(card.className).toContain('animate-breathe')
    expect(screen.getByText('执行中')).toBeInTheDocument()
  })

  it('renders completed state', () => {
    render(<TaskCard id="t-1" title="Done" status="completed" />)
    expect(screen.getByText('已完成')).toBeInTheDocument()
  })

  it('renders failed state with shake', () => {
    const { container } = render(<TaskCard id="t-1" title="Failed" status="failed" />)
    const card = container.firstChild as HTMLElement
    expect(card.className).toContain('animate-shake')
    expect(screen.getByText('失败')).toBeInTheDocument()
  })

  it('renders handoff state with rotate animation', () => {
    const { container } = render(<TaskCard id="t-1" title="Handoff" status="handoff" />)
    const card = container.firstChild as HTMLElement
    expect(card.className).toContain('animate-rotate-border')
    expect(screen.getByText('交接中')).toBeInTheDocument()
  })

  it('calls onSelect when clicked', () => {
    const onSelect = vi.fn()
    render(<TaskCard id="t-1" title="Click" status="pending" onSelect={onSelect} />)
    fireEvent.click(screen.getByRole('button'))
    expect(onSelect).toHaveBeenCalledWith('t-1')
  })

  it('shows priority badge when > 0', () => {
    render(<TaskCard id="t-1" title="Pri" status="pending" priority={2} />)
    expect(screen.getByText('P2')).toBeInTheDocument()
  })

  it('applies selected ring style', () => {
    const { container } = render(<TaskCard id="t-1" title="Sel" status="pending" isSelected />)
    const card = container.firstChild as HTMLElement
    expect(card.className).toContain('ring-2');
  })

  it('renders handoff indicator when provided', () => {
    const indicator = <span data-testid="handoff-indicator">Handoff indicator</span>
    render(<TaskCard id="t-1" title="H" status="handoff" handoffIndicator={indicator} />)
    expect(screen.getByTestId('handoff-indicator')).toBeInTheDocument()
  })

  it('offers handoff from an active task without selecting the card', () => {
    const onRequestHandoff = vi.fn()
    const onSelect = vi.fn()
    render(
      <TaskCard
        id="t-1"
        title="Active task"
        status="running"
        onSelect={onSelect}
        onRequestHandoff={onRequestHandoff}
        agentName="Coder"
        modelName="GPT-4o"
        outputSnippet="Implementation is in progress"
      />
    )
    expect(screen.getByText('Coder')).toBeInTheDocument()
    expect(screen.getByText('GPT-4o')).toBeInTheDocument()
    expect(screen.getByText('Implementation is in progress')).toBeInTheDocument()
    fireEvent.click(screen.getByText('交接任务'))
    expect(onRequestHandoff).toHaveBeenCalledWith('t-1')
    expect(onSelect).not.toHaveBeenCalled()
  })

  it('opens the task handoff timeline from its handoff summary', () => {
    const onOpenHandoff = vi.fn()
    render(
      <TaskCard
        id="t-1"
        title="Handoff task"
        status="handoff"
        handoff={{
          id: 'h-1', task_id: 't-1', status: 'ready', reason: 'manual',
          from_agent_id: 'a-1', from_agent_name: 'Coder', from_model_id: 'gpt',
          to_agent_id: 'a-2', to_agent_name: 'Reviewer', to_model_id: 'claude',
        }}
        onOpenHandoff={onOpenHandoff}
      />
    )
    fireEvent.click(screen.getByText(/交接 Coder → Reviewer/))
    expect(onOpenHandoff).toHaveBeenCalledWith('h-1')
  })
})
