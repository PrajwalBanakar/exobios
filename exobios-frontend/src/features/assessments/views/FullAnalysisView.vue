<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import AppShell from '@/shared/components/AppShell.vue'
import { usePatientsStore } from '@/features/patients/stores/patients'
import { MOCK_DIFFERENTIAL_DIAGNOSIS } from '@/features/assessments/constants/mockDiagnosis'
import { useI18n } from '@/i18n'
import { formatPatientId } from '@/shared/utils/format'

const router    = useRouter()
const route     = useRoute()
const store     = usePatientsStore()
const { t }     = useI18n()
const patientId  = computed(() => Number(route.params.id))
const historyIdx = computed(() => route.query.historyIdx !== undefined ? Number(route.query.historyIdx) : 0)
const patient    = computed(() => store.getById(patientId.value) || { name: 'Unknown', age: '—', gender: '—', location: '—' })
// The specific assessment being viewed (defaults to latest) — same lookup AIResultView uses.
const assessment = computed(() => {
  const history = patient.value?.assessmentHistory || []
  return history[historyIdx.value] || null
})

// The investigations/treatment/warnings/differential below only exist as canned demo
// content today (shared with AIResultView) — they only apply to the seeded records
// that carry a real aiDiagnosis. A freshly submitted assessment has no AI output yet
// (the live flow doesn't call a real AI/FastAPI endpoint), so this page shows an
// honest "not yet available" state instead of the same dengue-specific analysis for
// every patient regardless of their actual complaint.
const hasAiData = computed(() => !!assessment.value?.aiDiagnosis)
const conditions = MOCK_DIFFERENTIAL_DIAGNOSIS

// ── Vitals — the actual vitals recorded during the assessment, not hardcoded mock values ──
const vitalsDisplay = computed(() => {
  const v = assessment.value?.vitals
  if (!v) return []
  return [
    { label: 'Blood Pressure',   value: (v.bpSystolic && v.bpDiastolic) ? `${v.bpSystolic}/${v.bpDiastolic} mmHg` : null },
    { label: 'Heart Rate',       value: v.heartRate       ? `${v.heartRate} BPM`       : null },
    { label: 'Respiratory Rate', value: v.respiratoryRate ? `${v.respiratoryRate} /min` : null },
    { label: 'Temperature',      value: v.temperature     ? `${v.temperature} °F`      : null },
    { label: 'SpO₂',             value: v.spo2            ? `${v.spo2}%`               : null },
    { label: 'Blood Glucose (RBS)', value: v.rbs          ? `${v.rbs} mg/dL`           : null },
  ].filter(item => item.value)
})

const investigations = [
  { name: 'Complete Blood Count (CBC)', priority: 'Urgent', reason: 'Check platelet count and WBC for dengue confirmation' },
  { name: 'NS1 Antigen Test',           priority: 'Urgent', reason: 'Early dengue detection (best in first 5 days)' },
  { name: 'Dengue IgM/IgG',             priority: 'High',   reason: 'Confirm dengue serology' },
  { name: 'Malarial Parasite Smear',    priority: 'High',   reason: 'Rule out malaria in endemic area' },
  { name: 'Widal Test',                 priority: 'Medium', reason: 'Rule out typhoid if fever persists' },
  { name: 'Liver Function Tests',       priority: 'Medium', reason: 'Dengue can cause hepatic involvement' },
]

const treatmentProtocol = [
  'Paracetamol 650mg every 6 hours (avoid aspirin/ibuprofen in suspected dengue)',
  'Oral Rehydration: 2-3 litres of fluids daily (ORS, coconut water, fruit juices)',
  'Tepid sponging for temperature above 102°F',
  'Complete bed rest; monitor for warning signs',
  'Avoid mosquito bites to prevent further transmission',
  'Platelet monitoring every 24-48 hours',
]

const warnings = [
  { text: 'Severe abdominal pain or tenderness',            urgency: 'Critical' },
  { text: 'Persistent vomiting (>3 times in 24 hours)',     urgency: 'Critical' },
  { text: 'Bleeding from gums, nose, or in urine/stool',   urgency: 'Critical' },
  { text: 'Rapid breathing or difficulty breathing',        urgency: 'Critical' },
  { text: 'Fatigue, restlessness or confusion',             urgency: 'High'     },
  { text: 'Platelet count < 50,000',                        urgency: 'Critical' },
]

