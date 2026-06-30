import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import LogListItem from '../LogListItem'
import type { ExecutionLog } from '../../types/log'

const mockLog: ExecutionLog = {
  id: 'log-1',
  event_type: 'model_call',
  event_status: 'completed',
  agent_id: 'agent-1',
  agent_name: 'Coder',
  model_id: 'gpt-4o',
  input_summary: 'Generate login component',
  created_at: new Date().toISOString(),
}

const errorLog: ExecutionLog = {
  id: 'log-2',
  event_type: 'error',
  event_status: 'failed',
  agent_id: 'agent-2',
  error_message: 'Connection timeout',
  created_at: new Date().toISOString(),
}

describe('LogListItem', () => {
  it('renders log with type icon and status badge', () => {
    render(<LogListItem log={mockLog} />)
    expect(screen.getByText('Coder')).toBeInTheDocument()
    expect(screen.getByText('gpt-4o')).toBeInTheDocument()
    expect(screen.getByText('Generate login component')).toBeInTheDocument()
  })

  it('shows error styling for failed logs', () => {
    render(<LogListItem log={errorLog} />)
    expect(screen.getByText('Connection timeout')).toBeInTheDocument()
  })

  it('calls onClick when clicked', () => {
    const onClick = vi.fn()
    render(<LogListItem log={mockLog} onClick={onClick} />)
    fireEvent.click(screen.getByText('Generate login component'))
    expect(onClick).toHaveBeenCalled()
  })

  it('shows selected state', () => {
    const { container } = render(<LogListItem log={mockLog} isSelected={true} />)
    expect(container.firstChild).toHaveClass('bg-stone-100')
  })
})
