import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/vue'
import { reactive } from 'vue'
import ParamedicGeneralExam from '@/features/assessments/components/examination/ParamedicGeneralExam.vue'

function blankExam() {
  return {
    generalAppearance: [], eyes: [], skinMucosa: [], extremities: [],
    visibleInjuries: { present: false, description: '' },
  }
}

describe('ParamedicGeneralExam — examination section', () => {
  it('toggles a general-appearance finding into the exam object via v-model', async () => {
    const exam = reactive(blankExam())
    render(ParamedicGeneralExam, { props: { exam } })

    await fireEvent.click(screen.getByText('Distressed'))
    expect(exam.generalAppearance).toContain('Distressed')

    await fireEvent.click(screen.getByText('Distressed'))
    expect(exam.generalAppearance).not.toContain('Distressed')
  })

  it('supports multiple independent findings across different checklists', async () => {
    const exam = reactive(blankExam())
    render(ParamedicGeneralExam, { props: { exam } })

    await fireEvent.click(screen.getByText('Pallor'))
    await fireEvent.click(screen.getByText('Rash'))
    await fireEvent.click(screen.getByText('Edema'))

    expect(exam.eyes).toEqual(['Pallor'])
    expect(exam.skinMucosa).toEqual(['Rash'])
    expect(exam.extremities).toEqual(['Edema'])
  })

  it('reveals the injury description field only once "Visible Injuries" is checked', async () => {
    const exam = reactive(blankExam())
    render(ParamedicGeneralExam, { props: { exam } })

    expect(screen.queryByPlaceholderText('Describe visible injuries...')).toBeNull()
    await fireEvent.click(screen.getByText('Visible Injuries Present'))
    expect(exam.visibleInjuries.present).toBe(true)
    expect(screen.getByPlaceholderText('Describe visible injuries...')).toBeTruthy()
  })
})
