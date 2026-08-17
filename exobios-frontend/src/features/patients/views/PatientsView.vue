<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '@/shared/components/AppShell.vue'
import StatCard from '@/shared/components/StatCard.vue'
import RiskBadge from '@/shared/components/RiskBadge.vue'
import PatientAvatar from '@/shared/components/PatientAvatar.vue'
import PatientActionsMenu from '@/shared/components/PatientActionsMenu.vue'
import EmptyState from '@/shared/components/EmptyState.vue'
import ConfirmModal from '@/shared/components/ConfirmModal.vue'
import { usePatientsStore } from '@/features/patients/stores/patients'
import { useI18n } from '@/i18n'
import { useToast } from '@/shared/composables/useToast'
import { formatPatientId } from '@/shared/utils/format'

const router = useRouter()
const store  = usePatientsStore()
const { t }  = useI18n()
const { showToast } = useToast()

const search      = ref('')
const riskFilter  = ref('All')
const currentPage = ref(1)
const perPage     = 8
const riskOptions = ['All', 'High', 'Moderate', 'Low']
const sortKey     = ref('date')
const sortDir     = ref('desc')

function toggleSort(key) {
  if (sortKey.value === key) sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  else { sortKey.value = key; sortDir.value = 'asc' }
  currentPage.value = 1
}

const riskOptionLabel = (r) => {
  if (r === 'All')      return t('patients.all')
  if (r === 'High')     return t('risk.high')
  if (r === 'Moderate') return t('risk.moderate')
  if (r === 'Low')      return t('risk.low')
  return r
}

const RISK_ORDER = { High: 0, Moderate: 1, Low: 2 }

const filtered = computed(() => {
  const q    = search.value.toLowerCase().trim()
  const list = store.patients.filter(p => {
    const mQ = !q || p.name.toLowerCase().includes(q) || (p.address?.village || p.location || '').toLowerCase().includes(q) || String(p.id).includes(q)
    const mR = riskFilter.value === 'All' || p.risk === riskFilter.value
    return mQ && mR
  })
  return [...list].sort((a, b) => {
    let av, bv
    if      (sortKey.value === 'name')     { av = a.name.toLowerCase(); bv = b.name.toLowerCase() }
    else if (sortKey.value === 'age')      { av = a.age; bv = b.age }
    else if (sortKey.value === 'risk')     { av = RISK_ORDER[a.risk] ?? 9; bv = RISK_ORDER[b.risk] ?? 9 }
    else if (sortKey.value === 'date')     { av = new Date(a.date); bv = new Date(b.date) }
    else if (sortKey.value === 'location') { av = (a.address?.village || a.location || '').toLowerCase(); bv = (b.address?.village || b.location || '').toLowerCase() }
    else return 0
    if (av < bv) return sortDir.value === 'asc' ? -1 : 1
    if (av > bv) return sortDir.value === 'asc' ?  1 : -1
    return 0
  })
})

const totalPages = computed(() => Math.max(1, Math.ceil(filtered.value.length / perPage)))
const paged      = computed(() => filtered.value.slice((currentPage.value - 1) * perPage, currentPage.value * perPage))
function goToPage(p) { currentPage.value = Math.max(1, Math.min(p, totalPages.value)) }

const deleteConfirmId = ref(null)
function doDelete() {
  const id = deleteConfirmId.value
  const name = store.patients.find(p => p.id === id)?.name || 'Patient'
  store.remove(id)
  deleteConfirmId.value = null
  if (currentPage.value > totalPages.value) currentPage.value = totalPages.value
  showToast(`${name} removed`, 'success')
}

const counts = computed(() => ({
  total: store.patients.length,
  high:  store.patients.filter(p => p.risk === 'High').length,
  mod:   store.patients.filter(p => p.risk === 'Moderate').length,
  low:   store.patients.filter(p => p.risk === 'Low').length,
}))

function openPatient(id) { router.push(`/patients/${id}`) }
function goEdit(id)      { router.push(`/patients/${id}/edit`) }
function goAssess(id)    { router.push(`/assessment/new?patientId=${id}`) }

// Sortable column header helper — renders the up/down chevron pair
const sortArrows = (key) => ({
  active: sortKey.value === key,
})
</script>

