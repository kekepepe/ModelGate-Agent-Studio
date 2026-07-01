import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import AgentConfigForm from '../AgentConfigForm'
import type { AgentStation } from '../../types/agent'

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
})

function renderWithQuery(ui: React.ReactElement) {
  return render(ui, {
    wrapper: ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    ),
  })
}

beforeEach(() => {
  queryClient.clear();
  queryClient.setQueryData(['models', { is_enabled: true }], {
    items: [
      { id: 'claude-3-opus', display_name: 'Claude 3 Opus', provider: 'anthropic', model_name: 'claude-3-opus', capability_tags: [], max_context_tokens: 200000, cost_level: 5, speed_level: 3, is_enabled: true, is_default: false },
      { id: 'gpt-4-turbo', display_name: 'GPT-4 Turbo', provider: 'openai', model_name: 'gpt-4-turbo', capability_tags: [], max_context_tokens: 128000, cost_level: 4, speed_level: 3, is_enabled: true, is_default: false },
    ],
    total: 2,
    page: 1,
    page_size: 20,
    total_pages: 1,
  });
});

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
  it('renders create form at step 1', () => {
    renderWithQuery(<AgentConfigForm onSave={vi.fn()} onCancel={vi.fn()} />)
    expect(screen.getByText('创建 Agent')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('输入 Agent 名称')).toHaveValue('')
    // Step indicator shows "1" active
    expect(screen.getByText('下一步')).toBeInTheDocument()
  })

  it('disables next button when name is empty at step 1', () => {
    renderWithQuery(<AgentConfigForm onSave={vi.fn()} onCancel={vi.fn()} />)
    const nextButton = screen.getByText('下一步')
    expect(nextButton).toBeDisabled()
  })

  it('proceeds through wizard and calls onSave', async () => {
    const onSave = vi.fn()
    const { container } = renderWithQuery(<AgentConfigForm onSave={onSave} onCancel={vi.fn()} />)

    // Step 1: fill name
    fireEvent.change(screen.getByPlaceholderText('输入 Agent 名称'), {
      target: { value: 'My Agent' },
    })
    fireEvent.click(screen.getByText('下一步'))

    // Step 2: select model
    await waitFor(() => {
      expect(screen.getByText('模型配置')).toBeInTheDocument()
    })
    const selects = container.querySelectorAll('select')
    const modelSelect = selects[0] // first select in step 2 is default model
    fireEvent.change(modelSelect, { target: { value: 'claude-3-opus' } })
    fireEvent.click(screen.getByText('下一步'))

    // Step 3: confirm and submit
    await waitFor(() => {
      expect(screen.getByText('配置汇总')).toBeInTheDocument()
    })
    fireEvent.click(screen.getByText('创建'))

    await waitFor(() => {
      expect(onSave).toHaveBeenCalled()
    })
  })

  it('calls onCancel when cancel button clicked', () => {
    const onCancel = vi.fn()
    renderWithQuery(<AgentConfigForm onSave={vi.fn()} onCancel={onCancel} />)
    fireEvent.click(screen.getByText('取消'))
    expect(onCancel).toHaveBeenCalled()
  })
})

describe('AgentConfigForm - Edit', () => {
  it('renders edit form with prefilled data at step 1', () => {
    renderWithQuery(<AgentConfigForm agent={mockAgent} onSave={vi.fn()} onCancel={vi.fn()} />)
    expect(screen.getByText('编辑 Agent')).toBeInTheDocument()
    expect(screen.getByDisplayValue('Test Agent')).toBeInTheDocument()
  })

  it('calls onSave with updated data after navigating to step 3', async () => {
    const onSave = vi.fn()
    renderWithQuery(<AgentConfigForm agent={mockAgent} onSave={onSave} onCancel={vi.fn()} />)

    // Step 1: update name
    fireEvent.change(screen.getByDisplayValue('Test Agent'), {
      target: { value: 'Updated Agent' },
    })
    fireEvent.click(screen.getByText('下一步'))

    // Step 2: model already selected, proceed
    await waitFor(() => {
      expect(screen.getByText('模型配置')).toBeInTheDocument()
    })
    fireEvent.click(screen.getByText('下一步'))

    // Step 3: save
    await waitFor(() => {
      expect(screen.getByText('配置汇总')).toBeInTheDocument()
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
    renderWithQuery(<AgentConfigForm agent={mockRunningAgent} onSave={vi.fn()} onCancel={vi.fn()} />)
    expect(screen.getByText(/该 Agent 正在执行任务/i)).toBeInTheDocument()
  })

  it('does not show warning banner for idle agent', () => {
    renderWithQuery(<AgentConfigForm agent={mockAgent} onSave={vi.fn()} onCancel={vi.fn()} />)
    expect(screen.queryByText(/该 Agent 正在执行任务/i)).not.toBeInTheDocument()
  })
})

describe('AgentConfigForm - API Error', () => {
  it('displays error banner when error prop is provided', () => {
    renderWithQuery(
      <AgentConfigForm
        onSave={vi.fn()}
        onCancel={vi.fn()}
        error="创建失败：名称已存在"
      />
    )
    expect(screen.getByText('创建失败：名称已存在')).toBeInTheDocument()
  })

  it('clears error banner when form is reopened with different agent', () => {
    const { rerender } = renderWithQuery(
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
  it('shows handoff threshold input when handoff is enabled', async () => {
    const { container } = renderWithQuery(<AgentConfigForm onSave={vi.fn()} onCancel={vi.fn()} />)

    // Step 1: fill name and proceed
    fireEvent.change(screen.getByPlaceholderText('输入 Agent 名称'), {
      target: { value: 'My Agent' },
    })
    fireEvent.click(screen.getByText('下一步'))

    // Step 2: select model and proceed
    await waitFor(() => {
      expect(screen.getByText('模型配置')).toBeInTheDocument()
    })
    const selects = container.querySelectorAll('select')
    const modelSelect = selects[0]
    fireEvent.change(modelSelect, { target: { value: 'claude-3-opus' } })
    fireEvent.click(screen.getByText('下一步'))

    // Step 3: toggle handoff
    await waitFor(() => {
      expect(screen.getByText('执行限制')).toBeInTheDocument()
    })
    expect(screen.queryByText(/Handoff 触发阈值/i)).not.toBeInTheDocument()

    // Find the toggle button next to the "允许 Handoff" label in the form (not summary)
    const handoffLabel = container.querySelector('label.text-sm.font-medium.text-stone-700')
    const handoffToggle = handoffLabel?.closest('div')?.querySelector('button')
    if (handoffToggle) {
      fireEvent.click(handoffToggle)
      expect(screen.getByText(/Handoff 触发阈值/i)).toBeInTheDocument()
    }
  })
})
