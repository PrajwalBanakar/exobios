<script setup>
import { ref, reactive, computed } from 'vue'
import AppShell from '@/shared/components/AppShell.vue'
import { useAuthStore } from '@/features/auth/stores/auth'
import { useI18n } from '@/i18n'

const auth             = useAuthStore()
const { t, locale, setLocale } = useI18n()

const activeSection = ref('notifications')
const sections = [
  { id: 'notifications', label: 'settings.notifications', icon: 'bell'     },
  { id: 'app',           label: 'settings.app',           icon: 'settings'  },
  { id: 'language',      label: 'settings.language',      icon: 'globe'     },
  { id: 'security',      label: 'settings.security',      icon: 'lock'      },
  { id: 'devices',       label: 'settings.devices',       icon: 'sync'      },
]

const notifPrefs = reactive({
  highRiskAlerts: true, referralUpdates: true, teleconsultReminders: true,
  systemUpdates: false, dailySummary: true, emailNotifs: false,
})

const notifSettingsList = computed(() => [
  { key: 'highRiskAlerts',       label: t('settings.highRiskAlerts'),       desc: t('settings.highRiskAlertsDesc') },
  { key: 'referralUpdates',      label: t('settings.referralUpdates'),      desc: t('settings.referralUpdatesDesc') },
  { key: 'teleconsultReminders', label: t('settings.teleconsultReminders'), desc: t('settings.teleconsultRemindersDesc') },
  { key: 'systemUpdates',        label: t('settings.systemUpdatesNotif'),   desc: t('settings.systemUpdatesNotifDesc') },
  { key: 'dailySummary',         label: t('settings.dailySummary'),         desc: t('settings.dailySummaryDesc') },
  { key: 'emailNotifs',          label: t('settings.emailNotifs'),          desc: t('settings.emailNotifsDesc') },
])

const appSettings = reactive({ autoSync: true, offlineMode: false, largeText: false, compactView: false })

const appSettingsList = computed(() => [
  { key: 'autoSync',    label: t('settings.autoSync'),    desc: t('settings.autoSyncDesc') },
  { key: 'offlineMode', label: t('settings.offlineMode'), desc: t('settings.offlineModeDesc') },
  { key: 'largeText',   label: t('settings.largeText'),   desc: t('settings.largeTextDesc') },
  { key: 'compactView', label: t('settings.compactView'), desc: t('settings.compactViewDesc') },
])

const saved = ref(false)
function saveSettings() { saved.value = true; setTimeout(() => { saved.value = false }, 2000) }

const currentPassword = ref(''); const newPassword = ref(''); const confirmPassword = ref('')
const passwordError = ref(''); const passwordSuccess = ref(false)
function changePassword() {
  if (!currentPassword.value || !newPassword.value) { passwordError.value = 'Please fill all fields.'; return }
  if (newPassword.value !== confirmPassword.value)  { passwordError.value = 'Passwords do not match.'; return }
  passwordError.value = ''; passwordSuccess.value = true
  currentPassword.value = ''; newPassword.value = ''; confirmPassword.value = ''
  setTimeout(() => { passwordSuccess.value = false }, 3000)
}

const devices = ref([
  { id: 1, name: 'Redmi Note 12 (Current)', type: 'Mobile', lastSync: 'Just now',    active: true  },
  { id: 2, name: 'Laptop - Chrome',          type: 'Web',    lastSync: '2 hours ago', active: false },
  { id: 3, name: 'Tablet - Chrome',          type: 'Web',    lastSync: '3 days ago',  active: false },
  { id: 4, name: 'Old Phone (Redmi 9)',       type: 'Mobile', lastSync: '7 days ago',  active: false },
])

const availableLanguages = [
  { code: 'en', name: 'English', native: 'English', flag: '🇬🇧' },
  { code: 'hi', name: 'Hindi',   native: 'हिंदी',   flag: '🇮🇳' },
  { code: 'kn', name: 'Kannada', native: 'ಕನ್ನಡ',  flag: '🇮🇳' },
]
</script>

