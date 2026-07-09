import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/vue'
import { setActivePinia, createPinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import ConfirmModal from '@/shared/components/ConfirmModal.vue'
import SessionExpiryModal from '@/shared/components/SessionExpiryModal.vue'
import { useAuthStore } from '@/features/auth/stores/auth'

describe('ConfirmModal', () => {
  it('renders nothing visible when show is false', () => {
    render(ConfirmModal, { props: { show: false } })
    expect(screen.queryByText('Are you sure?')).toBeNull()
  })

  it('renders the provided title/message/button text when shown', () => {
    render(ConfirmModal, {
      props: { show: true, title: 'Delete patient?', message: 'This cannot be undone.', confirmText: 'Delete', cancelText: 'Keep' },
    })
    expect(screen.getByText('Delete patient?')).toBeTruthy()
    expect(screen.getByText('This cannot be undone.')).toBeTruthy()
    expect(screen.getByText('Delete')).toBeTruthy()
    expect(screen.getByText('Keep')).toBeTruthy()
  })

  it('emits confirm when the confirm button is clicked', async () => {
    const { emitted } = render(ConfirmModal, { props: { show: true } })
    await fireEvent.click(screen.getByRole('button', { name: 'Confirm' }))
    expect(emitted().confirm).toBeTruthy()
  })

  it('emits cancel when the cancel button is clicked', async () => {
    const { emitted } = render(ConfirmModal, { props: { show: true } })
    await fireEvent.click(screen.getByText('Cancel'))
    expect(emitted().cancel).toBeTruthy()
  })
})

function makeRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', name: 'Login', component: { template: '<div/>' } },
      { path: '/dashboard', name: 'Dashboard', component: { template: '<div/>' } },
    ],
  })
}

describe('SessionExpiryModal', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })

  it('shows nothing when the session is not near expiry or expired', async () => {
    const auth = useAuthStore()
    auth.login({ loginId: '9000000000', name: 'Sunita', role: 'ASHA Worker' })
    const router = makeRouter()
    await router.push('/')
    render(SessionExpiryModal, { global: { plugins: [router] } })
    expect(screen.queryByText('Session Expiring Soon')).toBeNull()
    expect(screen.queryByText('Session Expired')).toBeNull()
  })

  it('shows the near-expiry warning with a countdown once sessionNearExpiry is true', async () => {
    const auth = useAuthStore()
    auth.login({ loginId: '9000000001', name: 'Sunita', role: 'ASHA Worker' })
    const router = makeRouter()
    await router.push('/')
    render(SessionExpiryModal, { global: { plugins: [router] } })

    auth.sessionNearExpiry = true
    expect(await screen.findByText('Session Expiring Soon')).toBeTruthy()
    expect(screen.getByText(/05:00/)).toBeTruthy()
  })

  it('"Stay Logged In" extends the session and clears the warning', async () => {
    const auth = useAuthStore()
    auth.login({ loginId: '9000000002', name: 'Sunita', role: 'ASHA Worker' })
    const router = makeRouter()
    await router.push('/')
    render(SessionExpiryModal, { global: { plugins: [router] } })

    auth.sessionNearExpiry = true
    await screen.findByText('Session Expiring Soon')
    const expiryBefore = JSON.parse(localStorage.getItem('exobios_auth')).expiresAt

    await fireEvent.click(screen.getByText('Stay Logged In'))
    expect(auth.sessionNearExpiry).toBe(false)
    const expiryAfter = JSON.parse(localStorage.getItem('exobios_auth')).expiresAt
    expect(expiryAfter).toBeGreaterThanOrEqual(expiryBefore)
  })

  it('shows the expired modal and "Log Out" returns to Login', async () => {
    const auth = useAuthStore()
    auth.login({ loginId: '9000000003', name: 'Sunita', role: 'ASHA Worker' })
    const router = makeRouter()
    await router.push('/dashboard')
    render(SessionExpiryModal, { global: { plugins: [router] } })

    auth.sessionExpired = true
    expect(await screen.findByText('Session Expired')).toBeTruthy()

    await fireEvent.click(screen.getByText('Back to Login'))
    expect(auth.isLoggedIn).toBe(false)
  })
})
