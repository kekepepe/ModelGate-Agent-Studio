import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import StatsSummaryCards from '../StatsSummaryCards'
import type { DashboardStats } from '../../types/dashboard'

const stats: DashboardStats = {
  active_goals: 2,
  completed_goals_today: 3,
  total_tokens_today: 1200,
  total_model_calls_today: 4,
  total_tool_calls_today: 5,
  handoffs_today: 1,
  agents_status: [],
  model_usage: [],
  tool_usage: [],
  recent_goals: [],
}

describe('StatsSummaryCards', () => {
  it('renders dashboard summary values', () => {
    render(<StatsSummaryCards data={stats} />)
    expect(screen.getByText('Active Goals')).toBeInTheDocument()
    expect(screen.getByText('Completed Today')).toBeInTheDocument()
    expect(screen.getByText('Tokens Today')).toBeInTheDocument()
    expect(screen.getByText('1,200')).toBeInTheDocument()
  })

  it('renders loading skeletons', () => {
    const { container } = render(<StatsSummaryCards isLoading />)
    expect(container.querySelectorAll('.animate-pulse').length).toBeGreaterThan(0)
  })
})
