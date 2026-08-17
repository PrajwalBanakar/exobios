<script setup>
import { computed } from 'vue'
import AppShell from '@/shared/components/AppShell.vue'
import StatCard from '@/shared/components/StatCard.vue'
import { usePatientsStore } from '@/features/patients/stores/patients'
import { useReferralsStore } from '@/features/referrals/stores/referrals'
import { useTeleconsultStore } from '@/features/teleconsult/stores/teleconsult'
import { useI18n } from '@/i18n'

const { t }            = useI18n()
const patientsStore     = usePatientsStore()
const referralsStore    = useReferralsStore()
const teleconsultStore  = useTeleconsultStore()

// Every figure below is derived from the real Pinia stores — no fabricated trend
// percentages or invented time-series. There's no historical event log in this app
// yet (stores hold current state only), so month-over-month charts aren't shown —
// see the note at the bottom of the page.
const highRiskCount = computed(() => patientsStore.patients.filter(p => p.risk === 'High').length)
const activeReferralsCount = computed(() => referralsStore.items.filter(r => r.status !== 'Completed').length)

const stats = computed(() => [
  { labelKey: 'dashboard.totalPatients', value: patientsStore.patients.length,     tone: 'blue'  },
  { labelKey: 'risk.high',               value: highRiskCount.value,               tone: 'red'   },
  { labelKey: 'dashboard.referrals',     value: activeReferralsCount.value,        tone: 'amber' },
  { labelKey: 'dashboard.teleconsult',   value: teleconsultStore.items.length,     tone: 'green' },
])

const totalPatients = computed(() => patientsStore.patients.length)
const riskDist = computed(() => {
  const counts = { High: 0, Moderate: 0, Low: 0 }
  patientsStore.patients.forEach(p => { if (counts[p.risk] !== undefined) counts[p.risk]++ })
  const total = totalPatients.value || 1
  return [
    { labelKey: 'risk.high',     key: 'High',     color: 'bg-red-500',    count: counts.High },
    { labelKey: 'risk.moderate', key: 'Moderate', color: 'bg-amber-400',  count: counts.Moderate },
    { labelKey: 'risk.low',      key: 'Low',      color: 'bg-green-500',  count: counts.Low },
  ].map(r => ({ ...r, pct: Math.round((r.count / total) * 100) }))
})
</script>

<template>
  <AppShell>
    <template #page-title>{{ t('nav.reports') }}</template>
    <template #page-subtitle>{{ t('reports.subtitle') }}</template>

    <div class="p-4 md:p-6 space-y-5">
      <!-- Stats -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard v-for="s in stats" :key="s.labelKey" :label="t(s.labelKey)" :value="s.value" :tone="s.tone">
          <template #icon>
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/></svg>
          </template>
        </StatCard>
      </div>

      <!-- Risk distribution — real, derived from the current patient list -->
      <div class="bg-white rounded-xl border border-slate-100 shadow-sm p-5">
        <h3 class="font-semibold text-slate-800 mb-1">{{ t('reports.riskDistribution') }}</h3>
        <p class="text-xs text-slate-400 mb-4">Across all {{ totalPatients }} registered patients</p>
        <div v-if="totalPatients === 0" class="py-6 text-center text-sm text-slate-400">No patients yet.</div>
        <div v-else class="space-y-3 max-w-xl">
          <div v-for="r in riskDist" :key="r.key">
            <div class="flex justify-between text-xs mb-1">
              <span class="font-medium text-slate-700">{{ t(r.labelKey) }}</span>
              <span class="text-slate-500">{{ r.count }} {{ t('reports.patientsUnit') }} ({{ r.pct }}%)</span>
            </div>
            <div class="h-2.5 bg-slate-100 rounded-full overflow-hidden">
              <div :class="[r.color, 'h-full rounded-full transition-all']" :style="`width:${r.pct}%`"/>
            </div>
          </div>
        </div>
      </div>

      <!-- Generated reports — honest placeholder, no fake report artifacts -->
      <div class="bg-white rounded-xl border border-slate-100 shadow-sm p-8">
        <div class="flex flex-col items-center text-center max-w-md mx-auto">
          <div class="w-12 h-12 rounded-full bg-blue-50 flex items-center justify-center mb-3">
            <svg class="w-6 h-6 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
          </div>
          <h3 class="font-semibold text-slate-800 mb-1">Report generation coming soon</h3>
          <p class="text-sm text-slate-400">Exportable monthly/quarterly PDF reports aren't available yet. The metrics above reflect your live data and update automatically.</p>
        </div>
      </div>
    </div>
  </AppShell>
</template>
