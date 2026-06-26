import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import AgentList from '../AgentList'
import type { AgentListItem } from '../../types/agent'

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
})

function Wrapper({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

const mockAgents: AgentListItem[] = [
  {
    id: 'agent-1',
    name: 'Planner Agent',
    role: 'planner',
    description: '任务规划专家',
    status: 'idle',
    default_model_id: 'claude-3-opus',
    is_enabled: true,
    total_tasks_completed: 10,
    created_at: '2026-06-25T00:00:00Z',
  },
  {
    id: 'agent-2',
    name: 'Coder Agent',
    role: 'coder',
    description: '代码编写专家',
    status: 'running',
    default_model_id: 'deepseek-coder',
    is_enabled: true,
    total_tasks_completed: 25,
    created_at: '2026-06-25T00:00:00Z',
  },
  {
    id: 'agent-3',
    name: 'Disabled Agent',
    role: 'reviewer',
    description: '已禁用',
    status: 'idle',
    default_model_id: 'gpt-4-turbo',
    is_enabled: false,
    total_tasks_completed: 0,
    created_at: '2026-06-25T00:00:00Z',
  },
]

describe('AgentList', () => {
  it('renders empty state when no agents', () => {
    render(<Wrapper><AgentList agents={[]} onSelect={vi.fn()} /></Wrapper>)
    expect(screen.getByText(/还没有配置 Agent Station/i)).toBeInTheDocument()
  })

  it('renders agent names', () => {
    render(<Wrapper><AgentList agents={mockAgents} onSelect={vi.fn()} /></Wrapper>)
    expect(screen.getByText('Planner Agent')).toBeInTheDocument()
    expect(screen.getByText('Coder Agent')).toBeInTheDocument()
    expect(screen.getByText('Disabled Agent')).toBeInTheDocument()
  })

  it('renders role tags', () => {
    render(<Wrapper><AgentList agents={mockAgents} onSelect={vi.fn()} /></Wrapper>)
    expect(screen.getByText('规划师')).toBeInTheDocument()
    expect(screen.getByText('编码师')).toBeInTheDocument()
    expect(screen.getByText('审查员')).toBeInTheDocument()
  })

  it('renders status indicators', () => {
    render(<Wrapper><AgentList agents={mockAgents} onSelect={vi.fn()} /></Wrapper>)
    expect(screen.getByText('空闲')).toBeInTheDocument()
    expect(screen.getByText('执行中')).toBeInTheDocument()
    expect(screen.getByText('禁用')).toBeInTheDocument()
  })

  it('calls onSelect when clicking an agent row', () => {
    const onSelect = vi.fn()
    render(<Wrapper><AgentList agents={mockAgents} onSelect={onSelect} /></Wrapper>)
    fireEvent.click(screen.getByText('Planner Agent'))
    expect(onSelect).toHaveBeenCalledWith(mockAgents[0])
  })

  it('disabled agent has reduced opacity styling', () => {
    const { container } = render(<Wrapper><AgentList agents={mockAgents} onSelect={vi.fn()} /></Wrapper>)
    const rows = container.querySelectorAll('.opacity-60')
    expect(rows.length).toBe(1)
  })
})
