import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const ROLE_PERMISSIONS = {
  'ASHA Worker':     ['view_patients', 'add_patient', 'create_assessment'],
  'ANM':             ['view_patients', 'add_patient', 'create_assessment', 'view_reports'],
  'Doctor':          ['view_patients', 'add_patient', 'create_assessment', 'view_reports', 'manage_teleconsult'],
  'Supervisor':      ['view_patients', 'add_patient', 'create_assessment', 'view_reports', 'manage_teleconsult', 'manage_users'],
  'Admin':           ['view_patients', 'add_patient', 'create_assessment', 'view_reports', 'manage_teleconsult', 'manage_users', 'manage_system'],
  'Hospital Staff':  ['view_patients', 'view_reports'],
  'Super Admin':     ['view_patients', 'add_patient', 'create_assessment', 'view_reports', 'manage_teleconsult', 'manage_users', 'manage_system', 'super_admin'],
}

// 8-hour session
const SESSION_TTL_MS = 8 * 60 * 60 * 1000
// Warn 5 minutes before expiry
const SESSION_WARN_MS = 5 * 60 * 1000

const AUTH_KEY = 'exobios_auth'

function loadSession() {
  try {
    const raw = localStorage.getItem(AUTH_KEY)
    if (!raw) return null
    const session = JSON.parse(raw)
    if (!session?.expiresAt) return null
    if (Date.now() > session.expiresAt) {
      localStorage.removeItem(AUTH_KEY)
      return null
    }
    return session
  } catch {
    return null
  }
}

export const useAuthStore = defineStore('auth', () => {
  const session = ref(loadSession())

  const user       = computed(() => session.value?.user ?? null)
  const isLoggedIn = computed(() => !!session.value && Date.now() < (session.value?.expiresAt ?? 0))
  const isAdmin       = computed(() => ['Admin', 'Super Admin'].includes(user.value?.role))
  const isDoctor      = computed(() => user.value?.role === 'Doctor')
  const isSuperAdmin  = computed(() => user.value?.role === 'Super Admin')
  const canManageUsers = computed(() => (ROLE_PERMISSIONS[user.value?.role] ?? []).includes('manage_users'))

  // Reactive session-expiry warning (true when < 5 min left)
  const sessionNearExpiry = ref(false)
  const sessionExpired    = ref(false)

  let _expiryTimer  = null
  let _warnTimer    = null

  function scheduleExpiry() {
    if (_expiryTimer) clearTimeout(_expiryTimer)
    if (_warnTimer)   clearTimeout(_warnTimer)
    if (!session.value?.expiresAt) return
    const msLeft = session.value.expiresAt - Date.now()
    if (msLeft <= 0) { forceExpire(); return }
    if (msLeft > SESSION_WARN_MS) {
      _warnTimer = setTimeout(() => { sessionNearExpiry.value = true }, msLeft - SESSION_WARN_MS)
    } else {
      sessionNearExpiry.value = true
    }
    _expiryTimer = setTimeout(forceExpire, msLeft)
  }

  function forceExpire() {
    sessionExpired.value    = true
    sessionNearExpiry.value = false
    session.value           = null
    localStorage.removeItem(AUTH_KEY)
  }

  function hasPermission(action) {
    return (ROLE_PERMISSIONS[user.value?.role] ?? []).includes(action)
  }

  function login(userData) {
    const expiresAt = Date.now() + SESSION_TTL_MS
    const token     = btoa(JSON.stringify({ sub: userData.loginId, role: userData.role, iat: Date.now() }))
    session.value   = { user: { ...userData, token }, expiresAt, token }
    sessionExpired.value    = false
    sessionNearExpiry.value = false
    localStorage.setItem(AUTH_KEY, JSON.stringify(session.value))
    scheduleExpiry()
  }

  function extendSession() {
    if (!session.value) return
    const expiresAt = Date.now() + SESSION_TTL_MS
    session.value   = { ...session.value, expiresAt }
    sessionNearExpiry.value = false
    localStorage.setItem(AUTH_KEY, JSON.stringify(session.value))
    scheduleExpiry()
  }

  function logout() {
    if (_expiryTimer) clearTimeout(_expiryTimer)
    if (_warnTimer)   clearTimeout(_warnTimer)
    session.value           = null
    sessionExpired.value    = false
    sessionNearExpiry.value = false
    localStorage.removeItem(AUTH_KEY)
  }

  // Kick off expiry timer if session already loaded
  scheduleExpiry()

  return {
    user, isLoggedIn, isAdmin, isDoctor, isSuperAdmin, canManageUsers,
    hasPermission, login, logout, extendSession,
    sessionNearExpiry, sessionExpired,
  }
})
