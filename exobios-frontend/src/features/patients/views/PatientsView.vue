<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '@/shared/components/AppShell.vue'
import { usePatientsStore } from '@/features/patients/stores/patients'
import { useI18n } from '@/i18n'

const router = useRouter()
const store  = usePatientsStore()
const { t }  = useI18n()

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

const riskClasses = {
  High:     'bg-red-100 text-red-600',
  Moderate: 'bg-orange-100 text-orange-600',
  Low:      'bg-green-100 text-green-600',
}

const RISK_ORDER = { High: 0, Moderate: 1, Low: 2 }

const filtered = computed(() => {
  const q    = search.value.toLowerCase().trim()
  const list = store.patients.filter(p => {
    const mQ = !q || p.name.toLowerCase().includes(q) || p.location.toLowerCase().includes(q) || String(p.id).includes(q)
    const mR = riskFilter.value === 'All' || p.risk === riskFilter.value
    return mQ && mR
  })
  return [...list].sort((a, b) => {
    let av, bv
    if      (sortKey.value === 'name')     { av = a.name.toLowerCase(); bv = b.name.toLowerCase() }
    else if (sortKey.value === 'age')      { av = a.age; bv = b.age }
    else if (sortKey.value === 'risk')     { av = RISK_ORDER[a.risk] ?? 9; bv = RISK_ORDER[b.risk] ?? 9 }
    else if (sortKey.value === 'date')     { av = new Date(a.date); bv = new Date(b.date) }
    else if (sortKey.value === 'location') { av = a.location.toLowerCase(); bv = b.location.toLowerCase() }
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
function doDelete(id) { store.remove(id); deleteConfirmId.value = null }

const counts = computed(() => ({
  total: store.patients.length,
  high:  store.patients.filter(p => p.risk === 'High').length,
  mod:   store.patients.filter(p => p.risk === 'Moderate').length,
  low:   store.patients.filter(p => p.risk === 'Low').length,
}))

// Sortable column header helper — renders the up/down chevron pair
const sortArrows = (key) => ({
  active: sortKey.value === key,
  asc:    sortKey.value === key && sortDir.value === 'asc',
})
</script>

<template>
  <AppShell>
    <template #page-title>{{ t('nav.patients') }}</template>
    <template #page-subtitle>{{ t('patients.subtitle') }}</template>

    <template #topbar-left>
      <div class="flex items-center gap-3">
        <div class="relative hidden md:block">
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
          <input v-model="search" type="text" :placeholder="t('patients.searchPlaceholder')"
            class="pl-9 pr-4 py-2 text-sm border border-gray-200 rounded-lg bg-gray-50 w-64 focus:outline-none focus:ring-2 focus:ring-blue-500"
            @input="currentPage = 1"/>
        </div>
      </div>
    </template>

    <div class="p-6 space-y-5">
      <!-- Summary stat cards -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div v-for="c in [
          { val: counts.total, labelKey: 'dashboard.totalPatients', color: 'bg-blue-600'   },
          { val: counts.high,  labelKey: 'risk.high',               color: 'bg-red-500'    },
          { val: counts.mod,   labelKey: 'risk.moderate',           color: 'bg-orange-400' },
          { val: counts.low,   labelKey: 'risk.low',                color: 'bg-green-500'  },
        ]" :key="c.labelKey"
          class="bg-white rounded-xl border border-gray-100 shadow-sm p-4 flex items-center gap-3">
          <div :class="[c.color, 'w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0']">
            <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>
          </div>
          <div>
            <div class="text-xl font-bold text-gray-900">{{ c.val }}</div>
            <div class="text-xs text-gray-500">{{ t(c.labelKey) }}</div>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-xl border border-gray-100 shadow-sm">
        <!-- Table toolbar -->
        <div class="flex items-center justify-between px-5 py-4 border-b border-gray-100 gap-3 flex-wrap">
          <h2 class="font-semibold text-gray-900">{{ t('nav.patients') }}</h2>
          <div class="flex items-center gap-3">
            <!-- Risk filter tabs -->
            <div class="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
              <button v-for="r in riskOptions" :key="r"
                :class="['px-3 py-1 text-xs font-medium rounded-md transition', riskFilter === r ? 'bg-white shadow-sm text-gray-800' : 'text-gray-500 hover:text-gray-700']"
                @click="riskFilter = r; currentPage = 1">{{ riskOptionLabel(r) }}</button>
            </div>
            <button @click="router.push('/patients/new')"
              class="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white text-xs font-semibold rounded-lg hover:bg-blue-700 transition">
              <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M12 5v14M5 12h14"/></svg>
              {{ t('nav.addPatient') }}
            </button>
          </div>
        </div>

        <!-- Empty state -->
        <div v-if="!filtered.length" class="py-16 text-center">
          <svg class="w-12 h-12 text-gray-300 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>
          <p class="text-sm text-gray-500">{{ t('patients.noResults') }}</p>
        </div>

        <!-- Sortable table -->
        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-gray-100 bg-gray-50/50">
                <th v-for="col in [
                  { key: 'name',     label: t('table.patientName') },
                  { key: 'age',      label: t('table.ageGender') },
                  { key: null,       label: t('common.phone') },
                  { key: 'location', label: t('common.location') },
                  { key: 'risk',     label: t('table.risk') },
                  { key: 'date',     label: t('common.date') },
                  { key: null,       label: t('common.actions') },
                ]" :key="col.label" class="text-left px-4 py-3 first:px-5">
                  <button v-if="col.key" @click="toggleSort(col.key)"
                    class="flex items-center gap-1 text-xs font-semibold text-gray-500 hover:text-gray-800 group">
                    {{ col.label }}
                    <span :class="['flex flex-col leading-none', sortArrows(col.key).active ? 'text-blue-600' : 'opacity-50 group-hover:opacity-100']">
                      <svg class="w-2.5 h-2.5" fill="currentColor" viewBox="0 0 10 6"><path d="M5 0L10 6H0z"/></svg>
                      <svg class="w-2.5 h-2.5" fill="currentColor" viewBox="0 0 10 6"><path d="M5 6L0 0h10z"/></svg>
                    </span>
                  </button>
                  <span v-else class="text-xs font-semibold text-gray-500">{{ col.label }}</span>
                </th>
              </tr>
            </thead>
            <tbody>
              <template v-for="p in paged" :key="p.id">
                <!-- Normal row -->
                <tr v-if="deleteConfirmId !== p.id"
                  class="border-b border-gray-50 hover:bg-gray-50 cursor-pointer transition-colors"
                  @click="router.push(`/patients/${p.id}`)">
                  <td class="px-5 py-3">
                    <div class="flex items-center gap-2.5">
                      <div class="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-xs font-semibold text-blue-600 flex-shrink-0">
                        {{ p.name.split(' ').map(n => n[0]).join('').slice(0,2).toUpperCase() }}
                      </div>
                      <div>
                        <div class="font-medium text-gray-800 text-sm">{{ p.name }}</div>
                        <div class="text-xs text-gray-400">PT-2025-{{ String(p.id).padStart(6,'0') }}</div>
                      </div>
                    </div>
                  </td>
                  <td class="px-4 py-3 text-gray-600 text-sm">{{ p.age }} / {{ p.gender }}</td>
                  <td class="px-4 py-3 text-gray-600 text-sm">{{ p.phone }}</td>
                  <td class="px-4 py-3 text-gray-600 text-sm max-w-[160px] truncate">{{ p.location }}</td>
                  <td class="px-4 py-3">
                    <span :class="[riskClasses[p.risk] || 'bg-gray-100 text-gray-600', 'px-2.5 py-1 rounded-full text-xs font-semibold']">{{ riskOptionLabel(p.risk) }}</span>
                  </td>
                  <td class="px-4 py-3 text-gray-500 text-xs whitespace-nowrap">{{ p.date }}</td>
                  <td class="px-4 py-3">
                    <div class="flex items-center gap-1">
                      <button @click.stop="router.push(`/assessment/new?patientId=${p.id}`)" title="New Assessment" class="p-1.5 text-green-600 hover:bg-green-50 rounded transition">
                        <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M9 12h6m-3-3v6m9-6a9 9 0 1 1-18 0 9 9 0 0 1 18 0z"/></svg>
                      </button>
                      <button @click.stop="router.push(`/patients/${p.id}`)" :title="t('common.viewAll')" class="p-1.5 text-gray-400 hover:bg-gray-100 rounded transition">
                        <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                      </button>
                      <button @click.stop="router.push(`/patients/${p.id}/edit`)" :title="t('common.edit')" class="p-1.5 text-blue-500 hover:bg-blue-50 rounded transition">
                        <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                      </button>
                      <button @click.stop="deleteConfirmId = p.id" :title="t('common.delete')" class="p-1.5 text-red-400 hover:bg-red-50 rounded transition">
                        <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4h6v2"/></svg>
                      </button>
                    </div>
                  </td>
                </tr>
                <!-- Delete confirmation row -->
                <tr v-else class="border-b border-red-100 bg-red-50">
                  <td colspan="7" class="px-5 py-3">
                    <div class="flex items-center justify-between">
                      <span class="text-sm text-red-700 font-medium">{{ t('common.delete') }} <strong>{{ p.name }}</strong>? {{ t('patients.deleteConfirm') }}</span>
                      <div class="flex gap-2">
                        <button @click.stop="deleteConfirmId = null" class="px-3 py-1.5 text-xs border border-gray-300 text-gray-600 rounded-lg hover:bg-white">{{ t('common.cancel') }}</button>
                        <button @click.stop="doDelete(p.id)" class="px-3 py-1.5 text-xs bg-red-500 hover:bg-red-600 text-white font-semibold rounded-lg">{{ t('common.yesDelete') }}</button>
                      </div>
                    </div>
                  </td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div class="flex items-center justify-between px-5 py-4">
          <span class="text-xs text-gray-500">
            {{ t('patients.showing') }} {{ Math.min((currentPage-1)*perPage+1, filtered.length) }}–{{ Math.min(currentPage*perPage, filtered.length) }} {{ t('patients.of') }} {{ filtered.length }} {{ t('patients.patients') }}
          </span>
          <div class="flex items-center gap-1">
            <button :disabled="currentPage === 1" @click="goToPage(currentPage - 1)" aria-label="Previous page" class="w-7 h-7 flex items-center justify-center text-gray-400 hover:bg-gray-100 rounded disabled:opacity-40">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>
            </button>
            <button v-for="pg in Math.min(totalPages, 5)" :key="pg"
              :class="['w-7 h-7 flex items-center justify-center text-xs rounded transition', currentPage === pg ? 'bg-blue-600 text-white font-semibold' : 'text-gray-600 hover:bg-gray-100']"
              :aria-label="`Page ${pg}`" :aria-current="currentPage === pg ? 'page' : undefined"
              @click="goToPage(pg)">{{ pg }}</button>
            <button :disabled="currentPage === totalPages" @click="goToPage(currentPage + 1)" aria-label="Next page" class="w-7 h-7 flex items-center justify-center text-gray-400 hover:bg-gray-100 rounded disabled:opacity-40">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </AppShell>
</template>
