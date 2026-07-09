<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '@/shared/components/AppShell.vue'
import { useAuthStore } from '@/features/auth/stores/auth'
import { useReferralsStore } from '@/features/referrals/stores/referrals'
import { useToast } from '@/shared/composables/useToast'

const router = useRouter()
const auth   = useAuthStore()
const store  = useReferralsStore()
const { showToast } = useToast()

const filter = ref('all') // all | unassigned | mine | closed
const search = ref('')

const reviewStageClasses = {
  CREATED:            'bg-gray-100 text-gray-600',
  ASSIGNED_TO_DOCTOR:  'bg-blue-100 text-blue-600',
  UNDER_REVIEW:        'bg-orange-100 text-orange-600',
  ACTION_TAKEN:        'bg-purple-100 text-purple-600',
  CLOSED:              'bg-green-100 text-green-600',
}
const reviewStageLabel = {
  CREATED: 'Unassigned', ASSIGNED_TO_DOCTOR: 'Assigned', UNDER_REVIEW: 'Under Review',
  ACTION_TAKEN: 'Action Taken', CLOSED: 'Closed',
}

const filterChips = [
  { key: 'all',        label: 'All' },
  { key: 'unassigned', label: 'Unassigned' },
  { key: 'mine',       label: 'Mine' },
  { key: 'closed',     label: 'Closed' },
]

const filteredReferrals = computed(() => {
  let list = store.items
  if (filter.value === 'unassigned') list = list.filter(r => r.reviewStage === 'CREATED')
  else if (filter.value === 'mine')  list = list.filter(r => r.assignedDoctorId === auth.user?.loginId)
  else if (filter.value === 'closed') list = list.filter(r => r.reviewStage === 'CLOSED')

  const q = search.value.toLowerCase().trim()
  if (q) {
    list = list.filter(r =>
      r.patientName.toLowerCase().includes(q) ||
      r.hospital.toLowerCase().includes(q))
  }
  return list
})

function claim(id, e) {
  e.stopPropagation()
  store.claim(id, auth.user?.loginId)
  showToast('Referral claimed', 'success')
}

function openReferral(id) { router.push(`/doctor/referrals/${id}`) }
</script>

<template>
  <AppShell>
    <template #page-title>Referral Inbox</template>
    <template #page-subtitle>Claim unassigned referrals and manage your worklist</template>

    <template #topbar-left>
      <div class="flex items-center gap-3">
        <div class="relative hidden md:block">
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
          <input v-model="search" type="text" placeholder="Search patient, hospital…"
            class="pl-9 pr-4 py-2 text-sm border border-gray-200 rounded-lg bg-gray-50 w-72 focus:outline-none focus:ring-2 focus:ring-blue-500"/>
        </div>
      </div>
    </template>

    <div class="p-4 md:p-6 space-y-4">
      <!-- Filter chips -->
      <div class="flex items-center gap-2">
        <button v-for="chip in filterChips" :key="chip.key"
          :class="['px-3.5 py-1.5 rounded-full text-xs font-semibold transition',
            filter === chip.key ? 'bg-blue-600 text-white' : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50']"
          @click="filter = chip.key">
          {{ chip.label }}
        </button>
      </div>

      <div class="bg-white rounded-xl border border-gray-100 shadow-sm">
        <div v-if="filteredReferrals.length === 0" class="py-16 text-center">
          <svg class="w-12 h-12 text-gray-300 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.2"><path d="M22 12h-6l-2 3h-4l-2-3H2"/><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/></svg>
          <p class="text-sm text-gray-500">No referrals match this filter.</p>
        </div>

        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-gray-100">
                <th class="text-left text-xs font-semibold text-gray-500 px-5 py-3">Patient</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">Hospital</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">Priority</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">Stage</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">Assigned Doctor</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">Action</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in filteredReferrals" :key="r.id"
                class="border-b border-gray-50 hover:bg-gray-50 cursor-pointer transition-colors"
                @click="openReferral(r.id)">
                <td class="px-5 py-3.5">
                  <div class="flex items-center gap-2.5">
                    <div class="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-xs font-semibold text-blue-600 flex-shrink-0">
                      {{ r.patientName.split(' ').map(n => n[0]).join('').slice(0,2).toUpperCase() }}
                    </div>
                    <span class="font-medium text-gray-800">{{ r.patientName }}</span>
                  </div>
                </td>
                <td class="px-4 py-3.5 text-gray-600">{{ r.hospital }}</td>
                <td class="px-4 py-3.5 text-gray-600">{{ r.type }}</td>
                <td class="px-4 py-3.5">
                  <span :class="[reviewStageClasses[r.reviewStage], 'px-2.5 py-1 rounded-full text-xs font-semibold']">
                    {{ reviewStageLabel[r.reviewStage] }}
                  </span>
                </td>
                <td class="px-4 py-3.5 text-gray-500 text-xs">{{ r.assignedDoctorId || '—' }}</td>
                <td class="px-4 py-3.5">
                  <button v-if="!r.assignedDoctorId"
                    class="px-3 py-1.5 bg-blue-600 text-white text-xs font-semibold rounded-lg hover:bg-blue-700 transition"
                    @click="claim(r.id, $event)">
                    Claim
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </AppShell>
</template>
