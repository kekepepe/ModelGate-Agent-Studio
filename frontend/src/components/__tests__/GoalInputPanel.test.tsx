import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import GoalInputPanel from '../GoalInputPanel'

function renderWithQuery(ui: React.ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>)
}

describe('GoalInputPanel', () => {
  it('renders input form when no active goal', () => {
    renderWithQuery(<GoalInputPanel onGoalCreated={vi.fn()} />)
    expect(screen.getByPlaceholderText('描述你的目标...')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '开始' })).toBeInTheDocument()
  })

  it('disables button when input is empty', () => {
    renderWithQuery(<GoalInputPanel onGoalCreated={vi.fn()} />)
    const btn = screen.getByRole('button', { name: '开始' })
    expect(btn).toBeDisabled()
  })

  it('shows active goal info when goalId is set', () => {
    renderWithQuery(<GoalInputPanel onGoalCreated={vi.fn()} activeGoalId="g-1" goalTitle="Test Goal" />)
    expect(screen.getByText('Test Goal')).toBeInTheDocument()
    expect(screen.getByText('g-1')).toBeInTheDocument()
    expect(screen.queryByPlaceholderText('描述你的目标...')).not.toBeInTheDocument()
  })
})
