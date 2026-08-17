<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import AppShell from '@/shared/components/AppShell.vue'
import RiskBadge from '@/shared/components/RiskBadge.vue'
import EmptyState from '@/shared/components/EmptyState.vue'
import { usePatientsStore } from '@/features/patients/stores/patients'

const router    = useRouter()
const route     = useRoute()
const store     = usePatientsStore()
const patientId = computed(() => Number(route.params.patientId))
const index     = computed(() => Number(route.params.index))
const patient   = computed(() => store.getById(patientId.value))
const assessment = computed(() => patient.value?.assessmentHistory?.[index.value] ?? null)

const vitalsList = computed(() => {
  const v = assessment.value?.vitals
  if (!v) return []
  return [
    { label: 'Blood Pressure', value: v.bpSystolic ? `${v.bpSystolic}/${v.bpDiastolic} mmHg` : null },
    { label: 'Heart Rate',     value: v.heartRate ? `${v.heartRate} bpm` : null },
    { label: 'Respiratory Rate', value: v.respiratoryRate ? `${v.respiratoryRate} /min` : null },
    { label: 'Temperature',    value: v.temperature ? `${v.temperature}°F` : null },
    { label: 'SpO₂',           value: v.spo2 ? `${v.spo2}%` : null },
    { label: 'Random Blood Sugar', value: v.rbs ? `${v.rbs} mg/dL` : null },
  ].filter(item => item.value)
})

const examFindings = computed(() => {
  const e = assessment.value?.examForm
  if (!e) return []
  const flags = []
  if (e.height) flags.push({ label: 'Height', value: `${e.height} cm` })
  if (e.weight) flags.push({ label: 'Weight', value: `${e.weight} kg` })
  if (e.dehydration) flags.push({ label: 'Dehydration', value: 'Present' })
  if (e.rashes) flags.push({ label: 'Rashes', value: 'Present' })
  if (e.swelling) flags.push({ label: 'Swelling', value: 'Present' })
  if (e.eyeDiscolouration) flags.push({ label: 'Eye Discolouration', value: 'Present' })
  if (e.generalOther) flags.push({ label: 'Other Findings', value: e.generalOther })
  return flags
})
</script>

<template>
  <AppShell>
    <template #page-title>Assessment Review</template>
    <template #page-subtitle>{{ patient?.name }} — read only</template>

    <div v-if="!patient || !assessment" class="p-8">
      <EmptyState icon="folder" title="Assessment not found" message="This assessment record may have been removed."/>
    </div>

    <div v-else class="p-4 md:p-6 space-y-5 max-w-3xl">

      <button @click="router.back()" class="flex items-center gap-1.5 text-sm text-blue-600 hover:underline">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 5l-7 7 7 7"/></svg>
        Back
      </button>

      <!-- Header -->
      <div class="bg-white rounded-xl border border-slate-100 shadow-sm p-5">
        <div class="flex items-center justify-between flex-wrap gap-2">
          <div>
            <h2 class="text-lg font-semibold text-slate-900">{{ assessment.primaryComplaint || 'Assessment' }}</h2>
            <p class="text-xs text-slate-400 mt-0.5">{{ assessment.date }} · {{ assessment.time }}</p>
          </div>
          <RiskBadge :risk="assessment.risk"/>
        </div>
      </div>

      <!-- Complaints -->
      <div v-if="assessment.complaints?.length" class="bg-white rounded-xl border border-slate-100 shadow-sm">
        <div class="px-5 py-4 border-b border-slate-100">
          <h3 class="font-semibold text-slate-900">Presenting Complaints</h3>
        </div>
        <div class="p-5 space-y-3">
          <div v-for="(c, idx) in assessment.complaints" :key="idx" class="text-sm">
            <div class="font-medium text-slate-800">{{ c.complaint }}</div>
            <div class="text-xs text-slate-500 mt-0.5">Onset: {{ c.onset }} · Duration: {{ c.duration }} · Intensity: {{ c.intensity }}/10</div>
            <div v-if="c.associatedSymptoms?.length" class="flex flex-wrap gap-1.5 mt-1.5">
              <span v-for="s in c.associatedSymptoms" :key="s" class="text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full">{{ s }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Vitals -->
      <div v-if="vitalsList.length" class="bg-white rounded-xl border border-slate-100 shadow-sm">
        <div class="px-5 py-4 border-b border-slate-100">
          <h3 class="font-semibold text-slate-900">Vitals</h3>
        </div>
        <div class="p-5 grid grid-cols-2 md:grid-cols-3 gap-4">
          <div v-for="v in vitalsList" :key="v.label">
            <div class="text-[10px] text-slate-400 uppercase tracking-wide mb-0.5">{{ v.label }}</div>
            <div class="text-sm text-slate-700">{{ v.value }}</div>
          </div>
        </div>
      </div>

      <!-- Examination findings -->
      <div v-if="examFindings.length" class="bg-white rounded-xl border border-slate-100 shadow-sm">
        <div class="px-5 py-4 border-b border-slate-100">
          <h3 class="font-semibold text-slate-900">Examination Findings</h3>
        </div>
        <div class="p-5 grid grid-cols-2 md:grid-cols-3 gap-4">
          <div v-for="f in examFindings" :key="f.label">
            <div class="text-[10px] text-slate-400 uppercase tracking-wide mb-0.5">{{ f.label }}</div>
            <div class="text-sm text-slate-700">{{ f.value }}</div>
          </div>
        </div>
      </div>

      <!-- AI Assessment Result (read-only, mocked) -->
      <div v-if="assessment.aiDiagnosis || assessment.aiSummary" class="bg-white rounded-xl border border-slate-100 shadow-sm">
        <div class="px-5 py-4 border-b border-slate-100 flex items-center gap-2">
          <svg class="w-4 h-4 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M12 2a4 4 0 0 1 4 4c0 1.5-.8 2.8-2 3.5V12h2a2 2 0 0 1 2 2v1a5 5 0 0 1-5 5h-2a5 5 0 0 1-5-5v-1a2 2 0 0 1 2-2h2V9.5C9.8 8.8 9 7.5 9 6a4 4 0 0 1 4-4z"/></svg>
          <h3 class="font-semibold text-slate-900">AI Assessment Result</h3>
        </div>
        <div class="p-5 space-y-3">
          <div v-if="assessment.aiDiagnosis">
            <div class="text-[10px] text-slate-400 uppercase tracking-wide mb-0.5">Likely Diagnosis</div>
            <div class="text-sm font-medium text-slate-800">{{ assessment.aiDiagnosis }}</div>
          </div>
          <div v-if="assessment.aiSummary">
            <div class="text-[10px] text-slate-400 uppercase tracking-wide mb-0.5">Summary</div>
            <div class="text-sm text-slate-600 leading-relaxed">{{ assessment.aiSummary }}</div>
          </div>
        </div>
      </div>
    </div>
  </AppShell>
</template>
