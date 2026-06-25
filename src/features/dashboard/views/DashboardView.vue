<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '@/shared/components/AppShell.vue'
import SyncStatusBadge from '@/shared/components/SyncStatusBadge.vue'
import ConfirmModal from '@/shared/components/ConfirmModal.vue'
import { usePatientsStore } from '@/features/patients/stores/patients'
import { useI18n } from '@/i18n'
import { useToast } from '@/shared/composables/useToast'

const router = useRouter()
const store  = usePatientsStore()
const { t }  = useI18n()
const { showToast } = useToast()

const stats = computed(() => [
  { labelKey: 'dashboard.totalPatients', value: store.patients.length,                                    color: 'bg-blue-600',   icon: 'patients'  },
  { labelKey: 'dashboard.emergency',     value: store.patients.filter(p => p.risk === 'High').length,     color: 'bg-red-500',    icon: 'emergency' },
  { labelKey: 'dashboard.referrals',     value: store.patients.filter(p => p.risk === 'Moderate').length, color: 'bg-orange-400', icon: 'referral'  },
  { labelKey: 'dashboard.teleconsult',   value: 24,                                                        color: 'bg-green-500',  icon: 'video'     },
])

const riskClasses = {
  High:     'bg-red-100 text-red-600',
  Moderate: 'bg-orange-100 text-orange-600',
  Low:      'bg-green-100 text-green-600',
}

const search         = ref('')
const currentPage    = ref(1)
const perPage        = 5
const deleteConfirmId = ref(null)

const filteredPatients = computed(() => {
  const q = search.value.toLowerCase().trim()
  if (!q) return store.patients
  return store.patients.filter(p =>
    p.name.toLowerCase().includes(q) ||
    (p.address?.village || p.location || '').toLowerCase().includes(q) ||
    (p.address?.district || '').toLowerCase().includes(q) ||
    p.risk.toLowerCase().includes(q) ||
    String(p.id).includes(q)
  )
})

const totalPages  = computed(() => Math.max(1, Math.ceil(filteredPatients.value.length / perPage)))
const pagedPatients = computed(() => {
  const start = (currentPage.value - 1) * perPage
  return filteredPatients.value.slice(start, start + perPage)
})

function goToPage(p) { currentPage.value = Math.max(1, Math.min(p, totalPages.value)) }
function openPatient(id)        { router.push(`/patients/${id}`) }
function editPatient(p, e)      { e.stopPropagation(); router.push(`/patients/${p.id}/edit`) }
function newAssessment(id, e)   { e.stopPropagation(); router.push(`/assessment/new?patientId=${id}`) }

function confirmDelete(id, e) { e.stopPropagation(); deleteConfirmId.value = id }
function cancelDelete(e)      { if (e) e.stopPropagation(); deleteConfirmId.value = null }
function doDelete() {
  const id = deleteConfirmId.value
  const name = store.patients.find(p => p.id === id)?.name || 'Patient'
  store.remove(id)
  deleteConfirmId.value = null
  if (currentPage.value > totalPages.value) currentPage.value = totalPages.value
  showToast(`${name} removed`, 'success')
}
</script>

