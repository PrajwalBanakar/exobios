<script setup>
import { ref } from 'vue'
import AppShell from '../components/AppShell.vue'
import { useI18n } from '../i18n/index'

const { t } = useI18n()

const stats = [
  { labelKey: 'reports.assessmentsMonth', value: '47', trend: '+12%',  color: 'bg-blue-600' },
  { labelKey: 'reports.highRiskCases',    value: '11', trend: '+3%',   color: 'bg-red-500' },
  { labelKey: 'reports.successReferrals', value: '28', trend: '+8%',   color: 'bg-green-500' },
  { labelKey: 'reports.teleconsultations',value: '19', trend: '+15%',  color: 'bg-purple-500' },
]

const riskDist = [
  { labelKey: 'risk.high',     pct: 28, color: 'bg-red-500',    count: 36 },
  { labelKey: 'risk.moderate', pct: 45, color: 'bg-orange-400', count: 57 },
  { labelKey: 'risk.low',      pct: 27, color: 'bg-green-500',  count: 35 },
]

const monthlyData = [
  { month: 'Jan', cases: 32, referrals: 14 },
  { month: 'Feb', cases: 41, referrals: 19 },
  { month: 'Mar', cases: 38, referrals: 17 },
  { month: 'Apr', cases: 55, referrals: 24 },
  { month: 'May', cases: 47, referrals: 28 },
  { month: 'Jun', cases: 62, referrals: 31 },
]

const maxCases = Math.max(...monthlyData.map(d => d.cases))

const topConditions = [
  { name: 'Dengue Fever',  cases: 18, pct: 38, color: 'bg-blue-500' },
  { name: 'Viral Fever',   cases: 14, pct: 30, color: 'bg-cyan-500' },
  { name: 'Malaria',       cases: 8,  pct: 17, color: 'bg-orange-500' },
  { name: 'Typhoid',       cases: 4,  pct: 9,  color: 'bg-yellow-500' },
  { name: 'Others',        cases: 3,  pct: 6,  color: 'bg-gray-400' },
]

const recentReports = [
  { id: 'RPT-001', title: 'Monthly Health Report – May 2025',      type: 'Monthly',    date: '1 Jun 2025',  status: 'Published' },
  { id: 'RPT-002', title: 'High Risk Patient Summary – Week 20',   type: 'Weekly',     date: '20 May 2025', status: 'Published' },
  { id: 'RPT-003', title: 'Referral Effectiveness Report Q1',      type: 'Quarterly',  date: '1 Apr 2025',  status: 'Published' },
  { id: 'RPT-004', title: 'Dengue Outbreak Analysis – Rampur',     type: 'Incident',   date: '18 May 2025', status: 'Draft' },
]

const statusLabel = (s) => s === 'Published' ? t('reports.published') : t('reports.draft')
</script>

