<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/features/auth/stores/auth'
import { useNotificationsStore } from '@/features/notifications/stores/notifications'
import { useI18n } from '@/i18n'

const router     = useRouter()
const route      = useRoute()
const auth       = useAuthStore()
const notifStore = useNotificationsStore()
const { t, locale, setLocale } = useI18n()

const sidebarOpen       = ref(false)
const showNotifications = ref(false)
const showProfileMenu   = ref(false)
const showLangMenu      = ref(false)
const syncTime          = ref('')
const isOnline          = ref(navigator.onLine)

const nav = computed(() => {
  const items = [
    { key: 'nav.dashboard',     icon: 'grid',     to: '/dashboard' },
    { key: 'nav.patients',      icon: 'person',   to: '/patients'  },
    { key: 'nav.childHealth',    icon: 'child',    to: '/child-health' },
    { key: 'nav.maternalHealth', icon: 'maternal', to: '/maternal-health' },
    { key: 'nav.sos',           icon: 'sos',      to: '/sos' },
    { key: 'nav.referrals',     icon: 'referral', to: '/referrals' },
    { key: 'nav.teleconsult',   icon: 'video',    to: '/teleconsult' },
    { key: 'nav.devices',       icon: 'device',   to: '/devices' },
    { key: 'nav.notifications', icon: 'bell',     to: '/notifications' },
    { key: 'nav.feedback',      icon: 'feedback', to: '/feedback' },
    ...(auth.hasPermission('view_reports') ? [{ key: 'nav.reports', icon: 'chart', to: '/reports' }] : []),
    ...(auth.canManageUsers ? [{ key: 'nav.users', icon: 'shield', to: '/users' }] : []),
    ...(auth.isSuperAdmin   ? [{ key: 'nav.admin', icon: 'cog',    to: '/admin' }] : []),
    { key: 'nav.settings', icon: 'settings', to: '/settings' },
  ]
  return items
})

const languages = [
  { code: 'en', label: 'EN',  full: 'English' },
  { code: 'hi', label: 'हिं', full: 'हिंदी' },
  { code: 'kn', label: 'ಕನ',  full: 'ಕನ್ನಡ' },
]

const currentLangLabel = computed(() => languages.find(l => l.code === locale.value)?.label || 'EN')

// A route is "active" when the current path starts with the nav item's path
function isActive(path) { return route.path.startsWith(path) }

function logout() {
  showProfileMenu.value = false
  auth.logout()
  router.push('/')
}

function closeSidebar() { sidebarOpen.value = false }

function goToProfile()         { showProfileMenu.value   = false; router.push('/profile') }
function viewAllNotifications() { showNotifications.value = false; router.push('/notifications') }

const userInitials = computed(() => {
  if (!auth.user?.name) return 'U'
  return auth.user.name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()
})

// Scoped per logged-in user (by loginId) so switching accounts on the same device
// doesn't show the previous user's photo — matches the key used in ProfileView.vue.
const profilePhoto = computed(() => localStorage.getItem(`exobios_profile_photo_${auth.user?.loginId || 'guest'}`) || '')

function updateSyncTime() {
  const now = new Date()
  syncTime.value =
    now.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) +
    ', ' + now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true })
}

// Close dropdowns when clicking outside any [data-popup] element
function handleOutsideClick(e) {
  if (!e.target.closest('[data-popup]')) {
    showNotifications.value = false
    showProfileMenu.value   = false
    showLangMenu.value      = false
  }
  if (!e.target.closest('[data-sidebar]') && !e.target.closest('[data-hamburger]')) {
    sidebarOpen.value = false
  }
}

let syncInterval
onMounted(() => {
  updateSyncTime()
  syncInterval = setInterval(updateSyncTime, 60_000)
  document.addEventListener('click', handleOutsideClick)
  window.addEventListener('online',  () => { isOnline.value = true  })
  window.addEventListener('offline', () => { isOnline.value = false })
})
onUnmounted(() => {
  clearInterval(syncInterval)
  document.removeEventListener('click', handleOutsideClick)
})