<template>
  <AppShell>
    <template #page-title>{{ t('nav.dashboard') }}</template>

    <SyncStatusBadge variant="bar"/>

    <!-- Topbar search slot -->
    <template #topbar-left>
      <div class="flex items-center gap-3">
        <div class="relative hidden md:block">
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
          <input v-model="search" type="text" :placeholder="t('dashboard.searchPlaceholder')"
            class="pl-9 pr-4 py-2 text-sm border border-gray-200 rounded-lg bg-gray-50 w-72 focus:outline-none focus:ring-2 focus:ring-blue-500"
            @input="currentPage = 1"/>
        </div>
      </div>
    </template>

    <div class="p-4 md:p-6 space-y-6">
      <!-- Mobile search (hidden on md+) -->
      <div class="relative md:hidden">
        <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
        <input v-model="search" type="search" :placeholder="t('dashboard.searchPlaceholder')"
          class="w-full pl-9 pr-4 py-2.5 text-sm border border-gray-200 rounded-xl bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
          @input="currentPage = 1"/>
      </div>

      <!-- Stat cards -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div v-for="s in stats" :key="s.labelKey" class="bg-white rounded-xl border border-gray-100 p-5 flex items-center gap-4 shadow-sm">
          <div :class="[s.color, 'w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0']">
            <svg v-if="s.icon === 'patients'"  class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
            <svg v-else-if="s.icon === 'emergency'" class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            <svg v-else-if="s.icon === 'referral'"  class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><polyline points="23 6 17 12 23 18"/></svg>
            <svg v-else-if="s.icon === 'video'"     class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2"/></svg>
          </div>
          <div>
            <div class="text-2xl font-bold text-gray-900">{{ s.value }}</div>
            <div class="text-xs text-gray-500 mt-0.5">{{ t(s.labelKey) }}</div>
          </div>
        </div>
      </div>

      <!-- Recent Patients table -->
      <div class="bg-white rounded-xl border border-gray-100 shadow-sm">
        <div class="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <h2 class="font-semibold text-gray-900">{{ t('dashboard.recentPatients') }}</h2>
          <button @click="router.push('/patients/new')"
            class="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white text-xs font-semibold rounded-lg hover:bg-blue-700 transition">
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M12 5v14M5 12h14"/></svg>
            {{ t('dashboard.addPatient') }}
          </button>
        </div>

        <!-- Empty state -->
        <div v-if="filteredPatients.length === 0" class="py-16 text-center">
          <svg class="w-12 h-12 text-gray-300 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>
          <p class="text-sm text-gray-500">{{ t('dashboard.noPatients') }} "{{ search }}"</p>
        </div>

        <!-- Table -->
        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-gray-100">
                <th class="text-left text-xs font-semibold text-gray-500 px-5 py-3">{{ t('table.patientName') }}</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">{{ t('table.ageGender') }}</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">{{ t('table.location') }}</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">{{ t('table.risk') }}</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">{{ t('table.dateTime') }}</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">{{ t('table.actions') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="p in pagedPatients" :key="p.id"
                class="border-b border-gray-50 hover:bg-gray-50 cursor-pointer transition-colors"
                @click="openPatient(p.id)">
                <td class="px-5 py-3.5">
                  <div class="flex items-center gap-2.5">
                    <div class="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-xs font-semibold text-blue-600 flex-shrink-0">
                      {{ p.name.split(' ').map(n => n[0]).join('').slice(0,2).toUpperCase() }}
                    </div>
                    <span class="font-medium text-gray-800">{{ p.name }}</span>
                  </div>
                </td>
                <td class="px-4 py-3.5 text-gray-600">{{ p.age }} / {{ p.gender }}</td>
                <td class="px-4 py-3.5 text-gray-600 max-w-[160px] truncate">{{ p.address?.village || p.location || '—' }}</td>
                <td class="px-4 py-3.5">
                  <span :class="[riskClasses[p.risk] || 'bg-gray-100 text-gray-600', 'px-2.5 py-1 rounded-full text-xs font-semibold']">
                    {{ p.risk === 'High' ? t('risk.high') : p.risk === 'Moderate' ? t('risk.moderate') : t('risk.low') }}
                  </span>
                </td>
                <td class="px-4 py-3.5 text-gray-500 text-xs">{{ p.date }}</td>
                <td class="px-4 py-3.5">
                  <div class="flex items-center gap-1">
                    <button title="New Assessment" class="p-1.5 text-green-600 hover:bg-green-50 rounded transition" @click="newAssessment(p.id, $event)">
                      <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M9 12h6m-3-3v6m9-6a9 9 0 1 1-18 0 9 9 0 0 1 18 0z"/></svg>
                    </button>
                    <button title="Edit Patient" class="p-1.5 text-blue-500 hover:bg-blue-50 rounded transition" @click="editPatient(p, $event)">
                      <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                    </button>
                    <button title="Delete" class="p-1.5 text-red-400 hover:bg-red-50 rounded transition" @click="confirmDelete(p.id, $event)">
                      <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4h6v2"/></svg>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div class="flex items-center justify-between px-5 py-4">
          <span class="text-xs text-gray-500">
            {{ t('common.showing') }} {{ Math.min((currentPage - 1) * perPage + 1, filteredPatients.length) }}–{{ Math.min(currentPage * perPage, filteredPatients.length) }} {{ t('common.of') }} {{ filteredPatients.length }} {{ t('dashboard.patients') }}
          </span>
          <div class="flex items-center gap-1">
            <button :disabled="currentPage === 1" class="w-7 h-7 flex items-center justify-center text-gray-400 hover:bg-gray-100 rounded transition disabled:opacity-40" @click="goToPage(currentPage - 1)">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>
            </button>
            <button v-for="pg in Math.min(totalPages, 3)" :key="pg"
              :class="['w-7 h-7 flex items-center justify-center text-xs rounded transition', currentPage === pg ? 'bg-blue-600 text-white font-semibold' : 'text-gray-600 hover:bg-gray-100']"
              @click="goToPage(pg)">{{ pg }}</button>
            <span v-if="totalPages > 3" class="text-gray-400 px-1">…</span>
            <button v-if="totalPages > 3"
              :class="['w-7 h-7 flex items-center justify-center text-xs rounded transition', currentPage === totalPages ? 'bg-blue-600 text-white font-semibold' : 'text-gray-600 hover:bg-gray-100']"
              @click="goToPage(totalPages)">{{ totalPages }}</button>
            <button :disabled="currentPage === totalPages" class="w-7 h-7 flex items-center justify-center text-gray-400 hover:bg-gray-100 rounded transition disabled:opacity-40" @click="goToPage(currentPage + 1)">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Delete confirm modal -->
    <ConfirmModal
      :show="!!deleteConfirmId"
      title="Delete Patient"
      :message="`Remove ${store.patients.find(p => p.id === deleteConfirmId)?.name || 'this patient'}? This cannot be undone.`"
      confirm-text="Delete"
      :danger="true"
      @confirm="doDelete"
      @cancel="cancelDelete(null)"
    />
  </AppShell>
</template>
