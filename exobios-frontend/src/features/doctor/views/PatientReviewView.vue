<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import AppShell from '@/shared/components/AppShell.vue'
import { usePatientsStore } from '@/features/patients/stores/patients'

const router    = useRouter()
const route     = useRoute()
const store     = usePatientsStore()
const patientId = computed(() => Number(route.params.id))
const patient   = computed(() => store.getById(patientId.value))

const riskClasses = {
  High:     'bg-red-100 text-red-700',
  Moderate: 'bg-orange-100 text-orange-700',
  Low:      'bg-green-100 text-green-700',
}
const riskIcon = { High: '⚠', Moderate: '●', Low: '✓' }

const initials = computed(() => {
  if (!patient.value?.name) return '?'
  return patient.value.name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()
})

function reviewAssessment(idx) {
  router.push(`/doctor/patients/${patientId.value}/assessments/${idx}`)
}
</script>

<template>
  <AppShell>
    <template #page-title>Patient Review</template>
    <template #page-subtitle>{{ patient?.name || 'Unknown Patient' }} — read only</template>

    <div v-if="!patient" class="p-8 text-center text-gray-400">Patient not found.</div>

    <div v-else class="p-4 md:p-6 space-y-5">

      <button @click="router.back()" class="flex items-center gap-1.5 text-sm text-blue-600 hover:underline">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 5l-7 7 7 7"/></svg>
        Back
      </button>

      <!-- Patient info card (read-only — no edit/new-assessment affordances) -->
      <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
        <div class="flex items-start gap-4 flex-wrap">
          <div class="w-16 h-16 rounded-full bg-blue-100 flex items-center justify-center text-xl font-bold text-blue-700 flex-shrink-0">
            {{ initials }}
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-3 flex-wrap">
              <h2 class="text-lg font-bold text-gray-900">{{ patient.name }}</h2>
              <span :class="[riskClasses[patient.risk] || 'bg-gray-100 text-gray-600', 'px-2.5 py-0.5 rounded-full text-xs font-semibold']">
                {{ riskIcon[patient.risk] }} {{ patient.risk }} Risk
              </span>
            </div>
            <div class="text-sm text-gray-500 mt-1">
              {{ patient.age }} yrs · {{ patient.gender }} · {{ patient.phone }}
            </div>
            <div class="text-xs text-gray-400 mt-0.5">
              {{ patient.address?.village }}, {{ patient.address?.district }}, {{ patient.address?.state }}
            </div>
            <div v-if="patient.abhaId" class="text-xs text-blue-600 mt-1 font-mono">ABHA: {{ patient.abhaId }}</div>
          </div>
        </div>

        <div class="mt-5 grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-gray-100">
          <div>
            <div class="text-[10px] text-gray-400 uppercase tracking-wide mb-0.5">Occupation</div>
            <div class="text-sm text-gray-700">{{ patient.occupation || '—' }}</div>
          </div>
          <div>
            <div class="text-[10px] text-gray-400 uppercase tracking-wide mb-0.5">Father / Spouse</div>
            <div class="text-sm text-gray-700">{{ patient.fatherSpouseName || '—' }}</div>
          </div>
          <div>
            <div class="text-[10px] text-gray-400 uppercase tracking-wide mb-0.5">Marital Status</div>
            <div class="text-sm text-gray-700">{{ patient.family?.maritalStatus || '—' }}</div>
          </div>
          <div>
            <div class="text-[10px] text-gray-400 uppercase tracking-wide mb-0.5">Registered</div>
            <div class="text-sm text-gray-700">{{ patient.date || '—' }}</div>
          </div>
        </div>
      </div>

      <!-- Assessment History (read-only — links to Assessment Review, not edit) -->
      <div class="bg-white rounded-xl border border-gray-100 shadow-sm">
        <div class="px-5 py-4 border-b border-gray-100">
          <h3 class="font-semibold text-gray-900">Assessment History</h3>
          <p class="text-xs text-gray-400 mt-0.5">{{ (patient.assessmentHistory || []).length }} assessments on record</p>
        </div>

        <div v-if="!(patient.assessmentHistory || []).length" class="py-12 text-center">
          <svg class="w-10 h-10 text-gray-200 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.2"><path d="M9 12h6m-3-3v6m9-6a9 9 0 1 1-18 0 9 9 0 0 1 18 0z"/></svg>
          <p class="text-sm text-gray-400">No assessments on record.</p>
        </div>

        <div v-else class="divide-y divide-gray-50">
          <div
            v-for="(a, idx) in (patient.assessmentHistory || [])"
            :key="idx"
            class="px-5 py-4 hover:bg-gray-50 cursor-pointer transition-colors group"
            @click="reviewAssessment(idx)">
            <div class="flex items-start gap-4">
              <div class="flex flex-col items-center mt-1 flex-shrink-0">
                <div :class="[idx === 0 ? 'bg-blue-500' : 'bg-gray-300', 'w-2.5 h-2.5 rounded-full']"/>
                <div v-if="idx < (patient.assessmentHistory || []).length - 1" class="w-px flex-1 bg-gray-200 mt-1 min-h-[24px]"/>
              </div>
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 flex-wrap">
                  <span class="text-sm font-semibold text-gray-800">{{ a.primaryComplaint || 'Assessment' }}</span>
                  <span v-if="idx === 0" class="text-[10px] bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded font-semibold">Latest</span>
                  <span :class="[riskClasses[a.risk] || 'bg-gray-100 text-gray-600', 'text-[10px] px-1.5 py-0.5 rounded font-semibold']">
                    {{ a.risk }}
                  </span>
                </div>
                <div class="text-xs text-gray-400 mt-0.5">{{ a.date }} · {{ a.time }}</div>
                <div v-if="a.aiDiagnosis" class="mt-1.5 text-xs text-gray-600 bg-gray-50 rounded px-2 py-1 inline-block">
                  <span class="text-gray-400 mr-1">Likely:</span> {{ a.aiDiagnosis }}
                </div>
              </div>
              <svg class="w-4 h-4 text-gray-300 group-hover:text-gray-500 transition flex-shrink-0 mt-1" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
            </div>
          </div>
        </div>
      </div>
    </div>
  </AppShell>
</template>
