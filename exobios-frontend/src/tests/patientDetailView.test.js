import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/vue'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import PatientDetailView from '@/features/patients/views/PatientDetailView.vue'
import { usePatientsStore } from '@/features/patients/stores/patients'
import { AppShellStub, SyncStatusBadgeStub } from './testUtils.js'

function makeRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/patients', name: 'Patients', component: { template: '<div/>' } },
      { path: '/patients/:id', name: 'PatientDetail', component: PatientDetailView },
      { path: '/patients/:id/edit', name: 'EditPatient', component: { template: '<div/>' } },
      { path: '/assessment/new', name: 'NewAssessment', component: { template: '<div/>' } },
      { path: '/assessment/:id/result', name: 'AIResult', component: { template: '<div/>' } },
    ],
  })
}

async function renderDetail(id) {
  setActivePinia(createPinia())
  const router = makeRouter()
  await router.push(`/patients/${id}`)
  await router.isReady()
  const utils = render(PatientDetailView, { global: { plugins: [router], stubs: { AppShell: AppShellStub, SyncStatusBadge: SyncStatusBadgeStub } } })
  return { ...utils, router }
}

describe('PatientDetailView', () => {
  beforeEach(() => { localStorage.clear() })

  it('shows a not-found message for an unknown patient id', async () => {
    await renderDetail(999999)
    expect(screen.getByText('Patient not found.')).toBeTruthy()
  })

  it('renders patient demographics and assessment history for a known patient', async () => {
    await renderDetail(1)
    // "Priya Sharma" also appears in the AppShell-stub page-subtitle slot — scope to the heading.
    expect(screen.getByRole('heading', { name: 'Priya Sharma' })).toBeTruthy()
    expect(screen.getByText(/High Risk/)).toBeTruthy()
    expect(screen.getByText(/Rampur Village/)).toBeTruthy()
    expect(screen.getByText('High Fever & Body Pain')).toBeTruthy()
    expect(screen.getByText('Latest')).toBeTruthy()
  })

  it('shows an empty state for a patient with no assessment history', async () => {
    setActivePinia(createPinia())
    const store = usePatientsStore()
    const id = store.add({ name: 'Fresh Patient', dob: '1990-01-01', gender: 'Female', phone: '9000000050', risk: 'Low', date: '1 Jan 2025', assessmentHistory: [] })
    const router = makeRouter()
    await router.push(`/patients/${id}`)
    await router.isReady()
    render(PatientDetailView, { global: { plugins: [router], stubs: { AppShell: AppShellStub, SyncStatusBadge: SyncStatusBadgeStub } } })

    expect(screen.getByText('No assessments yet.')).toBeTruthy()
    expect(screen.getByText('Start first assessment')).toBeTruthy()
  })

  it('navigates to a new assessment when "New Assessment" is clicked', async () => {
    const { router } = await renderDetail(2)
    await fireEvent.click(screen.getByText('New Assessment'))
    await waitFor(() => expect(router.currentRoute.value.name).toBe('NewAssessment'))
    expect(router.currentRoute.value.query.patientId).toBe('2')
  })

  it('navigates to the edit form when "Edit Info" is clicked', async () => {
    const { router } = await renderDetail(3)
    await fireEvent.click(screen.getByText('Edit Info'))
    await waitFor(() => expect(router.currentRoute.value.name).toBe('EditPatient'))
  })
})
