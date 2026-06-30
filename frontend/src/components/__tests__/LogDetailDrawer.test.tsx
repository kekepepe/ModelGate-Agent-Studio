import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import LogDetailDrawer from '../LogDetailDrawer'
import type { ExecutionLog } from '../../types/log'

const mockLog: ExecutionLog = {
  id: 'log-detail-1',
  event_type: 'model_call',
  event_status: 'completed',
  goal_id: 'goal-1',
  task_id: 'task-1',
  agent_id: 'agent-1',
  agent_name: 'Coder',
  model_id: 'gpt-4o',
  model_name: 'GPT-4o',
  input_summary: 'Generate login',
  output_summary: '```tsx\nimport React',
  token_usage: { input_tokens: 100, output_tokens: 50, total_tokens: 150 },
  latency_ms: 1200,
  created_at: new Date().toISOString(),
}

const errorLog: ExecutionLog = {
  id: 'log-detail-2',
  event_type: 'error',
  event_status: 'failed',
  error_type: 'api_error',
  error_code: '429',
  error_message: 'Rate limit exceeded',
  created_at: new Date().toISOString(),
}

function renderWithRouter(ui: React.ReactElement) {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
}

describe('LogDetailDrawer', () => {
  it('renders null when log is null', () => {
    const { container } = renderWithRouter(<LogDetailDrawer log={null} onClose={() => {}} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders log details for model_call', () => {
    renderWithRouter(<LogDetailDrawer log={mockLog} onClose={() => {}} />)
    expect(screen.getByText('模型调用')).toBeInTheDocument()
    expect(screen.getByText('Coder')).toBeInTheDocument()
    expect(screen.getByText('GPT-4o')).toBeInTheDocument()
    expect(screen.getByText('150')).toBeInTheDocument()
    expect(screen.getByText(/延迟: 1200 ms/)).toBeInTheDocument()
  })

  it('renders error details for error log', () => {
    renderWithRouter(<LogDetailDrawer log={errorLog} onClose={() => {}} />)
    expect(screen.getByText('Rate limit exceeded')).toBeInTheDocument()
    expect(screen.getByText(/api_error/)).toBeInTheDocument()
  })

  it('calls onClose when close button clicked', () => {
    const onClose = vi.fn()
    renderWithRouter(<LogDetailDrawer log={mockLog} onClose={onClose} />)
    fireEvent.click(screen.getByLabelText('close drawer'))
    expect(onClose).toHaveBeenCalled()
  })
})
