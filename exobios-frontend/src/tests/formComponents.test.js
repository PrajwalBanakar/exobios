import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/vue'
import CheckboxGroup from '@/shared/components/forms/CheckboxGroup.vue'
import RadioGroup from '@/shared/components/forms/RadioGroup.vue'

describe('CheckboxGroup', () => {
  it('renders one checkbox per option and reflects the initial selection', () => {
    render(CheckboxGroup, { props: { modelValue: ['B'], options: ['A', 'B', 'C'] } })
    expect(screen.getByText('A').previousElementSibling.checked).toBe(false)
    expect(screen.getByText('B').previousElementSibling.checked).toBe(true)
  })

  it('emits update:modelValue with the option added when an unchecked box is clicked', async () => {
    const { emitted } = render(CheckboxGroup, { props: { modelValue: ['A'], options: ['A', 'B', 'C'] } })
    await fireEvent.click(screen.getByText('B'))
    expect(emitted()['update:modelValue'][0]).toEqual([['A', 'B']])
  })

  it('emits update:modelValue with the option removed when a checked box is clicked', async () => {
    const { emitted } = render(CheckboxGroup, { props: { modelValue: ['A', 'B'], options: ['A', 'B', 'C'] } })
    await fireEvent.click(screen.getByText('A'))
    expect(emitted()['update:modelValue'][0]).toEqual([['B']])
  })

  it('supports {value,label} option objects', async () => {
    const { emitted } = render(CheckboxGroup, {
      props: { modelValue: [], options: [{ value: 'x', label: 'Option X' }] },
    })
    expect(screen.getByText('Option X')).toBeTruthy()
    await fireEvent.click(screen.getByText('Option X'))
    expect(emitted()['update:modelValue'][0]).toEqual([['x']])
  })
})

describe('RadioGroup', () => {
  it('renders one radio per option and marks the selected one', () => {
    render(RadioGroup, { props: { modelValue: 'B', options: ['A', 'B', 'C'] } })
    expect(screen.getByText('A').previousElementSibling.checked).toBe(false)
    expect(screen.getByText('B').previousElementSibling.checked).toBe(true)
  })

  it('emits update:modelValue with the newly selected option', async () => {
    const { emitted } = render(RadioGroup, { props: { modelValue: 'A', options: ['A', 'B', 'C'] } })
    await fireEvent.click(screen.getByText('C'))
    expect(emitted()['update:modelValue'][0]).toEqual(['C'])
  })

  it('only one option is selected at a time (single-select semantics)', () => {
    const { container } = render(RadioGroup, { props: { modelValue: 'B', options: ['A', 'B', 'C'] } })
    const checked = [...container.querySelectorAll('input[type="radio"]')].filter(i => i.checked)
    expect(checked.length).toBe(1)
  })
})
