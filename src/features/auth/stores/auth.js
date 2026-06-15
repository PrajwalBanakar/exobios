import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

/**
 * Role-based permission map.
 * Each role lists which actions it may perform — checked via hasPermission().
 */
const ROLE_PERMISSIONS = {
  'ASHA Worker':     ['view_patients', 'add_patient', 'create_assessment'],
  'ANM':             ['view_patients', 'add_patient', 'create_assessment', 'view_reports'],
  'Doctor':          ['view_patients', 'add_patient', 'create_assessment', 'view_reports', 'manage_teleconsult'],
  'Supervisor':      ['view_patients', 'add_patient', 'create_assessment', 'view_reports', 'manage_teleconsult', 'manage_users'],
  'Admin':           ['view_patients', 'add_patient', 'create_assessment', 'view_reports', 'manage_teleconsult', 'manage_users', 'manage_system'],
  'Hospital Staff':  ['view_patients', 'view_reports'],
  'Super Admin':     ['view_patients', 'add_patient', 'create_assessment', 'view_reports', 'manage_teleconsult', 'manage_users', 'manage_system', 'super_admin'],
}

export const useAuthStore = defineStore('auth', () => {
  // Rehydrate user from localStorage on store creation
  const raw  = localStorage.getItem('exobios_auth')
  const user = ref(raw ? JSON.parse(raw) : null)

  const isLoggedIn    = computed(() => !!user.value)
  const isAdmin       = computed(() => ['Admin', 'Super Admin'].includes(user.value?.role))
  const isDoctor      = computed(() => user.value?.role === 'Doctor')
  const isSuperAdmin  = computed(() => user.value?.role === 'Super Admin')
  const canManageUsers = computed(() => {
    const perms = ROLE_PERMISSIONS[user.value?.role] ?? []
    return perms.includes('manage_users')
  })

  function hasPermission(action) {
    return (ROLE_PERMISSIONS[user.value?.role] ?? []).includes(action)
  }

  function login(userData) {
    user.value = userData
    localStorage.setItem('exobios_auth', JSON.stringify(userData))
  }

  function logout() {
    user.value = null
    localStorage.removeItem('exobios_auth')
  }

  return { user, isLoggedIn, isAdmin, isDoctor, isSuperAdmin, canManageUsers, hasPermission, login, logout }
})
