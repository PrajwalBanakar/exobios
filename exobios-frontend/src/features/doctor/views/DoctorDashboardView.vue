<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '@/shared/components/AppShell.vue'
import { useAuthStore } from '@/features/auth/stores/auth'
import { useReferralsStore } from '@/features/referrals/stores/referrals'

const router = useRouter()
const auth   = useAuthStore()
const store  = useReferralsStore()

const myReferrals = computed(() =>
  store.items.filter(r => r.assignedDoctorId === auth.user?.loginId))

const stats = computed(() => [
  { label: 'Assigned to Me',   value: myReferrals.value.filter(r => r.reviewStage === 'ASSIGNED_TO_DOCTOR').length, color: 'bg-blue-600',   icon: 'assigned' },
  { label: 'Under Review',     value: myReferrals.value.filter(r => r.reviewStage === 'UNDER_REVIEW').length,       color: 'bg-orange-400', icon: 'review'   },
  { label: 'Action Taken',     value: myReferrals.value.filter(r => r.reviewStage === 'ACTION_TAKEN').length,       color: 'bg-purple-500', icon: 'action'   },
  { label: 'Closed',           value: myReferrals.value.filter(r => r.reviewStage === 'CLOSED').length,             color: 'bg-green-500',  icon: 'closed'   },
  { label: 'Unassigned Inbox', value: store.items.filter(r => r.reviewStage === 'CREATED').length,                  color: 'bg-red-500',    icon: 'inbox'    },
])

const reviewStageClasses = {
  CREATED:            'bg-gray-100 text-gray-600',
  ASSIGNED_TO_DOCTOR:  'bg-blue-100 text-blue-600',
  UNDER_REVIEW:        'bg-orange-100 text-orange-600',
  ACTION_TAKEN:        'bg-purple-100 text-purple-600',
  CLOSED:              'bg-green-100 text-green-600',
}
const reviewStageLabel = {
  CREATED: 'Created', ASSIGNED_TO_DOCTOR: 'Assigned', UNDER_REVIEW: 'Under Review',
  ACTION_TAKEN: 'Action Taken', CLOSED: 'Closed',
}

const worklist = computed(() => myReferrals.value.slice(0, 5))

function openReferral(id) { router.push(`/doctor/referrals/${id}`) }
</script>

<template>
  <AppShell>
    <template #page-title>Doctor Dashboard</template>
    <template #page-subtitle>Referral review overview for {{ auth.user?.name }}</template>

    <div class="p-4 md:p-6 space-y-6">
      <!-- Stat cards -->
      <div class="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <div v-for="s in stats" :key="s.label" class="bg-white rounded-xl border border-gray-100 p-5 flex items-center gap-4 shadow-sm">
          <div :class="[s.color, 'w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0']">
            <svg v-if="s.icon === 'assigned'" class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><polyline points="17 11 19 13 23 9"/></svg>
            <svg v-else-if="s.icon === 'review'" class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
            <svg v-else-if="s.icon === 'action'" class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M9 12h6m-3-3v6m9-6a9 9 0 1 1-18 0 9 9 0 0 1 18 0z"/></svg>
            <svg v-else-if="s.icon === 'closed'" class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M20 6L9 17l-5-5"/></svg>
            <svg v-else-if="s.icon === 'inbox'" class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M22 12h-6l-2 3h-4l-2-3H2"/><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/></svg>
          </div>
          <div>
            <div class="text-2xl font-bold text-gray-900">{{ s.value }}</div>
            <div class="text-xs text-gray-500 mt-0.5">{{ s.label }}</div>
          </div>
        </div>
      </div>

      <!-- Worklist -->
      <div class="bg-white rounded-xl border border-gray-100 shadow-sm">
        <div class="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <h2 class="font-semibold text-gray-900">My Worklist</h2>
          <button @click="router.push('/doctor/referrals')"
            class="text-xs font-semibold text-blue-600 hover:underline">
            View Referral Inbox
          </button>
        </div>

        <div v-if="worklist.length === 0" class="py-16 text-center">
          <svg class="w-12 h-12 text-gray-300 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.2"><path d="M22 12h-6l-2 3h-4l-2-3H2"/><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/></svg>
          <p class="text-sm text-gray-500">You haven't claimed any referrals yet.</p>
        </div>

        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-gray-100">
                <th class="text-left text-xs font-semibold text-gray-500 px-5 py-3">Patient</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">Hospital</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">Stage</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">Date</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in worklist" :key="r.id"
                class="border-b border-gray-50 hover:bg-gray-50 cursor-pointer transition-colors"
                @click="openReferral(r.id)">
                <td class="px-5 py-3.5 font-medium text-gray-800">{{ r.patientName }}</td>
                <td class="px-4 py-3.5 text-gray-600">{{ r.hospital }}</td>
                <td class="px-4 py-3.5">
                  <span :class="[reviewStageClasses[r.reviewStage], 'px-2.5 py-1 rounded-full text-xs font-semibold']">
                    {{ reviewStageLabel[r.reviewStage] }}
                  </span>
                </td>
                <td class="px-4 py-3.5 text-gray-500 text-xs">{{ r.date }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </AppShell>
</template>
