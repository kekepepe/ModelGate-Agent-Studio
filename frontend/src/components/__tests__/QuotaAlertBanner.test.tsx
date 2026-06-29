import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import QuotaAlertBanner from '../QuotaAlertBanner'
import type { QuotaStatus } from '../../types/quota'

describe('QuotaAlertBanner', () => {
  it('returns null when no alerts', () => {
    const { container } = render(<QuotaAlertBanner alerts={[]} />)
    expect(container.firstChild).toBeNull()
  })

  it('shows limited alert with highest priority', () => {
    const alerts = [
      { modelId: 'm1', modelName: 'GPT-4', status: 'warning' as QuotaStatus, usagePercent: 0.75 },
      { modelId: 'm2', modelName: 'Claude', status: 'limited' as QuotaStatus, usagePercent: 1.0 },
    ]
    render(<QuotaAlertBanner alerts={alerts} />)
    expect(screen.getByText(/Claude 已受限/)).toBeInTheDocument()
    expect(screen.getByText(/还有 1 个模型预警/)).toBeInTheDocument()
  })

  it('shows cooldown alert', () => {
    const alerts = [
      { modelId: 'm1', modelName: 'Kimi', status: 'cooldown' as QuotaStatus },
    ]
    render(<QuotaAlertBanner alerts={alerts} />)
    expect(screen.getByText(/Kimi 冷却中/)).toBeInTheDocument()
  })

  it('shows warning alert', () => {
    const alerts = [
      { modelId: 'm1', modelName: 'GPT-4', status: 'warning' as QuotaStatus, usagePercent: 0.78 },
    ]
    render(<QuotaAlertBanner alerts={alerts} onDismiss={vi.fn()} />)
    expect(screen.getByText(/GPT-4 注意/)).toBeInTheDocument()
    expect(screen.getByText(/使用率 78.0%/)).toBeInTheDocument()
  })

  it('calls onDismiss when clicking X', () => {
    const onDismiss = vi.fn()
    const alerts = [
      { modelId: 'm1', modelName: 'GPT-4', status: 'warning' as QuotaStatus },
    ]
    render(<QuotaAlertBanner alerts={alerts} onDismiss={onDismiss} />)
    const closeBtn = screen.getByRole('button')
    fireEvent.click(closeBtn)
    expect(onDismiss).toHaveBeenCalledWith('m1')
  })

  it('does not show dismiss button for limited', () => {
    const onDismiss = vi.fn()
    const alerts = [
      { modelId: 'm1', modelName: 'GPT-4', status: 'limited' as QuotaStatus },
    ]
    const { container } = render(<QuotaAlertBanner alerts={alerts} onDismiss={onDismiss} />)
    const buttons = container.querySelectorAll('button')
    expect(buttons.length).toBe(0)
  })
})
