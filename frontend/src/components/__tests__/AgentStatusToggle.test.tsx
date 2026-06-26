import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import AgentStatusToggle from '../AgentStatusToggle'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false },
  },
})

function Wrapper({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

describe('AgentStatusToggle', () => {
  it('renders enabled state correctly', () => {
    render(<Wrapper><AgentStatusToggle agentId="a1" isEnabled={true} /></Wrapper>)
    const toggle = screen.getByLabelText('禁用 Agent')
    expect(toggle).toBeInTheDocument()
  })

  it('renders disabled state correctly', () => {
    render(<Wrapper><AgentStatusToggle agentId="a1" isEnabled={false} /></Wrapper>)
    const toggle = screen.getByLabelText('启用 Agent')
    expect(toggle).toBeInTheDocument()
  })

  it('shows confirmation dialog when disabling running agent', () => {
    render(
      <Wrapper>
        <AgentStatusToggle agentId="a1" isEnabled={true} hasRunningTask={true} />
      </Wrapper>
    )
    fireEvent.click(screen.getByLabelText('禁用 Agent'))
    expect(screen.getByText(/该 Agent 有进行中任务/i)).toBeInTheDocument()
  })

  it('can cancel confirmation dialog', () => {
    render(
      <Wrapper>
        <AgentStatusToggle agentId="a1" isEnabled={true} hasRunningTask={true} />
      </Wrapper>
    )
    fireEvent.click(screen.getByLabelText('禁用 Agent'))
    expect(screen.getByText(/该 Agent 有进行中任务/i)).toBeInTheDocument()

    fireEvent.click(screen.getByText('取消'))
    expect(screen.queryByText(/该 Agent 有进行中任务/i)).not.toBeInTheDocument()
  })
})
