<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/features/auth/stores/auth'
import { useNotificationsStore } from '@/features/notifications/stores/notifications'
import { useI18n } from '@/i18n'
import StatusIndicator from '@/shared/components/StatusIndicator.vue'
import exobiosLogo from '@/assets/brand/exobios-logo-dark.png'

const router     = useRouter()
const route      = useRoute()
const auth       = useAuthStore()
const notifStore = useNotificationsStore()
const { t, locale, setLocale } = useI18n()

const sidebarOpen       = ref(false)
const showNotifications = ref(false)
const showProfileMenu   = ref(false)
const showLangMenu      = ref(false)

// Nav items grouped into subtle sections. Routes/permissions are unchanged —
// only the presentational grouping is new.
const navGroups = computed(() => {
  const groups = [
    {
      labelKey: 'nav.groupCore',
      items: [
        { key: 'nav.dashboard', icon: 'grid', to: '/dashboard' },
        ...(auth.isDoctor ? [
          { key: 'nav.doctorDashboard', icon: 'grid',     to: '/doctor/dashboard' },
          { key: 'nav.referralInbox',   icon: 'referral', to: '/doctor/referrals' },
        ] : []),
        { key: 'nav.patients', icon: 'person', to: '/patients' },
      ],
    },
    {
      labelKey: 'nav.groupCare',
      items: [
        { key: 'nav.childHealth',    icon: 'child',    to: '/child-health' },
        { key: 'nav.maternalHealth', icon: 'maternal', to: '/maternal-health' },
        { key: 'nav.sos',            icon: 'sos',      to: '/sos' },
      ],
    },
    {
      labelKey: 'nav.groupClinicalOps',
      items: [
        { key: 'nav.referrals',   icon: 'referral', to: '/referrals' },
        { key: 'nav.teleconsult', icon: 'video',    to: '/teleconsult' },
        { key: 'nav.devices',     icon: 'device',    to: '/devices' },
      ],
    },
    {
      labelKey: 'nav.groupAdmin',
      items: [
        ...(auth.hasPermission('view_reports') ? [{ key: 'nav.reports', icon: 'chart',  to: '/reports' }] : []),
        ...(auth.canManageUsers               ? [{ key: 'nav.users',   icon: 'shield', to: '/users'   }] : []),
        ...(auth.isSuperAdmin                 ? [{ key: 'nav.admin',   icon: 'cog',    to: '/admin'   }] : []),
      ],
    },
    {
      labelKey: 'nav.groupAccount',
      items: [
        { key: 'nav.notifications', icon: 'bell',     to: '/notifications' },
        { key: 'nav.feedback',      icon: 'feedback', to: '/feedback' },
        { key: 'nav.settings',      icon: 'settings', to: '/settings' },
      ],
    },
  ]
  return groups.filter(g => g.items.length > 0)
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

function goToProfile()          { showProfileMenu.value   = false; router.push('/profile') }
function viewAllNotifications() { showNotifications.value = false; router.push('/notifications') }

const userInitials = computed(() => {
  if (!auth.user?.name) return 'U'
  return auth.user.name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()
})

// Scoped per logged-in user (by loginId) so switching accounts on the same device
// doesn't show the previous user's photo — matches the key used in ProfileView.vue.
const profilePhoto = computed(() => localStorage.getItem(`exobios_profile_photo_${auth.user?.loginId || 'guest'}`) || '')

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

function handleEscape(e) {
  if (e.key !== 'Escape') return
  if (sidebarOpen.value) sidebarOpen.value = false
  showNotifications.value = false
  showProfileMenu.value   = false
  showLangMenu.value      = false
}

onMounted(() => {
  document.addEventListener('click', handleOutsideClick)
  document.addEventListener('keydown', handleEscape)
})
onUnmounted(() => {
  document.removeEventListener('click', handleOutsideClick)
  document.removeEventListener('keydown', handleEscape)
})

const notifDotColor = {
  error: 'bg-red-500', warning: 'bg-orange-400', success: 'bg-green-500', info: 'bg-blue-500',
}
</script>

<template>
  <div class="flex h-screen overflow-hidden bg-slate-50">

    <!-- Overlay behind sidebar on mobile -->
    <div v-if="sidebarOpen" class="fixed inset-0 z-40 bg-black/50 lg:hidden" @click="closeSidebar"/>

    <!-- ─── Sidebar ─── -->
    <aside
      data-sidebar
      :class="[
        'flex w-[236px] flex-shrink-0 select-none flex-col transition-transform duration-300 ease-in-out',
        'fixed inset-y-0 left-0 z-50 lg:relative lg:translate-x-0',
        sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0',
      ]"
      style="background: linear-gradient(180deg, #0a1628 0%, #0f1b35 60%, #0a1628 100%)"
    >
      <!-- Logo row -->
      <div class="flex items-center justify-between px-4 py-5">
        <button
          class="rounded-lg transition hover:opacity-85 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400/60"
          @click="router.push('/dashboard')"
        >
          <div class="inline-flex items-center rounded-xl bg-white/95 px-3 py-2">
            <img :src="exobiosLogo" alt="Exobios" class="h-5 w-auto object-contain"/>
          </div>
        </button>
        <!-- Close button visible only on mobile -->
        <button class="p-1 text-slate-400 transition hover:text-white lg:hidden" @click="closeSidebar" aria-label="Close menu">
          <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18M6 6l12 12"/></svg>
        </button>
      </div>

      <!-- Navigation links -->
      <nav class="flex-1 space-y-4 overflow-y-auto px-3 py-2 scrollbar-thin">
        <div v-for="group in navGroups" :key="group.labelKey">
          <p class="px-3 pb-1.5 text-[10px] font-semibold uppercase tracking-wider text-slate-500">{{ t(group.labelKey) }}</p>
          <div class="space-y-0.5">
            <router-link
              v-for="item in group.items"
              :key="item.to"
              :to="item.to"
              @click="closeSidebar"
              class="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400/60"
              :class="isActive(item.to)
                ? 'bg-blue-600 text-white'
                : 'text-slate-300 hover:bg-white/10 hover:text-white'"
            >
              <!-- Icon set for each nav type -->
              <svg v-if="item.icon === 'grid'"          class="h-5 w-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
              <div  v-else-if="item.icon === 'sos'"      class="flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-red-500" aria-hidden="true"><span class="text-[8px] font-bold text-white">SOS</span></div>
              <svg v-else-if="item.icon === 'chart'"     class="h-5 w-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/></svg>
              <svg v-else-if="item.icon === 'person'"    class="h-5 w-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></svg>
              <svg v-else-if="item.icon === 'settings'"  class="h-5 w-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
              <svg v-else-if="item.icon === 'referral'"  class="h-5 w-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
              <svg v-else-if="item.icon === 'video'"     class="h-5 w-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2"/></svg>
              <svg v-else-if="item.icon === 'feedback'"  class="h-5 w-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
              <svg v-else-if="item.icon === 'device'"    class="h-5 w-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M8.111 16.404a5.5 5.5 0 0 1 7.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0"/></svg>
              <svg v-else-if="item.icon === 'shield'"    class="h-5 w-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
              <svg v-else-if="item.icon === 'cog'"       class="h-5 w-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
              <svg v-else-if="item.icon === 'bell'"      class="h-5 w-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
              <svg v-else-if="item.icon === 'child'"     class="h-5 w-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="5" r="2.5"/><path d="M12 8v6M9 11H5.5a1.5 1.5 0 0 0 0 3H9m3-3h3.5a1.5 1.5 0 0 1 0 3H12m-2 3-1 4m4-4 1 4"/></svg>
              <svg v-else-if="item.icon === 'maternal'"  class="h-5 w-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="4.5" r="2.5"/><path d="M9 21v-6a5 5 0 0 1 10 0M4 21c0-3 2-5 4-5"/></svg>
              <span>{{ t(item.key) }}</span>
            </router-link>
          </div>
        </div>
      </nav>

      <!-- CTA -->
      <div class="flex-shrink-0 border-t border-white/10 px-3 py-4">
        <router-link
          to="/patients/new"
          @click="closeSidebar"
          class="flex h-11 w-full items-center justify-center gap-2 rounded-xl border border-transparent bg-blue-600 text-sm font-semibold text-white shadow-sm shadow-blue-600/20 transition-colors hover:bg-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400/60"
        >
          <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M12 5v14M5 12h14"/></svg>
          {{ t('nav.addPatient') }}
        </router-link>
      </div>
    </aside>

    <!-- ─── Main content area ─── -->
    <div class="flex min-w-0 flex-1 flex-col overflow-hidden">

      <!-- Topbar -->
      <header class="flex h-16 flex-shrink-0 items-center justify-between border-b border-slate-200 bg-white px-4 md:px-6">
        <div class="flex min-w-0 items-center gap-3">
          <!-- Hamburger — mobile only -->
          <button
            data-hamburger
            class="flex-shrink-0 rounded-lg p-1.5 text-slate-500 transition hover:bg-slate-100 hover:text-slate-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/40 lg:hidden"
            @click.stop="sidebarOpen = !sidebarOpen"
            aria-label="Toggle navigation menu"
          >
            <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>
            </svg>
          </button>

          <!-- Consumers inject the page title via slots -->
          <slot name="topbar-left">
            <div class="min-w-0">
              <h1 class="truncate text-sm font-semibold leading-tight text-slate-900 md:text-base">
                <slot name="page-title">Dashboard</slot>
              </h1>
              <p class="hidden truncate text-xs text-slate-400 sm:block"><slot name="page-subtitle"/></p>
            </div>
          </slot>
        </div>

        <div class="flex flex-shrink-0 items-center gap-2 md:gap-3">
          <!-- Connectivity + last sync -->
          <StatusIndicator/>

          <!-- Language switcher -->
          <div class="relative hidden sm:block" data-popup>
            <button
              class="flex items-center gap-1 rounded-lg border border-slate-200 px-2.5 py-1.5 text-xs font-semibold text-slate-600 transition hover:bg-slate-50 hover:text-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/40"
              @click.stop="showLangMenu = !showLangMenu; showNotifications = false; showProfileMenu = false"
              aria-haspopup="menu"
              :aria-expanded="showLangMenu"
            >
              <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
              <span>{{ currentLangLabel }}</span>
            </button>
            <div v-if="showLangMenu" class="absolute right-0 top-full z-50 mt-2 w-36 overflow-hidden rounded-xl border border-slate-100 bg-white py-1 shadow-lg">
              <button
                v-for="lang in languages"
                :key="lang.code"
                @click="setLocale(lang.code); showLangMenu = false"
                :class="['flex w-full items-center justify-between px-4 py-2.5 text-left text-sm transition hover:bg-slate-50', locale === lang.code ? 'font-semibold text-blue-600' : 'text-slate-700']"
              >
                {{ lang.full }}
                <svg v-if="locale === lang.code" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M20 6L9 17l-5-5"/></svg>
              </button>
            </div>
          </div>

          <!-- Notification bell -->
          <div class="relative" data-popup>
            <button
              class="relative rounded-lg p-2 text-slate-400 transition hover:bg-slate-100 hover:text-slate-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/40"
              @click.stop="showNotifications = !showNotifications; showProfileMenu = false; showLangMenu = false"
              :aria-label="`Notifications${notifStore.unreadCount > 0 ? ` (${notifStore.unreadCount} unread)` : ''}`"
              aria-haspopup="menu"
              :aria-expanded="showNotifications"
            >
              <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
              <span v-if="notifStore.unreadCount > 0"
                class="absolute right-1 top-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[9px] font-bold text-white">
                {{ notifStore.unreadCount }}
              </span>
            </button>

            <div v-if="showNotifications" class="absolute right-0 top-full z-50 mt-2 w-80 overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-lg">
              <div class="flex items-center justify-between border-b border-slate-100 px-4 py-3">
                <span class="text-sm font-semibold text-slate-800">{{ t('notif.title') }}</span>
                <button v-if="notifStore.unreadCount > 0" @click="notifStore.markAllRead()" class="text-xs text-blue-600 hover:underline">
                  {{ t('notif.markAllRead') }}
                </button>
              </div>
              <div class="max-h-72 overflow-y-auto">
                <div
                  v-for="n in notifStore.items.slice(0, 5)"
                  :key="n.id"
                  :class="['flex cursor-pointer gap-3 border-b border-slate-50 px-4 py-3 transition hover:bg-slate-50', !n.read ? 'bg-blue-50/40' : '']"
                  @click="notifStore.markRead(n.id)"
                >
                  <span :class="[notifDotColor[n.type], 'mt-1.5 h-2 w-2 flex-shrink-0 rounded-full']"/>
                  <div class="min-w-0 flex-1">
                    <div class="text-xs font-semibold text-slate-800">{{ n.title }}</div>
                    <div class="mt-0.5 line-clamp-2 text-xs leading-relaxed text-slate-500">{{ n.body }}</div>
                    <div class="mt-1 text-[10px] text-slate-400">{{ n.time }}</div>
                  </div>
                  <span v-if="!n.read" class="mt-1.5 h-2 w-2 flex-shrink-0 rounded-full bg-blue-500"/>
                </div>
                <div v-if="!notifStore.items.length" class="px-4 py-8 text-center">
                  <p class="text-xs text-slate-400">{{ t('notif.noNotifications') }}</p>
                </div>
              </div>
              <div class="border-t border-slate-100 px-4 py-2.5 text-center">
                <button @click="viewAllNotifications" class="text-xs font-medium text-blue-600 hover:underline">
                  {{ t('notif.viewAll') }}
                </button>
              </div>
            </div>
          </div>

          <!-- User avatar / profile dropdown -->
          <div class="relative" data-popup>
            <button
              class="flex cursor-pointer items-center gap-2 rounded-lg p-1 transition hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/40"
              @click.stop="showProfileMenu = !showProfileMenu; showNotifications = false; showLangMenu = false"
              aria-haspopup="menu"
              :aria-expanded="showProfileMenu"
            >
              <div class="flex h-8 w-8 flex-shrink-0 items-center justify-center overflow-hidden rounded-full bg-amber-100">
                <img v-if="profilePhoto" :src="profilePhoto" class="h-full w-full object-cover" alt="Profile photo"/>
                <span v-else class="text-xs font-semibold text-amber-700">{{ userInitials }}</span>
              </div>
              <div class="hidden text-right sm:block">
                <div class="text-sm font-medium leading-tight text-slate-800">{{ auth.user?.name }}</div>
                <div class="text-xs text-slate-400">{{ auth.user?.role }}</div>
              </div>
              <svg class="hidden h-3.5 w-3.5 flex-shrink-0 text-slate-400 sm:block" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M19 9l-7 7-7-7"/></svg>
            </button>

            <div v-if="showProfileMenu" class="absolute right-0 top-full z-50 mt-2 w-44 overflow-hidden rounded-xl border border-slate-100 bg-white shadow-lg">
              <button class="flex w-full items-center gap-3 px-4 py-3 text-left text-sm text-slate-700 transition hover:bg-slate-50" @click="goToProfile">
                <svg class="h-4 w-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                {{ t('profile.viewProfile') }}
              </button>
              <div class="mx-3 h-px bg-slate-100"/>
              <button class="flex w-full items-center gap-3 px-4 py-3 text-left text-sm text-red-600 transition hover:bg-red-50" @click="logout">
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
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
