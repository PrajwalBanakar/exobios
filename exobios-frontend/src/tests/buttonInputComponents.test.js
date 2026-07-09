import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/vue'
import BaseButton from '@/shared/components/BaseButton.vue'
import BaseInput from '@/shared/components/BaseInput.vue'

describe('BaseButton', () => {
  it('renders slot content and defaults to an enabled, primary, medium button', () => {
    render(BaseButton, { slots: { default: 'Save' } })
    const btn = screen.getByText('Save').closest('button') ?? screen.getByRole('button')
    expect(btn.disabled).toBe(false)
    expect(btn.className).toContain('bg-blue-600')
  })

  it('is disabled and shows a spinner when loading is true', () => {
    render(BaseButton, { props: { loading: true }, slots: { default: 'Save' } })
    const btn = screen.getByRole('button')
    expect(btn.disabled).toBe(true)
    expect(btn.querySelector('svg.animate-spin')).toBeTruthy()
  })

  it('is disabled when the disabled prop is set, independent of loading', () => {
    render(BaseButton, { props: { disabled: true }, slots: { default: 'Save' } })
    expect(screen.getByRole('button').disabled).toBe(true)
  })

  it('invokes the click handler when enabled', async () => {
    const onClick = vi.fn()
    render(BaseButton, { props: { onClick }, slots: { default: 'Save' } })
    await fireEvent.click(screen.getByRole('button'))
    expect(onClick).toHaveBeenCalledOnce()
  })

  it('does not invoke the click handler when disabled (native button behavior)', () => {
    const onClick = vi.fn()
    render(BaseButton, { props: { disabled: true, onClick }, slots: { default: 'Save' } })
    // Use the native .click() activation path (what a real user interaction triggers) rather
    // than a raw dispatchEvent — jsdom only suppresses activation behavior for the former.
    screen.getByRole('button').click()
    expect(onClick).not.toHaveBeenCalled()
  })

  it('applies the danger variant styling', () => {
    render(BaseButton, { props: { variant: 'danger' }, slots: { default: 'Delete' } })
    expect(screen.getByRole('button').className).toContain('bg-red-600')
  })
})

describe('BaseInput', () => {
  it('renders a label with a required asterisk when required is true', () => {
    render(BaseInput, { props: { label: 'Full Name', required: true } })
    expect(screen.getByText('Full Name')).toBeTruthy()
    expect(screen.getByText('*')).toBeTruthy()
  })

  it('emits update:modelValue as the user types', async () => {
    const { emitted } = render(BaseInput, { props: { modelValue: '' } })
    await fireEvent.update(screen.getByRole('textbox'), 'hello')
    expect(emitted()['update:modelValue'][0]).toEqual(['hello'])
  })

  it('shows the error message and hides the helper text when both are set', () => {
    render(BaseInput, { props: { error: 'Required field', helper: 'Enter your name' } })
    expect(screen.getByText('Required field')).toBeTruthy()
    expect(screen.queryByText('Enter your name')).toBeNull()
  })

  it('shows helper text when there is no error', () => {
    render(BaseInput, { props: { helper: 'Enter your name' } })
    expect(screen.getByText('Enter your name')).toBeTruthy()
  })

  it('disables the input when disabled is true', () => {
    render(BaseInput, { props: { disabled: true } })
    expect(screen.getByRole('textbox').disabled).toBe(true)
  })
})