<template>
  <AppShell>
    <template #page-title>{{ t('nav.reports') }}</template>
    <template #page-subtitle>{{ t('reports.subtitle') }}</template>

    <div class="p-4 md:p-6 space-y-5">
      <!-- Stats -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div v-for="s in stats" :key="s.labelKey"
          class="bg-white rounded-xl border border-gray-100 shadow-sm p-4 flex items-center gap-3">
          <div :class="[s.color, 'w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0']">
            <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/></svg>
          </div>
          <div>
            <div class="text-xl font-bold text-gray-900">{{ s.value }}</div>
            <div class="text-xs text-gray-500">{{ t(s.labelKey) }}</div>
            <div class="text-xs text-green-600 font-medium">{{ s.trend }} {{ t('reports.vsLastMonth') }}</div>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <!-- Bar chart (CSS-based) -->
        <div class="lg:col-span-2 bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <h3 class="font-semibold text-gray-800 mb-4">{{ t('reports.monthlyChart') }}</h3>
          <div class="flex items-end gap-3 h-40">
            <div v-for="d in monthlyData" :key="d.month" class="flex-1 flex flex-col items-center gap-1">
              <div class="w-full flex gap-1 items-end justify-center h-32">
                <div :style="`height: ${(d.cases / maxCases) * 100}%`" class="flex-1 bg-blue-500 rounded-t-sm min-h-[4px] transition-all"></div>
                <div :style="`height: ${(d.referrals / maxCases) * 100}%`" class="flex-1 bg-green-400 rounded-t-sm min-h-[4px] transition-all"></div>
              </div>
              <span class="text-[10px] text-gray-400">{{ d.month }}</span>
            </div>
          </div>
          <div class="flex items-center gap-4 mt-3 text-xs text-gray-500">
            <div class="flex items-center gap-1.5"><span class="w-3 h-3 rounded bg-blue-500"></span>{{ t('reports.cases') }}</div>
            <div class="flex items-center gap-1.5"><span class="w-3 h-3 rounded bg-green-400"></span>{{ t('reports.referrals') }}</div>
          </div>
        </div>

        <!-- Risk distribution -->
        <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <h3 class="font-semibold text-gray-800 mb-4">{{ t('reports.riskDistribution') }}</h3>
          <div class="space-y-3">
            <div v-for="r in riskDist" :key="r.labelKey">
              <div class="flex justify-between text-xs mb-1">
                <span class="font-medium text-gray-700">{{ t(r.labelKey) }}</span>
                <span class="text-gray-500">{{ r.count }} {{ t('reports.patientsUnit') }} ({{ r.pct }}%)</span>
              </div>
              <div class="h-2.5 bg-gray-100 rounded-full overflow-hidden">
                <div :class="[r.color, 'h-full rounded-full transition-all']" :style="`width:${r.pct}%`"></div>
              </div>
            </div>
          </div>

          <div class="mt-5">
            <h4 class="font-semibold text-gray-800 text-sm mb-3">{{ t('reports.topConditions') }}</h4>
            <div class="space-y-2">
              <div v-for="c in topConditions" :key="c.name" class="flex items-center gap-2 text-xs">
                <span :class="[c.color, 'w-2 h-2 rounded-full flex-shrink-0']"></span>
                <span class="flex-1 text-gray-700">{{ c.name }}</span>
                <span class="text-gray-500">{{ c.cases }} {{ t('reports.casesUnit') }}</span>
                <span class="text-gray-400">({{ c.pct }}%)</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Reports table -->
      <div class="bg-white rounded-xl border border-gray-100 shadow-sm">
        <div class="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <h2 class="font-semibold text-gray-900">{{ t('reports.generatedReports') }}</h2>
          <button class="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white text-xs font-semibold rounded-lg hover:bg-blue-700 transition">
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M12 5v14M5 12h14"/></svg>
            {{ t('reports.newReport') }}
          </button>
        </div>
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-gray-100 bg-gray-50/50">
              <th class="text-left text-xs font-semibold text-gray-500 px-5 py-3">{{ t('reports.reportId') }}</th>
              <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">{{ t('reports.title') }}</th>
              <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">{{ t('reports.type') }}</th>
              <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">{{ t('reports.date') }}</th>
              <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">{{ t('reports.status') }}</th>
              <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">{{ t('reports.actionsCol') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in recentReports" :key="r.id" class="border-b border-gray-50 hover:bg-gray-50 transition-colors">
              <td class="px-5 py-3"><span class="font-mono text-xs bg-gray-100 px-2 py-1 rounded">{{ r.id }}</span></td>
              <td class="px-4 py-3 font-medium text-gray-800">{{ r.title }}</td>
              <td class="px-4 py-3"><span class="px-2 py-0.5 bg-blue-50 text-blue-600 text-xs rounded font-medium">{{ r.type }}</span></td>
              <td class="px-4 py-3 text-gray-500 text-xs">{{ r.date }}</td>
              <td class="px-4 py-3">
                <span :class="['px-2.5 py-1 rounded-full text-xs font-semibold', r.status === 'Published' ? 'bg-green-100 text-green-600' : 'bg-yellow-100 text-yellow-600']">{{ statusLabel(r.status) }}</span>
              </td>
              <td class="px-4 py-3">
                <div class="flex items-center gap-1.5">
                  <button class="p-1.5 text-blue-500 hover:bg-blue-50 rounded transition" :title="t('reports.view')">
                    <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                  </button>
                  <button class="p-1.5 text-gray-400 hover:bg-gray-100 rounded transition" :title="t('reports.download')" @click="window.print()">
                    <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </AppShell>
</template>
