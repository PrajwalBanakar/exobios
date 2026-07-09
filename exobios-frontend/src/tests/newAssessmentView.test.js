import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/vue'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import { ref } from 'vue'
import NewAssessmentView from '@/features/assessments/views/NewAssessmentView.vue'
import { usePatientsStore } from '@/features/patients/stores/patients'
import { useAuthStore } from '@/features/auth/stores/auth'
import { addToQueue } from '@/shared/offline/syncQueue'
import { AppShellStub, SyncStatusBadgeStub } from './testUtils.js'

// Controllable network status — NewAssessmentView reads `isOnline` directly from this
// module (not through useNetwork()), so we mock the module and flip the ref per test.
vi.mock('@/shared/offline/network.js', () => {
  const isOnline = ref(true)
  return { isOnline, useNetwork: () => ({ isOnline }) }
})
import * as networkModule from '@/shared/offline/network.js'

// The exam sub-components are covered by their own dedicated tests — stub them here so
// these tests stay focused on the container's own complaint/validation/draft/offline logic.
const examStub = { props: ['exam'], template: '<div />' }
const stubs = {
  AppShell: AppShellStub,
  SyncStatusBadge: SyncStatusBadgeStub,
  ParamedicGeneralExam: examStub,
  DoctorGeneralExam: examStub,
  RespiratoryExam: examStub,
  CVSExam: examStub,
  GIExam: examStub,
  CNSExam: examStub,
}

function makeRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/assessment/new', name: 'NewAssessment', component: NewAssessmentView },
      { path: '/assessment/:id/edit', name: 'EditAssessment', component: NewAssessmentView },
      { path: '/assessment/:id/result', name: 'AIResult', component: { template: '<div/>' } },
      { path: '/patients/:id', name: 'PatientDetail', component: { template: '<div/>' } },
    ],
  })
}

async function renderNew({ role = 'ASHA Worker', query = '' } = {}) {
  setActivePinia(createPinia())
  useAuthStore().login({ loginId: '9000000000', name: 'Test User', role })
  const router = makeRouter()
  await router.push(`/assessment/new${query}`)
  await router.isReady()
  const utils = render(NewAssessmentView, { global: { plugins: [router], stubs } })
  return { ...utils, router }
}

describe('NewAssessmentView — Basic Info validation', () => {
  beforeEach(() => { localStorage.clear(); networkModule.isOnline.value = true; vi.clearAllMocks() })

  it('blocks Analyze and shows errors when name/age/gender are missing', async () => {
    await renderNew()
    await fireEvent.click(screen.getByText('Analyze'))
    expect(await screen.findByText('Full name is required')).toBeTruthy()
    expect(screen.getByText('Age is required')).toBeTruthy()
    expect(screen.getByText('Sex is required')).toBeTruthy()
  })
})

describe('NewAssessmentView — Complaint & symptom selection', () => {
  beforeEach(() => { localStorage.clear(); networkModule.isOnline.value = true; vi.clearAllMocks() })

  async function openComplaints() {
    const utils = await renderNew()
    await fireEvent.click(screen.getByText('Patient Complaints'))
    return utils
  }

  it('expands a complaint detail panel when its chip is selected, and collapses it when deselected', async () => {
    await openComplaints()
    expect(screen.queryByText('Associated Symptoms')).toBeNull()

    const feverChip = screen.getByRole('button', { name: 'Fever' })
    await fireEvent.click(feverChip)
    expect(await screen.findByText('Associated Symptoms')).toBeTruthy()
    expect(screen.getByText('1 selected')).toBeTruthy()

    // The chip itself also acts as the toggle-off control.
    await fireEvent.click(feverChip)
    expect(screen.queryByText('Associated Symptoms')).toBeNull()
  })

  it('checks an associated symptom for a selected complaint', async () => {
    await openComplaints()
    await fireEvent.click(screen.getByRole('button', { name: 'Fever' }))

    const symptomLabel = screen.getByText('Chills / severe shivering')
    const checkbox = symptomLabel.closest('label').querySelector('input[type="checkbox"]')
    expect(checkbox.checked).toBe(false)
    await fireEvent.click(symptomLabel)
    expect(checkbox.checked).toBe(true)
  })

  it('raises an AI flag banner when a long fever duration is selected', async () => {
    await openComplaints()
    await fireEvent.click(screen.getByRole('button', { name: 'Fever' }))
    await fireEvent.click(screen.getByText('> 2 weeks'))
    const matches = await screen.findAllByText(/Mandatory Tuberculosis Screening Protocol required/)
    expect(matches.length).toBeGreaterThan(0)
  })

  it('supports selecting more than one complaint at a time', async () => {
    await openComplaints()
    await fireEvent.click(screen.getByRole('button', { name: 'Fever' }))
    await fireEvent.click(screen.getByRole('button', { name: 'Cough' }))
    expect(screen.getByText('2 selected')).toBeTruthy()
  })
})

