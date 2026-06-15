<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '@/shared/components/AppShell.vue'

const router     = useRouter()
const typeFilter = ref('All')
const types      = ['All', 'Error', 'Warning', 'Success', 'Info']

const updates = ref([
  { id: 1, type: 'error',   title: 'High Risk Case Alert',          body: 'Ramesh Kumar (PT-2025-000001) from Rampur has been flagged as HIGH RISK. Immediate follow-up required.',            time: '10:32 AM', date: '20 May 2025', read: false },
  { id: 2, type: 'warning', title: '3 Referrals Pending Approval',  body: 'Three patient referrals from Rampur and Bhelwa areas are awaiting supervisor approval. Please review.',             time: '10:15 AM', date: '20 May 2025', read: false },
  { id: 3, type: 'success', title: 'Teleconsultation Available',    body: 'Dr. Anjali Sharma (General Physician) is now available for teleconsultation. Schedule a call for high-risk cases.',  time: '09:58 AM', date: '20 May 2025', read: true  },
  { id: 4, type: 'info',    title: 'System Maintenance Completed',  body: 'Scheduled maintenance completed. All services are operational. Patient data has been backed up successfully.',        time: '09:00 AM', date: '20 May 2025', read: true  },
  { id: 5, type: 'warning', title: 'Dengue Alert — Rampur District',body: 'District health authorities have issued a dengue advisory for Rampur. Increased screening recommended.',            time: '08:30 AM', date: '20 May 2025', read: false },
  { id: 6, type: 'success', title: 'Patient Referral Completed',    body: 'Savitri Devi (PT-2025-000002) has been successfully referred to Rampur Community Health Center.',                    time: '4:15 PM',  date: '19 May 2025', read: true  },
  { id: 7, type: 'info',    title: 'New Feature: Evidence Upload',  body: 'You can now upload photos and documents as evidence when recording patient measures. See the Measures page.',        time: '3:00 PM',  date: '19 May 2025', read: true  },
  { id: 8, type: 'error',   title: 'Ambulance Request — Bhelwa',   body: 'Emergency ambulance was requested for a patient in Bhelwa. Case E-002 is active. Please monitor.',                   time: '2:45 PM',  date: '19 May 2025', read: true  },
  { id: 9, type: 'success', title: 'Monthly Report Generated',      body: 'The monthly health report for May 2025 has been generated and is available in the Reports section.',                 time: '12:00 PM', date: '19 May 2025', read: true  },
  { id: 10,type: 'info',    title: 'New ASHA Worker Registered',    body: 'Meena Kumari has been registered as a new ASHA worker for Shahabad Block. Account is now active.',                  time: '10:00 AM', date: '19 May 2025', read: true  },
])

const filtered = computed(() => typeFilter.value === 'All' ? updates.value : updates.value.filter(u => u.type === typeFilter.value.toLowerCase()))
const unread   = computed(() => updates.value.filter(u => !u.read).length)

function markAllRead()  { updates.value.forEach(u => { u.read = true }) }
function markRead(id)   { const u = updates.value.find(u => u.id === id); if (u) u.read = true }

const typeIcon = {
  error:   { bg: 'bg-red-100' },
  warning: { bg: 'bg-orange-100' },
  success: { bg: 'bg-green-100' },
  info:    { bg: 'bg-blue-100' },
}
</script>

<template>
  <AppShell>
    <template #page-title>System Updates</template>
    <template #page-subtitle>All platform alerts, notifications, and activity</template>

    <div class="p-6 space-y-5">
      <!-- Header -->
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <button @click="router.back()" class="flex items-center gap-1.5 text-sm text-blue-600 hover:underline">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 5l-7 7 7 7"/></svg>
            Back
          </button>
          <span v-if="unread > 0" class="px-2.5 py-1 bg-red-100 text-red-600 text-xs font-semibold rounded-full">{{ unread }} unread</span>
        </div>
        <button v-if="unread > 0" @click="markAllRead" class="text-xs text-blue-600 hover:underline font-medium">Mark all as read</button>
      </div>

      <!-- Filter pills -->
      <div class="flex items-center gap-2">
        <button v-for="tp in types" :key="tp"
          :class="['px-3 py-1.5 rounded-full text-xs font-medium transition', typeFilter===tp ? 'bg-blue-600 text-white' : 'bg-white border border-gray-200 text-gray-600 hover:border-blue-300']"
          @click="typeFilter = tp">{{ tp }}</button>
      </div>

      <!-- Updates list -->
      <div class="space-y-3">
        <div v-for="u in filtered" :key="u.id"
          :class="['bg-white rounded-xl border shadow-sm px-5 py-4 flex items-start gap-4 transition cursor-pointer', u.read ? 'border-gray-100' : 'border-blue-200 bg-blue-50/20']"
          @click="markRead(u.id)">
          <div :class="[typeIcon[u.type].bg, 'w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5']">
            <svg v-if="u.type==='error'"   class="w-5 h-5 text-red-500"    fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/></svg>
            <svg v-else-if="u.type==='warning'" class="w-5 h-5 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            <svg v-else-if="u.type==='success'" class="w-5 h-5 text-green-500"  fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg>
            <svg v-else class="w-5 h-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-start justify-between gap-3">
              <span class="font-semibold text-gray-800 text-sm">{{ u.title }}</span>
              <div class="flex items-center gap-2 flex-shrink-0">
                <span class="text-xs text-gray-400">{{ u.date }}, {{ u.time }}</span>
                <span v-if="!u.read" class="w-2 h-2 rounded-full bg-blue-500"/>
              </div>
            </div>
            <p class="text-sm text-gray-600 mt-1 leading-relaxed">{{ u.body }}</p>
          </div>
        </div>
        <div v-if="!filtered.length" class="bg-white rounded-xl border border-gray-100 py-16 text-center">
          <p class="text-sm text-gray-500">No updates in this category.</p>
        </div>
      </div>
    </div>
  </AppShell>
</template>
