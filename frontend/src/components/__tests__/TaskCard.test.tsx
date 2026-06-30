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
})
