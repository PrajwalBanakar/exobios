<script setup>
import { useRouter } from 'vue-router'
import AppShell from '../components/AppShell.vue'

const router = useRouter()

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
  { name: 'Rampur Community Health Center', type: 'Government', dist: '2.3 km' },
  { name: 'Sharma Hospital',                type: 'Private',    dist: '4.6 km' },
  { name: 'City Care Hospital',             type: 'Private',    dist: '6.1 km' },
]

const doctors = [
  { name: 'Dr. Anjali Sharma', spec: 'General Physician', available: true },
  { name: 'Dr. Vivek Singh',   spec: 'Physician',          available: true },
  { name: 'Dr. Neha Verma',    spec: 'General Physician', available: true },
]
</script>

<template>
  <AppShell>
    <template #page-title>AI Result / Recommendation</template>
    <template #page-subtitle>AI-generated clinical summary and actionable recommendations.</template>

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
            <div class="text-xs text-gray-500">Patient Name</div>
            <div class="text-sm font-semibold text-gray-800">Ramesh Kumar</div>
          </div>
        </div>
        <div>
          <div class="text-xs text-gray-500">Patient ID</div>
          <div class="text-sm font-semibold text-gray-800">PT-2025-000123</div>
        </div>
        <div>
          <div class="text-xs text-gray-500">Age / Gender</div>
          <div class="text-sm font-semibold text-gray-800">45 / Male</div>
        </div>
        <div>
          <div class="text-xs text-gray-500">Location</div>
          <div class="text-sm font-semibold text-gray-800">Rampur, Uttar Pradesh - 244901</div>
        </div>
        <div>
          <div class="text-xs text-gray-500">Assessment Time</div>
          <div class="text-sm font-semibold text-gray-800">16 May 2025, 10:20 AM</div>
        </div>
        <div class="ml-auto">
          <button @click="router.push('/assessment/new')"
            class="flex items-center gap-1.5 px-3 py-2 border border-gray-200 text-gray-600 text-xs font-medium rounded-lg hover:bg-gray-50 transition">
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
            Edit Assessment
          </button>
        </div>
      </div>

      <div class="grid grid-cols-3 gap-5">
        <!-- Risk Level -->
        <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <h3 class="font-semibold text-gray-800 mb-4">Risk Level</h3>
          <div class="flex items-center gap-3 p-4 bg-red-50 rounded-xl border border-red-100">
            <div class="w-10 h-10 rounded-full bg-red-500 flex items-center justify-center flex-shrink-0">
              <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
              </svg>
            </div>
            <div>
              <div class="text-red-600 font-bold text-lg">HIGH RISK</div>
              <div class="text-xs text-red-500">Immediate attention recommended</div>
            </div>
          </div>

          <!-- Probable Conditions -->
          <div class="mt-5">
            <h4 class="font-semibold text-gray-800 mb-1 text-sm">Probable Conditions
              <span class="text-xs text-blue-500 font-normal">(AI Analysis)</span>
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
                    <div class="h-full bg-blue-500 rounded-full" :style="`width: ${c.pct}%`"></div>
                  </div>
                </div>
              </div>
            </div>
            <a href="#" class="text-xs text-blue-600 hover:underline mt-3 flex items-center gap-1">
              View full analysis
              <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
            </a>
          </div>

          <!-- Next Steps -->
          <div class="mt-5">
            <h4 class="font-semibold text-gray-800 mb-3 text-sm">Next Steps</h4>
            <div class="grid grid-cols-2 gap-2">
              <button class="flex items-center gap-2 p-3 border border-red-100 bg-red-50 rounded-lg hover:bg-red-100 transition text-left">
                <svg class="w-5 h-5 text-red-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
                  <rect x="1" y="3" width="15" height="13" rx="2"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/>
                  <circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/>
                </svg>
                <div>
                  <div class="text-xs font-semibold text-red-600">Call Ambulance</div>
                  <div class="text-[10px] text-gray-500">Request emergency help</div>
                </div>
              </button>
              <button class="flex items-center gap-2 p-3 border border-gray-100 rounded-lg hover:bg-gray-50 transition text-left">
                <svg class="w-5 h-5 text-blue-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
                  <polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/>
                  <rect x="6" y="14" width="12" height="8"/>
                </svg>
                <div>
                  <div class="text-xs font-semibold text-gray-700">Print / Save</div>
                  <div class="text-[10px] text-gray-500">Save or print this result</div>
                </div>
              </button>
            </div>
          </div>
        </div>

        <!-- Recommended Actions + Red Flags -->
        <div class="space-y-4">
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
            <h3 class="font-semibold text-gray-800 mb-4">Recommended Actions</h3>
            <ul class="space-y-2.5">
              <li v-for="a in actions" :key="a" class="flex items-center gap-2.5">
                <div class="w-5 h-5 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
                  <svg class="w-3 h-3 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path d="M20 6L9 17l-5-5"/></svg>
                </div>
                <span class="text-sm text-gray-700">{{ a }}</span>
              </li>
            </ul>
          </div>

          <div class="bg-white rounded-xl border border-red-100 shadow-sm p-5 bg-red-50/30">
            <h3 class="font-semibold text-gray-800 mb-4">Red Flags</h3>
            <ul class="space-y-2.5">
              <li v-for="r in redFlags" :key="r" class="flex items-center gap-2.5">
                <span class="w-2 h-2 rounded-full bg-red-500 flex-shrink-0"></span>
                <span class="text-sm text-gray-700">{{ r }}</span>
              </li>
            </ul>
            <a href="#" class="text-xs text-blue-600 hover:underline mt-3 flex items-center gap-1">
              View more
              <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
            </a>
          </div>
        </div>

        <!-- Referral + Teleconsultation -->
        <div class="space-y-4">
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
            <div class="flex items-center justify-between mb-4">
              <h3 class="font-semibold text-gray-800">Referral (Nearest Hospitals)</h3>
              <a href="#" class="text-xs text-blue-600 hover:underline flex items-center gap-1">
                View on Map
                <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
              </a>
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
                <div class="text-right flex-shrink-0 flex items-center gap-2">
                  <span class="text-xs text-gray-500">{{ h.dist }}</span>
                  <button class="w-7 h-7 rounded-full bg-blue-100 flex items-center justify-center hover:bg-blue-200 transition">
                    <svg class="w-3.5 h-3.5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 13a19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 3.6 2.18h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Teleconsultation -->
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
            <div class="flex items-center justify-between mb-4">
              <h3 class="font-semibold text-gray-800">Teleconsultation (Available Doctors)</h3>
              <a href="#" class="text-xs text-blue-600 hover:underline">View all</a>
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div v-for="d in doctors" :key="d.name" class="border border-gray-100 rounded-xl p-3">
                <div class="w-10 h-10 rounded-full bg-amber-100 flex items-center justify-center mx-auto mb-2">
                  <svg class="w-5 h-5 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
                  </svg>
                </div>
                <div class="text-xs font-semibold text-gray-800 text-center">{{ d.name }}</div>
                <div class="text-[10px] text-gray-500 text-center mb-2">{{ d.spec }}</div>
                <div class="flex items-center justify-center gap-1 mb-2">
                  <span class="w-1.5 h-1.5 rounded-full bg-green-500"></span>
                  <span class="text-[10px] text-green-600 font-medium">Available</span>
                </div>
                <div class="flex justify-center gap-2">
                  <button class="w-6 h-6 rounded-full bg-green-100 flex items-center justify-center hover:bg-green-200 transition">
                    <svg class="w-3 h-3 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 13a19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 3.6 2.18h3a2 2 0 0 1 2 1.72c.1.96.32 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
                  </button>
                  <button class="w-6 h-6 rounded-full bg-green-100 flex items-center justify-center hover:bg-green-200 transition">
                    <svg class="w-3 h-3 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2" ry="2"/></svg>
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
          This is an AI-generated analysis and should be reviewed by a qualified healthcare professional for final diagnosis and treatment.
        </div>
        <button @click="router.push('/assessment/1/measures')"
          class="flex items-center gap-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-lg transition ml-4 flex-shrink-0">
          Record Measures
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
        </button>
      </div>
    </div>
  </AppShell>
</template>
