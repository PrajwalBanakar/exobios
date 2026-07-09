import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useReferralsStore } from '@/features/referrals/stores/referrals'

describe('Referrals Store', () => {
  beforeEach(() => { setActivePinia(createPinia()) })

  it('seeds with sample referrals', () => {
    const store = useReferralsStore()
    expect(store.items.length).toBeGreaterThan(0)
  })

  it('govCount and privateCount reflect the referral type split', () => {
    const store = useReferralsStore()
    const gov = store.items.filter(r => r.type === 'Government').length
    const priv = store.items.filter(r => r.type === 'Private').length
    expect(store.govCount).toBe(gov)
    expect(store.privateCount).toBe(priv)
  })

  it('add() inserts a new referral at the front with sensible defaults', () => {
    const store = useReferralsStore()
    const before = store.items.length
    store.add({ patientName: 'New Patient', hospital: 'City Hospital', transport: 'Ambulance', ashaWorker: 'Sunita Devi', notes: 'Test referral' })
    expect(store.items.length).toBe(before + 1)
    expect(store.items[0].patientName).toBe('New Patient')
    expect(store.items[0].status).toBe('Pending')
    expect(store.items[0].type).toBe('Government')
  })

  it('add() with an explicit type overrides the default', () => {
    const store = useReferralsStore()
    store.add({ patientName: 'Private Patient', hospital: 'Sharma Hospital', type: 'Private', transport: 'Private Vehicle', ashaWorker: 'Meena Rani' })
    expect(store.items[0].type).toBe('Private')
    expect(store.privateCount).toBeGreaterThan(0)
  })

  it('add() assigns a new unique id even after existing max id', () => {
    const store = useReferralsStore()
    const maxIdBefore = Math.max(...store.items.map(r => r.id))
    store.add({ patientName: 'Another', hospital: 'X', transport: 'Walking', ashaWorker: 'Y' })
    expect(store.items[0].id).toBe(maxIdBefore + 1)
  })
})
