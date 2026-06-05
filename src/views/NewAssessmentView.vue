<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '../components/AppShell.vue'

const router = useRouter()

const form = reactive({
  fullName: 'Ramesh Kumar',
  age: '45',
  gender: 'Male',
  phone: '9876543210',
  location: 'Rampur, Uttar Pradesh - 244901',
  village: 'Rampur',
  abhaId: '',
})

const sections = ref({
  basic: true,
  family: false,
  history: false,
  symptoms: false,
  examination: false,
  legacy: false,
})

const vitals = {
  temperature: { value: '101.2 °F', color: 'text-red-500', label: 'Temperature' },
  bp:          { value: '120/80',  sub: 'mmHg', color: 'text-green-500', label: 'BP' },
  spo2:        { value: '98%',     color: 'text-green-500', label: 'SpO₂' },
  pulse:       { value: '88',      sub: 'BPM',  color: 'text-orange-400', label: 'Pulse' },
  respRate:    { value: '20',      sub: '/min', color: 'text-gray-800', label: 'Resp. Rate' },
  sugar:       { value: '110',     sub: 'mg/dL', color: 'text-red-500', label: 'Sugar' },
}

function toggleSection(key) {
  sections.value[key] = !sections.value[key]
}

function analyze() {
  router.push('/assessment/1/result')
}
</script>

