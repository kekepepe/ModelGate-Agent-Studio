import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import AgentTemplateCards from '../AgentTemplateCards'
import type { AgentTemplate } from '../../types/agent'

const mockTemplates: AgentTemplate[] = [
  {
    id: 'template-planner',
    name: 'Planner Agent',
    role: 'planner',
    description: '任务规划专家',
    default_config: { default_model_id: 'claude-3-opus', allow_handoff: false },
  },
  {
    id: 'template-coder',
    name: 'Coder Agent',
    role: 'coder',
    description: '代码编写专家',
    default_config: { default_model_id: 'deepseek-coder', allow_handoff: true },
  },
  {
    id: 'template-reviewer',
    name: 'Reviewer Agent',
    role: 'reviewer',
    description: '代码审查专家',
    default_config: { default_model_id: 'gpt-4-turbo', allow_handoff: true },
  },
  {
    id: 'template-research',
    name: 'Research Agent',
    role: 'research',
    description: '技术调研专家',
    default_config: { default_model_id: 'kimi-long-context', allow_handoff: true },
  },
  {
    id: 'template-summarizer',
    name: 'Summarizer Agent',
    role: 'summarizer',
    description: '摘要生成专家',
    default_config: { default_model_id: 'claude-3-haiku', allow_handoff: false },
  },
  {
    id: 'template-supervisor',
    name: 'Supervisor Agent',
    role: 'supervisor',
    description: '项目监督者',
    default_config: { default_model_id: 'claude-3-opus', allow_handoff: false },
  },
]

describe('AgentTemplateCards', () => {
  it('renders all 6 template cards', () => {
    render(<AgentTemplateCards templates={mockTemplates} onSelect={vi.fn()} onCustom={vi.fn()} />)
    expect(screen.getByText('Planner Agent')).toBeInTheDocument()
    expect(screen.getByText('Coder Agent')).toBeInTheDocument()
    expect(screen.getByText('Reviewer Agent')).toBeInTheDocument()
    expect(screen.getByText('Research Agent')).toBeInTheDocument()
    expect(screen.getByText('Summarizer Agent')).toBeInTheDocument()
    expect(screen.getByText('Supervisor Agent')).toBeInTheDocument()
  })

  it('renders custom card', () => {
    render(<AgentTemplateCards templates={mockTemplates} onSelect={vi.fn()} onCustom={vi.fn()} />)
    expect(screen.getByText('自定义')).toBeInTheDocument()
    expect(screen.getByText('从零开始配置 Agent')).toBeInTheDocument()
  })

  it('calls onSelect when clicking a template card', () => {
    const onSelect = vi.fn()
    render(<AgentTemplateCards templates={mockTemplates} onSelect={onSelect} onCustom={vi.fn()} />)
    fireEvent.click(screen.getByText('Coder Agent'))
    expect(onSelect).toHaveBeenCalledWith(mockTemplates[1])
  })

  it('calls onCustom when clicking custom card', () => {
    const onCustom = vi.fn()
    render(<AgentTemplateCards templates={mockTemplates} onSelect={vi.fn()} onCustom={onCustom} />)
    fireEvent.click(screen.getByText('自定义'))
    expect(onCustom).toHaveBeenCalled()
  })

  it('displays template metadata correctly', () => {
    render(<AgentTemplateCards templates={mockTemplates} onSelect={vi.fn()} onCustom={vi.fn()} />)
    expect(screen.getByText('建议模型: deepseek-coder')).toBeInTheDocument()
    expect(screen.getAllByText('允许 Handoff: 是').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('允许 Handoff: 否').length).toBeGreaterThanOrEqual(1)
  })
})
