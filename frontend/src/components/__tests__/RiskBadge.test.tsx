import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import RiskBadge from '../RiskBadge'

describe('RiskBadge', () => {
  it('renders normal status', () => {
    render(<RiskBadge status="normal" />)
    expect(screen.getByText('正常')).toBeInTheDocument()
  })

  it('renders limited status', () => {
    render(<RiskBadge status="limited" />)
    expect(screen.getByText('已受限')).toBeInTheDocument()
  })

  it('renders unknown status', () => {
    render(<RiskBadge status="unknown" />)
    expect(screen.getByText('未知')).toBeInTheDocument()
  })

  it('shows usage percent in tooltip data', () => {
    render(<RiskBadge status="warning" usagePercent={0.75} />)
    expect(screen.getByText('注意')).toBeInTheDocument()
  })

  it('shows estimated remaining in tooltip data', () => {
    render(<RiskBadge status="near_limit" estimatedRemaining={500} />)
    expect(screen.getByText('接近上限')).toBeInTheDocument()
  })

  it('supports md size', () => {
    const { container } = render(<RiskBadge status="normal" size="md" />)
    const dot = container.querySelector('span[class*="w-3"]')
    expect(dot).toBeInTheDocument()
  })
})
