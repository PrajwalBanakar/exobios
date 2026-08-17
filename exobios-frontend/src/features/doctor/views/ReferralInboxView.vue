<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '@/shared/components/AppShell.vue'
import PatientAvatar from '@/shared/components/PatientAvatar.vue'
import StatusBadge from '@/shared/components/StatusBadge.vue'
import EmptyState from '@/shared/components/EmptyState.vue'
import { useAuthStore } from '@/features/auth/stores/auth'
import { useReferralsStore } from '@/features/referrals/stores/referrals'
import { useToast } from '@/shared/composables/useToast'

const router = useRouter()
const auth   = useAuthStore()
const store  = useReferralsStore()
const { showToast } = useToast()

const filter = ref('all') // all | unassigned | mine | closed
const search = ref('')

const reviewStageTone = {
  CREATED: 'slate', ASSIGNED_TO_DOCTOR: 'blue', UNDER_REVIEW: 'amber', ACTION_TAKEN: 'blue', CLOSED: 'green',
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
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
          <input v-model="search" type="text" placeholder="Search patient, hospital…"
            class="pl-9 pr-4 py-2 text-sm border border-slate-200 rounded-xl bg-slate-50 w-72 focus:outline-none focus:ring-2 focus:ring-blue-500"/>
        </div>
      </div>
    </template>

    <div class="p-4 md:p-6 space-y-4">
      <!-- Filter chips -->
      <div class="flex items-center gap-2">
        <button v-for="chip in filterChips" :key="chip.key"
          :class="['px-3.5 py-1.5 rounded-full text-xs font-semibold transition',
            filter === chip.key ? 'bg-blue-600 text-white' : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50']"
          @click="filter = chip.key">
          {{ chip.label }}
        </button>
      </div>

      <div class="bg-white rounded-xl border border-slate-100 shadow-sm">
        <EmptyState v-if="filteredReferrals.length === 0" icon="folder" title="No referrals" message="No referrals match this filter."/>

        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-slate-100">
                <th scope="col" class="text-left text-xs font-semibold text-slate-500 px-5 py-3">Patient</th>
                <th scope="col" class="text-left text-xs font-semibold text-slate-500 px-4 py-3">Hospital</th>
                <th scope="col" class="text-left text-xs font-semibold text-slate-500 px-4 py-3">Priority</th>
                <th scope="col" class="text-left text-xs font-semibold text-slate-500 px-4 py-3">Stage</th>
                <th scope="col" class="text-left text-xs font-semibold text-slate-500 px-4 py-3">Assigned Doctor</th>
                <th scope="col" class="text-left text-xs font-semibold text-slate-500 px-4 py-3">Action</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in filteredReferrals" :key="r.id"
                class="border-b border-slate-50 hover:bg-slate-50 cursor-pointer transition-colors"
                @click="openReferral(r.id)">
                <td class="px-5 py-3.5">
                  <div class="flex items-center gap-2.5">
                    <PatientAvatar :name="r.patientName" size="sm"/>
                    <span class="font-medium text-slate-800">{{ r.patientName }}</span>
                  </div>
                </td>
                <td class="px-4 py-3.5 text-slate-600">{{ r.hospital }}</td>
                <td class="px-4 py-3.5 text-slate-600">{{ r.type }}</td>
                <td class="px-4 py-3.5"><StatusBadge :status="reviewStageLabel[r.reviewStage]" :tone="reviewStageTone[r.reviewStage]"/></td>
                <td class="px-4 py-3.5 text-slate-500 text-xs">{{ r.assignedDoctorId || '—' }}</td>
                <td class="px-4 py-3.5">
                  <button v-if="!r.assignedDoctorId"
                    class="px-3 py-1.5 bg-blue-600 text-white text-xs font-semibold rounded-xl hover:bg-blue-700 transition"
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
