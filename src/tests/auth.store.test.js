import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/features/auth/stores/auth'

describe('Auth Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })

  afterEach(() => {
    vi.clearAllTimers()
  })

  it('starts logged out when localStorage is empty', () => {
    const auth = useAuthStore()
    expect(auth.isLoggedIn).toBe(false)
    expect(auth.user).toBeNull()
  })

  it('login() sets user and persists to localStorage', () => {
    const auth = useAuthStore()
    auth.login({ loginId: 'asha01', name: 'Sunita', role: 'ASHA Worker' })
    expect(auth.isLoggedIn).toBe(true)
    expect(auth.user?.role).toBe('ASHA Worker')
    expect(localStorage.setItem).toHaveBeenCalledWith(
      'exobios_auth',
      expect.stringContaining('Sunita')
    )
  })

  it('logout() clears user and localStorage', () => {
    const auth = useAuthStore()
    auth.login({ loginId: 'asha01', name: 'Sunita', role: 'ASHA Worker' })
    auth.logout()
    expect(auth.isLoggedIn).toBe(false)
    expect(auth.user).toBeNull()
    expect(localStorage.removeItem).toHaveBeenCalledWith('exobios_auth')
  })

  it('hasPermission() returns correct permissions for ASHA Worker', () => {
    const auth = useAuthStore()
    auth.login({ loginId: 'asha01', name: 'Sunita', role: 'ASHA Worker' })
    expect(auth.hasPermission('view_patients')).toBe(true)
    expect(auth.hasPermission('create_assessment')).toBe(true)
    expect(auth.hasPermission('view_reports')).toBe(false)
    expect(auth.hasPermission('manage_users')).toBe(false)
  })

  it('hasPermission() returns all permissions for Super Admin', () => {
    const auth = useAuthStore()
    auth.login({ loginId: 'sa01', name: 'Rajesh', role: 'Super Admin' })
    expect(auth.hasPermission('view_reports')).toBe(true)
    expect(auth.hasPermission('manage_users')).toBe(true)
    expect(auth.hasPermission('manage_system')).toBe(true)
    expect(auth.hasPermission('super_admin')).toBe(true)
  })

  it('canManageUsers is false for ASHA Worker', () => {
    const auth = useAuthStore()
    auth.login({ loginId: 'asha01', name: 'Sunita', role: 'ASHA Worker' })
    expect(auth.canManageUsers).toBe(false)
  })

  it('canManageUsers is true for Super Admin', () => {
    const auth = useAuthStore()
    auth.login({ loginId: 'sa01', name: 'Rajesh', role: 'Super Admin' })
    expect(auth.canManageUsers).toBe(true)
  })

  it('isSuperAdmin is true only for Super Admin role', () => {
    const auth = useAuthStore()
    auth.login({ loginId: 'sa01', name: 'SA', role: 'Super Admin' })
    expect(auth.isSuperAdmin).toBe(true)
    auth.logout()
    auth.login({ loginId: 'asha01', name: 'Sunita', role: 'ASHA Worker' })
    expect(auth.isSuperAdmin).toBe(false)
  })

  it('extendSession() resets expiry', async () => {
    const auth = useAuthStore()
    auth.login({ loginId: 'asha01', name: 'Sunita', role: 'ASHA Worker' })
    const firstExpiry = JSON.parse(localStorage.getItem('exobios_auth')).expiresAt
    await new Promise(r => setTimeout(r, 10))
    auth.extendSession()
    const newExpiry = JSON.parse(localStorage.getItem('exobios_auth')).expiresAt
    expect(newExpiry).toBeGreaterThan(firstExpiry)
  })

  it('expired session returns isLoggedIn=false', () => {
    const expiredSession = {
      user: { loginId: 'x', name: 'X', role: 'ASHA Worker' },
      expiresAt: Date.now() - 1000,
    }
    localStorage.getItem.mockReturnValueOnce(JSON.stringify(expiredSession))
    const auth = useAuthStore()
    expect(auth.isLoggedIn).toBe(false)
  })
})