describe('NewAssessmentView — role-based examination module', () => {
  beforeEach(() => { localStorage.clear(); networkModule.isOnline.value = true; vi.clearAllMocks() })

  async function openExamination(role) {
    await renderNew({ role })
    await fireEvent.click(screen.getByText('Examination & Vitals'))
  }

  it('shows the Paramedic general exam module for a Paramedic role', async () => {
    await openExamination('ASHA Worker')
    expect(await screen.findByText('Paramedic General Examination')).toBeTruthy()
  })

  it('shows the Doctor general exam module for an MBBS Doctor role', async () => {
    await openExamination('MBBS Doctor')
    expect(await screen.findByText('Doctor General Physical Examination')).toBeTruthy()
  })
})

describe('NewAssessmentView — draft saving', () => {
  beforeEach(() => { localStorage.clear(); networkModule.isOnline.value = true; vi.clearAllMocks() })

  it('persists the current form to localStorage and confirms with "Draft Saved!"', async () => {
    vi.useFakeTimers()
    const { container } = await renderNew()
    const nameInput = container.querySelector('input[placeholder="Full Name"]')
    await fireEvent.update(nameInput, 'Draft Patient')

    await fireEvent.click(screen.getByText('Save Draft'))
    await vi.advanceTimersByTimeAsync(500)

    expect(screen.getByText('Draft Saved!')).toBeTruthy()
    const saved = JSON.parse(localStorage.getItem('assessment_draft_new'))
    expect(saved.form.fullName).toBe('Draft Patient')
    vi.useRealTimers()
  })

  it('restores a previously saved draft on mount', async () => {
    setActivePinia(createPinia())
    useAuthStore().login({ loginId: '9000000001', name: 'Test User', role: 'ASHA Worker' })
    localStorage.setItem('assessment_draft_new', JSON.stringify({
      form: { fullName: 'Restored Patient', age: '40', gender: 'Male', phone: '', location: '', abhaId: '' },
    }))
    const router = makeRouter()
    await router.push('/assessment/new')
    await router.isReady()
    const { container } = render(NewAssessmentView, { global: { plugins: [router], stubs } })

    const nameInput = container.querySelector('input[placeholder="Full Name"]')
    await waitFor(() => expect(nameInput.value).toBe('Restored Patient'))
  })
})

describe('NewAssessmentView — offline queue behavior', () => {
  beforeEach(() => { localStorage.clear(); vi.clearAllMocks() })

  it('queues the assessment for sync and shows an offline banner when submitted while offline', async () => {
    networkModule.isOnline.value = false
    setActivePinia(createPinia())
    useAuthStore().login({ loginId: '9000000002', name: 'Test User', role: 'ASHA Worker' })
    const patientsStore = usePatientsStore()
    const patientId = patientsStore.add({ name: 'Linked Patient', dob: '1990-01-01', gender: 'Female', phone: '9000000099', risk: 'Low', date: '1 Jan 2025', assessmentHistory: [] })

    const router = makeRouter()
    await router.push(`/assessment/new?patientId=${patientId}`)
    await router.isReady()
    render(NewAssessmentView, { global: { plugins: [router], stubs } })

    await fireEvent.click(screen.getByText('Analyze'))

    await waitFor(() => expect(addToQueue).toHaveBeenCalledWith('add_assessment', expect.objectContaining({ patientId })))
    expect(await screen.findByText(/saved offline/i)).toBeTruthy()
    await waitFor(() => expect(router.currentRoute.value.name).toBe('AIResult'))
  })

  it('does not touch the offline queue when submitted while online', async () => {
    networkModule.isOnline.value = true
    setActivePinia(createPinia())
    useAuthStore().login({ loginId: '9000000003', name: 'Test User', role: 'ASHA Worker' })
    const patientsStore = usePatientsStore()
    const patientId = patientsStore.add({ name: 'Online Patient', dob: '1990-01-01', gender: 'Male', phone: '9000000098', risk: 'Low', date: '1 Jan 2025', assessmentHistory: [] })

    const router = makeRouter()
    await router.push(`/assessment/new?patientId=${patientId}`)
    await router.isReady()
    render(NewAssessmentView, { global: { plugins: [router], stubs } })

    await fireEvent.click(screen.getByText('Analyze'))
    await waitFor(() => expect(router.currentRoute.value.name).toBe('AIResult'))
    expect(addToQueue).not.toHaveBeenCalled()
    expect(patientsStore.getById(patientId)?.assessmentHistory.length).toBe(1)
  })
})
