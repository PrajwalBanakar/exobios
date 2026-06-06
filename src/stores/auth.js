import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const ROLE_PERMISSIONS = {
  'ASHA Worker':   ['dashboard', 'patients', 'assessment', 'sos', 'referrals', 'teleconsult', 'reports', 'settings'],
  'ANM':           ['dashboard', 'patients', 'assessment', 'sos', 'referrals', 'teleconsult', 'reports', 'settings'],
  'Doctor':        ['dashboard', 'patients', 'sos', 'referrals', 'teleconsult', 'reports', 'users', 'settings'],
  'Supervisor':    ['dashboard', 'patients', 'sos', 'referrals', 'teleconsult', 'reports', 'users', 'settings'],
  'Admin':         ['dashboard', 'patients', 'assessment', 'sos', 'referrals', 'teleconsult', 'reports', 'users', 'settings'],
  'Hospital Staff':['dashboard', 'patients', 'sos', 'referrals', 'teleconsult', 'reports', 'settings'],
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref(JSON.parse(localStorage.getItem('exobios_user') || 'null'))

  function login(credentials) {
    const mockUser = { name: 'Sunita Devi', role: 'ASHA Worker', ashaId: 'ASHA-2023-00451', area: 'Rampur Block', avatar: null }
    user.value = mockUser
    localStorage.setItem('exobios_auth', 'true')
    localStorage.setItem('exobios_user', JSON.stringify(mockUser))
  }

  function logout() {
    user.value = null
    localStorage.removeItem('exobios_auth')
    localStorage.removeItem('exobios_user')
  }

  function hasPermission(permission) {
    const role = user.value?.role || 'ASHA Worker'
    return ROLE_PERMISSIONS[role]?.includes(permission) ?? true
  }

  const isAdmin        = computed(() => ['Admin', 'Supervisor'].includes(user.value?.role))
  const isDoctor       = computed(() => user.value?.role === 'Doctor')
  const canManageUsers = computed(() => hasPermission('users'))

  return { user, login, logout, hasPermission, isAdmin, isDoctor, canManageUsers }
})