const notifDotColor = {
  error: 'bg-red-500', warning: 'bg-orange-400', success: 'bg-green-500', info: 'bg-blue-500',
}
</script>

<template>
  <div class="flex h-screen bg-gray-50 overflow-hidden">

    <!-- Overlay behind sidebar on mobile -->
    <div v-if="sidebarOpen" class="fixed inset-0 bg-black/50 z-40 lg:hidden" @click="closeSidebar"/>

    <!-- ─── Sidebar ─── -->
    <aside
      data-sidebar
      :class="[
        'w-[200px] flex-shrink-0 flex flex-col select-none transition-transform duration-300 ease-in-out',
        'fixed inset-y-0 left-0 z-50 lg:relative lg:translate-x-0',
        sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0',
      ]"
      style="background: linear-gradient(180deg, #0a1628 0%, #0f1b35 60%, #0a1628 100%)"
    >
      <!-- Logo row -->
      <div class="px-5 py-5 flex items-center justify-between">
        <button class="flex items-center gap-2 hover:opacity-80 transition" @click="router.push('/dashboard')">
          <div class="w-9 h-9 rounded-lg bg-blue-500 flex items-center justify-center flex-shrink-0">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L2 7l10 5 10-5-10-5z" stroke="white" stroke-width="2" stroke-linejoin="round"/>
              <path d="M2 17l10 5 10-5"           stroke="white" stroke-width="2" stroke-linejoin="round"/>
              <path d="M2 12l10 5 10-5"           stroke="white" stroke-width="2" stroke-linejoin="round"/>
            </svg>
          </div>
          <span class="text-white font-bold text-lg tracking-tight">Exobios</span>
        </button>
        <!-- Close button visible only on mobile -->
        <button class="lg:hidden text-slate-400 hover:text-white p-1" @click="closeSidebar" aria-label="Close menu">
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18M6 6l12 12"/></svg>
        </button>
      </div>

      <!-- Navigation links -->
      <nav class="flex-1 px-3 py-2 space-y-0.5 overflow-y-auto scrollbar-thin">
        <router-link
          v-for="item in nav"
          :key="item.to"
          :to="item.to"
          @click="closeSidebar"
          class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors"
          :class="isActive(item.to)
            ? 'bg-blue-600 text-white'
            : 'text-slate-300 hover:bg-white/10 hover:text-white'"
        >
          <!-- Icon set for each nav type -->
          <svg v-if="item.icon === 'grid'"          class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
          <div  v-else-if="item.icon === 'sos'"      class="w-5 h-5 flex-shrink-0 rounded-full bg-red-500 flex items-center justify-center"><span class="text-white text-[8px] font-bold">SOS</span></div>
          <svg v-else-if="item.icon === 'chart'"     class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/></svg>
          <svg v-else-if="item.icon === 'person'"    class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></svg>
          <svg v-else-if="item.icon === 'settings'"  class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
          <svg v-else-if="item.icon === 'referral'"  class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
          <svg v-else-if="item.icon === 'video'"     class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2"/></svg>
          <svg v-else-if="item.icon === 'feedback'"  class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
          <svg v-else-if="item.icon === 'device'"    class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M8.111 16.404a5.5 5.5 0 0 1 7.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0"/></svg>
          <svg v-else-if="item.icon === 'shield'"    class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
          <svg v-else-if="item.icon === 'cog'"       class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
          <svg v-else-if="item.icon === 'bell'"      class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
          <svg v-else-if="item.icon === 'child'"     class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="5" r="2.5"/><path d="M12 8v6M9 11H5.5a1.5 1.5 0 0 0 0 3H9m3-3h3.5a1.5 1.5 0 0 1 0 3H12m-2 3-1 4m4-4 1 4"/></svg>
          <svg v-else-if="item.icon === 'maternal'"  class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="4.5" r="2.5"/><path d="M9 21v-6a5 5 0 0 1 10 0M4 21c0-3 2-5 4-5"/></svg>
          <span>{{ t(item.key) }}</span>
        </router-link>
      </nav>

      <!-- CTA -->
      <div class="px-3 pb-4 flex-shrink-0">
        <router-link
          to="/patients/new"
          @click="closeSidebar"
          class="flex items-center gap-2 w-full px-3 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold transition-colors"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M12 5v14M5 12h14"/></svg>
          {{ t('nav.addPatient') }}
        </router-link>
      </div>
    </aside>

    <!-- ─── Main content area ─── -->
    <div class="flex-1 flex flex-col min-w-0 overflow-hidden">

      <!-- Topbar -->
      <header class="h-14 bg-white border-b border-gray-200 flex items-center justify-between px-4 md:px-6 flex-shrink-0">
        <div class="flex items-center gap-3 min-w-0">
          <!-- Hamburger — mobile only -->
          <button
            data-hamburger
            class="lg:hidden flex-shrink-0 text-gray-500 hover:text-gray-700 p-1 rounded-lg hover:bg-gray-100 transition"
            @click.stop="sidebarOpen = !sidebarOpen"
            aria-label="Toggle navigation menu"
          >
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>
            </svg>
          </button>

          <!-- Consumers inject the page title via slots -->
          <slot name="topbar-left">
            <div class="min-w-0">
              <h1 class="text-sm md:text-base font-semibold text-gray-900 leading-tight truncate">
                <slot name="page-title">Dashboard</slot>
              </h1>
              <p class="text-xs text-gray-400 hidden sm:block truncate"><slot name="page-subtitle"/></p>
            </div>
          </slot>
        </div>

        <div class="flex items-center gap-2 md:gap-4 flex-shrink-0">
          <!-- Online / Offline indicator -->
          <div class="hidden md:flex items-center gap-1.5 text-xs" :class="isOnline ? 'text-gray-500' : 'text-orange-500'">
            <span :class="['w-2 h-2 rounded-full', isOnline ? 'bg-green-500' : 'bg-orange-500 animate-pulse']"/>
            <span>{{ isOnline ? t('topbar.online') : t('sync.offline') }}</span>
          </div>

          <!-- Last sync timestamp -->
          <div class="hidden lg:flex items-center gap-1.5 text-xs text-gray-500">
            <svg class="w-3.5 h-3.5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M4 4v5h.582m15.356 2A8.001 8.001 0 0 0 4.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 0 1-15.357-2m15.357 2H15"/></svg>
            <div>
              <div class="font-medium text-green-600">{{ t('topbar.synced') }}</div>
              <div>{{ syncTime }}</div>
            </div>
          </div>

          <!-- Language switcher -->
          <div class="relative hidden sm:block" data-popup>
            <button
              class="flex items-center gap-1 px-2.5 py-1.5 text-xs font-semibold text-gray-600 hover:text-gray-800 border border-gray-200 rounded-lg hover:bg-gray-50 transition"
              @click.stop="showLangMenu = !showLangMenu; showNotifications = false; showProfileMenu = false"
            >
              <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
              <span>{{ currentLangLabel }}</span>
            </button>
            <div v-if="showLangMenu" class="absolute right-0 top-full mt-2 w-36 bg-white rounded-xl shadow-xl border border-gray-100 z-50 overflow-hidden py-1">
              <button
                v-for="lang in languages"
                :key="lang.code"
                @click="setLocale(lang.code); showLangMenu = false"
                :class="['w-full flex items-center justify-between px-4 py-2.5 text-sm hover:bg-gray-50 transition text-left', locale.value === lang.code ? 'text-blue-600 font-semibold' : 'text-gray-700']"
              >
                {{ lang.full }}
                <svg v-if="locale.value === lang.code" class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M20 6L9 17l-5-5"/></svg>
              </button>
            </div>
          </div>

          <!-- Notification bell -->
          <div class="relative" data-popup>
            <button
              class="relative text-gray-400 hover:text-gray-600 p-1.5 rounded-lg hover:bg-gray-100 transition"
              @click.stop="showNotifications = !showNotifications; showProfileMenu = false; showLangMenu = false"
              :aria-label="`Notifications${notifStore.unreadCount > 0 ? ` (${notifStore.unreadCount} unread)` : ''}`"
            >
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
              <span v-if="notifStore.unreadCount > 0"
                class="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white text-[9px] font-bold rounded-full flex items-center justify-center">
                {{ notifStore.unreadCount }}
              </span>
            </button>

            <div v-if="showNotifications" class="absolute right-0 top-full mt-2 w-80 bg-white rounded-xl shadow-xl border border-gray-100 z-50 overflow-hidden">
              <div class="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
                <span class="font-semibold text-gray-800 text-sm">{{ t('notif.title') }}</span>
                <button v-if="notifStore.unreadCount > 0" @click="notifStore.markAllRead()" class="text-xs text-blue-600 hover:underline">
                  {{ t('notif.markAllRead') }}
                </button>
              </div>
              <div class="max-h-72 overflow-y-auto">
                <div
                  v-for="n in notifStore.items.slice(0, 5)"
                  :key="n.id"
                  :class="['flex gap-3 px-4 py-3 hover:bg-gray-50 transition border-b border-gray-50 cursor-pointer', !n.read ? 'bg-blue-50/40' : '']"
                  @click="notifStore.markRead(n.id)"
                >
                  <span :class="[notifDotColor[n.type], 'w-2 h-2 rounded-full mt-1.5 flex-shrink-0']"/>
                  <div class="flex-1 min-w-0">
                    <div class="text-xs font-semibold text-gray-800">{{ n.title }}</div>
                    <div class="text-xs text-gray-500 mt-0.5 leading-relaxed line-clamp-2">{{ n.body }}</div>
                    <div class="text-[10px] text-gray-400 mt-1">{{ n.time }}</div>
                  </div>
                  <span v-if="!n.read" class="w-2 h-2 rounded-full bg-blue-500 mt-1.5 flex-shrink-0"/>
                </div>
                <div v-if="!notifStore.items.length" class="px-4 py-8 text-center">
                  <p class="text-xs text-gray-400">{{ t('notif.noNotifications') }}</p>
                </div>
              </div>
              <div class="px-4 py-2.5 text-center border-t border-gray-100">
                <button @click="viewAllNotifications" class="text-xs text-blue-600 hover:underline font-medium">
                  {{ t('notif.viewAll') }}
                </button>
              </div>
            </div>
          </div>

          <!-- User avatar / profile dropdown -->
          <div class="relative" data-popup>
            <button
              class="flex items-center gap-2 cursor-pointer p-1 rounded-lg hover:bg-gray-50 transition"
              @click.stop="showProfileMenu = !showProfileMenu; showNotifications = false; showLangMenu = false"
            >
              <div class="w-8 h-8 rounded-full bg-amber-200 flex items-center justify-center overflow-hidden flex-shrink-0">
                <img v-if="profilePhoto" :src="profilePhoto" class="w-full h-full object-cover" alt="Profile photo"/>
                <span v-else class="text-xs font-semibold text-amber-700">{{ userInitials }}</span>
              </div>
              <div class="hidden sm:block text-right">
                <div class="text-sm font-medium text-gray-800 leading-tight">{{ auth.user?.name }}</div>
                <div class="text-xs text-gray-400">{{ auth.user?.role }}</div>
              </div>
              <svg class="w-3.5 h-3.5 text-gray-400 hidden sm:block flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M19 9l-7 7-7-7"/></svg>
            </button>

            <div v-if="showProfileMenu" class="absolute right-0 top-full mt-2 w-44 bg-white rounded-xl shadow-xl border border-gray-100 z-50 overflow-hidden">
              <button class="w-full flex items-center gap-3 px-4 py-3 text-sm text-gray-700 hover:bg-gray-50 transition text-left" @click="goToProfile">
                <svg class="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                {{ t('profile.viewProfile') }}
              </button>
              <div class="h-px bg-gray-100 mx-3"/>
              <button class="w-full flex items-center gap-3 px-4 py-3 text-sm text-red-600 hover:bg-red-50 transition text-left" @click="logout">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
                {{ t('profile.logout') }}
              </button>
            </div>
          </div>
        </div>
      </header>

      <!-- Scrollable page content -->
      <main class="flex-1 overflow-y-auto">
        <slot />
      </main>
    </div>
  </div>
</template>
