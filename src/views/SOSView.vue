<script setup>
import { ref } from 'vue'
import AppShell from '../components/AppShell.vue'
import { useI18n } from '../i18n/index'

const { t } = useI18n()

const emergencies = ref([
  { id: 'E-001', patient: 'Ramesh Kumar', age: 45, location: 'Rampur, UP', type: 'Cardiac', time: '10:32 AM', status: 'Active',    priority: 'Critical' },
  { id: 'E-002', patient: 'Savitri Devi', age: 32, location: 'Bhelwa, UP', type: 'High Fever', time: '10:15 AM', status: 'Active', priority: 'High' },
  { id: 'E-003', patient: 'Harish Yadav', age: 50, location: 'Rampur, UP', type: 'Snake Bite', time: '09:58 AM', status: 'Resolved', priority: 'Critical' },
  { id: 'E-004', patient: 'Geeta Sharma', age: 28, location: 'Shahabad, UP', type: 'Pregnancy Complication', time: '09:30 AM', status: 'Active', priority: 'Critical' },
])

const contacts = [
  { name: 'Ambulance (108)',           phone: '108',         icon: 'ambulance', color: 'bg-red-500' },
  { name: 'District Hospital',         phone: '05952-234567', icon: 'hospital',  color: 'bg-blue-600' },
  { name: 'Police (100)',              phone: '100',         icon: 'police',    color: 'bg-gray-700' },
  { name: 'CHC Rampur',               phone: '05952-345678', icon: 'hospital',  color: 'bg-green-600' },
]

const priorityClasses = {
  Critical: 'bg-red-100 text-red-600 border-red-200',
  High:     'bg-orange-100 text-orange-600 border-orange-200',
  Medium:   'bg-yellow-100 text-yellow-600 border-yellow-200',
}

const priorityLabel = (p) => {
  if (p === 'Critical') return t('sos.critical')
  if (p === 'High')     return t('sos.highPriority')
  if (p === 'Medium')   return t('sos.mediumPriority')
  return p
}

const statusLabel = (s) => s === 'Active' ? t('sos.active') : t('sos.resolved')

function callNumber(phone) {
  window.location.href = `tel:${phone}`
}
</script>

<template>
  <AppShell>
    <template #page-title>{{ t('nav.sos') }}</template>
    <template #page-subtitle>{{ t('sos.subtitle') }}</template>

    <div class="p-6 space-y-5">
      <!-- Emergency contacts bar -->
      <div class="bg-red-600 rounded-xl p-4">
        <p class="text-white text-xs font-semibold mb-3 uppercase tracking-wide">{{ t('sos.quickContacts') }}</p>
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <button v-for="c in contacts" :key="c.phone"
            @click="callNumber(c.phone)"
            class="flex items-center gap-3 bg-white/10 hover:bg-white/20 rounded-xl px-4 py-3 transition text-left">
            <div :class="[c.color, 'w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0']">
              <svg class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 13a19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 3.6 2.18h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
              </svg>
            </div>
            <div>
              <div class="text-white text-xs font-semibold">{{ c.name }}</div>
              <div class="text-white/70 text-[10px]">{{ c.phone }}</div>
            </div>
          </button>
        </div>
      </div>

      <!-- Stats -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-4 flex items-center gap-3">
          <div class="w-10 h-10 rounded-full bg-red-500 flex items-center justify-center">
            <span class="text-white text-xs font-bold">SOS</span>
          </div>
          <div><div class="text-2xl font-bold text-gray-900">{{ emergencies.filter(e=>e.status==='Active').length }}</div><div class="text-xs text-gray-500">{{ t('sos.activeEmergencies') }}</div></div>
        </div>
        <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-4 flex items-center gap-3">
          <div class="w-10 h-10 rounded-full bg-orange-400 flex items-center justify-center">
            <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/></svg>
          </div>
          <div><div class="text-2xl font-bold text-gray-900">{{ emergencies.filter(e=>e.priority==='Critical').length }}</div><div class="text-xs text-gray-500">{{ t('sos.criticalCases') }}</div></div>
        </div>
        <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-4 flex items-center gap-3">
          <div class="w-10 h-10 rounded-full bg-green-500 flex items-center justify-center">
            <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg>
          </div>
          <div><div class="text-2xl font-bold text-gray-900">{{ emergencies.filter(e=>e.status==='Resolved').length }}</div><div class="text-xs text-gray-500">{{ t('sos.resolvedToday') }}</div></div>
        </div>
      </div>

      <!-- Emergency cases table -->
      <div class="bg-white rounded-xl border border-gray-100 shadow-sm">
        <div class="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <h2 class="font-semibold text-gray-900">{{ t('sos.activeCases') }}</h2>
          <div class="flex items-center gap-1.5 text-xs text-red-500 font-medium animate-pulse">
            <span class="w-2 h-2 rounded-full bg-red-500"></span>
            {{ t('sos.live') }}
          </div>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-gray-100 bg-gray-50/50">
                <th class="text-left text-xs font-semibold text-gray-500 px-5 py-3">{{ t('sos.caseId') }}</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">{{ t('sos.patient') }}</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">{{ t('sos.type') }}</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">{{ t('common.location') }}</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">{{ t('sos.priority') }}</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">{{ t('sos.status') }}</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">{{ t('sos.time') }}</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">{{ t('sos.actions') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="e in emergencies" :key="e.id"
                :class="['border-b border-gray-50 transition-colors', e.status==='Active' ? 'hover:bg-red-50/30' : 'hover:bg-gray-50']">
                <td class="px-5 py-3.5">
                  <span class="font-mono text-xs font-semibold text-gray-700 bg-gray-100 px-2 py-1 rounded">{{ e.id }}</span>
                </td>
                <td class="px-4 py-3.5">
                  <div class="font-medium text-gray-800">{{ e.patient }}</div>
                  <div class="text-xs text-gray-400">{{ t('common.age') }} {{ e.age }}</div>
                </td>
                <td class="px-4 py-3.5 text-gray-600 text-sm">{{ e.type }}</td>
                <td class="px-4 py-3.5 text-gray-600 text-sm">{{ e.location }}</td>
                <td class="px-4 py-3.5">
                  <span :class="[priorityClasses[e.priority], 'px-2.5 py-1 rounded-full text-xs font-semibold border']">{{ priorityLabel(e.priority) }}</span>
                </td>
                <td class="px-4 py-3.5">
                  <div class="flex items-center gap-1.5">
                    <span :class="[e.status==='Active' ? 'bg-red-500' : 'bg-green-500', 'w-2 h-2 rounded-full']"></span>
                    <span :class="['text-xs font-medium', e.status==='Active' ? 'text-red-600' : 'text-green-600']">{{ statusLabel(e.status) }}</span>
                  </div>
                </td>
                <td class="px-4 py-3.5 text-gray-500 text-xs">{{ e.time }}</td>
                <td class="px-4 py-3.5">
                  <div class="flex items-center gap-1">
                    <button @click="callNumber('108')"
                      class="px-2.5 py-1.5 bg-red-500 hover:bg-red-600 text-white text-xs font-semibold rounded-lg transition">
                      {{ t('sos.callAmbulance') }}
                    </button>
                    <button @click="window.open('https://www.google.com/maps/search/?api=1&query='+encodeURIComponent(e.location), '_blank')"
                      class="p-1.5 text-blue-500 hover:bg-blue-50 rounded transition">
                      <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </AppShell>
</template>
