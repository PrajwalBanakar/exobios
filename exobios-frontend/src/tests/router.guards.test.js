import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import router from '@/app/router/index.js'
import { useAuthStore } from '@/features/auth/stores/auth'

// These exercise the real router.beforeEach guard defined in app/router/index.js —
// no <router-view> is mounted, so navigating only resolves route records/lazy
// components, it never renders them (component setup() only runs on mount).
describe('Router — role-based navigation guards', () => {
  beforeEach(async () => {
    setActivePinia(createPinia())
    localStorage.clear()
    await router.push('/')
  })

  it('redirects an unauthenticated user away from a protected route to Login', async () => {
    await router.push('/dashboard')
    expect(router.currentRoute.value.name).toBe('Login')
  })

  it('allows an unauthenticated user to reach the public Landing route', async () => {
    await router.push('/')
    expect(router.currentRoute.value.name).toBe('Landing')
  })

  it('allows an unauthenticated user to reach the Login route itself', async () => {
    await router.push('/login')
    expect(router.currentRoute.value.name).toBe('Login')
  })

  it('redirects an already-logged-in user away from Landing to the Dashboard', async () => {
    useAuthStore().login({ loginId: '9000000001', name: 'Sunita', role: 'ASHA Worker' })
    // Navigate elsewhere first — pushing to the route we're already on is a no-op
    // in Vue Router (guards don't re-run for a fully-duplicate navigation).
    await router.push('/unauthorized')
    await router.push('/')
    expect(router.currentRoute.value.name).toBe('Dashboard')
  })

  it('redirects an already-logged-in user away from Login to the Dashboard', async () => {
    useAuthStore().login({ loginId: '9000000009', name: 'Sunita', role: 'ASHA Worker' })
    await router.push('/unauthorized')
    await router.push('/login')
    expect(router.currentRoute.value.name).toBe('Dashboard')
  })

  it('allows a logged-in user to reach a protected route with no extra permission', async () => {
    useAuthStore().login({ loginId: '9000000002', name: 'Sunita', role: 'ASHA Worker' })
    await router.push('/patients')
    expect(router.currentRoute.value.name).toBe('Patients')
  })

  it('blocks a Paramedic from a Super-Admin-only route (Unauthorized)', async () => {
    useAuthStore().login({ loginId: '9000000003', name: 'Sunita', role: 'ASHA Worker' })
    await router.push('/admin')
    expect(router.currentRoute.value.name).toBe('Unauthorized')
  })

  it('blocks a Paramedic from the manage_users-gated Users route', async () => {
    useAuthStore().login({ loginId: '9000000004', name: 'Sunita', role: 'ASHA Worker' })
    await router.push('/users')
    expect(router.currentRoute.value.name).toBe('Unauthorized')
  })

  it('allows a Super Admin through the manage_users-gated Users route', async () => {
    useAuthStore().login({ loginId: '9000000005', name: 'Admin', role: 'Super Admin' })
    await router.push('/users')
    expect(router.currentRoute.value.name).toBe('Users')
  })

  it('blocks a Paramedic from the view_reports-gated Reports route', async () => {
    useAuthStore().login({ loginId: '9000000006', name: 'Sunita', role: 'ASHA Worker' })
    await router.push('/reports')
    expect(router.currentRoute.value.name).toBe('Unauthorized')
  })

  it('allows an MBBS Doctor (has view_reports) through the Reports route', async () => {
    useAuthStore().login({ loginId: '9000000007', name: 'Dr. Rao', role: 'MBBS Doctor' })
    await router.push('/reports')
    expect(router.currentRoute.value.name).toBe('Reports')
  })

  it('redirects to Login when a session has expired', async () => {
    useAuthStore().login({ loginId: '9000000008', name: 'Sunita', role: 'ASHA Worker' })
    // Force the persisted session to look expired, then reload the store from it.
    const raw = JSON.parse(localStorage.getItem('exobios_auth'))
    raw.expiresAt = Date.now() - 1000
    localStorage.setItem('exobios_auth', JSON.stringify(raw))
    setActivePinia(createPinia())

    await router.push('/dashboard')
    expect(router.currentRoute.value.name).toBe('Login')
  })

  it('allows unauthenticated access to a route with no requiresAuth meta', async () => {
    await router.push('/unauthorized')
    expect(router.currentRoute.value.name).toBe('Unauthorized')
  })
})
