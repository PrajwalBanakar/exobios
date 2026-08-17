<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '@/shared/components/AppShell.vue'
import SyncStatusBadge from '@/shared/components/SyncStatusBadge.vue'
import ConfirmModal from '@/shared/components/ConfirmModal.vue'
import EmptyState from '@/shared/components/EmptyState.vue'
import StatCard from '@/shared/components/StatCard.vue'
import RiskBadge from '@/shared/components/RiskBadge.vue'
import PatientAvatar from '@/shared/components/PatientAvatar.vue'
import PatientActionsMenu from '@/shared/components/PatientActionsMenu.vue'
import { usePatientsStore } from '@/features/patients/stores/patients'
import { useTeleconsultStore } from '@/features/teleconsult/stores/teleconsult'
import { useReferralsStore } from '@/features/referrals/stores/referrals'
import { useAuthStore } from '@/features/auth/stores/auth'
import { useI18n } from '@/i18n'
import { useToast } from '@/shared/composables/useToast'
import { formatPatientId, isThisMonth } from '@/shared/utils/format'

const router          = useRouter()
const store           = usePatientsStore()
const teleconsultStore = useTeleconsultStore()
const referralsStore  = useReferralsStore()
const auth            = useAuthStore()
const { t }           = useI18n()
const { showToast }   = useToast()

// ─── Greeting ───────────────────────────────────────────────────────────────
const firstName = computed(() => auth.user?.name?.split(' ')[0] || '')
const greetingKey = computed(() => {
  const hour = new Date().getHours()
  if (hour < 12) return 'dashboard.greetingMorning'
  if (hour < 17) return 'dashboard.greetingAfternoon'
  return 'dashboard.greetingEvening'
})

// ─── KPI metrics (all derived from real store data) ────────────────────────
const newPatientsThisMonth  = computed(() => store.patients.filter(p => isThisMonth(p.date)).length)
const teleconsultsThisMonth = computed(() => teleconsultStore.items.filter(s => isThisMonth(s.date?.split(',')[0])).length)
const highRiskPatients      = computed(() => store.patients.filter(p => p.risk === 'High'))
const activeReferrals       = computed(() => referralsStore.items.filter(r => r.status !== 'Completed'))

const stats = computed(() => [
  {
    labelKey: 'dashboard.totalPatients', value: store.patients.length, tone: 'blue',
    secondary: newPatientsThisMonth.value > 0 ? `${newPatientsThisMonth.value} ${t('dashboard.addedThisMonth')}` : '',
  },
  {
    labelKey: 'dashboard.emergency', value: highRiskPatients.value.length, tone: 'red',
    secondary: highRiskPatients.value.length > 0 ? t('dashboard.requiresAttention') : t('dashboard.noEmergencyCases'),
  },
  {
    labelKey: 'dashboard.referrals', value: activeReferrals.value.length, tone: 'amber',
    secondary: activeReferrals.value.length > 0 ? t('dashboard.awaitingCompletion') : t('dashboard.noActiveReferrals'),
  },
  {
    labelKey: 'dashboard.teleconsult', value: teleconsultStore.items.length, tone: 'green',
    secondary: teleconsultsThisMonth.value > 0 ? `${teleconsultsThisMonth.value} ${t('dashboard.thisMonth')}` : '',
  },
])

// ─── Attention Required ─────────────────────────────────────────────────────
const attentionPatients  = computed(() => highRiskPatients.value.slice(0, 3))
const hasAttentionItems  = computed(() => attentionPatients.value.length > 0 || activeReferrals.value.length > 0)

// ─── Recent Patients (search, pagination, actions) ──────────────────────────
const search          = ref('')
const searchFocused   = ref(false)
const searchInput     = ref(null)
const currentPage     = ref(1)
const perPage         = 5
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

const totalPages    = computed(() => Math.max(1, Math.ceil(filteredPatients.value.length / perPage)))
const pagedPatients = computed(() => {
  const start = (currentPage.value - 1) * perPage
  return filteredPatients.value.slice(start, start + perPage)
})

function goToPage(p) { currentPage.value = Math.max(1, Math.min(p, totalPages.value)) }
function openPatient(id) { router.push(`/patients/${id}`) }
function goEdit(id)      { router.push(`/patients/${id}/edit`) }
function goAssess(id)    { router.push(`/assessment/new?patientId=${id}`) }

