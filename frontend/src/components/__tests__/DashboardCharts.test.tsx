import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import TokenUsageChart from '../TokenUsageChart'
import ToolUsageChart from '../ToolUsageChart'

describe('Dashboard charts', () => {
  it('shows token empty state', () => {
    render(<TokenUsageChart data={[]} />)
    expect(screen.getByText('暂无 Token 趋势数据')).toBeInTheDocument()
  })

  it('shows tool usage empty state', () => {
    render(<ToolUsageChart data={[]} />)
    expect(screen.getByText('暂无工具调用数据')).toBeInTheDocument()
  })
})
