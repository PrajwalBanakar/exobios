<script setup>
import { ref, computed } from 'vue'
import AppShell from '@/shared/components/AppShell.vue'
import { useI18n } from '@/i18n'
import { PARAMEDIC_ROLES, DOCTOR_ROLES, ADMIN_ROLES } from '@/features/auth/stores/auth'

const { t } = useI18n()

const search       = ref('')
const showAddModal = ref(false)
const addSuccess   = ref(false)

// 'ASHA Worker' is the legacy alias (see auth store) — hidden from the Add User role
// select so new field-worker records use the current role names.
const ROLE_OPTIONS = [...PARAMEDIC_ROLES.filter(r => r !== 'ASHA Worker'), ...DOCTOR_ROLES, ...ADMIN_ROLES]

const users = ref([
  { id: 1, name: 'Sunita Devi',   role: 'ASHA Worker', area: 'Rampur Block',   phone: '9876543210', status: 'Active',   patients: 32, lastActive: '2 hrs ago'  },
  { id: 2, name: 'Kavita Sharma', role: 'ASHA Worker', area: 'Bhelwa Block',   phone: '9876543220', status: 'Active',   patients: 28, lastActive: '1 day ago'  },
  { id: 3, name: 'Meena Kumari',  role: 'ASHA Worker', area: 'Shahabad Block', phone: '9876543230', status: 'Active',   patients: 21, lastActive: '3 hrs ago'  },
  { id: 4, name: 'Rekha Verma',   role: 'ASHA Worker', area: 'Rampur Block',   phone: '9876543260', status: 'Inactive', patients: 18, lastActive: '5 days ago' },
])

// Color by role category rather than one color per exact role string, so newer roles
// (ANM, CHO, LHV, Health Assistant, MBBS Doctor) aren't all uncolored.
function roleColor(r) {
  if (ADMIN_ROLES.includes(r)) return 'bg-red-100 text-red-600'
  if (DOCTOR_ROLES.includes(r)) return 'bg-purple-100 text-purple-600'
  if (PARAMEDIC_ROLES.includes(r)) return 'bg-blue-100 text-blue-600'
  return 'bg-gray-100 text-gray-600'
}

const filtered = computed(() => {
  const q = search.value.toLowerCase()
  return users.value.filter(u => !q || u.name.toLowerCase().includes(q) || u.role.toLowerCase().includes(q) || u.area.toLowerCase().includes(q))
})

const newUser = ref({ name: '', role: 'ASHA', area: '', phone: '' })

function addUser() {
  if (!newUser.value.name || !newUser.value.phone) return
  users.value.push({ id: users.value.length + 1, ...newUser.value, status: 'Active', patients: 0, lastActive: 'Just now' })
  newUser.value = { name: '', role: 'ASHA', area: '', phone: '' }
  showAddModal.value = false
  addSuccess.value = true
  setTimeout(() => { addSuccess.value = false }, 3000)
}

function toggleStatus(u) { u.status = u.status === 'Active' ? 'Inactive' : 'Active' }
const statusLabel = (s) => s === 'Active' ? t('users.active') : t('users.inactive')

const summaryStats = computed(() => [
  { labelKey: 'users.totalUsers',  val: users.value.length },
  { labelKey: 'users.ashaWorkers', val: users.value.filter(u => PARAMEDIC_ROLES.includes(u.role)).length },
  { labelKey: 'users.activeUsers', val: users.value.filter(u => u.status === 'Active').length },
  { labelKey: 'users.inactiveUsers', val: users.value.filter(u => u.status !== 'Active').length },
])
</script>

