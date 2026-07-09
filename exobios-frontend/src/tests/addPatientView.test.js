import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/vue'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import AddPatientView from '@/features/patients/views/AddPatientView.vue'
import { usePatientsStore } from '@/features/patients/stores/patients'
import { AppShellStub, SyncStatusBadgeStub } from './testUtils.js'

function makeRouter(initialPath = '/patients/new') {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/patients/new', name: 'AddPatient', component: AddPatientView },
      { path: '/patients/:id/edit', name: 'EditPatient', component: AddPatientView },
      { path: '/patients', name: 'Patients', component: { template: '<div>patients-list</div>' } },
      { path: '/assessment/new', name: 'NewAssessment', component: { template: '<div>new-assessment</div>' } },
    ],
  })
  return router
}

async function renderAddPatient(path = '/patients/new') {
  setActivePinia(createPinia())
  const router = makeRouter()
  await router.push(path)
  await router.isReady()
  const utils = render(AddPatientView, {
    global: { plugins: [router], stubs: { AppShell: AppShellStub, SyncStatusBadge: SyncStatusBadgeStub } },
  })
  return { ...utils, router }
}

describe('AddPatientView — validation', () => {
  beforeEach(() => { localStorage.clear() })

  it('shows field errors and does not save when required fields are missing', async () => {
    const { container } = await renderAddPatient()
    await fireEvent.click(screen.getByRole('button', { name: 'Register Patient' }))
    await waitFor(() => {
      expect(screen.getByText('Name is required')).toBeTruthy()
      expect(screen.getByText('Date of birth is required')).toBeTruthy()
      expect(screen.getByText('Sex is required')).toBeTruthy()
      expect(screen.getByText('Valid 10-digit phone required')).toBeTruthy()
    })
  })

  it('rejects a phone number shorter than 10 digits', async () => {
    const { container } = await renderAddPatient()
    await fireEvent.update(container.querySelector('input[placeholder="Patient\'s full name"]'), 'Test Patient')
    await fireEvent.update(container.querySelector('input[type="date"]'), '1990-01-01')
    await fireEvent.update(container.querySelector('select'), 'Female')
    await fireEvent.update(container.querySelector('input[placeholder="10-digit number"]'), '123')
    await fireEvent.click(screen.getByRole('button', { name: 'Register Patient' }))
    expect(await screen.findByText('Valid 10-digit phone required')).toBeTruthy()
  })

  it('shows the calculated age once a date of birth is entered', async () => {
    const { container } = await renderAddPatient()
    await fireEvent.update(container.querySelector('input[type="date"]'), '2000-01-01')
    expect(await screen.findByText(/^Age: \d+ years$/)).toBeTruthy()
  })
})

describe('AddPatientView — create flow', () => {
  beforeEach(() => { localStorage.clear() })

  it('registers a new patient and navigates to a linked new assessment', async () => {
    vi.useFakeTimers()
    const { container, router } = await renderAddPatient()
    const store = usePatientsStore()
    const before = store.patients.length

    await fireEvent.update(container.querySelector('input[placeholder="Patient\'s full name"]'), 'New Patient')
    await fireEvent.update(container.querySelector('input[type="date"]'), '1995-05-05')
    await fireEvent.update(container.querySelector('select'), 'Male')
    await fireEvent.update(container.querySelector('input[placeholder="10-digit number"]'), '9123456780')
    await fireEvent.click(screen.getByRole('button', { name: 'Register Patient' }))
    await vi.advanceTimersByTimeAsync(400)

    expect(store.patients.length).toBe(before + 1)
    expect(store.patients[0].name).toBe('New Patient')
    expect(router.currentRoute.value.name).toBe('NewAssessment')
    vi.useRealTimers()
  })

  it('combines village and district into a single location field', async () => {
    vi.useFakeTimers()
    const { container } = await renderAddPatient()
    const store = usePatientsStore()

    await fireEvent.update(container.querySelector('input[placeholder="Patient\'s full name"]'), 'Location Patient')
    await fireEvent.update(container.querySelector('input[type="date"]'), '1995-05-05')
    await fireEvent.update(container.querySelector('select'), 'Male')
    await fireEvent.update(container.querySelector('input[placeholder="10-digit number"]'), '9123456781')
    await fireEvent.update(container.querySelector('input[placeholder="Village or town name"]'), 'Rampur')
    await fireEvent.update(container.querySelector('input[placeholder="District name"]'), 'Rampur District')
    await fireEvent.click(screen.getByRole('button', { name: 'Register Patient' }))
    await vi.advanceTimersByTimeAsync(400)

    expect(store.patients[0].location).toBe('Rampur, Rampur District')
    vi.useRealTimers()
  })
})

describe('AddPatientView — edit flow', () => {
  beforeEach(() => { localStorage.clear() })

  it('pre-fills the form with the existing patient and saves changes in place', async () => {
    vi.useFakeTimers()
    setActivePinia(createPinia())
    const store = usePatientsStore()
    const id = store.add({ name: 'Original Name', dob: '1980-01-01', gender: 'Male', phone: '9000000099', risk: 'Low', date: '1 Jan 2025' })

    const router = makeRouter()
    await router.push(`/patients/${id}/edit`)
    await router.isReady()
    const { container } = render(AddPatientView, {
      global: { plugins: [router], stubs: { AppShell: AppShellStub, SyncStatusBadge: SyncStatusBadgeStub } },
    })

    const nameInput = container.querySelector('input[placeholder="Patient\'s full name"]')
    expect(nameInput.value).toBe('Original Name')

    await fireEvent.update(nameInput, 'Updated Name')
    await fireEvent.click(screen.getByRole('button', { name: 'Save Changes' }))
    await vi.advanceTimersByTimeAsync(400)

    expect(store.getById(id)?.name).toBe('Updated Name')
    expect(router.currentRoute.value.name).toBe('Patients')
    vi.useRealTimers()
  })
})

describe('AddPatientView — family details (marital status)', () => {
  beforeEach(() => { localStorage.clear() })

  it('shows the Spouses section only after selecting Married', async () => {
    const { container } = await renderAddPatient()
    expect(screen.queryByText('Spouses')).toBeNull()
    await fireEvent.click(screen.getByText('Married'))
    expect(await screen.findByText('Spouses')).toBeTruthy()
  })

  it('adds and removes a spouse from the list', async () => {
    const { container } = await renderAddPatient()
    await fireEvent.click(screen.getByText('Married'))
    await fireEvent.update(container.querySelector('input[placeholder="Spouse\'s full name"]'), 'Ramesh')
    await fireEvent.update(container.querySelector('input[placeholder="Age"]'), '30')
    await fireEvent.click(screen.getAllByRole('button', { name: '+ Add' })[0])
    expect(await screen.findByText('Ramesh')).toBeTruthy()

    await fireEvent.click(screen.getByLabelText('Remove Ramesh'))
    expect(screen.queryByText('Ramesh')).toBeNull()
  })
})
