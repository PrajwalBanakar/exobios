import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useTeleconsultStore } from '@/features/teleconsult/stores/teleconsult'

describe('Teleconsult Store', () => {
  beforeEach(() => { setActivePinia(createPinia()) })

  it('seeds with sample sessions', () => {
    const store = useTeleconsultStore()
    expect(store.items.length).toBeGreaterThan(0)
  })

  it('scheduledCount and completedCount reflect session status', () => {
    const store = useTeleconsultStore()
    expect(store.scheduledCount).toBe(store.items.filter(s => s.status === 'Scheduled').length)
    expect(store.completedCount).toBe(store.items.filter(s => s.status === 'Completed').length)
  })

  it('avgDuration averages only sessions that have a recorded duration', () => {
    const store = useTeleconsultStore()
    const completed = store.items.filter(s => s.duration)
    const expected = Math.round(completed.reduce((s, i) => s + i.duration, 0) / completed.length)
    expect(store.avgDuration).toBe(expected)
  })

  it('avgDuration is 0 when no session has a duration', () => {
    const store = useTeleconsultStore()
    store.items.forEach(s => { s.duration = null })
    expect(store.avgDuration).toBe(0)
  })

  it('add() inserts a new scheduled session at the front', () => {
    const store = useTeleconsultStore()
    const before = store.items.length
    store.add({ patientName: 'New Patient', doctor: 'Dr. Rao', spec: 'General Physician', ashaWorker: 'Sunita Devi', status: 'Scheduled' })
    expect(store.items.length).toBe(before + 1)
    expect(store.items[0].patientName).toBe('New Patient')
  })

  it('updateStatus() changes an existing session status', () => {
    const store = useTeleconsultStore()
    const target = store.items[0]
    store.updateStatus(target.id, 'Completed')
    expect(target.status).toBe('Completed')
  })

  it('updateStatus() with an unknown id does not throw', () => {
    const store = useTeleconsultStore()
    expect(() => store.updateStatus(999999, 'Completed')).not.toThrow()
  })
})
