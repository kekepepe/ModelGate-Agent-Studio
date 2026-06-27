import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import RoutingResultCard from '../RoutingResultCard'
import type { RoutingResult } from '../../types/router'

const mockResult: RoutingResult = {
  selected_model_id: 'claude-3-opus',
  selected_agent_id: 'agent-coder',
  backup_model_ids: ['deepseek-coder', 'gpt-4-turbo'],
  routing_reason: {
    summary: 'Claude 3 Opus 被选为编码任务的首选模型',
    primary_factors: ['编码任务优先选择代码能力强的模型', 'Claude 3 Opus 在 Coder 角色中排名第1'],
    secondary_factors: ['上下文窗口充足'],
    tradeoffs: ['成本较高'],
  },
  confidence: 0.92,
  risk_flags: [
    {
      type: 'quota_warning',
      severity: 'medium',
      message: 'Claude 3 Opus 额度使用率较高',
      suggestion: '系统已自动设置备用模型',
    },
  ],
  score_breakdown: [
    {
      model_id: 'claude-3-opus',
      model_name: 'Claude 3 Opus',
      total_score: 0.92,
      dimension_scores: [
        { dimension: 'capability_match', score: 0.95, weight: 0.25, weighted_score: 0.2375, reason: '匹配度高' },
        { dimension: 'role_match', score: 1.0, weight: 0.20, weighted_score: 0.20, reason: '排名第1' },
      ],
    },
  ],
  is_user_override: false,
}

const mockResultNoFlags: RoutingResult = {
  ...mockResult,
  risk_flags: [],
  confidence: 0.85,
}

const mockResultLowConfidence: RoutingResult = {
  ...mockResult,
  confidence: 0.55,
  risk_flags: [
    {
      type: 'low_confidence',
      severity: 'low',
      message: '多个模型评分接近',
    },
  ],
}

describe('RoutingResultCard', () => {
  it('renders selected model name and confidence', () => {
    render(<RoutingResultCard result={mockResult} autoDismiss={false} />)
    expect(screen.getByText('Claude 3 Opus')).toBeInTheDocument()
    expect(screen.getByText('92%')).toBeInTheDocument()
  })

  it('renders routing reason summary and factors', () => {
    render(<RoutingResultCard result={mockResult} autoDismiss={false} />)
    expect(screen.getByText(/Claude 3 Opus 被选为编码任务的首选模型/)).toBeInTheDocument()
    expect(screen.getByText(/编码任务优先选择代码能力强的模型/)).toBeInTheDocument()
  })

  it('renders risk flags when present', () => {
    render(<RoutingResultCard result={mockResult} autoDismiss={false} />)
    expect(screen.getByText(/Claude 3 Opus 额度使用率较高/)).toBeInTheDocument()
  })

  it('does not render risk flags when empty', () => {
    render(<RoutingResultCard result={mockResultNoFlags} autoDismiss={false} />)
    expect(screen.queryByTestId('risk-flag')).not.toBeInTheDocument()
  })

  it('renders backup models', () => {
    render(<RoutingResultCard result={mockResult} autoDismiss={false} />)
    expect(screen.getByText('DeepSeek Coder')).toBeInTheDocument()
    expect(screen.getByText('GPT-4 Turbo')).toBeInTheDocument()
  })

  it('calls onAccept when accept button clicked', () => {
    const onAccept = vi.fn()
    render(<RoutingResultCard result={mockResult} onAccept={onAccept} autoDismiss={false} />)
    fireEvent.click(screen.getByTestId('accept-model'))
    expect(onAccept).toHaveBeenCalled()
  })

  it('opens override modal when switch model clicked', () => {
    render(<RoutingResultCard result={mockResult} autoDismiss={false} />)
    fireEvent.click(screen.getByTestId('switch-model'))
    expect(screen.getByTestId('backup-model-deepseek-coder')).toBeInTheDocument()
    expect(screen.getByText(/当前推荐模型/)).toBeInTheDocument()
  })

  it('dismisses card when X clicked', () => {
    const onDismiss = vi.fn()
    render(<RoutingResultCard result={mockResult} onDismiss={onDismiss} autoDismiss={false} />)
    fireEvent.click(screen.getByTestId('card-dismiss'))
    expect(onDismiss).toHaveBeenCalled()
  })

  it('shows green confidence bar for high confidence', () => {
    render(<RoutingResultCard result={mockResult} autoDismiss={false} />)
    expect(screen.getByText('92%')).toBeInTheDocument()
  })

  it('shows yellow confidence bar for medium confidence', () => {
    render(<RoutingResultCard result={mockResultLowConfidence} autoDismiss={false} />)
    expect(screen.getByText('55%')).toBeInTheDocument()
  })

  it('renders score breakdown toggle', () => {
    render(<RoutingResultCard result={mockResult} autoDismiss={false} />)
    expect(screen.getByTestId('score-breakdown-toggle')).toBeInTheDocument()
  })
})
