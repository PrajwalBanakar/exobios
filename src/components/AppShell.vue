<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const route  = useRoute()
const auth   = useAuthStore()

const sidebarOpen = ref(false)

const nav = [
  { name: 'Dashboard',     icon: 'grid',     to: '/dashboard' },
  { name: 'Patients',      icon: 'users',    to: '/patients' },
  { name: 'SOS / Emergency', icon: 'sos',   to: '/sos',  badge: true },
  { name: 'Reports',       icon: 'chart',    to: '/reports' },
  { name: 'Users',         icon: 'person',   to: '/users' },
  { name: 'Settings',      icon: 'settings', to: '/settings' },
]

function isActive(path) {
  return route.path.startsWith(path)
}

function logout() {
  auth.logout()
  router.push('/')
}

const userInitials = computed(() => {
  if (!auth.user?.name) return 'U'
  return auth.user.name.split(' ').map(n => n[0]).join('').slice(0, 2)
})
</script>

<template>
  <div class="flex h-screen bg-gray-50 overflow-hidden">
    <!-- Sidebar -->
    <aside class="w-[180px] flex-shrink-0 bg-navy-900 flex flex-col select-none"
           style="background: linear-gradient(180deg, #0a1628 0%, #0f1b35 60%, #0a1628 100%)">
      <!-- Logo -->
      <div class="px-5 py-5 flex items-center gap-2">
        <div class="w-9 h-9 rounded-lg bg-blue-500 flex items-center justify-center flex-shrink-0">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L2 7l10 5 10-5-10-5z" stroke="white" stroke-width="2" stroke-linejoin="round"/>
            <path d="M2 17l10 5 10-5" stroke="white" stroke-width="2" stroke-linejoin="round"/>
            <path d="M2 12l10 5 10-5" stroke="white" stroke-width="2" stroke-linejoin="round"/>
          </svg>
        </div>
        <span class="text-white font-bold text-lg tracking-tight">Exobios</span>
      </div>

      <!-- Nav -->
      <nav class="flex-1 px-3 py-2 space-y-1">
        <router-link
          v-for="item in nav"
          :key="item.to"
          :to="item.to"
          class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors"
          :class="isActive(item.to)
            ? 'bg-blue-600 text-white'
            : 'text-slate-300 hover:bg-white/10 hover:text-white'"
        >
          <!-- Icons -->
          <svg v-if="item.icon === 'grid'" class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
            <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>
            <rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>
          </svg>
          <svg v-else-if="item.icon === 'users'" class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
            <path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
          </svg>
          <div v-else-if="item.icon === 'sos'" class="w-5 h-5 flex-shrink-0 rounded-full bg-red-500 flex items-center justify-center">
            <span class="text-white text-[8px] font-bold leading-none">SOS</span>
          </div>
          <svg v-else-if="item.icon === 'chart'" class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
            <rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/>
          </svg>
          <svg v-else-if="item.icon === 'person'" class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
          </svg>
          <svg v-else-if="item.icon === 'settings'" class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
            <circle cx="12" cy="12" r="3"/>
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
          </svg>
          <span>{{ item.name }}</span>
        </router-link>
      </nav>

      <!-- Add New -->
      <div class="px-3 pb-4">
        <router-link to="/assessment/new"
          class="flex items-center gap-2 w-full px-3 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold transition-colors">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
            <path d="M12 5v14M5 12h14"/>
          </svg>
          Add New
        </router-link>
      </div>
    </aside>

    <!-- Main area -->
    <div class="flex-1 flex flex-col min-w-0">
      <!-- Topbar -->
      <header class="h-14 bg-white border-b border-gray-200 flex items-center justify-between px-6 flex-shrink-0">
        <slot name="topbar-left">
          <div class="flex items-center gap-3">
            <button @click="sidebarOpen = !sidebarOpen" class="text-gray-400 hover:text-gray-600 lg:hidden">
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path d="M4 6h16M4 12h16M4 18h16"/>
              </svg>
            </button>
            <div>
              <h1 class="text-base font-semibold text-gray-900 leading-tight">
                <slot name="page-title">Dashboard</slot>
              </h1>
              <p class="text-xs text-gray-400">
                <slot name="page-subtitle"></slot>
              </p>
            </div>
          </div>
        </slot>

        <div class="flex items-center gap-4">
          <!-- Network -->
          <div class="hidden sm:flex items-center gap-1.5 text-xs text-gray-500">
            <span class="w-2 h-2 rounded-full bg-green-500"></span>
            <span>Online</span>
          </div>

          <!-- Sync -->
          <div class="hidden sm:flex items-center gap-1.5 text-xs text-gray-500">
            <svg class="w-3.5 h-3.5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 0 0 4.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 0 1-15.357-2m15.357 2H15"/>
            </svg>
            <div>
              <div class="font-medium text-green-600">Synced</div>
              <div>16 May 2025, 10:30 AM</div>
            </div>
          </div>

          <!-- Bell -->
          <button class="relative text-gray-400 hover:text-gray-600">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
              <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
            </svg>
            <span class="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white text-[9px] font-bold rounded-full flex items-center justify-center">3</span>
          </button>

          <!-- User -->
          <div class="flex items-center gap-2 cursor-pointer" @click="logout">
            <div class="w-8 h-8 rounded-full bg-amber-200 flex items-center justify-center">
              <span class="text-xs font-semibold text-amber-700">{{ userInitials }}</span>
            </div>
            <div class="hidden sm:block text-right">
              <div class="text-sm font-medium text-gray-800">{{ auth.user?.name }}</div>
              <div class="text-xs text-gray-400">{{ auth.user?.role }}</div>
            </div>
          </div>
        </div>
      </header>

      <!-- Page content -->
      <main class="flex-1 overflow-y-auto">
        <slot />
      </main>
    </div>
  </div>
</template>
