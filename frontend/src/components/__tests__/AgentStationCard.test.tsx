import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import AgentStationCard from '../AgentStationCard'
import type { WorkspaceAgent } from '../../types/workspace'

const agent: WorkspaceAgent = {
  id: 'a-1',
  name: 'Coder #1',
  role: 'coder',
  status: 'running',
  default_model_id: 'model-gpt-4-turbo',
  is_enabled: true,
}

describe('AgentStationCard', () => {
  it('renders agent name and role', () => {
    render(
      <MemoryRouter>
        <AgentStationCard agent={agent} tasks={[]} />
      </MemoryRouter>
    )
    expect(screen.getByText('Coder #1')).toBeInTheDocument()
    expect(screen.getByText('coder')).toBeInTheDocument()
  })

  it('renders worker badge with model info', () => {
    render(
      <MemoryRouter>
        <AgentStationCard
          agent={agent}
          worker={{ id: 'w-1', agent_id: 'a-1', model_id: 'model-gpt-4-turbo', status: 'running', total_tokens_used: 100, model_name: 'GPT-4 Turbo' }}
          tasks={[]}
        />
      </MemoryRouter>
    )
    expect(screen.getByText('GPT-4 Turbo')).toBeInTheDocument()
  })

  it('shows empty state when no tasks', () => {
    render(
      <MemoryRouter>
        <AgentStationCard agent={agent} tasks={[]} />
      </MemoryRouter>
    )
    expect(screen.getByText('暂无任务')).toBeInTheDocument()
  })

  it('shows tasks assigned to this agent', () => {
    const tasks = [
      { id: 't-1', title: 'Build login', status: 'running', agent_id: 'a-1' },
    ]
    render(
      <MemoryRouter>
        <AgentStationCard agent={agent} tasks={tasks} />
      </MemoryRouter>
    )
    expect(screen.getByText('Build login')).toBeInTheDocument()
  })

  it('calls onTaskClick when task is clicked', () => {
    const onTaskClick = vi.fn()
    const tasks = [
      { id: 't-1', title: 'Build login', status: 'running', agent_id: 'a-1' },
    ]
    render(
      <MemoryRouter>
        <AgentStationCard agent={agent} tasks={tasks} onTaskClick={onTaskClick} />
      </MemoryRouter>
    )
    fireEvent.click(screen.getByText('Build login'))
    expect(onTaskClick).toHaveBeenCalledWith('t-1')
  })
})