<template>
  <AppShell>
    <template #page-title>{{ t('nav.users') }}</template>
    <template #page-subtitle>{{ t('users.subtitle') }}</template>

    <template #topbar-left>
      <div class="relative hidden md:block">
        <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
        <input v-model="search" type="text" :placeholder="t('users.searchPlaceholder')"
          class="pl-9 pr-4 py-2 text-sm border border-gray-200 rounded-lg bg-gray-50 w-64 focus:outline-none focus:ring-2 focus:ring-blue-500"/>
      </div>
    </template>

    <div class="p-4 md:p-6 space-y-5">
      <div v-if="addSuccess" class="flex items-center gap-2 px-4 py-3 bg-green-50 border border-green-200 text-green-700 rounded-xl text-sm">
        <svg class="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M20 6L9 17l-5-5"/></svg>
        {{ t('users.userAdded') }}
      </div>

      <!-- Summary stats -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div v-for="s in summaryStats" :key="s.labelKey" class="bg-white rounded-xl border border-gray-100 shadow-sm p-4 flex items-center gap-3">
          <div class="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center">
            <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
          </div>
          <div>
            <div class="text-xl font-bold text-gray-900">{{ s.val }}</div>
            <div class="text-xs text-gray-500">{{ t(s.labelKey) }}</div>
          </div>
        </div>
      </div>

      <!-- Users table -->
      <div class="bg-white rounded-xl border border-gray-100 shadow-sm">
        <div class="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <h2 class="font-semibold text-gray-900">{{ t('users.allUsers') }}</h2>
          <button @click="showAddModal = true" class="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white text-xs font-semibold rounded-lg hover:bg-blue-700 transition">
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M12 5v14M5 12h14"/></svg>
            {{ t('users.addUser') }}
          </button>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-gray-100 bg-gray-50/50">
                <th class="text-left text-xs font-semibold text-gray-500 px-5 py-3">{{ t('common.name') }}</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">{{ t('users.role') }}</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">{{ t('users.area') }}</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">{{ t('common.phone') }}</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">{{ t('users.patients') }}</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">{{ t('users.lastActive') }}</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">{{ t('users.status') }}</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">{{ t('common.actions') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="u in filtered" :key="u.id" class="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                <td class="px-5 py-3">
                  <div class="flex items-center gap-2.5">
                    <div class="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-xs font-semibold text-blue-600 flex-shrink-0">
                      {{ u.name.split(' ').map(n=>n[0]).join('').slice(0,2).toUpperCase() }}
                    </div>
                    <span class="font-medium text-gray-800">{{ u.name }}</span>
                  </div>
                </td>
                <td class="px-4 py-3">
                  <span :class="[roleColor(u.role), 'px-2.5 py-1 rounded-full text-xs font-semibold']">{{ u.role }}</span>
                </td>
                <td class="px-4 py-3 text-gray-600 text-sm">{{ u.area }}</td>
                <td class="px-4 py-3 text-gray-600 text-sm">{{ u.phone }}</td>
                <td class="px-4 py-3 text-center font-semibold text-gray-700">{{ u.patients }}</td>
                <td class="px-4 py-3 text-gray-500 text-xs">{{ u.lastActive }}</td>
                <td class="px-4 py-3">
                  <button @click="toggleStatus(u)"
                    :class="['px-2.5 py-1 rounded-full text-xs font-semibold transition', u.status==='Active' ? 'bg-green-100 text-green-600 hover:bg-green-200' : 'bg-gray-100 text-gray-500 hover:bg-gray-200']">
                    {{ statusLabel(u.status) }}
                  </button>
                </td>
                <td class="px-4 py-3">
                  <div class="flex items-center gap-1">
                    <button class="p-1.5 text-blue-500 hover:bg-blue-50 rounded transition" :title="t('common.edit')">
                      <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                    </button>
                    <button class="p-1.5 text-red-400 hover:bg-red-50 rounded transition" :title="t('common.delete')"
                      @click="users = users.filter(x=>x.id!==u.id)">
                      <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4h6v2"/></svg>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Add User Modal (no teleport — intentionally uses fixed overlay) -->
    <div v-if="showAddModal" class="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" @click.self="showAddModal = false">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md">
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h3 class="font-semibold text-gray-800">{{ t('users.addNewUser') }}</h3>
          <button @click="showAddModal = false" class="text-gray-400 hover:text-gray-600" aria-label="Close">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18M6 6l12 12"/></svg>
          </button>
        </div>
        <div class="px-6 py-5 space-y-4">
          <div>
            <label class="block text-xs font-medium text-gray-600 mb-1.5">{{ t('users.fullName') }} <span class="text-red-500">*</span></label>
            <input v-model="newUser.name" type="text" :placeholder="t('users.fullNamePlaceholder')" class="w-full border border-gray-200 rounded-xl px-3.5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"/>
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-600 mb-1.5">{{ t('users.role') }}</label>
            <select v-model="newUser.role" class="w-full border border-gray-200 rounded-xl px-3.5 py-3 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500">
              <option v-for="r in ROLE_OPTIONS" :key="r" :value="r">{{ r }}</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-600 mb-1.5">{{ t('users.area') }}</label>
            <input v-model="newUser.area" type="text" :placeholder="t('users.areaPlaceholder')" class="w-full border border-gray-200 rounded-xl px-3.5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"/>
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-600 mb-1.5">{{ t('login.phoneNumber') }} <span class="text-red-500">*</span></label>
            <input v-model="newUser.phone" type="tel" :placeholder="t('users.phonePlaceholder')" class="w-full border border-gray-200 rounded-xl px-3.5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"/>
          </div>
        </div>
        <div class="px-6 py-4 border-t border-gray-100 flex justify-end gap-3">
          <button @click="showAddModal = false" class="px-5 py-2.5 border border-gray-200 text-gray-600 text-sm font-medium rounded-xl hover:bg-gray-50">{{ t('common.cancel') }}</button>
          <button @click="addUser" class="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-xl">{{ t('users.addUser') }}</button>
        </div>
      </div>
    </div>
  </AppShell>
</template>