<template>
  <AppShell>
    <template #page-title>{{ t('nav.patients') }}</template>
    <template #page-subtitle>{{ t('patients.subtitle') }}</template>

    <template #topbar-left>
      <div class="flex items-center gap-3">
        <h1 class="truncate text-sm font-semibold text-slate-900 md:hidden">{{ t('nav.patients') }}</h1>
        <div class="relative hidden md:block">
          <svg class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
          <input v-model="search" type="text" :placeholder="t('patients.searchPlaceholder')"
            class="w-64 rounded-lg border border-slate-200 bg-slate-50 py-2 pl-9 pr-4 text-sm transition focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/40"
            @input="currentPage = 1"/>
        </div>
      </div>
    </template>

    <div class="space-y-5 p-4 md:p-6">
      <!-- Mobile search -->
      <div class="relative md:hidden">
        <svg class="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
        <input v-model="search" type="search" :placeholder="t('patients.searchPlaceholder')"
          class="w-full rounded-xl border border-slate-200 bg-slate-50 py-2.5 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/40"
          @input="currentPage = 1"/>
      </div>

      <!-- Summary stat cards -->
      <div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard :label="t('dashboard.totalPatients')" :value="counts.total" tone="blue">
          <template #icon>
            <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>
          </template>
        </StatCard>
        <StatCard :label="t('risk.high')" :value="counts.high" tone="red">
          <template #icon>
            <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          </template>
        </StatCard>
        <StatCard :label="t('risk.moderate')" :value="counts.mod" tone="amber">
          <template #icon>
            <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
          </template>
        </StatCard>
        <StatCard :label="t('risk.low')" :value="counts.low" tone="green">
          <template #icon>
            <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M20 6L9 17l-5-5"/></svg>
          </template>
        </StatCard>
      </div>

      <div class="rounded-2xl border border-slate-200 bg-white">
        <!-- Table toolbar -->
        <div class="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 px-5 py-4">
          <h2 class="font-semibold text-slate-900">{{ t('nav.patients') }}</h2>
          <div class="flex items-center gap-3">
            <!-- Risk filter tabs -->
            <div class="flex items-center gap-1 rounded-lg bg-slate-100 p-1">
              <button v-for="r in riskOptions" :key="r"
                :class="['rounded-md px-3 py-1 text-xs font-medium transition', riskFilter === r ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500 hover:text-slate-700']"
                @click="riskFilter = r; currentPage = 1">{{ riskOptionLabel(r) }}</button>
            </div>
            <button @click="router.push('/patients/new')"
              class="flex items-center gap-1.5 rounded-lg bg-blue-600 px-3.5 py-2 text-xs font-semibold text-white transition hover:bg-blue-700">
              <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M12 5v14M5 12h14"/></svg>
              {{ t('nav.addPatient') }}
            </button>
          </div>
        </div>

        <!-- Empty states -->
        <EmptyState v-if="store.patients.length === 0" icon="users" :title="t('dashboard.noPatientsYet')" :message="t('dashboard.noPatientsYetDesc')">
          <button @click="router.push('/patients/new')" class="mt-4 rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700">
            {{ t('nav.addPatient') }}
          </button>
        </EmptyState>
        <EmptyState v-else-if="!filtered.length" icon="search" :title="t('dashboard.noResults')" :message="t('patients.noResults')"/>

        <template v-else>
          <!-- Desktop table -->
          <div class="hidden overflow-x-auto md:block">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-slate-100 bg-slate-50/50">
                  <th v-for="col in [
                    { key: 'name',     label: t('table.patientName') },
                    { key: 'age',      label: t('table.ageGender') },
                    { key: null,       label: t('common.phone') },
                    { key: 'location', label: t('common.location') },
                    { key: 'risk',     label: t('table.risk') },
                    { key: 'date',     label: t('common.date') },
                    { key: null,       label: t('common.actions') },
                  ]" :key="col.label" scope="col" class="px-4 py-3 text-left first:px-5 last:text-right">
                    <button v-if="col.key" @click="toggleSort(col.key)"
                      class="group flex items-center gap-1 text-xs font-semibold text-slate-500 hover:text-slate-800">
                      {{ col.label }}
                      <span :class="['flex flex-col leading-none', sortArrows(col.key).active ? 'text-blue-600' : 'opacity-50 group-hover:opacity-100']">
                        <svg class="h-2.5 w-2.5" fill="currentColor" viewBox="0 0 10 6"><path d="M5 0L10 6H0z"/></svg>
                        <svg class="h-2.5 w-2.5" fill="currentColor" viewBox="0 0 10 6"><path d="M5 6L0 0h10z"/></svg>
                      </span>
                    </button>
                    <span v-else class="text-xs font-semibold text-slate-500">{{ col.label }}</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="p in paged" :key="p.id"
                  class="cursor-pointer border-b border-slate-50 transition-colors hover:bg-slate-50"
                  @click="openPatient(p.id)">
                  <td class="px-5 py-3.5">
                    <div class="flex items-center gap-2.5">
                      <PatientAvatar :name="p.name" size="sm"/>
                      <div>
                        <div class="text-sm font-medium text-slate-800">{{ p.name }}</div>
                        <div class="text-xs text-slate-400">{{ formatPatientId(p.id) }}</div>
                      </div>
                    </div>
                  </td>
                  <td class="px-4 py-3.5 text-sm text-slate-600">{{ p.age }} / {{ p.gender }}</td>
                  <td class="px-4 py-3.5 text-sm text-slate-600">{{ p.phone }}</td>
                  <td class="max-w-[160px] truncate px-4 py-3.5 text-sm text-slate-600">{{ p.address?.village || p.location || '—' }}</td>
                  <td class="px-4 py-3.5"><RiskBadge :risk="p.risk"/></td>
                  <td class="whitespace-nowrap px-4 py-3.5 text-xs text-slate-500">{{ p.date }}</td>
                  <td class="px-4 py-3.5">
                    <div class="flex items-center justify-end gap-1.5" @click.stop>
                      <button @click="openPatient(p.id)" class="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-50">
                        {{ t('dashboard.viewPatient') }}
                      </button>
                      <PatientActionsMenu :patient-name="p.name"
                        @view="openPatient(p.id)" @assess="goAssess(p.id)" @edit="goEdit(p.id)" @delete="deleteConfirmId = p.id"/>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Mobile patient cards -->
          <div class="divide-y divide-slate-100 md:hidden">
            <div v-for="p in paged" :key="p.id" class="p-4" @click="openPatient(p.id)">
              <div class="flex items-start justify-between gap-3">
                <div class="flex min-w-0 items-center gap-3">
                  <PatientAvatar :name="p.name"/>
                  <div class="min-w-0">
                    <div class="truncate font-semibold text-slate-800">{{ p.name }}</div>
                    <div class="text-xs text-slate-400">{{ formatPatientId(p.id) }}</div>
                  </div>
                </div>
                <div @click.stop>
                  <PatientActionsMenu :patient-name="p.name"
                    @view="openPatient(p.id)" @assess="goAssess(p.id)" @edit="goEdit(p.id)" @delete="deleteConfirmId = p.id"/>
                </div>
              </div>
              <div class="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500">
                <span>{{ p.age }} · {{ p.gender }}</span>
                <span class="truncate">{{ p.address?.village || p.location || '—' }}</span>
                <span>{{ p.phone }}</span>
              </div>
              <div class="mt-3 flex items-center justify-between">
                <RiskBadge :risk="p.risk"/>
                <span class="text-xs text-slate-500">{{ p.date }}</span>
              </div>
              <button @click.stop="openPatient(p.id)"
                class="mt-3 w-full rounded-lg border border-slate-200 py-2 text-xs font-semibold text-slate-700 transition hover:bg-slate-50">
                {{ t('dashboard.viewPatient') }}
              </button>
            </div>
          </div>

          <!-- Pagination -->
          <div class="flex items-center justify-between px-5 py-4">
            <span class="text-xs text-slate-500">
              {{ t('patients.showing') }} {{ Math.min((currentPage-1)*perPage+1, filtered.length) }}–{{ Math.min(currentPage*perPage, filtered.length) }} {{ t('patients.of') }} {{ filtered.length }} {{ t('patients.patients') }}
            </span>
            <div class="flex items-center gap-1">
              <button :disabled="currentPage === 1" @click="goToPage(currentPage - 1)" aria-label="Previous page" class="flex h-7 w-7 items-center justify-center rounded text-slate-400 hover:bg-slate-100 disabled:opacity-40">
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>
              </button>
              <button v-for="pg in Math.min(totalPages, 5)" :key="pg"
                :class="['flex h-7 w-7 items-center justify-center rounded text-xs transition', currentPage === pg ? 'bg-blue-600 font-semibold text-white' : 'text-slate-600 hover:bg-slate-100']"
                :aria-label="`Page ${pg}`" :aria-current="currentPage === pg ? 'page' : undefined"
                @click="goToPage(pg)">{{ pg }}</button>
              <button :disabled="currentPage === totalPages" @click="goToPage(currentPage + 1)" aria-label="Next page" class="flex h-7 w-7 items-center justify-center rounded text-slate-400 hover:bg-slate-100 disabled:opacity-40">
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
              </button>
            </div>
          </div>
        </template>
      </div>
    </div>

    <ConfirmModal
      :show="!!deleteConfirmId"
      :title="t('dashboard.deletePatient')"
      :message="`Remove ${store.patients.find(p => p.id === deleteConfirmId)?.name || 'this patient'}? This cannot be undone.`"
      :confirm-text="t('common.delete')"
      :danger="true"
      @confirm="doDelete"
      @cancel="deleteConfirmId = null"
    />
  </AppShell>
</template>
