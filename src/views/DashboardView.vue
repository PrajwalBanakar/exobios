<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '../components/AppShell.vue'

const router = useRouter()

const stats = [
  { label: 'Total Patients',     value: '128', color: 'bg-blue-600',   icon: 'patients' },
  { label: 'Emergency Cases',    value: '18',  color: 'bg-red-500',    icon: 'emergency' },
  { label: 'Active Referrals',   value: '32',  color: 'bg-orange-400', icon: 'referral' },
  { label: 'Teleconsultations',  value: '24',  color: 'bg-green-500',  icon: 'video' },
]

const systemUpdates = [
  { type: 'error',   text: 'High risk case reported in Rampur' },
  { type: 'warning', text: '3 referrals pending approval' },
  { type: 'success', text: 'Teleconsultation available: Dr. Sharma' },
]

const patients = [
  { initials: 'RK', name: 'Ramesh Kumar',  age: 45, gender: 'Male',   location: 'Rampur', risk: 'Moderate', date: '20 May 2025, 10:30 AM' },
  { initials: 'SD', name: 'Savitri Devi',  age: 32, gender: 'Female', location: 'Bhelwa', risk: 'High',     date: '20 May 2025, 09:45 AM' },
  { initials: 'MS', name: 'Mukesh Singh',  age: 60, gender: 'Male',   location: 'Rampur', risk: 'Low',      date: '20 May 2025, 09:20 AM' },
  { initials: 'PK', name: 'Pooja Kumari',  age: 28, gender: 'Female', location: 'Bhelwa', risk: 'Moderate', date: '20 May 2025, 08:50 AM' },
  { initials: 'HY', name: 'Harish Yadav',  age: 50, gender: 'Male',   location: 'Rampur', risk: 'High',     date: '20 May 2025, 08:15 AM' },
]

const avatarColors = {
  RK: 'bg-slate-200 text-slate-600',
  SD: 'bg-blue-100 text-blue-600',
  MS: 'bg-green-100 text-green-600',
  PK: 'bg-purple-100 text-purple-600',
  HY: 'bg-yellow-100 text-yellow-600',
}

const riskClasses = {
  High:     'bg-red-100 text-red-600',
  Moderate: 'bg-orange-100 text-orange-600',
  Low:      'bg-green-100 text-green-600',
}

const updateDotColor = { error: 'bg-red-500', warning: 'bg-orange-400', success: 'bg-green-500' }

const currentPage = ref(1)
const totalPages  = 26
const search = ref('')
</script>

