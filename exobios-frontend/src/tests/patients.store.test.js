import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { usePatientsStore } from '@/features/patients/stores/patients'

// Bypass version gate so we start fresh every test
beforeEach(() => {
  setActivePinia(createPinia())
  localStorage.clear()
  // Force fresh seed by faking the version key as mismatched
  localStorage.getItem.mockImplementation((key) => {
    if (key === 'exobios_patients_ver') return null // triggers reseed
    return null
  })
})

describe('Patients Store', () => {
  it('initialises with seed data', () => {
    const store = usePatientsStore()
    expect(store.patients.length).toBeGreaterThan(0)
  })

  it('add() inserts a new patient and persists', () => {
    const store = usePatientsStore()
    const before = store.patients.length
    const id = store.add({ name: 'Test Patient', dob: '1990-01-01', gender: 'Female', phone: '9000000000', risk: 'Low', date: '1 Jan 2025' })
    expect(store.patients.length).toBe(before + 1)
    expect(store.getById(id)?.name).toBe('Test Patient')
    expect(localStorage.setItem).toHaveBeenCalled()
  })

  it('add() auto-calculates age from dob', () => {
    const store = usePatientsStore()
    const id = store.add({ name: 'Age Test', dob: '2000-01-01', gender: 'Male', phone: '9000000001', risk: 'Low', date: '1 Jan 2025' })
    const patient = store.getById(id)
    expect(patient?.age).toBeGreaterThan(20)
    expect(patient?.age).toBeLessThan(40)
  })

  it('update() modifies an existing patient', () => {
    const store  = usePatientsStore()
    const id     = store.add({ name: 'Old Name', dob: '1985-06-15', gender: 'Male', phone: '9000000002', risk: 'Low', date: '1 Jan 2025' })
    store.update(id, { name: 'New Name' })
    expect(store.getById(id)?.name).toBe('New Name')
  })

  it('remove() deletes a patient', () => {
    const store  = usePatientsStore()
    const id     = store.add({ name: 'To Delete', dob: '1985-06-15', gender: 'Male', phone: '9000000003', risk: 'Low', date: '1 Jan 2025' })
    store.remove(id)
    expect(store.getById(id)).toBeNull()
  })

  it('getById() returns null for unknown id', () => {
    const store = usePatientsStore()
    expect(store.getById(99999)).toBeNull()
  })

  it('addAssessment() prepends to assessmentHistory', () => {
    const store = usePatientsStore()
    const id    = store.add({ name: 'Pat', dob: '1990-01-01', gender: 'Female', phone: '9000000004', risk: 'Low', date: '1 Jan 2025', assessmentHistory: [] })
    store.addAssessment(id, { primaryComplaint: 'Fever', risk: 'High', vitals: {}, examForm: {} })
    const patient = store.getById(id)
    expect(patient?.assessmentHistory).toHaveLength(1)
    expect(patient?.assessmentHistory[0].primaryComplaint).toBe('Fever')
    expect(patient?.risk).toBe('High')
  })

  it('addAssessment() updates patient root risk', () => {
    const store = usePatientsStore()
    const id    = store.add({ name: 'Pat2', dob: '1990-01-01', gender: 'Male', phone: '9000000005', risk: 'Low', date: '1 Jan 2025', assessmentHistory: [] })
    store.addAssessment(id, { risk: 'Moderate', vitals: {}, examForm: {} })
    expect(store.getById(id)?.risk).toBe('Moderate')
  })

  it('new patients are inserted at the front (newest first)', () => {
    const store  = usePatientsStore()
    const before = store.patients.length
    store.add({ name: 'Newest', dob: '2000-01-01', gender: 'Male', phone: '9000000006', risk: 'Low', date: '1 Jan 2025' })
    expect(store.patients[0].name).toBe('Newest')
    expect(store.patients.length).toBe(before + 1)
  })

  it('addAssessment() is a no-op for an unknown patient id', () => {
    const store = usePatientsStore()
    const before = JSON.stringify(store.patients)
    store.addAssessment(999999, { primaryComplaint: 'Fever' })
    expect(JSON.stringify(store.patients)).toBe(before)
  })

  it('update() is a no-op for an unknown patient id', () => {
    const store = usePatientsStore()
    const before = store.patients.length
    store.update(999999, { name: 'Ghost' })
    expect(store.patients.length).toBe(before)
  })

  it('surfaces a toast instead of throwing when localStorage.setItem quota is exceeded', () => {
    const store = usePatientsStore()
    localStorage.setItem.mockImplementationOnce(() => { throw new Error('QuotaExceededError') })
    expect(() => store.add({ name: 'Big Photo Patient', dob: '1990-01-01', gender: 'Male', phone: '9000000007', risk: 'Low', date: '1 Jan 2025' })).not.toThrow()
    // The in-memory change still applies even though persistence failed.
    expect(store.patients.some(p => p.name === 'Big Photo Patient')).toBe(true)
  })
})
