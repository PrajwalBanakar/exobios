<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import AppShell from '../components/AppShell.vue'
import { usePatientsStore } from '../stores/patients'
import { useI18n } from '../i18n/index'

const router  = useRouter()
const route   = useRoute()
const store   = usePatientsStore()
const { t }   = useI18n()
const patientId = computed(() => Number(route.params.id))
const patient   = computed(() => store.getById(patientId.value) || {
  name: 'Unknown', id: patientId.value, age: '—', gender: '—', location: '—',
})

const conditions = [
  { name: 'Dengue Fever', pct: 72 },
  { name: 'Viral Fever',  pct: 18 },
  { name: 'Malaria',      pct: 6  },
  { name: 'Typhoid',      pct: 4  },
]
const actions = [
  'Give Paracetamol 650mg',
  'Ensure plenty of fluids',
  'ORS if loose motions',
  'Rest and monitor temperature',
  'Monitor for red flags',
]
const redFlags = [
  'High fever (> 101°F)',
  'Severe body pain and weakness',
  'Vomiting or unable to take fluids',
]

const hospitals = [
  { name: 'Rampur Community Health Center', type: 'Government', dist: '2.3 km', phone: '05952-234567', address: 'Rampur Community Health Center, Rampur, Uttar Pradesh' },
  { name: 'Sharma Hospital',                type: 'Private',    dist: '4.6 km', phone: '05952-345678', address: 'Sharma Hospital, Rampur, Uttar Pradesh' },
  { name: 'City Care Hospital',             type: 'Private',    dist: '6.1 km', phone: '05952-456789', address: 'City Care Hospital, Rampur, Uttar Pradesh' },
]

const doctors = [
  { name: 'Dr. Anjali Sharma', spec: 'General Physician', available: true, phone: '9876500001' },
  { name: 'Dr. Vivek Singh',   spec: 'Physician',          available: true, phone: '9876500002' },
  { name: 'Dr. Neha Verma',    spec: 'General Physician', available: true, phone: '9876500003' },
]

function openMap(address) {
  const query = encodeURIComponent(address)
  window.open(`https://www.google.com/maps/search/?api=1&query=${query}`, '_blank')
}

function callNumber(phone) {
  window.location.href = `tel:${phone}`
}

function startVideoCall() {
  window.open('https://meet.google.com/new', '_blank')
}

function printResult() {
  window.print()
}
</script>

