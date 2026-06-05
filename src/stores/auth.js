import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(JSON.parse(localStorage.getItem('exobios_user') || 'null'))

  function login(credentials) {
    // Mock auth — replace with real API call
    const mockUser = { name: 'Sunita Devi', role: 'ASHA Worker', avatar: null }
    user.value = mockUser
    localStorage.setItem('exobios_auth', 'true')
    localStorage.setItem('exobios_user', JSON.stringify(mockUser))
  }

  function logout() {
    user.value = null
    localStorage.removeItem('exobios_auth')
    localStorage.removeItem('exobios_user')
  }

  return { user, login, logout }
})
