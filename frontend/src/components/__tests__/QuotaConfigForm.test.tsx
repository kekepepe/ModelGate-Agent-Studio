import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import QuotaConfigForm from '../QuotaConfigForm'

describe('QuotaConfigForm', () => {
  it('renders with initial values', () => {
    render(
      <QuotaConfigForm
        initialTokenLimit={100000}
        initialResetPeriod="weekly"
        onSave={vi.fn()}
        onCancel={vi.fn()}
      />
    )
    const input = screen.getByPlaceholderText('例如: 1000000') as HTMLInputElement
    expect(input.value).toBe('100000')
    const select = screen.getByDisplayValue('每周') as HTMLSelectElement
    expect(select.value).toBe('weekly')
  })

  it('renders with empty initial values', () => {
    render(<QuotaConfigForm onSave={vi.fn()} onCancel={vi.fn()} />)
    const input = screen.getByPlaceholderText('例如: 1000000') as HTMLInputElement
    expect(input.value).toBe('')
    const select = screen.getByDisplayValue('每月') as HTMLSelectElement
    expect(select.value).toBe('monthly')
  })

  it('calls onSave with parsed data on submit', () => {
    const onSave = vi.fn()
    render(<QuotaConfigForm onSave={onSave} onCancel={vi.fn()} />)

    const input = screen.getByPlaceholderText('例如: 1000000')
    fireEvent.change(input, { target: { value: '500000' } })

    const select = screen.getByDisplayValue('每月')
    fireEvent.change(select, { target: { value: 'daily' } })

    fireEvent.click(screen.getByText('保存'))
    expect(onSave).toHaveBeenCalledWith({
      token_limit: 500000,
      reset_period: 'daily',
    })
  })

  it('calls onSave with parsed data after entering limit', () => {
    const onSave = vi.fn()
    render(<QuotaConfigForm onSave={onSave} onCancel={vi.fn()} />)
    const input = screen.getByPlaceholderText('例如: 1000000')
    fireEvent.change(input, { target: { value: '' } })
    fireEvent.click(screen.getByText('保存'))
    // Empty input + required won't submit via HTML5 validation
    expect(onSave).not.toHaveBeenCalled()
  })

  it('calls onCancel when clicking cancel', () => {
    const onCancel = vi.fn()
    render(<QuotaConfigForm onSave={vi.fn()} onCancel={onCancel} />)
    fireEvent.click(screen.getByText('取消'))
    expect(onCancel).toHaveBeenCalled()
  })

  it('has required attribute on token input', () => {
    render(<QuotaConfigForm onSave={vi.fn()} onCancel={vi.fn()} />)
    const input = screen.getByPlaceholderText('例如: 1000000')
    expect(input).toHaveAttribute('required')
  })
})
