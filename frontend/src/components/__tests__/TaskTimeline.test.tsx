import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import TaskTimeline from '../TaskTimeline'
import type { TaskTimelineResponse } from '../../types/log'

const mockTimeline: TaskTimelineResponse = {
  events: [
    {
      time: '2026-06-30T10:00:00Z',
      event_type: 'model_call',
      event_status: 'completed',
      agent_id: 'agent-1',
      summary: 'Generate component',
      icon_type: 'model_call',
    },
    {
      time: '2026-06-30T10:05:00Z',
      event_type: 'handoff_created',
      event_status: 'created',
      summary: 'Handoff created',
      icon_type: 'handoff_created',
    },
    {
      time: '2026-06-30T10:10:00Z',
      event_type: 'error',
      event_status: 'failed',
      summary: 'Something broke',
      icon_type: 'error',
    },
  ],
  summary: {
    total_duration_ms: 600000,
    total_tokens: 150,
    model_call_count: 1,
    handoff_count: 1,
    error_count: 1,
  },
}

describe('TaskTimeline', () => {
  it('renders loading state', () => {
    render(<TaskTimeline isLoading={true} />)
    expect(document.querySelector('.animate-pulse')).toBeInTheDocument()
  })

  it('renders empty state', () => {
    render(<TaskTimeline timeline={{ events: [], summary: { total_duration_ms: 0, total_tokens: 0, model_call_count: 0, handoff_count: 0, error_count: 0 } }} />)
    expect(screen.getByText('该 Task 暂无执行日志')).toBeInTheDocument()
  })

  it('renders timeline events and summary stats', () => {
    render(<TaskTimeline timeline={mockTimeline} />)
    expect(screen.getByText('Generate component')).toBeInTheDocument()
    expect(screen.getByText('Handoff created')).toBeInTheDocument()
    expect(screen.getByText('Something broke')).toBeInTheDocument()
    expect(screen.getByText('150')).toBeInTheDocument()
    const ones = screen.getAllByText('1')
    expect(ones.length).toBe(3) // model_call_count, handoff_count, error_count
  })

  it('renders error event with red background', () => {
    const { container } = render(<TaskTimeline timeline={mockTimeline} />)
    const errorElements = container.querySelectorAll('.bg-red-50')
    expect(errorElements.length).toBeGreaterThan(0)
  })
})