function confirmDelete(id) { deleteConfirmId.value = id }
function cancelDelete()    { deleteConfirmId.value = null }
function doDelete() {
  const id = deleteConfirmId.value
  const name = store.patients.find(p => p.id === id)?.name || 'Patient'
  store.remove(id)
  deleteConfirmId.value = null
  if (currentPage.value > totalPages.value) currentPage.value = totalPages.value
  showToast(`${name} removed`, 'success')
}

// '/' focuses search from anywhere on the page, unless already typing somewhere
function handleSlashShortcut(e) {
  if (e.key !== '/') return
  const tag = document.activeElement?.tagName
  if (tag === 'INPUT' || tag === 'TEXTAREA') return
  e.preventDefault()
  searchInput.value?.focus()
}
onMounted(() => window.addEventListener('keydown', handleSlashShortcut))
onUnmounted(() => window.removeEventListener('keydown', handleSlashShortcut))

// ─── Referral & teleconsult panels ──────────────────────────────────────────
const referralStatusClasses = {
  Pending: 'bg-amber-50 text-amber-700', Confirmed: 'bg-blue-50 text-blue-700', Completed: 'bg-green-50 text-green-700',
}
const teleconsultStatusClasses = {
  Scheduled: 'bg-blue-50 text-blue-700', Completed: 'bg-green-50 text-green-700', Cancelled: 'bg-red-50 text-red-700',
}
</script>

