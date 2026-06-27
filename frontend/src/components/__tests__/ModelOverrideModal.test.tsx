import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import ModelOverrideModal from '../ModelOverrideModal'
import type { RoutingResult } from '../../types/router'

const mockResult: RoutingResult = {
  selected_model_id: 'claude-3-opus',
  selected_agent_id: 'agent-coder',
  backup_model_ids: ['deepseek-coder', 'gpt-4-turbo'],
  routing_reason: {
    summary: '推荐 Claude 3 Opus',
    primary_factors: [],
    secondary_factors: [],
    tradeoffs: [],
  },
  confidence: 0.92,
  risk_flags: [],
  score_breakdown: [],
  is_user_override: false,
}

describe('ModelOverrideModal', () => {
  it('renders current recommended model', () => {
    render(<ModelOverrideModal result={mockResult} onConfirm={vi.fn()} onCancel={vi.fn()} />)
    expect(screen.getByText(/当前推荐模型/)).toBeInTheDocument()
    expect(screen.getByText('Claude 3 Opus')).toBeInTheDocument()
  })

  it('renders backup model list', () => {
    render(<ModelOverrideModal result={mockResult} onConfirm={vi.fn()} onCancel={vi.fn()} />)
    expect(screen.getByText('备用模型')).toBeInTheDocument()
    expect(screen.getByTestId('backup-model-deepseek-coder')).toBeInTheDocument()
    expect(screen.getByTestId('backup-model-gpt-4-turbo')).toBeInTheDocument()
  })

  it('selects a backup model when clicked', () => {
    render(<ModelOverrideModal result={mockResult} onConfirm={vi.fn()} onCancel={vi.fn()} />)
    fireEvent.click(screen.getByTestId('backup-model-deepseek-coder'))
    expect(screen.getByText(/将切换至/)).toBeInTheDocument()
    // The confirmation message shows the selected model name
    expect(screen.getByText(/原推荐模型为/)).toBeInTheDocument()
  })

  it('disables confirm button when no model selected', () => {
    render(<ModelOverrideModal result={mockResult} onConfirm={vi.fn()} onCancel={vi.fn()} />)
    const confirmBtn = screen.getByTestId('override-confirm')
    expect(confirmBtn).toBeDisabled()
  })

  it('enables confirm button after selection', () => {
    render(<ModelOverrideModal result={mockResult} onConfirm={vi.fn()} onCancel={vi.fn()} />)
    fireEvent.click(screen.getByTestId('backup-model-deepseek-coder'))
    const confirmBtn = screen.getByTestId('override-confirm')
    expect(confirmBtn).not.toBeDisabled()
  })

  it('calls onConfirm with selected model id', () => {
    const onConfirm = vi.fn()
    render(<ModelOverrideModal result={mockResult} onConfirm={onConfirm} onCancel={vi.fn()} />)
    fireEvent.click(screen.getByTestId('backup-model-deepseek-coder'))
    fireEvent.click(screen.getByTestId('override-confirm'))
    expect(onConfirm).toHaveBeenCalledWith('deepseek-coder')
  })

  it('calls onCancel when cancel button clicked', () => {
    const onCancel = vi.fn()
    render(<ModelOverrideModal result={mockResult} onConfirm={vi.fn()} onCancel={onCancel} />)
    fireEvent.click(screen.getByTestId('override-cancel'))
    expect(onCancel).toHaveBeenCalled()
  })

  it('shows empty state when no backup models', () => {
    const noBackupResult = { ...mockResult, backup_model_ids: [] }
    render(<ModelOverrideModal result={noBackupResult} onConfirm={vi.fn()} onCancel={vi.fn()} />)
    expect(screen.getByText('无备用模型')).toBeInTheDocument()
  })
})
