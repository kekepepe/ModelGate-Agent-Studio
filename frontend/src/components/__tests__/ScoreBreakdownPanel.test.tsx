import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import ScoreBreakdownPanel from '../ScoreBreakdownPanel'
import type { ScoreBreakdown } from '../../types/router'

const mockScoreBreakdown: ScoreBreakdown[] = [
  {
    model_id: 'claude-3-opus',
    model_name: 'Claude 3 Opus',
    total_score: 0.92,
    dimension_scores: [
      { dimension: 'capability_match', score: 0.95, weight: 0.25, weighted_score: 0.2375, reason: '匹配度高' },
      { dimension: 'role_match', score: 1.0, weight: 0.20, weighted_score: 0.20, reason: '排名第1' },
      { dimension: 'context_fit', score: 0.90, weight: 0.15, weighted_score: 0.135, reason: '余量充足' },
    ],
  },
]

describe('ScoreBreakdownPanel', () => {
  it('renders toggle button', () => {
    render(<ScoreBreakdownPanel scoreBreakdown={mockScoreBreakdown} confidence={0.92} />)
    expect(screen.getByTestId('score-breakdown-toggle')).toBeInTheDocument()
    expect(screen.getByText('查看评分详情')).toBeInTheDocument()
  })

  it('expands when toggle clicked', () => {
    render(<ScoreBreakdownPanel scoreBreakdown={mockScoreBreakdown} confidence={0.92} />)
    fireEvent.click(screen.getByTestId('score-breakdown-toggle'))
    expect(screen.getByTestId('score-breakdown-content')).toBeInTheDocument()
    expect(screen.getByText(/Claude 3 Opus/)).toBeInTheDocument()
  })

  it('collapses when toggle clicked again', () => {
    render(<ScoreBreakdownPanel scoreBreakdown={mockScoreBreakdown} confidence={0.92} />)
    fireEvent.click(screen.getByTestId('score-breakdown-toggle'))
    expect(screen.getByTestId('score-breakdown-content')).toBeInTheDocument()
    fireEvent.click(screen.getByTestId('score-breakdown-toggle'))
    expect(screen.queryByTestId('score-breakdown-content')).not.toBeInTheDocument()
  })

  it('displays dimension labels', () => {
    render(<ScoreBreakdownPanel scoreBreakdown={mockScoreBreakdown} confidence={0.92} />)
    fireEvent.click(screen.getByTestId('score-breakdown-toggle'))
    expect(screen.getByText('能力匹配度')).toBeInTheDocument()
    expect(screen.getByText('角色匹配度')).toBeInTheDocument()
    expect(screen.getByText('上下文适配度')).toBeInTheDocument()
  })

  it('displays score calculation', () => {
    render(<ScoreBreakdownPanel scoreBreakdown={mockScoreBreakdown} confidence={0.92} />)
    fireEvent.click(screen.getByTestId('score-breakdown-toggle'))
    expect(screen.getByText(/0.95 × 0.25 = 0.2375/)).toBeInTheDocument()
  })

  it('displays total weighted score and confidence', () => {
    render(<ScoreBreakdownPanel scoreBreakdown={mockScoreBreakdown} confidence={0.92} />)
    fireEvent.click(screen.getByTestId('score-breakdown-toggle'))
    expect(screen.getByText('加权得分总和')).toBeInTheDocument()
    expect(screen.getByText('置信度')).toBeInTheDocument()
    expect(screen.getByText('92.0%')).toBeInTheDocument()
  })

  it('returns null when scoreBreakdown is empty', () => {
    const { container } = render(<ScoreBreakdownPanel scoreBreakdown={[]} confidence={0.5} />)
    expect(container.firstChild).toBeNull()
  })
})
