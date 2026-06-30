import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import LogFilters from '../LogFilters'

describe('LogFilters', () => {
  it('renders quick filter buttons', () => {
    render(<LogFilters filters={{}} onChange={vi.fn()} />)
    expect(screen.getByRole('button', { name: '全部' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '仅错误' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '模型调用' })).toBeInTheDocument()
  })

  it('calls onChange with event_type when quick filter clicked', () => {
    const onChange = vi.fn()
    render(<LogFilters filters={{}} onChange={onChange} />)
    fireEvent.click(screen.getByRole('button', { name: '模型调用' }))
    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ event_type: 'model_call' }))
  })

  it('calls onChange with error status when 仅错误 clicked', () => {
    const onChange = vi.fn()
    render(<LogFilters filters={{}} onChange={onChange} />)
    fireEvent.click(screen.getByRole('button', { name: '仅错误' }))
    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ event_status: 'error,failed' }))
  })

  it('calls onChange with search term', () => {
    const onChange = vi.fn()
    render(<LogFilters filters={{}} onChange={onChange} />)
    const input = screen.getByPlaceholderText('搜索日志内容...')
    fireEvent.change(input, { target: { value: 'timeout' } })
    fireEvent.click(screen.getByRole('button', { name: '搜索' }))
    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ search: 'timeout' }))
  })

  it('calls onChange with page_size when select changes', () => {
    const onChange = vi.fn()
    render(<LogFilters filters={{ page_size: 20 }} onChange={onChange} />)
    const select = screen.getByRole('combobox')
    fireEvent.change(select, { target: { value: '50' } })
    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ page_size: 50 }))
  })
})