<template>
  <AppShell>
    <template #page-title>New Assessment</template>
    <template #page-subtitle>Start a new patient assessment</template>

    <div class="p-6">
      <button @click="router.back()" class="flex items-center gap-1.5 text-sm text-blue-600 hover:underline mb-5">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 5l-7 7 7 7"/></svg>
        Back to Dashboard
      </button>

      <div class="flex gap-6">
        <!-- Left: Form -->
        <div class="flex-1 min-w-0 space-y-4">
          <!-- Header card -->
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm px-5 py-4 flex items-center gap-6 flex-wrap">
            <div class="flex items-center gap-3">
              <div class="w-9 h-9 rounded-full bg-blue-100 flex items-center justify-center">
                <svg class="w-5 h-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
                </svg>
              </div>
              <div>
                <div class="text-xs text-gray-500">Patient ID</div>
                <div class="text-sm font-semibold text-gray-800">PT-2025-000123</div>
              </div>
            </div>
            <button class="flex items-center gap-2 px-3 py-2 border border-blue-200 text-blue-600 text-xs font-medium rounded-lg hover:bg-blue-50 transition">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
                <rect x="3" y="3" width="5" height="5"/><rect x="16" y="3" width="5" height="5"/>
                <rect x="3" y="16" width="5" height="5"/><path d="M21 16h-3a2 2 0 0 0-2 2v3"/><path d="M21 21v.01"/><path d="M12 7v3a2 2 0 0 1-2 2H7"/>
                <path d="M3 12h.01"/><path d="M12 3h.01"/><path d="M12 16v.01"/>
                <path d="M16 12h1"/><path d="M21 12v.01"/>
              </svg>
              Scan ABHA ID
            </button>
            <div class="ml-auto text-right text-xs text-gray-500">
              <div class="font-medium text-gray-700">Date &amp; Time</div>
              <div>16 May 2025, 10:30 AM</div>
            </div>
            <div class="text-right text-xs">
              <div class="text-gray-500 mb-1">Assessment Type</div>
              <span class="px-2.5 py-1 bg-blue-50 text-blue-600 border border-blue-200 text-xs font-medium rounded-md">New Assessment</span>
            </div>
          </div>

          <!-- Basic Patient Info -->
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
            <button class="w-full flex items-center justify-between px-5 py-4"
              @click="toggleSection('basic')">
              <div class="flex items-center gap-3">
                <svg class="w-5 h-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
                </svg>
                <span class="font-semibold text-gray-800">Basic Patient Information</span>
              </div>
              <svg :class="['w-5 h-5 text-gray-400 transition-transform', sections.basic ? 'rotate-180' : '']"
                fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M19 9l-7 7-7-7"/></svg>
            </button>

            <div v-if="sections.basic" class="px-5 pb-5 space-y-4">
              <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <div class="col-span-2 lg:col-span-1">
                  <label class="block text-xs font-medium text-gray-600 mb-1.5">Full Name <span class="text-red-500">*</span></label>
                  <input v-model="form.fullName" type="text" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500"/>
                </div>
                <div>
                  <label class="block text-xs font-medium text-gray-600 mb-1.5">Age <span class="text-red-500">*</span></label>
                  <input v-model="form.age" type="number" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500"/>
                </div>
                <div>
                  <label class="block text-xs font-medium text-gray-600 mb-1.5">Gender <span class="text-red-500">*</span></label>
                  <select v-model="form.gender" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white">
                    <option>Male</option><option>Female</option><option>Other</option>
                  </select>
                </div>
                <div>
                  <label class="block text-xs font-medium text-gray-600 mb-1.5">Phone Number <span class="text-red-500">*</span></label>
                  <input v-model="form.phone" type="tel" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500"/>
                </div>
              </div>
              <div class="grid grid-cols-2 lg:grid-cols-3 gap-4">
                <div class="col-span-2 lg:col-span-1">
                  <label class="block text-xs font-medium text-gray-600 mb-1.5">Location <span class="text-red-500">*</span></label>
                  <div class="relative">
                    <input v-model="form.location" type="text" class="w-full border border-gray-200 rounded-lg px-3 py-2 pr-9 text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500"/>
                    <svg class="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
                      <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>
                    </svg>
                  </div>
                </div>
                <div>
                  <label class="block text-xs font-medium text-gray-600 mb-1.5">Village / Area</label>
                  <input v-model="form.village" type="text" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500"/>
                </div>
                <div>
                  <label class="block text-xs font-medium text-gray-600 mb-1.5">ABHA ID (Optional)</label>
                  <div class="relative">
                    <input v-model="form.abhaId" type="text" placeholder="Enter ABHA ID"
                      class="w-full border border-gray-200 rounded-lg px-3 py-2 pr-9 text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"/>
                    <button class="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-blue-500">
                      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
                        <rect x="3" y="3" width="5" height="5"/><rect x="16" y="3" width="5" height="5"/>
                        <rect x="3" y="16" width="5" height="5"/><path d="M21 16h-3a2 2 0 0 0-2 2v3"/><path d="M21 21v.01"/>
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Collapsible sections -->
          <div v-for="sec in [
            { key: 'family',      icon: 'family',  label: 'Family Information',   hint: 'Add relevant family medical history' },
            { key: 'history',     icon: 'history', label: 'Past History',          hint: 'Add past illnesses, surgeries, allergies, medications' },
            { key: 'symptoms',    icon: 'symptoms',label: 'Symptoms',              hint: 'Add chief complaint and select symptoms' },
            { key: 'examination', icon: 'exam',    label: 'Examination Findings',  hint: 'Add clinical signs or examination findings' },
            { key: 'legacy',      icon: 'legacy',  label: 'Legacy',                hint: 'Add relevant legacy information' },
          ]" :key="sec.key"
            class="bg-white rounded-xl border border-gray-100 shadow-sm">
            <button class="w-full flex items-center justify-between px-5 py-4"
              @click="toggleSection(sec.key)">
              <div class="flex items-center gap-3">
                <div class="w-5 h-5 text-blue-500">
                  <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
                  </svg>
                </div>
                <span class="font-semibold text-gray-800">{{ sec.label }}</span>
                <span class="text-xs text-gray-400">{{ sec.hint }}</span>
              </div>
              <div :class="['w-7 h-7 rounded-full flex items-center justify-center transition-colors', sections[sec.key] ? 'bg-blue-100 text-blue-500' : 'bg-gray-100 text-gray-400 hover:bg-blue-50']">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                  <path :d="sections[sec.key] ? 'M5 12h14' : 'M12 5v14M5 12h14'"/>
                </svg>
              </div>
            </button>
            <div v-if="sections[sec.key]" class="px-5 pb-5">
              <div class="border border-dashed border-gray-200 rounded-lg p-6 text-center text-sm text-gray-400">
                Click to add {{ sec.label.toLowerCase() }}
              </div>
            </div>
          </div>
        </div>

        <!-- Right: Vitals + AI -->
        <div class="w-72 flex-shrink-0 space-y-4">
          <!-- Vitals card -->
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
            <div class="flex items-center gap-2 mb-4">
              <svg class="w-4 h-4 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
              </svg>
              <h3 class="font-semibold text-gray-800 text-sm">Vitals</h3>
              <span class="text-xs text-gray-400">(From Connected Devices)</span>
            </div>
            <div class="grid grid-cols-3 gap-3">
              <div v-for="(v, k) in vitals" :key="k" class="text-center border-b border-gray-100 pb-3">
                <div class="text-xs text-gray-500 mb-1">{{ v.label }}</div>
                <div :class="[v.color, 'font-bold text-base']">{{ v.value }}</div>
                <div v-if="v.sub" class="text-xs text-gray-400">{{ v.sub }}</div>
              </div>
            </div>
          </div>

          <!-- AI Assistant -->
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
            <div class="flex items-center gap-2 mb-2">
              <svg class="w-4 h-4 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
                <path d="M12 2a10 10 0 0 1 10 10c0 5.52-4.48 10-10 10S2 17.52 2 12 6.48 2 12 2z"/>
                <path d="M12 8v4l3 3"/>
              </svg>
              <h3 class="font-semibold text-gray-800 text-sm">AI Assistant</h3>
            </div>
            <p class="text-xs text-gray-500 mb-4">Get clinical suggestions, possible conditions, and recommendations.</p>
            <button class="w-full flex items-center justify-center gap-2 px-4 py-2.5 border border-blue-200 text-blue-600 text-sm font-medium rounded-lg hover:bg-blue-50 transition">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
              </svg>
              Ask AI Assistant
            </button>
          </div>
        </div>
      </div>

      <!-- Bottom actions -->
      <div class="flex items-center justify-between mt-6 pt-4 border-t border-gray-200">
        <div class="flex items-center gap-3">
          <button @click="router.back()" class="px-5 py-2.5 border border-gray-200 text-gray-600 text-sm font-medium rounded-lg hover:bg-gray-50 transition">Cancel</button>
          <button class="flex items-center gap-2 px-5 py-2.5 border border-blue-200 text-blue-600 text-sm font-medium rounded-lg hover:bg-blue-50 transition">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
              <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/>
            </svg>
            Save Draft
          </button>
        </div>
        <button @click="analyze"
          class="flex items-center gap-2 px-8 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-lg transition">
          Analyze
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
        </button>
      </div>
    </div>
  </AppShell>
</template>
