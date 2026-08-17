<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import AppShell from '@/shared/components/AppShell.vue'
import PatientAvatar from '@/shared/components/PatientAvatar.vue'
import RiskBadge from '@/shared/components/RiskBadge.vue'
import EmptyState from '@/shared/components/EmptyState.vue'
import { usePatientsStore } from '@/features/patients/stores/patients'
import { formatPatientId } from '@/shared/utils/format'

const router    = useRouter()
const route     = useRoute()
const store     = usePatientsStore()
const patientId = computed(() => Number(route.params.id))
const patient   = computed(() => store.getById(patientId.value))

const riskClasses = {
  High:     'bg-red-50 text-red-700',
  Moderate: 'bg-amber-50 text-amber-700',
  Low:      'bg-green-50 text-green-700',
}

function reviewAssessment(idx) {
  router.push(`/doctor/patients/${patientId.value}/assessments/${idx}`)
}
</script>

<template>
  <AppShell>
    <template #page-title>Patient Review</template>
    <template #page-subtitle>{{ patient?.name || 'Unknown Patient' }} — read only</template>

    <div v-if="!patient" class="p-8">
      <EmptyState icon="users" title="Patient not found" message="This patient record may have been removed."/>
    </div>

    <div v-else class="p-4 md:p-6 space-y-5">

      <button @click="router.back()" class="flex items-center gap-1.5 text-sm text-blue-600 hover:underline">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 5l-7 7 7 7"/></svg>
        Back
      </button>

      <!-- Patient info card (read-only — no edit/new-assessment affordances) -->
      <div class="bg-white rounded-2xl border border-slate-100 shadow-sm p-5">
        <div class="flex items-start gap-4 flex-wrap">
          <PatientAvatar :name="patient.name" size="lg"/>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-3 flex-wrap">
              <h2 class="text-lg font-bold text-slate-900">{{ patient.name }}</h2>
              <RiskBadge :risk="patient.risk"/>
            </div>
            <div class="text-sm text-slate-500 mt-1">
              {{ formatPatientId(patient.id) }} · {{ patient.age }} yrs · {{ patient.gender }} · {{ patient.phone }}
            </div>
            <div class="text-xs text-slate-400 mt-0.5">
              {{ patient.address?.village }}, {{ patient.address?.district }}, {{ patient.address?.state }}
            </div>
            <div v-if="patient.abhaId" class="text-xs text-blue-600 mt-1 font-mono">ABHA: {{ patient.abhaId }}</div>
          </div>
        </div>

        <div class="mt-5 grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-slate-100">
          <div>
            <div class="text-[10px] text-slate-400 uppercase tracking-wide mb-0.5">Occupation</div>
            <div class="text-sm text-slate-700">{{ patient.occupation || '—' }}</div>
          </div>
          <div>
            <div class="text-[10px] text-slate-400 uppercase tracking-wide mb-0.5">Father / Spouse</div>
            <div class="text-sm text-slate-700">{{ patient.fatherSpouseName || '—' }}</div>
          </div>
          <div>
            <div class="text-[10px] text-slate-400 uppercase tracking-wide mb-0.5">Marital Status</div>
            <div class="text-sm text-slate-700">{{ patient.family?.maritalStatus || '—' }}</div>
          </div>
          <div>
            <div class="text-[10px] text-slate-400 uppercase tracking-wide mb-0.5">Registered</div>
            <div class="text-sm text-slate-700">{{ patient.date || '—' }}</div>
          </div>
        </div>
      </div>

      <!-- Assessment History (read-only — links to Assessment Review, not edit) -->
      <div class="bg-white rounded-xl border border-slate-100 shadow-sm">
        <div class="px-5 py-4 border-b border-slate-100">
          <h3 class="font-semibold text-slate-900">Assessment History</h3>
          <p class="text-xs text-slate-400 mt-0.5">{{ (patient.assessmentHistory || []).length }} assessments on record</p>
        </div>

        <div v-if="!(patient.assessmentHistory || []).length" class="py-12 text-center">
          <svg class="w-10 h-10 text-slate-200 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.2"><path d="M9 12h6m-3-3v6m9-6a9 9 0 1 1-18 0 9 9 0 0 1 18 0z"/></svg>
          <p class="text-sm text-slate-400">No assessments on record.</p>
        </div>

        <div v-else class="divide-y divide-slate-50">
          <div
            v-for="(a, idx) in (patient.assessmentHistory || [])"
            :key="idx"
            class="px-5 py-4 hover:bg-slate-50 cursor-pointer transition-colors group"
            @click="reviewAssessment(idx)">
            <div class="flex items-start gap-4">
              <div class="flex flex-col items-center mt-1 flex-shrink-0">
                <div :class="[idx === 0 ? 'bg-blue-500' : 'bg-slate-300', 'w-2.5 h-2.5 rounded-full']"/>
                <div v-if="idx < (patient.assessmentHistory || []).length - 1" class="w-px flex-1 bg-slate-200 mt-1 min-h-[24px]"/>
              </div>
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 flex-wrap">
                  <span class="text-sm font-semibold text-slate-800">{{ a.primaryComplaint || 'Assessment' }}</span>
                  <span v-if="idx === 0" class="text-[10px] bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded font-semibold">Latest</span>
                  <span :class="[riskClasses[a.risk] || 'bg-slate-100 text-slate-600', 'text-[10px] px-1.5 py-0.5 rounded font-semibold']">
                    {{ a.risk }}
                  </span>
                </div>
                <div class="text-xs text-slate-400 mt-0.5">{{ a.date }} · {{ a.time }}</div>
                <div v-if="a.aiDiagnosis" class="mt-1.5 text-xs text-slate-600 bg-slate-50 rounded px-2 py-1 inline-block">
                  <span class="text-slate-400 mr-1">Likely:</span> {{ a.aiDiagnosis }}
                </div>
              </div>
              <svg class="w-4 h-4 text-slate-300 group-hover:text-slate-500 transition flex-shrink-0 mt-1" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
            </div>
          </div>
        </div>
      </div>
    </div>
  </AppShell>
</template>