<template>
  <AppShell>
    <template #page-title>{{ t('result.title') }}</template>
    <template #page-subtitle>{{ t('result.subtitle') }}</template>

    <div class="p-6 space-y-5">
      <!-- Patient header -->
      <div class="bg-white rounded-xl border border-gray-100 shadow-sm px-5 py-4 flex items-center gap-6 flex-wrap">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 rounded-full bg-blue-100 flex items-center justify-center">
            <svg class="w-5 h-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
            </svg>
          </div>
          <div>
            <div class="text-xs text-gray-500">{{ t('result.patientName') }}</div>
            <div class="text-sm font-semibold text-gray-800">{{ patient.name }}</div>
          </div>
        </div>
        <div><div class="text-xs text-gray-500">{{ t('result.patientId') }}</div><div class="text-sm font-semibold text-gray-800">PT-2025-{{ String(patientId).padStart(6,'0') }}</div></div>
        <div><div class="text-xs text-gray-500">{{ t('result.ageGender') }}</div><div class="text-sm font-semibold text-gray-800">{{ patient.age }} / {{ patient.gender }}</div></div>
        <div><div class="text-xs text-gray-500">{{ t('result.location') }}</div><div class="text-sm font-semibold text-gray-800">{{ patient.location }}</div></div>
        <div><div class="text-xs text-gray-500">{{ t('result.assessmentTime') }}</div><div class="text-sm font-semibold text-gray-800">{{ patient.assessmentTime || patient.date || '—' }}</div></div>
        <div class="ml-auto flex items-center gap-2 flex-wrap">
          <button @click="router.push('/dashboard')"
            class="flex items-center gap-1.5 px-3 py-2 bg-gray-100 hover:bg-gray-200 text-gray-600 text-xs font-medium rounded-lg transition">
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 5l-7 7 7 7"/></svg>
            {{ t('result.dashboard') }}
          </button>
          <button @click="router.push(`/assessment/${patientId}/edit`)"
            class="flex items-center gap-1.5 px-3 py-2 border border-gray-200 text-gray-600 text-xs font-medium rounded-lg hover:bg-gray-50 transition">
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
            {{ t('result.editAssessment') }}
          </button>
          <button @click="printResult"
            class="flex items-center gap-1.5 px-3 py-2 border border-gray-200 text-gray-600 text-xs font-medium rounded-lg hover:bg-gray-50 transition">
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>
            {{ t('result.printSave') }}
          </button>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <!-- Col 1: Risk + Conditions + Next Steps -->
        <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <h3 class="font-semibold text-gray-800 mb-4">{{ t('result.riskLevel') }}</h3>
          <div class="flex items-center gap-3 p-4 bg-red-50 rounded-xl border border-red-100">
            <div class="w-10 h-10 rounded-full bg-red-500 flex items-center justify-center flex-shrink-0">
              <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
              </svg>
            </div>
            <div>
              <div class="text-red-600 font-bold text-lg">{{ t('result.highRisk') }}</div>
              <div class="text-xs text-red-500">{{ t('result.immediateAttention') }}</div>
            </div>
          </div>

          <!-- Probable Conditions -->
          <div class="mt-5">
            <h4 class="font-semibold text-gray-800 mb-1 text-sm">{{ t('result.probableConditions') }}
              <span class="text-xs text-blue-500 font-normal">{{ t('result.aiAnalysis') }}</span>
            </h4>
            <div class="space-y-2 mt-3">
              <div v-for="(c, i) in conditions" :key="c.name" class="flex items-center gap-3">
                <span class="text-xs font-semibold text-gray-500 w-3">{{ i + 1 }}.</span>
                <div class="flex-1">
                  <div class="flex justify-between text-xs mb-1">
                    <span class="font-medium text-gray-700">{{ c.name }}</span>
                    <span class="font-semibold text-gray-600">{{ c.pct }}%</span>
                  </div>
                  <div class="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                    <div class="h-full bg-blue-500 rounded-full" :style="`width:${c.pct}%`"></div>
                  </div>
                </div>
              </div>
            </div>
            <button @click="router.push(`/assessment/${patientId}/analysis`)"
              class="text-xs text-blue-600 hover:underline mt-3 flex items-center gap-1">
              {{ t('result.viewFullAnalysis') }}
              <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
            </button>
          </div>

          <!-- Next Steps -->
          <div class="mt-5">
            <h4 class="font-semibold text-gray-800 mb-3 text-sm">{{ t('result.nextSteps') }}</h4>
            <div class="grid grid-cols-2 gap-2">
              <button class="flex items-center gap-2 p-3 border border-red-100 bg-red-50 rounded-lg hover:bg-red-100 transition text-left">
                <svg class="w-5 h-5 text-red-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
                  <rect x="1" y="3" width="15" height="13" rx="2"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/>
                  <circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/>
                </svg>
                <div>
                  <div class="text-xs font-semibold text-red-600">{{ t('result.callAmbulance') }}</div>
                  <div class="text-[10px] text-gray-500">{{ t('result.requestHelp') }}</div>
                </div>
              </button>
              <button @click="printResult" class="flex items-center gap-2 p-3 border border-gray-100 rounded-lg hover:bg-gray-50 transition text-left">
                <svg class="w-5 h-5 text-blue-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
                  <polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/>
                </svg>
                <div>
                  <div class="text-xs font-semibold text-gray-700">{{ t('result.printSave') }}</div>
                  <div class="text-[10px] text-gray-500">{{ t('result.saveResult') }}</div>
                </div>
              </button>
            </div>
          </div>
        </div>

        <!-- Col 2: Recommended Actions + Red Flags -->
        <div class="space-y-4">
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
            <h3 class="font-semibold text-gray-800 mb-4">{{ t('result.recommendedActions') }}</h3>
            <ul class="space-y-2.5">
              <li v-for="a in actions" :key="a" class="flex items-center gap-2.5">
                <div class="w-5 h-5 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
                  <svg class="w-3 h-3 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path d="M20 6L9 17l-5-5"/></svg>
                </div>
                <span class="text-sm text-gray-700">{{ a }}</span>
              </li>
            </ul>
          </div>

          <!-- Red Flags (no "view more") -->
          <div class="bg-white rounded-xl border border-red-100 shadow-sm p-5 bg-red-50/30">
            <h3 class="font-semibold text-gray-800 mb-4">{{ t('result.redFlags') }}</h3>
            <ul class="space-y-2.5">
              <li v-for="r in redFlags" :key="r" class="flex items-center gap-2.5">
                <span class="w-2 h-2 rounded-full bg-red-500 flex-shrink-0"></span>
                <span class="text-sm text-gray-700">{{ r }}</span>
              </li>
            </ul>
          </div>
        </div>

        <!-- Col 3: Referral + Teleconsultation -->
        <div class="space-y-4">
          <!-- Hospitals -->
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
            <div class="flex items-center justify-between mb-4">
              <h3 class="font-semibold text-gray-800">{{ t('result.referral') }}</h3>
              <button @click="openMap('hospitals near ' + patient.location)"
                class="text-xs text-blue-600 hover:underline flex items-center gap-1">
                {{ t('result.viewOnMap') }}
                <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
              </button>
            </div>
            <div class="space-y-3">
              <div v-for="(h, i) in hospitals" :key="h.name" class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-full bg-gray-800 flex items-center justify-center flex-shrink-0">
                  <span class="text-white text-xs font-bold">{{ i + 1 }}</span>
                </div>
                <div class="flex-1 min-w-0">
                  <div class="text-sm font-medium text-gray-800 truncate">{{ h.name }}</div>
                  <span :class="['text-xs px-2 py-0.5 rounded font-medium', h.type === 'Government' ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-600']">{{ h.type }}</span>
                </div>
                <div class="flex items-center gap-1.5 flex-shrink-0">
                  <span class="text-xs text-gray-500">{{ h.dist }}</span>
                  <button @click="openMap(h.address)"
                    title="View on map"
                    class="w-7 h-7 rounded-full bg-blue-50 flex items-center justify-center hover:bg-blue-100 transition">
                    <svg class="w-3.5 h-3.5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
                  </button>
                  <button @click="callNumber(h.phone)"
                    title="Call hospital"
                    class="w-7 h-7 rounded-full bg-blue-100 flex items-center justify-center hover:bg-blue-200 transition">
                    <svg class="w-3.5 h-3.5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 13a19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 3.6 2.18h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Teleconsultation (no "view all") -->
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
            <h3 class="font-semibold text-gray-800 mb-4">{{ t('result.teleconsultation') }}</h3>
            <div class="space-y-3">
              <div v-for="d in doctors" :key="d.name" class="border border-gray-100 rounded-xl p-3 flex items-center gap-3">
                <div class="w-9 h-9 rounded-full bg-amber-100 flex items-center justify-center flex-shrink-0">
                  <svg class="w-4 h-4 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
                  </svg>
                </div>
                <div class="flex-1 min-w-0">
                  <div class="text-xs font-semibold text-gray-800">{{ d.name }}</div>
                  <div class="text-[10px] text-gray-500">{{ d.spec }}</div>
                  <div class="flex items-center gap-1 mt-0.5">
                    <span class="w-1.5 h-1.5 rounded-full bg-green-500"></span>
                    <span class="text-[10px] text-green-600 font-medium">{{ t('result.available') }}</span>
                  </div>
                </div>
                <div class="flex items-center gap-2">
                  <button @click="callNumber(d.phone)"
                    title="Voice call"
                    class="w-7 h-7 rounded-full bg-green-100 flex items-center justify-center hover:bg-green-200 transition">
                    <svg class="w-3.5 h-3.5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 13a19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 3.6 2.18h3a2 2 0 0 1 2 1.72c.1.96.32 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
                  </button>
                  <button @click="startVideoCall()"
                    title="Video call via Google Meet"
                    class="w-7 h-7 rounded-full bg-blue-100 flex items-center justify-center hover:bg-blue-200 transition">
                    <svg class="w-3.5 h-3.5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2"/></svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Disclaimer + Proceed -->
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2 text-xs text-blue-600 bg-blue-50 border border-blue-100 rounded-lg px-4 py-2.5">
          <svg class="w-4 h-4 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm1 15h-2v-6h2zm0-8h-2V7h2z"/>
          </svg>
          This is an AI-generated analysis. A qualified healthcare professional should review before final diagnosis.
        </div>
        <button @click="router.push(`/assessment/${patientId}/measures`)"
          class="flex items-center gap-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-lg transition ml-4 flex-shrink-0">
          {{ t('result.recordMeasures') }}
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
        </button>
      </div>
    </div>
  </AppShell>
</template>
