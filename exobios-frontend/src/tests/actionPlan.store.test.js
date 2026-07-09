import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useActionPlanStore } from '@/shared/stores/actionPlan'

describe('ActionPlan Store', () => {
  beforeEach(() => { setActivePinia(createPinia()) })

  it('getPlan() lazily creates a default plan for a new patient id', () => {
    const store = useActionPlanStore()
    const plan = store.getPlan(42)
    expect(plan).toEqual({
      immediateMeasures: [],
      referral: { hospitalId: null, status: '' },
      teleconsult: { doctorId: null, status: '' },
      outcome: '',
      notes: '',
    })
  })

  it('getPlan() returns the same plan object on repeated calls for the same patient', () => {
    const store = useActionPlanStore()
    const first = store.getPlan(1)
    first.notes = 'first call'
    const second = store.getPlan(1)
    expect(second.notes).toBe('first call')
  })

  it('setImmediateMeasures() stores the measures list for a patient', () => {
    const store = useActionPlanStore()
    store.setImmediateMeasures(1, ['Oral rehydration', 'Paracetamol'])
    expect(store.getPlan(1).immediateMeasures).toEqual(['Oral rehydration', 'Paracetamol'])
  })

  it('setReferral() merges a patch into the referral sub-object without clobbering other fields', () => {
    const store = useActionPlanStore()
    store.setReferral(1, { hospitalId: 5 })
    store.setReferral(1, { status: 'yes' })
    expect(store.getPlan(1).referral).toEqual({ hospitalId: 5, status: 'yes' })
  })

  it('setTeleconsult() merges a patch into the teleconsult sub-object', () => {
    const store = useActionPlanStore()
    store.setTeleconsult(2, { doctorId: 9, status: 'yes' })
    expect(store.getPlan(2).teleconsult).toEqual({ doctorId: 9, status: 'yes' })
  })

  it('setOutcome() and setNotes() update their respective fields', () => {
    const store = useActionPlanStore()
    store.setOutcome(3, 'Improved')
    store.setNotes(3, 'Follow up in 1 week')
    const plan = store.getPlan(3)
    expect(plan.outcome).toBe('Improved')
    expect(plan.notes).toBe('Follow up in 1 week')
  })

  it('pendingReferrals lists only patients whose referral status is "yes"', () => {
    const store = useActionPlanStore()
    store.setReferral(10, { status: 'yes', hospitalId: 1 })
    store.setReferral(11, { status: 'no', hospitalId: 2 })
    store.setReferral(12, { status: '', hospitalId: 3 })

    const ids = store.pendingReferrals.map(p => p.patientId)
    expect(ids).toContain(10)
    expect(ids).not.toContain(11)
    expect(ids).not.toContain(12)
  })

  it('pendingReferrals reflects a referral once its status is finalized away from "yes"', () => {
    const store = useActionPlanStore()
    store.setReferral(20, { status: 'yes', hospitalId: 1 })
    expect(store.pendingReferrals.map(p => p.patientId)).toContain(20)
    store.setReferral(20, { status: 'completed' })
    expect(store.pendingReferrals.map(p => p.patientId)).not.toContain(20)
  })
})