<template>
  <AppShell>
    <template #page-title>{{ t('nav.dashboard') }}</template>

    <SyncStatusBadge variant="bar"/>

    <!-- Topbar search slot -->
    <template #topbar-left>
      <div class="flex items-center gap-3">
        <h1 class="truncate text-sm font-semibold text-slate-900 md:hidden">{{ t('nav.dashboard') }}</h1>
        <div class="relative hidden md:block">
          <svg class="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
          <input ref="searchInput" v-model="search" type="text" :placeholder="t('dashboard.searchPlaceholder')"
            class="w-80 rounded-lg border border-slate-200 bg-slate-50 py-2 pl-10 pr-9 text-sm transition focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/40 lg:w-96"
            @input="currentPage = 1" @focus="searchFocused = true" @blur="searchFocused = false"/>
          <kbd v-if="!search && !searchFocused" class="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 rounded border border-slate-300 bg-white px-1.5 py-0.5 text-[10px] font-semibold text-slate-400">/</kbd>
        </div>
      </div>
    </template>

    <div class="space-y-6 p-4 md:p-6">
      <!-- Mobile search (hidden on md+) -->
      <div class="relative md:hidden">
        <svg class="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
        <input v-model="search" type="search" :placeholder="t('dashboard.searchPlaceholder')"
          class="w-full rounded-xl border border-slate-200 bg-slate-50 py-2.5 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/40"
          @input="currentPage = 1"/>
      </div>

      <!-- Header: greeting -->
      <div>
        <h1 class="text-2xl font-bold text-slate-900">{{ t(greetingKey) }}<template v-if="firstName">, {{ firstName }}</template></h1>
        <p class="mt-1 text-sm text-slate-500">{{ t('dashboard.greetingSubtitle') }}</p>
      </div>

      <!-- Quick actions -->
      <div class="flex flex-wrap gap-2.5">
        <button @click="router.push('/patients/new')"
          class="flex h-10 items-center gap-2 rounded-xl bg-blue-600 px-4 text-sm font-semibold text-white shadow-sm shadow-blue-600/20 transition hover:bg-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/40">
          <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M12 5v14M5 12h14"/></svg>
          {{ t('dashboard.addPatient') }}
        </button>
        <button @click="router.push('/assessment/new')"
          class="flex h-10 items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/40">
          <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M9 12h6m-3-3v6m9-6a9 9 0 1 1-18 0 9 9 0 0 1 18 0z"/></svg>
          {{ t('dashboard.startAssessment') }}
        </button>
        <button @click="router.push('/referrals')"
          class="flex h-10 items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/40">
          <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
          {{ t('dashboard.createReferral') }}
        </button>
      </div>

      <!-- Stat cards -->
      <div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard :label="t('dashboard.totalPatients')" :value="stats[0].value" :secondary="stats[0].secondary" tone="blue">
          <template #icon>
            <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
          </template>
        </StatCard>
        <StatCard :label="t('dashboard.emergency')" :value="stats[1].value" :secondary="stats[1].secondary" tone="red">
          <template #icon>
            <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          </template>
        </StatCard>
        <StatCard :label="t('dashboard.referrals')" :value="stats[2].value" :secondary="stats[2].secondary" tone="amber">
          <template #icon>
            <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><polyline points="23 6 17 12 23 18"/></svg>
          </template>
        </StatCard>
        <StatCard :label="t('dashboard.teleconsult')" :value="stats[3].value" :secondary="stats[3].secondary" tone="green">
          <template #icon>
            <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2"/></svg>
          </template>
        </StatCard>
      </div>

      <!-- Attention Required -->
      <div class="rounded-2xl border border-slate-200 bg-white">
        <div class="border-b border-slate-100 px-5 py-4">
          <h2 class="font-semibold text-slate-900">{{ t('dashboard.attentionRequired') }}</h2>
        </div>

        <div v-if="!hasAttentionItems" class="flex flex-col items-center px-5 py-10 text-center">
          <div class="mb-3 flex h-11 w-11 items-center justify-center rounded-full bg-green-50 text-green-600">
            <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg>
          </div>
          <p class="text-sm font-medium text-slate-700">{{ t('dashboard.noUrgentItems') }}</p>
          <p class="mt-1 max-w-xs text-xs text-slate-400">{{ t('dashboard.noUrgentItemsDesc') }}</p>
        </div>

        <div v-else class="divide-y divide-slate-100">
          <div v-for="p in attentionPatients" :key="`hr-${p.id}`" class="flex items-center gap-3 px-5 py-3.5">
            <PatientAvatar :name="p.name" size="sm"/>
            <div class="min-w-0 flex-1">
              <p class="truncate text-sm font-semibold text-slate-800">{{ p.name }} — {{ t('risk.high') }}</p>
              <p class="text-xs text-slate-500">{{ t('dashboard.highRiskReason') }}</p>
            </div>
            <button @click="openPatient(p.id)" class="flex-shrink-0 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-50">
              {{ t('dashboard.viewPatient') }}
            </button>
          </div>

          <div v-if="activeReferrals.length > 0" class="flex items-center gap-3 px-5 py-3.5">
            <div class="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-amber-50 text-amber-600">
              <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
            </div>
            <div class="min-w-0 flex-1">
              <p class="text-sm font-semibold text-slate-800">{{ activeReferrals.length }} {{ t('dashboard.referralsPendingLabel') }}</p>
              <p class="text-xs text-slate-500">{{ t('dashboard.referralsPendingDesc') }}</p>
            </div>
            <button @click="router.push('/referrals')" class="flex-shrink-0 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-50">
              {{ t('dashboard.viewReferrals') }}
            </button>
          </div>
        </div>
      </div>

      <!-- Recent Patients -->
      <div class="rounded-2xl border border-slate-200 bg-white">
        <div class="flex items-center justify-between gap-3 border-b border-slate-100 px-5 py-4">
          <div>
            <h2 class="font-semibold text-slate-900">{{ t('dashboard.recentPatients') }}</h2>
            <p class="mt-0.5 text-xs text-slate-400">{{ t('dashboard.recentPatientsSubtitle') }}</p>
          </div>
          <button @click="router.push('/patients/new')"
            class="flex flex-shrink-0 items-center gap-1.5 rounded-lg bg-blue-600 px-3.5 py-2 text-xs font-semibold text-white transition hover:bg-blue-700">
            <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M12 5v14M5 12h14"/></svg>
            {{ t('dashboard.addPatient') }}
          </button>
        </div>

        <!-- Empty: no patients at all -->
        <EmptyState v-if="store.patients.length === 0" icon="users" :title="t('dashboard.noPatientsYet')" :message="t('dashboard.noPatientsYetDesc')">
          <button @click="router.push('/patients/new')" class="mt-4 rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700">
            {{ t('dashboard.addPatient') }}
          </button>
        </EmptyState>

        <!-- Empty: search yielded nothing -->
        <EmptyState v-else-if="filteredPatients.length === 0" icon="search" :title="t('dashboard.noResults')" :message="`${t('dashboard.noPatients')} “${search}”`"/>

        <template v-else>
          <!-- Desktop table -->
          <div class="hidden overflow-x-auto md:block">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-slate-100">
                  <th scope="col" class="px-5 py-3 text-left text-xs font-semibold text-slate-500">{{ t('table.patientName') }}</th>
                  <th scope="col" class="px-4 py-3 text-left text-xs font-semibold text-slate-500">{{ t('table.ageGender') }}</th>
                  <th scope="col" class="px-4 py-3 text-left text-xs font-semibold text-slate-500">{{ t('table.location') }}</th>
                  <th scope="col" class="px-4 py-3 text-left text-xs font-semibold text-slate-500">{{ t('table.risk') }}</th>
                  <th scope="col" class="px-4 py-3 text-left text-xs font-semibold text-slate-500">{{ t('dashboard.lastAssessment') }}</th>
                  <th scope="col" class="px-4 py-3 text-right text-xs font-semibold text-slate-500">{{ t('table.actions') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="p in pagedPatients" :key="p.id"
                  class="cursor-pointer border-b border-slate-50 transition-colors hover:bg-slate-50"
                  @click="openPatient(p.id)">
                  <td class="px-5 py-4">
                    <div class="flex items-center gap-3">
                      <PatientAvatar :name="p.name" size="sm"/>
                      <div class="min-w-0">
                        <div class="truncate font-medium text-slate-800">{{ p.name }}</div>
                        <div class="text-xs text-slate-400">{{ formatPatientId(p.id) }}</div>
                      </div>
                    </div>
                  </td>
                  <td class="px-4 py-4 text-slate-600">{{ p.age }} / {{ p.gender }}</td>
                  <td class="max-w-[160px] truncate px-4 py-4 text-slate-600">{{ p.address?.village || p.location || '—' }}</td>
                  <td class="px-4 py-4"><RiskBadge :risk="p.risk"/></td>
                  <td class="px-4 py-4 text-xs text-slate-500">{{ p.date }}</td>
                  <td class="px-4 py-4">
                    <div class="flex items-center justify-end gap-1.5" @click.stop>
                      <button @click="openPatient(p.id)" class="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-50">
                        {{ t('dashboard.viewPatient') }}
                      </button>
                      <PatientActionsMenu :patient-name="p.name"
                        @view="openPatient(p.id)" @assess="goAssess(p.id)" @edit="goEdit(p.id)" @delete="confirmDelete(p.id)"/>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Mobile patient cards -->
          <div class="divide-y divide-slate-100 md:hidden">
            <div v-for="p in pagedPatients" :key="p.id" class="p-4" @click="openPatient(p.id)">
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
                    @view="openPatient(p.id)" @assess="goAssess(p.id)" @edit="goEdit(p.id)" @delete="confirmDelete(p.id)"/>
                </div>
              </div>
              <div class="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500">
                <span>{{ p.age }} · {{ p.gender }}</span>
                <span class="truncate">{{ p.address?.village || p.location || '—' }}</span>
              </div>
              <div class="mt-3 flex items-center justify-between">
                <RiskBadge :risk="p.risk"/>
                <div class="text-right">
                  <div class="text-[10px] uppercase tracking-wide text-slate-400">{{ t('dashboard.lastAssessment') }}</div>
                  <div class="text-xs font-medium text-slate-600">{{ p.date }}</div>
                </div>
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
              {{ t('common.showing') }} {{ Math.min((currentPage - 1) * perPage + 1, filteredPatients.length) }}–{{ Math.min(currentPage * perPage, filteredPatients.length) }} {{ t('common.of') }} {{ filteredPatients.length }} {{ t('dashboard.patients') }}
            </span>
            <div class="flex items-center gap-1">
              <button :disabled="currentPage === 1" class="flex h-7 w-7 items-center justify-center rounded text-slate-400 transition hover:bg-slate-100 disabled:opacity-40" @click="goToPage(currentPage - 1)">
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>
              </button>
              <button v-for="pg in Math.min(totalPages, 3)" :key="pg"
                :class="['flex h-7 w-7 items-center justify-center rounded text-xs transition', currentPage === pg ? 'bg-blue-600 font-semibold text-white' : 'text-slate-600 hover:bg-slate-100']"
                @click="goToPage(pg)">{{ pg }}</button>
              <span v-if="totalPages > 3" class="px-1 text-slate-400">…</span>
              <button v-if="totalPages > 3"
                :class="['flex h-7 w-7 items-center justify-center rounded text-xs transition', currentPage === totalPages ? 'bg-blue-600 font-semibold text-white' : 'text-slate-600 hover:bg-slate-100']"
                @click="goToPage(totalPages)">{{ totalPages }}</button>
              <button :disabled="currentPage === totalPages" class="flex h-7 w-7 items-center justify-center rounded text-slate-400 transition hover:bg-slate-100 disabled:opacity-40" @click="goToPage(currentPage + 1)">
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
              </button>
            </div>
          </div>
        </template>
      </div>

      <!-- Referral Status + Recent Teleconsults -->
      <div class="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div class="rounded-2xl border border-slate-200 bg-white">
          <div class="flex items-center justify-between border-b border-slate-100 px-5 py-4">
            <h2 class="font-semibold text-slate-900">{{ t('dashboard.referralStatus') }}</h2>
            <button @click="router.push('/referrals')" class="text-xs font-medium text-blue-600 hover:underline">{{ t('common.viewAll') }}</button>
          </div>
          <div v-if="referralsStore.items.length === 0" class="px-5 py-8 text-center text-sm text-slate-400">{{ t('dashboard.noReferrals') }}</div>
          <template v-else>
            <div class="grid grid-cols-3 divide-x divide-slate-100 border-b border-slate-100">
              <div class="px-4 py-3 text-center">
                <div class="text-lg font-bold text-amber-600">{{ referralsStore.items.filter(r => r.status === 'Pending').length }}</div>
                <div class="text-[11px] text-slate-500">Pending</div>
              </div>
              <div class="px-4 py-3 text-center">
                <div class="text-lg font-bold text-blue-600">{{ referralsStore.items.filter(r => r.status === 'Confirmed').length }}</div>
                <div class="text-[11px] text-slate-500">Confirmed</div>
              </div>
              <div class="px-4 py-3 text-center">
                <div class="text-lg font-bold text-green-600">{{ referralsStore.items.filter(r => r.status === 'Completed').length }}</div>
                <div class="text-[11px] text-slate-500">Completed</div>
              </div>
            </div>
            <div class="divide-y divide-slate-50">
              <div v-for="r in referralsStore.items.slice(0, 3)" :key="r.id" class="flex items-center gap-3 px-5 py-3">
                <PatientAvatar :name="r.patientName" size="sm"/>
                <div class="min-w-0 flex-1">
                  <div class="truncate text-sm font-medium text-slate-800">{{ r.patientName }}</div>
                  <div class="truncate text-xs text-slate-400">{{ r.hospital }}</div>
                </div>
                <span :class="referralStatusClasses[r.status] || 'bg-slate-100 text-slate-600'" class="flex-shrink-0 rounded-full px-2.5 py-1 text-[11px] font-semibold">{{ r.status }}</span>
              </div>
            </div>
          </template>
        </div>

        <div class="rounded-2xl border border-slate-200 bg-white">
          <div class="flex items-center justify-between border-b border-slate-100 px-5 py-4">
            <h2 class="font-semibold text-slate-900">{{ t('dashboard.recentTeleconsults') }}</h2>
            <button @click="router.push('/teleconsult')" class="text-xs font-medium text-blue-600 hover:underline">{{ t('common.viewAll') }}</button>
          </div>
          <div v-if="teleconsultStore.items.length === 0" class="px-5 py-8 text-center text-sm text-slate-400">{{ t('dashboard.noTeleconsults') }}</div>
          <div v-else class="divide-y divide-slate-50">
            <div v-for="s in teleconsultStore.items.slice(0, 4)" :key="s.id" class="flex items-center gap-3 px-5 py-3">
              <div class="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-green-50 text-green-600">
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2"/></svg>
              </div>
              <div class="min-w-0 flex-1">
                <div class="truncate text-sm font-medium text-slate-800">{{ s.patientName }}</div>
                <div class="truncate text-xs text-slate-400">{{ s.doctor }} · {{ s.date }}</div>
              </div>
              <span :class="teleconsultStatusClasses[s.status] || 'bg-slate-100 text-slate-600'" class="flex-shrink-0 rounded-full px-2.5 py-1 text-[11px] font-semibold">{{ s.status }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Delete confirm modal -->
    <ConfirmModal
      :show="!!deleteConfirmId"
      :title="t('dashboard.deletePatient')"
      :message="`Remove ${store.patients.find(p => p.id === deleteConfirmId)?.name || 'this patient'}? This cannot be undone.`"
      :confirm-text="t('common.delete')"
      :danger="true"
      @confirm="doDelete"
      @cancel="cancelDelete"
    />
  </AppShell>
</template>
