import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import WorkerBadge from '../WorkerBadge'

describe('WorkerBadge', () => {
  it('renders model name', () => {
    render(<WorkerBadge modelName="GPT-4o" status="running" />)
    expect(screen.getByText('GPT-4o')).toBeInTheDocument()
  })

  it('shows status label in non-compact mode', () => {
    render(<WorkerBadge modelName="GPT-4o" status="running" />)
    expect(screen.getByText('运行中')).toBeInTheDocument()
  })

  it('hides status label in compact mode', () => {
    render(<WorkerBadge modelName="GPT-4o" status="running" compact />)
    expect(screen.queryByText('运行中')).not.toBeInTheDocument()
  })

  it('renders dash for missing model name', () => {
    render(<WorkerBadge status="idle" />)
    expect(screen.getByText('—')).toBeInTheDocument()
  })

  it('uses correct dot color for each status', () => {
    const statuses = ['idle', 'running', 'handoff_required', 'completed', 'failed']
    statuses.forEach((status) => {
      const { container } = render(<WorkerBadge modelName="test" status={status} />)
      const dot = container.querySelector('.rounded-full')
      expect(dot).toBeTruthy()
    })
  })

  it('applies breathe animation for running', () => {
    const { container } = render(<WorkerBadge modelName="test" status="running" />)
    const dot = container.querySelector('.animate-breathe-dot')
    expect(dot).toBeTruthy()
  })

  it('applies dot-pulse animation for handoff_required', () => {
    const { container } = render(<WorkerBadge modelName="test" status="handoff_required" />)
    const dot = container.querySelector('.animate-dot-pulse')
    expect(dot).toBeTruthy()
  })
})
