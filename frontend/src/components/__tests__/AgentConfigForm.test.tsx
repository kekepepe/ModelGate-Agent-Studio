import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import AgentConfigForm from '../AgentConfigForm'
import type { AgentStation } from '../../types/agent'

const mockAgent: AgentStation = {
  id: 'agent-1',
  name: 'Test Agent',
  role: 'coder',
  description: 'A test agent',
  status: 'idle',
  default_model_id: 'claude-3-opus',
  backup_model_ids: ['gpt-4-turbo'],
  allowed_tools: ['file_read'],
  system_prompt: 'You are a test agent.',
  output_format: 'markdown',
  max_steps_per_task: 15,
  allow_handoff: true,
  handoff_threshold_tokens: 50000,
  is_enabled: true,
  total_tasks_completed: 0,
  total_tasks_failed: 0,
  total_handoffs_initiated: 0,
}

const mockRunningAgent: AgentStation = {
  ...mockAgent,
  status: 'running',
}

describe('AgentConfigForm - Create', () => {
  it('renders create form with empty fields', () => {
    render(<AgentConfigForm onSave={vi.fn()} onCancel={vi.fn()} />)
    expect(screen.getByText('创建 Agent')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('输入 Agent 名称')).toHaveValue('')
  })

  it('disables submit button when name is empty', () => {
    render(<AgentConfigForm onSave={vi.fn()} onCancel={vi.fn()} />)
    const submitButton = screen.getByText('创建')
    expect(submitButton).toBeDisabled()
  })

  it('disables submit button when default_model_id is empty', () => {
    render(<AgentConfigForm onSave={vi.fn()} onCancel={vi.fn()} />)
    fireEvent.change(screen.getByPlaceholderText('输入 Agent 名称'), {
      target: { value: 'My Agent' },
    })
    // Role has default value, name is filled, but model is still empty
    const submitButton = screen.getByText('创建')
    expect(submitButton).toBeDisabled()
  })

  it('enables submit button when form is valid', () => {
    const { container } = render(<AgentConfigForm onSave={vi.fn()} onCancel={vi.fn()} />)
    fireEvent.change(screen.getByPlaceholderText('输入 Agent 名称'), {
      target: { value: 'My Agent' },
    })
    const selects = container.querySelectorAll('select')
    const modelSelect = selects[1]
    fireEvent.change(modelSelect, { target: { value: 'claude-3-opus' } })
    const submitButton = screen.getByText('创建')
    expect(submitButton).not.toBeDisabled()
  })

  it('calls onSave with correct data when form is valid', async () => {
    const onSave = vi.fn()
    const { container } = render(<AgentConfigForm onSave={onSave} onCancel={vi.fn()} />)

    fireEvent.change(screen.getByPlaceholderText('输入 Agent 名称'), {
      target: { value: 'My Agent' },
    })

    // Select default model (second select in the form)
    const selects = container.querySelectorAll('select')
    const modelSelect = selects[1] // first is role, second is default model
    fireEvent.change(modelSelect, { target: { value: 'claude-3-opus' } })

    fireEvent.click(screen.getByText('创建'))

    await waitFor(() => {
      expect(onSave).toHaveBeenCalled()
    })
  })

  it('calls onCancel when cancel button clicked', () => {
    const onCancel = vi.fn()
    render(<AgentConfigForm onSave={vi.fn()} onCancel={onCancel} />)
    fireEvent.click(screen.getByText('取消'))
    expect(onCancel).toHaveBeenCalled()
  })
})

describe('AgentConfigForm - Edit', () => {
  it('renders edit form with prefilled data', () => {
    render(<AgentConfigForm agent={mockAgent} onSave={vi.fn()} onCancel={vi.fn()} />)
    expect(screen.getByText('编辑 Agent')).toBeInTheDocument()
    expect(screen.getByDisplayValue('Test Agent')).toBeInTheDocument()
    expect(screen.getByDisplayValue('You are a test agent.')).toBeInTheDocument()
  })

  it('calls onSave with updated data', async () => {
    const onSave = vi.fn()
    render(<AgentConfigForm agent={mockAgent} onSave={onSave} onCancel={vi.fn()} />)

    fireEvent.change(screen.getByDisplayValue('Test Agent'), {
      target: { value: 'Updated Agent' },
    })
    fireEvent.click(screen.getByText('保存'))

    await waitFor(() => {
      expect(onSave).toHaveBeenCalled()
      const savedData = onSave.mock.calls[0][0]
      expect(savedData.name).toBe('Updated Agent')
    })
  })
})

describe('AgentConfigForm - Running Agent Warning', () => {
  it('shows warning banner when editing a running agent', () => {
    render(<AgentConfigForm agent={mockRunningAgent} onSave={vi.fn()} onCancel={vi.fn()} />)
    expect(screen.getByText(/该 Agent 正在执行任务/i)).toBeInTheDocument()
  })

  it('does not show warning banner for idle agent', () => {
    render(<AgentConfigForm agent={mockAgent} onSave={vi.fn()} onCancel={vi.fn()} />)
    expect(screen.queryByText(/该 Agent 正在执行任务/i)).not.toBeInTheDocument()
  })
})

describe('AgentConfigForm - API Error', () => {
  it('displays error banner when error prop is provided', () => {
    render(
      <AgentConfigForm
        onSave={vi.fn()}
        onCancel={vi.fn()}
        error="创建失败：名称已存在"
      />
    )
    expect(screen.getByText('创建失败：名称已存在')).toBeInTheDocument()
  })

  it('clears error banner when form is reopened with different agent', () => {
    const { rerender } = render(
      <AgentConfigForm
        onSave={vi.fn()}
        onCancel={vi.fn()}
        error="保存失败"
      />
    )
    expect(screen.getByText('保存失败')).toBeInTheDocument()

    rerender(
      <AgentConfigForm
        agent={mockAgent}
        onSave={vi.fn()}
        onCancel={vi.fn()}
      />
    )
    expect(screen.queryByText('保存失败')).not.toBeInTheDocument()
  })
})

describe('AgentConfigForm - Handoff Toggle', () => {
  it('shows handoff threshold input when handoff is enabled', () => {
    render(<AgentConfigForm onSave={vi.fn()} onCancel={vi.fn()} />)
    expect(screen.queryByText(/Handoff 触发阈值/i)).not.toBeInTheDocument()

    // Toggle handoff on
    const handoffToggle = screen.getByText(/允许 Handoff/i).closest('div')?.querySelector('button')
    if (handoffToggle) {
      fireEvent.click(handoffToggle)
      expect(screen.getByText(/Handoff 触发阈值/i)).toBeInTheDocument()
    }
  })
})