<template>
  <AppShell>
    <template #page-title>Dashboard</template>

    <!-- Topbar search slot -->
    <template #topbar-left>
      <div class="flex items-center gap-3">
        <div class="relative hidden md:block">
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
            <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
          </svg>
          <input v-model="search" type="text" placeholder="Search patients, ID, symptoms..."
            class="pl-9 pr-4 py-2 text-sm border border-gray-200 rounded-lg bg-gray-50 w-72 focus:outline-none focus:ring-2 focus:ring-blue-500"/>
        </div>
      </div>
    </template>

    <div class="p-6 space-y-6">
      <!-- Stat cards -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div v-for="s in stats" :key="s.label"
          class="bg-white rounded-xl border border-gray-100 p-5 flex items-center gap-4 shadow-sm">
          <div :class="[s.color, 'w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0']">
            <!-- Patients icon -->
            <svg v-if="s.icon === 'patients'" class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
            </svg>
            <!-- Emergency icon -->
            <svg v-else-if="s.icon === 'emergency'" class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
              <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
            <!-- Referral icon -->
            <svg v-else-if="s.icon === 'referral'" class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
              <polyline points="23 6 17 12 23 18"/>
            </svg>
            <!-- Video icon -->
            <svg v-else-if="s.icon === 'video'" class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
              <polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2" ry="2"/>
            </svg>
          </div>
          <div>
            <div class="text-2xl font-bold text-gray-900">{{ s.value }}</div>
            <div class="text-xs text-gray-500 mt-0.5">{{ s.label }}</div>
          </div>
        </div>
      </div>

      <!-- System Updates ticker -->
      <div class="bg-white rounded-xl border border-gray-100 shadow-sm px-5 py-3 flex items-center gap-3 text-sm overflow-hidden">
        <span class="font-semibold text-gray-700 flex-shrink-0">System Updates</span>
        <div class="flex items-center gap-6 overflow-x-auto scrollbar-thin">
          <div v-for="u in systemUpdates" :key="u.text" class="flex items-center gap-2 flex-shrink-0">
            <span :class="[updateDotColor[u.type], 'w-2 h-2 rounded-full flex-shrink-0']"></span>
            <span class="text-gray-600">{{ u.text }}</span>
          </div>
        </div>
        <a href="#" class="ml-auto text-blue-600 font-medium flex-shrink-0 hover:underline text-sm flex items-center gap-1">
          View all
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
        </a>
      </div>

      <!-- Recent Patients table -->
      <div class="bg-white rounded-xl border border-gray-100 shadow-sm">
        <div class="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <h2 class="font-semibold text-gray-900">Recent Patients</h2>
          <div class="flex items-center gap-2">
            <button @click="router.push('/assessment/new')"
              class="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white text-xs font-semibold rounded-lg hover:bg-blue-700 transition">
              <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M12 5v14M5 12h14"/></svg>
              Add Patient
            </button>
            <button class="flex items-center gap-1.5 px-3 py-1.5 border border-gray-200 text-gray-600 text-xs font-medium rounded-lg hover:bg-gray-50 transition">
              <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
              Edit Data
            </button>
            <button class="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-50 transition">
              <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><circle cx="12" cy="5" r="1.5"/><circle cx="12" cy="12" r="1.5"/><circle cx="12" cy="19" r="1.5"/></svg>
            </button>
          </div>
        </div>

        <!-- Table -->
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-gray-100">
                <th class="text-left text-xs font-semibold text-gray-500 px-5 py-3">Patient Name</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">Age / Gender</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">Location</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">Risk Assessment</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">
                  <div class="flex items-center gap-1">Date &amp; Time
                    <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M7 16V4m0 0L3 8m4-4 4 4M17 8v12m0 0 4-4m-4 4-4-4"/></svg>
                  </div>
                </th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="p in patients" :key="p.name"
                class="border-b border-gray-50 hover:bg-gray-50 cursor-pointer transition-colors"
                @click="router.push('/assessment/1/result')">
                <td class="px-5 py-3.5">
                  <div class="flex items-center gap-2.5">
                    <div :class="[avatarColors[p.initials] || 'bg-gray-100 text-gray-600', 'w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold flex-shrink-0']">
                      {{ p.initials }}
                    </div>
                    <span class="font-medium text-gray-800">{{ p.name }}</span>
                  </div>
                </td>
                <td class="px-4 py-3.5 text-gray-600">{{ p.age }} / {{ p.gender }}</td>
                <td class="px-4 py-3.5 text-gray-600">{{ p.location }}</td>
                <td class="px-4 py-3.5">
                  <span :class="[riskClasses[p.risk], 'px-2.5 py-1 rounded-full text-xs font-semibold']">{{ p.risk }}</span>
                </td>
                <td class="px-4 py-3.5 text-gray-500 text-xs">{{ p.date }}</td>
                <td class="px-4 py-3.5">
                  <div class="flex items-center gap-2">
                    <button class="p-1.5 text-blue-500 hover:bg-blue-50 rounded transition" @click.stop>
                      <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                    </button>
                    <button class="p-1.5 text-red-400 hover:bg-red-50 rounded transition" @click.stop>
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
          <span class="text-xs text-gray-500">Showing 1 to 5 of 128 patients</span>
          <div class="flex items-center gap-1">
            <button class="w-7 h-7 flex items-center justify-center text-gray-400 hover:bg-gray-100 rounded transition">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>
            </button>
            <button v-for="p in [1,2,3]" :key="p"
              :class="['w-7 h-7 flex items-center justify-center text-xs rounded transition', currentPage === p ? 'bg-blue-600 text-white font-semibold' : 'text-gray-600 hover:bg-gray-100']"
              @click="currentPage = p">{{ p }}</button>
            <span class="text-gray-400 px-1">…</span>
            <button class="w-7 h-7 flex items-center justify-center text-xs text-gray-600 hover:bg-gray-100 rounded transition">{{ totalPages }}</button>
            <button class="w-7 h-7 flex items-center justify-center text-gray-400 hover:bg-gray-100 rounded transition">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </AppShell>
</template>
