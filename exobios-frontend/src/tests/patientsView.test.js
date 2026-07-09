import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/vue'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import PatientsView from '@/features/patients/views/PatientsView.vue'
import { usePatientsStore } from '@/features/patients/stores/patients'
import { AppShellStub } from './testUtils.js'

function makeRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/patients', name: 'Patients', component: PatientsView },
      { path: '/patients/new', name: 'AddPatient', component: { template: '<div/>' } },
      { path: '/patients/:id', name: 'PatientDetail', component: { template: '<div/>' } },
      { path: '/patients/:id/edit', name: 'EditPatient', component: { template: '<div/>' } },
      { path: '/assessment/new', name: 'NewAssessment', component: { template: '<div/>' } },
    ],
  })
}

async function renderPatients() {
  setActivePinia(createPinia())
  const router = makeRouter()
  await router.push('/patients')
  await router.isReady()
  const utils = render(PatientsView, { global: { plugins: [router], stubs: { AppShell: AppShellStub } } })
  return { ...utils, router }
}

describe('PatientsView — search & filter', () => {
  beforeEach(() => { localStorage.clear() })

  it('lists all seed patients by default', async () => {
    await renderPatients()
    expect(screen.getByText('Priya Sharma')).toBeTruthy()
    expect(screen.getByText('Rajesh Kumar')).toBeTruthy()
  })

  it('filters the list by name without crashing on patients that lack a top-level location field', async () => {
    const { container } = await renderPatients()
    const search = container.querySelector('input[type="text"]')
    await fireEvent.update(search, 'priya')
    expect(screen.getByText('Priya Sharma')).toBeTruthy()
    expect(screen.queryByText('Rajesh Kumar')).toBeNull()
  })

  it('filters the list by village (nested address field)', async () => {
    const { container } = await renderPatients()
    const search = container.querySelector('input[type="text"]')
    await fireEvent.update(search, 'Sitapur')
    expect(screen.getByText('Rajesh Kumar')).toBeTruthy()
    expect(screen.queryByText('Priya Sharma')).toBeNull()
  })

  it('shows the empty state when a search matches nothing', async () => {
    const { container } = await renderPatients()
    const search = container.querySelector('input[type="text"]')
    await fireEvent.update(search, 'nobody-matches-this-xyz')
    expect(await screen.findByText(/no patients found/i)).toBeTruthy()
  })

  it('filters by risk level using the risk tabs', async () => {
    await renderPatients()
    // "High Risk" also appears as a stat-card label (a <div>) — scope to the tab <button>.
    await fireEvent.click(screen.getByRole('button', { name: 'High Risk' }))
    expect(screen.getByText('Priya Sharma')).toBeTruthy() // High risk
    expect(screen.queryByText('Rajesh Kumar')).toBeNull() // Moderate risk
  })

  it('sorting by location does not crash for seed patients without a top-level location field', async () => {
    const { container } = await renderPatients()
    const locationHeader = screen.getByText('Location')
    expect(() => fireEvent.click(locationHeader)).not.toThrow()
  })
})

describe('PatientsView — delete flow', () => {
  beforeEach(() => { localStorage.clear() })

  it('shows an inline confirmation before deleting, and cancel keeps the patient', async () => {
    await renderPatients()
    const store = usePatientsStore()
    const before = store.patients.length

    const deleteButtons = screen.getAllByTitle('Delete')
    await fireEvent.click(deleteButtons[0])
    expect(await screen.findByText('Cancel')).toBeTruthy()

    await fireEvent.click(screen.getByText('Cancel'))
    expect(store.patients.length).toBe(before)
  })

  it('removes the patient after confirming delete', async () => {
    await renderPatients()
    const store = usePatientsStore()
    const before = store.patients.length
    const firstName = store.patients[0].name

    const deleteButtons = screen.getAllByTitle('Delete')
    await fireEvent.click(deleteButtons[0])
    await fireEvent.click(await screen.findByText('Yes, Delete'))

    expect(store.patients.length).toBe(before - 1)
    expect(store.patients.find(p => p.name === firstName)).toBeUndefined()
  })
})
