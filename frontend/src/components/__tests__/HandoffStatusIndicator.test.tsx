import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import HandoffStatusIndicator from '../HandoffStatusIndicator'
import { HANDOFF_STATUS_LABELS } from '../../types/handoff'

describe('HandoffStatusIndicator', () => {
  it('marks earlier steps as done for ready status', () => {
    render(<HandoffStatusIndicator status="ready" />)
    expect(screen.getByText(HANDOFF_STATUS_LABELS.requested)).toBeInTheDocument()
    expect(screen.getByText(HANDOFF_STATUS_LABELS.generating_summary)).toBeInTheDocument()
    expect(screen.getByText(HANDOFF_STATUS_LABELS.ready)).toBeInTheDocument()
  })

  it('highlights current step for accepted', () => {
    render(<HandoffStatusIndicator status="accepted" />)
    expect(screen.getByText(HANDOFF_STATUS_LABELS.accepted)).toBeInTheDocument()
  })

  it('renders failed message and dims steps', () => {
    render(<HandoffStatusIndicator status="failed" />)
    expect(screen.getByText('失败')).toBeInTheDocument()
  })
})
