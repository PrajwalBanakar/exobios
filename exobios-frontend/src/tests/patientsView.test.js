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

  // The desktop table and mobile card list both render in jsdom at once (CSS media
  // queries aren't evaluated), so each visible patient's name appears twice — once
  // per layout. Assertions below check for that count rather than a single match.
  it('lists all seed patients by default', async () => {
    await renderPatients()
    expect(screen.getAllByText('Priya Sharma').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Rajesh Kumar').length).toBeGreaterThan(0)
  })

  it('filters the list by name without crashing on patients that lack a top-level location field', async () => {
    const { container } = await renderPatients()
    const search = container.querySelector('input[type="text"]')
    await fireEvent.update(search, 'priya')
    expect(screen.getAllByText('Priya Sharma').length).toBeGreaterThan(0)
    expect(screen.queryAllByText('Rajesh Kumar').length).toBe(0)
  })

  it('filters the list by village (nested address field)', async () => {
    const { container } = await renderPatients()
    const search = container.querySelector('input[type="text"]')
    await fireEvent.update(search, 'Sitapur')
    expect(screen.getAllByText('Rajesh Kumar').length).toBeGreaterThan(0)
    expect(screen.queryAllByText('Priya Sharma').length).toBe(0)
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
    expect(screen.getAllByText('Priya Sharma').length).toBeGreaterThan(0) // High risk
    expect(screen.queryAllByText('Rajesh Kumar').length).toBe(0) // Moderate risk
  })

  it('sorting by location does not crash for seed patients without a top-level location field', async () => {
    const { container } = await renderPatients()
    const locationHeader = screen.getByText('Location')
    expect(() => fireEvent.click(locationHeader)).not.toThrow()
  })
})

describe('PatientsView — delete flow', () => {
  beforeEach(() => { localStorage.clear() })

  async function openDeleteConfirm() {
    const menuButtons = screen.getAllByRole('button', { name: /more actions for/i })
    await fireEvent.click(menuButtons[0])
    await fireEvent.click(await screen.findByRole('menuitem', { name: /delete patient/i }))
  }

  it('shows a confirmation dialog before deleting, and cancel keeps the patient', async () => {
    await renderPatients()
    const store = usePatientsStore()
    const before = store.patients.length

    await openDeleteConfirm()
    expect(await screen.findByText('Cancel')).toBeTruthy()

    await fireEvent.click(screen.getByText('Cancel'))
    expect(store.patients.length).toBe(before)
  })

  it('removes the patient after confirming delete', async () => {
    await renderPatients()
    const store = usePatientsStore()
    const before = store.patients.length
    const firstName = store.patients[0].name

    await openDeleteConfirm()
    await fireEvent.click(await screen.findByRole('button', { name: 'Delete' }))

    expect(store.patients.length).toBe(before - 1)
    expect(store.patients.find(p => p.name === firstName)).toBeUndefined()
  })
})