<template>
  <AppShell>
    <template #page-title>{{ t('settings.title') }}</template>
    <template #page-subtitle>{{ t('settings.subtitle') }}</template>

    <div class="p-4 md:p-6">
      <div class="flex flex-col lg:flex-row gap-5">

        <!-- Sidebar nav -->
        <div class="lg:w-48 flex-shrink-0">
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-2 flex lg:flex-col gap-1 overflow-x-auto lg:overflow-visible">
            <button v-for="s in sections" :key="s.id"
              @click="activeSection = s.id"
              :class="['flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm font-medium transition whitespace-nowrap flex-shrink-0', activeSection === s.id ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-50']">
              <svg v-if="s.icon==='bell'" class="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
              <svg v-else-if="s.icon==='settings'" class="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
              <svg v-else-if="s.icon==='globe'" class="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
              <svg v-else-if="s.icon==='lock'" class="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
              <svg v-else-if="s.icon==='sync'" class="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M4 4v5h.582m15.356 2A8.001 8.001 0 0 0 4.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 0 1-15.357-2m15.357 2H15"/></svg>
              <span>{{ t(s.label) }}</span>
            </button>
          </div>
        </div>

        <!-- Content panels -->
        <div class="flex-1 min-w-0">

          <!-- Notifications -->
          <div v-if="activeSection==='notifications'" class="bg-white rounded-xl border border-gray-100 shadow-sm p-5 md:p-6">
            <h2 class="font-semibold text-gray-800 text-base mb-1">{{ t('settings.notifications') }}</h2>
            <p class="text-xs text-gray-400 mb-6">{{ t('settings.notifSubtitle') }}</p>
            <div v-for="item in notifSettingsList" :key="item.key" class="flex items-center justify-between py-4 border-b border-gray-50 last:border-0">
              <div class="flex-1 min-w-0 pr-4">
                <div class="text-sm font-medium text-gray-800">{{ item.label }}</div>
                <div class="text-xs text-gray-500 mt-0.5">{{ item.desc }}</div>
              </div>
              <button class="relative w-11 h-6 rounded-full flex-shrink-0 transition-colors duration-200"
                :class="notifPrefs[item.key] ? 'bg-blue-600' : 'bg-gray-200'"
                @click="notifPrefs[item.key] = !notifPrefs[item.key]">
                <span class="absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow-sm transition-transform duration-200"
                  :class="notifPrefs[item.key] ? 'translate-x-5' : 'translate-x-0'"/>
              </button>
            </div>
            <div class="mt-5">
              <button @click="saveSettings" class="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-xl transition">
                <svg v-if="!saved" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
                <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M20 6L9 17l-5-5"/></svg>
                {{ saved ? t('settings.saved') : t('common.save') }}
              </button>
            </div>
          </div>

          <!-- App Settings -->
          <div v-if="activeSection==='app'" class="bg-white rounded-xl border border-gray-100 shadow-sm p-5 md:p-6">
            <h2 class="font-semibold text-gray-800 text-base mb-1">{{ t('settings.app') }}</h2>
            <p class="text-xs text-gray-400 mb-6">{{ t('settings.appSubtitle') }}</p>
            <div v-for="item in appSettingsList" :key="item.key" class="flex items-center justify-between py-4 border-b border-gray-50 last:border-0">
              <div class="flex-1 min-w-0 pr-4">
                <div class="text-sm font-medium text-gray-800">{{ item.label }}</div>
                <div class="text-xs text-gray-500 mt-0.5">{{ item.desc }}</div>
              </div>
              <button class="relative w-11 h-6 rounded-full flex-shrink-0 transition-colors duration-200"
                :class="appSettings[item.key] ? 'bg-blue-600' : 'bg-gray-200'"
                @click="appSettings[item.key] = !appSettings[item.key]">
                <span class="absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow-sm transition-transform duration-200"
                  :class="appSettings[item.key] ? 'translate-x-5' : 'translate-x-0'"/>
              </button>
            </div>
            <div class="mt-5">
              <button @click="saveSettings" class="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-xl transition">
                <svg v-if="!saved" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
                <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M20 6L9 17l-5-5"/></svg>
                {{ saved ? t('settings.saved') : t('common.save') }}
              </button>
            </div>
          </div>

          <!-- Language -->
          <div v-if="activeSection==='language'" class="bg-white rounded-xl border border-gray-100 shadow-sm p-5 md:p-6">
            <h2 class="font-semibold text-gray-800 text-base mb-1">{{ t('settings.language') }}</h2>
            <p class="text-xs text-gray-400 mb-6">{{ t('settings.langSubtitle') }}</p>
            <div class="space-y-3 max-w-sm">
              <div v-for="lang in availableLanguages" :key="lang.code"
                @click="setLocale(lang.code)"
                :class="['flex items-center justify-between p-4 rounded-xl border-2 cursor-pointer transition', locale===lang.code ? 'border-blue-500 bg-blue-50/50' : 'border-gray-100 hover:border-gray-200 hover:bg-gray-50']">
                <div class="flex items-center gap-3">
                  <span class="text-2xl">{{ lang.flag }}</span>
                  <div>
                    <div class="text-sm font-semibold text-gray-800">{{ lang.native }}</div>
                    <div class="text-xs text-gray-500">{{ lang.name }}</div>
                  </div>
                </div>
                <div :class="['w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0', locale===lang.code ? 'border-blue-500 bg-blue-500' : 'border-gray-300']">
                  <svg v-if="locale===lang.code" class="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path d="M20 6L9 17l-5-5"/></svg>
                </div>
              </div>
            </div>
            <p class="text-xs text-gray-400 mt-4">{{ t('settings.langNote') }}</p>
          </div>

          <!-- Security -->
          <div v-if="activeSection==='security'" class="bg-white rounded-xl border border-gray-100 shadow-sm p-5 md:p-6">
            <h2 class="font-semibold text-gray-800 text-base mb-1">{{ t('settings.security') }}</h2>
            <p class="text-xs text-gray-400 mb-6">{{ t('settings.securitySubtitle') }}</p>
            <div class="max-w-md space-y-4">
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1.5">{{ t('settings.currentPassword') }}</label>
                <input v-model="currentPassword" type="password" class="w-full border border-gray-200 rounded-xl px-3.5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"/>
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1.5">{{ t('settings.newPassword') }}</label>
                <input v-model="newPassword" type="password" class="w-full border border-gray-200 rounded-xl px-3.5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"/>
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1.5">{{ t('settings.confirmNewPassword') }}</label>
                <input v-model="confirmPassword" type="password" class="w-full border border-gray-200 rounded-xl px-3.5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"/>
              </div>
              <p v-if="passwordError" class="text-xs text-red-500">{{ passwordError }}</p>
              <div v-if="passwordSuccess" class="flex items-center gap-2 text-green-600 text-xs bg-green-50 px-3 py-2 rounded-lg">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg>
                {{ t('settings.passwordChanged') }}
              </div>
              <button @click="changePassword" class="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-xl transition">{{ t('settings.changePassword') }}</button>
            </div>
            <div class="mt-8 pt-6 border-t border-gray-100">
              <h3 class="font-medium text-gray-800 text-sm mb-4">{{ t('settings.activeSessions') }}</h3>
              <div class="space-y-3">
                <div class="flex items-center gap-3 py-3 border-b border-gray-50">
                  <div class="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                    <svg class="w-4 h-4 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><rect x="5" y="2" width="14" height="20" rx="2"/><line x1="12" y1="18" x2="12.01" y2="18"/></svg>
                  </div>
                  <div class="flex-1">
                    <div class="text-sm font-medium text-gray-800">Redmi Note 12 <span class="text-xs text-green-500">({{ t('settings.current') }})</span></div>
                    <div class="text-xs text-gray-400">Rampur, Uttar Pradesh · Just now</div>
                  </div>
                </div>
                <div class="flex items-center gap-3 py-3">
                  <div class="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center">
                    <svg class="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/></svg>
                  </div>
                  <div class="flex-1">
                    <div class="text-sm font-medium text-gray-800">Chrome on Windows</div>
                    <div class="text-xs text-gray-400">Delhi · 2 hours ago</div>
                  </div>
                  <button class="text-xs text-red-500 hover:text-red-700 transition">{{ t('settings.signOut') }}</button>
                </div>
              </div>
            </div>
          </div>

          <!-- Devices -->
          <div v-if="activeSection==='devices'" class="bg-white rounded-xl border border-gray-100 shadow-sm p-5 md:p-6">
            <h2 class="font-semibold text-gray-800 text-base mb-1">{{ t('settings.devices') }}</h2>
            <p class="text-xs text-gray-400 mb-6">{{ t('settings.devicesSubtitle') }}</p>
            <div class="space-y-3">
              <div v-for="d in devices" :key="d.id"
                :class="['flex items-center justify-between p-4 rounded-xl border transition', d.active ? 'border-blue-200 bg-blue-50/30' : 'border-gray-100 hover:bg-gray-50']">
                <div class="flex items-center gap-3">
                  <div :class="['w-10 h-10 rounded-full flex items-center justify-center', d.active ? 'bg-blue-100' : 'bg-gray-100']">
                    <svg v-if="d.type==='Mobile'" class="w-5 h-5" :class="d.active ? 'text-blue-600' : 'text-gray-500'" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><rect x="5" y="2" width="14" height="20" rx="2"/><line x1="12" y1="18" x2="12.01" y2="18"/></svg>
                    <svg v-else class="w-5 h-5" :class="d.active ? 'text-blue-600' : 'text-gray-500'" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/></svg>
                  </div>
                  <div>
                    <div class="text-sm font-medium text-gray-800">{{ d.name }}</div>
                    <div class="text-xs text-gray-400">{{ d.type }} · Last sync: {{ d.lastSync }}</div>
                  </div>
                </div>
                <span v-if="d.active" class="flex items-center gap-1 text-xs text-green-600 font-medium">
                  <span class="w-1.5 h-1.5 rounded-full bg-green-500"/>{{ t('settings.active') }}
                </span>
                <button v-else class="text-xs text-gray-400 hover:text-red-500 border border-gray-200 px-2.5 py-1 rounded-lg transition">{{ t('settings.remove') }}</button>
              </div>
            </div>
            <div class="mt-5 p-4 bg-blue-50 rounded-xl border border-blue-100">
              <div class="flex items-start gap-3">
                <svg class="w-4 h-4 text-blue-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
                <p class="text-xs text-blue-700">{{ t('settings.deviceInfo') }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </AppShell>
</template>