const priorityColors  = { Urgent: 'bg-red-100 text-red-600', High: 'bg-orange-100 text-orange-600', Medium: 'bg-yellow-100 text-yellow-600' }
const urgencyColors   = { Critical: 'bg-red-100 text-red-600 border-red-200', High: 'bg-orange-100 text-orange-600 border-orange-200' }
const confidenceColors = { High: 'text-red-600', Medium: 'text-orange-500', Low: 'text-green-600' }
</script>

<template>
  <AppShell>
    <template #page-title>{{ t('analysis.title') }}</template>
    <template #page-subtitle>{{ t('analysis.subtitle') }}</template>

    <div class="p-4 md:p-6 space-y-5">
      <!-- Patient header -->
      <div class="bg-white rounded-xl border border-slate-100 shadow-sm px-5 py-4 flex items-center justify-between flex-wrap gap-4">
        <div class="flex items-center gap-6 flex-wrap text-sm">
          <div><span class="text-slate-500 text-xs">{{ t('result.patientName') }}: </span><span class="font-semibold text-slate-800">{{ patient.name }}</span></div>
          <div><span class="text-slate-500 text-xs">Patient ID: </span><span class="font-semibold text-slate-800">{{ formatPatientId(patientId) }}</span></div>
          <div><span class="text-slate-500 text-xs">{{ t('result.ageGender') }}: </span><span class="font-semibold text-slate-800">{{ patient.age }} / {{ patient.gender }}</span></div>
          <div><span class="text-slate-500 text-xs">{{ t('result.location') }}: </span><span class="font-semibold text-slate-800">{{ patient.address?.village || patient.location || '—' }}</span></div>
        </div>
        <div class="flex items-center gap-2">
          <button @click="router.back()" class="flex items-center gap-1.5 px-3 py-2 border border-slate-200 text-slate-600 text-xs font-medium rounded-xl hover:bg-slate-50 transition">
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 5l-7 7 7 7"/></svg>
            {{ t('common.back') }}
          </button>
          <button @click="window.print()" class="flex items-center gap-1.5 px-3 py-2 border border-slate-200 text-slate-600 text-xs font-medium rounded-xl hover:bg-slate-50 transition">
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>
            {{ t('result.printSave') }}
          </button>
        </div>
      </div>

      <!-- AI disclaimer -->
      <div class="flex items-start gap-3 bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 text-xs text-amber-700">
        <svg class="w-4 h-4 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm1 15h-2v-6h2zm0-8h-2V7h2z"/></svg>
        This analysis is generated by AI and should be validated by a qualified healthcare professional before clinical decision-making. Confidence values represent probabilistic estimates, not definitive diagnoses.
      </div>

      <template v-if="hasAiData">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
          <!-- Differential diagnoses — full width -->
          <div class="bg-white rounded-xl border border-slate-100 shadow-sm p-5 md:col-span-2">
            <h3 class="font-semibold text-slate-800 mb-4">Differential Diagnosis (AI Probability Analysis)</h3>
            <div class="space-y-4">
              <div v-for="(c, i) in conditions" :key="c.name"
                :class="['p-4 rounded-xl border', i === 0 ? 'border-red-200 bg-red-50/30' : 'border-slate-100']">
                <div class="flex items-start justify-between mb-2">
                  <div class="flex items-center gap-3">
                    <span class="w-6 h-6 rounded-full bg-slate-800 text-white text-xs font-bold flex items-center justify-center">{{ i + 1 }}</span>
                    <div>
                      <span class="font-semibold text-slate-800">{{ c.name }}</span>
                      <span class="ml-2 text-xs text-slate-400">ICD-10: {{ c.icd }}</span>
                    </div>
                  </div>
                  <div class="flex items-center gap-3">
                    <span :class="[confidenceColors[c.confidence], 'text-xs font-semibold']">{{ c.confidence }} Confidence</span>
                    <span class="text-lg font-bold text-slate-800">{{ c.pct }}%</span>
                  </div>
                </div>
                <div class="h-2 bg-slate-100 rounded-full overflow-hidden mb-3">
                  <div :class="[c.color, 'h-full rounded-full']" :style="`width:${c.pct}%`"/>
                </div>
                <div class="flex items-start gap-2 flex-wrap">
                  <span class="text-xs text-slate-500 font-medium">Supporting evidence:</span>
                  <span v-for="e in c.evidence" :key="e" class="text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded font-medium">{{ e }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Vitals — the actual vitals recorded for this assessment -->
          <div class="bg-white rounded-xl border border-slate-100 shadow-sm p-5">
            <h3 class="font-semibold text-slate-800 mb-4">Vitals</h3>
            <div v-if="vitalsDisplay.length" class="space-y-2.5">
              <div v-for="v in vitalsDisplay" :key="v.label" class="rounded-xl p-3 bg-slate-50 flex items-center justify-between">
                <span class="text-xs text-slate-500">{{ v.label }}</span>
                <span class="font-bold text-sm text-slate-800">{{ v.value }}</span>
              </div>
            </div>
            <p v-else class="text-sm text-slate-400 italic">No vitals recorded</p>
          </div>

          <!-- Investigations + Treatment -->
          <div class="space-y-4">
            <div class="bg-white rounded-xl border border-slate-100 shadow-sm p-5">
              <h3 class="font-semibold text-slate-800 mb-4">Recommended Investigations</h3>
              <div class="space-y-2.5">
                <div v-for="inv in investigations" :key="inv.name" class="flex items-start gap-3">
                  <span :class="[priorityColors[inv.priority], 'px-2 py-0.5 rounded text-[10px] font-bold flex-shrink-0 mt-0.5']">{{ inv.priority }}</span>
                  <div>
                    <div class="text-sm font-medium text-slate-800">{{ inv.name }}</div>
                    <div class="text-xs text-slate-500">{{ inv.reason }}</div>
                  </div>
                </div>
              </div>
            </div>

            <div class="bg-white rounded-xl border border-slate-100 shadow-sm p-5">
              <h3 class="font-semibold text-slate-800 mb-4">Treatment Protocol</h3>
              <ul class="space-y-2">
                <li v-for="(step, i) in treatmentProtocol" :key="i" class="flex items-start gap-2.5 text-sm text-slate-700">
                  <span class="w-5 h-5 rounded-full bg-green-100 flex items-center justify-center text-green-600 text-xs font-bold flex-shrink-0 mt-0.5">{{ i + 1 }}</span>
                  {{ step }}
                </li>
              </ul>
            </div>
          </div>

          <!-- Warning signs — full width -->
          <div class="md:col-span-2 bg-white rounded-xl border border-red-100 bg-red-50/20 shadow-sm p-5">
            <h3 class="font-semibold text-slate-800 mb-4">Warning Signs — Seek Immediate Medical Care If:</h3>
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              <div v-for="w in warnings" :key="w.text"
                :class="[urgencyColors[w.urgency], 'rounded-xl p-3 border flex items-start gap-2']">
                <svg class="w-4 h-4 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/></svg>
                <span class="text-xs font-medium">{{ w.text }}</span>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- Honest empty state + real vitals when no AI output exists for this assessment -->
      <template v-else>
        <div class="bg-white rounded-xl border border-slate-100 shadow-sm p-5">
          <h3 class="font-semibold text-slate-800 mb-4">Vitals</h3>
          <div v-if="vitalsDisplay.length" class="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
            <div v-for="v in vitalsDisplay" :key="v.label" class="rounded-xl p-3 bg-slate-50 flex items-center justify-between">
              <span class="text-xs text-slate-500">{{ v.label }}</span>
              <span class="font-bold text-sm text-slate-800">{{ v.value }}</span>
            </div>
          </div>
          <p v-else class="text-sm text-slate-400 italic">No vitals recorded</p>
        </div>
        <div class="flex flex-col items-center rounded-xl border border-dashed border-slate-200 bg-white py-12 text-center">
          <svg class="w-10 h-10 text-slate-300 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.3"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          <p class="text-sm font-medium text-slate-600">Full AI analysis pending</p>
          <p class="text-xs text-slate-400 max-w-sm mt-1">Differential diagnosis, recommended investigations, treatment protocol and warning signs will appear here once this assessment has been scored by the AI service.</p>
        </div>
      </template>

      <!-- Bottom actions -->
      <div class="flex items-center justify-end gap-3">
        <button @click="router.push(`/assessment/${patientId}/result`)"
          class="px-5 py-2.5 border border-slate-200 text-slate-600 text-sm font-medium rounded-xl hover:bg-slate-50 transition">
          {{ t('result.title') }}
        </button>
        <button @click="router.push(`/assessment/${patientId}/measures`)"
          class="flex items-center gap-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-xl transition">
          {{ t('result.recordMeasures') }}
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
        </button>
      </div>
    </div>
  </AppShell>
</template>
