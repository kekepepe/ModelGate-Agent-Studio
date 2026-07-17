import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import PixelOfficeRenderer from '../PixelOfficeRenderer'
import type { WorkspaceViewModel } from '../../utils/workspaceViewModel'

const emptyViewModel: WorkspaceViewModel = {
  stations: [],
  edges: [],
  handoffs: [],
}

describe('PixelOfficeRenderer', () => {
  it('renders the empty-state message outside the office scene', () => {
    const { container } = render(
      <PixelOfficeRenderer
        viewModel={emptyViewModel}
        onSelectTask={vi.fn()}
        onRequestHandoff={vi.fn()}
        onOpenHandoff={vi.fn()}
      />,
    )

    const emptyState = screen.getByRole('status')
    const officeRoom = container.querySelector('.pixel-office-room')

    expect(emptyState).toHaveTextContent('办公室等待任务')
    expect(emptyState).toHaveTextContent('创建 Goal 后，Agent 会进入对应工位。')
    expect(officeRoom).not.toContainElement(emptyState)
    expect(container.querySelector('.pixel-office-empty')).not.toBeInTheDocument()
  })
})
