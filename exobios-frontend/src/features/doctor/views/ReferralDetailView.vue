<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppShell from '@/shared/components/AppShell.vue'
import EmptyState from '@/shared/components/EmptyState.vue'
import StatusBadge from '@/shared/components/StatusBadge.vue'
import { useAuthStore } from '@/features/auth/stores/auth'
import { useReferralsStore } from '@/features/referrals/stores/referrals'
import { useToast } from '@/shared/composables/useToast'

const route  = useRoute()
const router = useRouter()
const auth   = useAuthStore()
const store  = useReferralsStore()
const { showToast } = useToast()

const referralId = computed(() => Number(route.params.id))
const referral    = computed(() => store.getById(referralId.value))

const reviewStageTone = {
  CREATED: 'slate', ASSIGNED_TO_DOCTOR: 'blue', UNDER_REVIEW: 'amber', ACTION_TAKEN: 'blue', CLOSED: 'green',
}
const reviewStageLabel = {
  CREATED: 'Unassigned', ASSIGNED_TO_DOCTOR: 'Assigned to Doctor', UNDER_REVIEW: 'Under Review',
  ACTION_TAKEN: 'Action Taken', CLOSED: 'Closed',
}

const nextStage = computed(() => referral.value ? store.nextReviewStage(referral.value.reviewStage) : null)
const isMine    = computed(() => referral.value?.assignedDoctorId === auth.user?.loginId)

function claim() {
  store.claim(referralId.value, auth.user?.loginId)
  showToast('Referral claimed', 'success')
}

function advanceStage() {
  if (!nextStage.value) return
  store.setReviewStage(referralId.value, nextStage.value)
  showToast(`Moved to ${reviewStageLabel[nextStage.value]}`, 'success')
}

const noteText = ref('')
function addNote() {
  if (!noteText.value.trim()) return
  store.addNote(referralId.value, noteText.value, auth.user?.name)
  noteText.value = ''
  showToast('Note added', 'success')
}

const recommendationDraft = ref(referral.value?.doctorRecommendation || '')
function saveRecommendation() {
  store.setRecommendation(referralId.value, recommendationDraft.value)
  showToast('Recommendation saved', 'success')
}

function viewPatient() {
  if (referral.value?.patientId) router.push(`/doctor/patients/${referral.value.patientId}`)
}
function reviewAssessment() {
  if (referral.value?.patientId != null) {
    router.push(`/doctor/patients/${referral.value.patientId}/assessments/${referral.value.assessmentIndex || 0}`)
  }
}
</script>

<template>
  <AppShell>
    <template #page-title>Referral Detail</template>
    <template #page-subtitle>{{ referral?.patientName }}</template>

    <div v-if="!referral" class="p-6">
      <EmptyState icon="folder" title="Referral not found" message="This referral may have been removed."/>
    </div>

    <div v-else class="p-4 md:p-6 space-y-6 max-w-4xl">
      <!-- Header -->
      <div class="bg-white rounded-xl border border-slate-100 shadow-sm p-5 space-y-4">
        <div class="flex items-start justify-between flex-wrap gap-3">
          <div>
            <h2 class="text-lg font-semibold text-slate-900">{{ referral.patientName }}</h2>
            <p class="text-sm text-slate-500 mt-0.5">Referred to {{ referral.hospital }} · {{ referral.date }}</p>
          </div>
          <div class="flex items-center gap-2">
            <StatusBadge :status="reviewStageLabel[referral.reviewStage]" :tone="reviewStageTone[referral.reviewStage]"/>
          </div>
        </div>

        <p class="text-sm text-slate-600">{{ referral.notes }}</p>

        <div class="flex items-center gap-2 flex-wrap pt-2 border-t border-slate-100">
          <button v-if="!referral.assignedDoctorId"
            class="px-4 py-2 bg-blue-600 text-white text-sm font-semibold rounded-xl hover:bg-blue-700 transition"
            @click="claim">
            Claim Referral
          </button>
          <button v-else-if="nextStage && isMine"
            class="px-4 py-2 bg-blue-600 text-white text-sm font-semibold rounded-xl hover:bg-blue-700 transition"
            @click="advanceStage">
            Advance to {{ reviewStageLabel[nextStage] }}
          </button>
          <span v-else-if="referral.reviewStage === 'CLOSED'" class="text-xs text-slate-400">
            Referral review is closed.
          </span>
          <span v-else-if="!isMine" class="text-xs text-slate-400">
            Assigned to another doctor.
          </span>

          <button class="px-4 py-2 border border-slate-200 text-slate-700 text-sm font-semibold rounded-xl hover:bg-slate-50 transition"
            @click="viewPatient">
            View Patient
          </button>
          <button class="px-4 py-2 border border-slate-200 text-slate-700 text-sm font-semibold rounded-xl hover:bg-slate-50 transition"
            @click="reviewAssessment">
            Review AI Assessment
          </button>
        </div>
      </div>

      <!-- Clinical notes -->
      <div class="bg-white rounded-xl border border-slate-100 shadow-sm">
        <div class="px-5 py-4 border-b border-slate-100">
          <h3 class="font-semibold text-slate-900">Clinical Notes</h3>
        </div>
        <div class="p-5 space-y-3">
          <div class="flex gap-2">
            <textarea v-model="noteText" rows="2" placeholder="Add a clinical note…"
              class="flex-1 text-sm border border-slate-200 rounded-xl p-3 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"/>
            <button class="px-4 py-2 bg-blue-600 text-white text-sm font-semibold rounded-xl hover:bg-blue-700 transition self-start"
              @click="addNote">
              Add
            </button>
          </div>

          <div v-if="referral.clinicalNotes.length === 0" class="text-sm text-slate-400 py-4 text-center">
            No clinical notes yet.
          </div>
          <div v-else class="space-y-3">
            <div v-for="note in referral.clinicalNotes" :key="note.id" class="border-l-2 border-blue-200 pl-3 py-1">
              <p class="text-sm text-slate-700">{{ note.text }}</p>
              <p class="text-xs text-slate-400 mt-1">{{ note.author }} · {{ note.createdAt }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Recommendation -->
      <div class="bg-white rounded-xl border border-slate-100 shadow-sm">
        <div class="px-5 py-4 border-b border-slate-100">
          <h3 class="font-semibold text-slate-900">Action Recommendation</h3>
        </div>
        <div class="p-5 space-y-3">
          <textarea v-model="recommendationDraft" rows="3" placeholder="Enter your recommendation for this referral…"
            class="w-full text-sm border border-slate-200 rounded-xl p-3 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"/>
          <button class="px-4 py-2 bg-blue-600 text-white text-sm font-semibold rounded-xl hover:bg-blue-700 transition"
            @click="saveRecommendation">
            Save Recommendation
          </button>
        </div>
      </div>
    </div>
  </AppShell>
</template>
