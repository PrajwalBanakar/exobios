<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '@/shared/components/AppShell.vue'
import PatientAvatar from '@/shared/components/PatientAvatar.vue'
import StatusBadge from '@/shared/components/StatusBadge.vue'
import EmptyState from '@/shared/components/EmptyState.vue'
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

const reviewStageTone = {
  CREATED: 'slate', ASSIGNED_TO_DOCTOR: 'blue', UNDER_REVIEW: 'amber', ACTION_TAKEN: 'blue', CLOSED: 'green',
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
        <div v-for="s in stats" :key="s.label" class="bg-white rounded-xl border border-slate-100 p-5 flex items-center gap-4 shadow-sm">
          <div :class="[s.color, 'w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0']">
            <svg v-if="s.icon === 'assigned'" class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><polyline points="17 11 19 13 23 9"/></svg>
            <svg v-else-if="s.icon === 'review'" class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
            <svg v-else-if="s.icon === 'action'" class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M9 12h6m-3-3v6m9-6a9 9 0 1 1-18 0 9 9 0 0 1 18 0z"/></svg>
            <svg v-else-if="s.icon === 'closed'" class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M20 6L9 17l-5-5"/></svg>
            <svg v-else-if="s.icon === 'inbox'" class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M22 12h-6l-2 3h-4l-2-3H2"/><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/></svg>
          </div>
          <div>
            <div class="text-2xl font-bold text-slate-900">{{ s.value }}</div>
            <div class="text-xs text-slate-500 mt-0.5">{{ s.label }}</div>
          </div>
        </div>
      </div>

      <!-- Worklist -->
      <div class="bg-white rounded-xl border border-slate-100 shadow-sm">
        <div class="flex items-center justify-between px-5 py-4 border-b border-slate-100">
          <h2 class="font-semibold text-slate-900">My Worklist</h2>
          <button @click="router.push('/doctor/referrals')"
            class="text-xs font-semibold text-blue-600 hover:underline">
            View Referral Inbox
          </button>
        </div>

        <EmptyState v-if="worklist.length === 0" icon="folder" title="No claimed referrals" message="You haven't claimed any referrals yet."/>

        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-slate-100">
                <th scope="col" class="text-left text-xs font-semibold text-slate-500 px-5 py-3">Patient</th>
                <th scope="col" class="text-left text-xs font-semibold text-slate-500 px-4 py-3">Hospital</th>
                <th scope="col" class="text-left text-xs font-semibold text-slate-500 px-4 py-3">Stage</th>
                <th scope="col" class="text-left text-xs font-semibold text-slate-500 px-4 py-3">Date</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in worklist" :key="r.id"
                class="border-b border-slate-50 hover:bg-slate-50 cursor-pointer transition-colors"
                @click="openReferral(r.id)">
                <td class="px-5 py-3.5">
                  <div class="flex items-center gap-2.5">
                    <PatientAvatar :name="r.patientName" size="sm"/>
                    <span class="font-medium text-slate-800">{{ r.patientName }}</span>
                  </div>
                </td>
                <td class="px-4 py-3.5 text-slate-600">{{ r.hospital }}</td>
                <td class="px-4 py-3.5"><StatusBadge :status="reviewStageLabel[r.reviewStage]" :tone="reviewStageTone[r.reviewStage]"/></td>
                <td class="px-4 py-3.5 text-slate-500 text-xs">{{ r.date }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </AppShell>
</template>
