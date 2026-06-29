import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import HandoffConfirmModal from '../HandoffConfirmModal'
import type { AgentListItem } from '../../types/agent'

const agents: AgentListItem[] = [
  { id: 'a-1', name: 'Coder', role: 'coder', status: 'running', default_model_id: 'claude-opus-4-7', is_enabled: true, total_tasks_completed: 0, created_at: '' },
  { id: 'a-2', name: 'Reviewer', role: 'reviewer', status: 'idle', default_model_id: 'claude-sonnet-4-6', is_enabled: true, total_tasks_completed: 0, created_at: '' },
]

describe('HandoffConfirmModal', () => {
  it('excludes the from agent from candidates', () => {
    render(
      <HandoffConfirmModal
        taskId="task-1"
        agents={agents}
        fromAgentId="a-1"
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />
    )
    const select = screen.getByRole('combobox', { name: /接手 Agent/ }) as HTMLSelectElement
    const optionValues = Array.from(select.options).map((o) => o.value)
    expect(optionValues).toEqual(['a-2'])
  })

  it('submits the chosen agent, reason and description', () => {
    const onConfirm = vi.fn()
    render(
      <HandoffConfirmModal
        taskId="task-1"
        agents={agents}
        fromAgentId="a-1"
        onConfirm={onConfirm}
        onCancel={vi.fn()}
      />
    )
    fireEvent.change(screen.getByRole('combobox', { name: /接手 Agent/ }), { target: { value: 'a-2' } })
    fireEvent.change(screen.getByRole('combobox', { name: /交接原因/ }), { target: { value: 'quota_exceeded' } })
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'token 接近上限' } })
    fireEvent.click(screen.getByRole('button', { name: '确认交接' }))
    expect(onConfirm).toHaveBeenCalledWith({
      to_agent_id: 'a-2',
      reason: 'quota_exceeded',
      reason_description: 'token 接近上限',
    })
  })

  it('calls onCancel when cancel is clicked', () => {
    const onCancel = vi.fn()
    render(
      <HandoffConfirmModal
        taskId="task-1"
        agents={agents}
        fromAgentId="a-1"
        onConfirm={vi.fn()}
        onCancel={onCancel}
      />
    )
    fireEvent.click(screen.getByRole('button', { name: '取消' }))
    expect(onCancel).toHaveBeenCalled()
  })

  it('disables submit while submitting', () => {
    render(
      <HandoffConfirmModal
        taskId="task-1"
        agents={agents}
        fromAgentId="a-1"
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
        isSubmitting
      />
    )
    const submit = screen.getByRole('button', { name: '生成中...' })
    expect(submit).toBeDisabled()
  })
})
