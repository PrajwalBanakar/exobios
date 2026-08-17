<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import AppShell from '@/shared/components/AppShell.vue'
import SyncStatusBadge from '@/shared/components/SyncStatusBadge.vue'
import RiskBadge from '@/shared/components/RiskBadge.vue'
import PatientAvatar from '@/shared/components/PatientAvatar.vue'
import EmptyState from '@/shared/components/EmptyState.vue'
import { usePatientsStore } from '@/features/patients/stores/patients'
import { formatPatientId } from '@/shared/utils/format'

const router    = useRouter()
const route     = useRoute()
const store     = usePatientsStore()
const patientId = computed(() => Number(route.params.id))
const patient   = computed(() => store.getById(patientId.value))

const riskClasses = {
  High:     'bg-red-50 text-red-700 border-red-100',
  Moderate: 'bg-amber-50 text-amber-700 border-amber-100',
  Low:      'bg-green-50 text-green-700 border-green-100',
}
</script>

<template>
  <AppShell>
    <template #page-title>Patient Profile</template>
    <template #page-subtitle>{{ patient?.name || 'Unknown Patient' }}</template>

    <SyncStatusBadge variant="bar"/>

    <div v-if="!patient" class="p-8">
      <EmptyState icon="users" title="Patient not found" message="This patient record may have been removed.">
        <button @click="router.push('/patients')" class="mt-4 rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700">
          Back to Patients
        </button>
      </EmptyState>
    </div>

    <div v-else class="space-y-5 p-4 md:p-6">

      <!-- Back -->
      <button @click="router.push('/patients')" class="flex items-center gap-1.5 text-sm text-blue-600 hover:underline">
        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 5l-7 7 7 7"/></svg>
        Back to Patients
      </button>

      <!-- Patient info card -->
      <div class="rounded-2xl border border-slate-200 bg-white p-5">
        <div class="flex flex-wrap items-start gap-4">
          <PatientAvatar :name="patient.name" size="lg"/>

          <!-- Core info -->
          <div class="min-w-0 flex-1">
            <div class="flex flex-wrap items-center gap-3">
              <h2 class="text-lg font-bold text-slate-900">{{ patient.name }}</h2>
              <RiskBadge :risk="patient.risk"/>
            </div>
            <div class="mt-1 text-sm text-slate-500">
              {{ formatPatientId(patient.id) }} · {{ patient.age }} yrs · {{ patient.gender }} · {{ patient.phone }}
            </div>
            <div class="mt-0.5 text-xs text-slate-400">
              {{ [patient.address?.village, patient.address?.district, patient.address?.state].filter(Boolean).join(', ') || '—' }}
            </div>
            <div v-if="patient.abhaId" class="mt-1 font-mono text-xs text-blue-600">ABHA: {{ patient.abhaId }}</div>
          </div>

          <!-- Action buttons -->
          <div class="flex flex-shrink-0 gap-2">
            <button
              @click="router.push(`/assessment/new?patientId=${patient.id}`)"
              class="flex items-center gap-1.5 rounded-lg bg-blue-600 px-3 py-2 text-xs font-semibold text-white transition hover:bg-blue-700">
              <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M12 5v14M5 12h14"/></svg>
              New Assessment
            </button>
            <button
              @click="router.push(`/patients/${patient.id}/edit`)"
              class="flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-600 transition hover:bg-slate-50">
              <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
              Edit Info
            </button>
          </div>
        </div>

        <!-- Demographic grid -->
        <div class="mt-5 grid grid-cols-2 gap-4 border-t border-slate-100 pt-4 md:grid-cols-4">
          <div>
            <div class="mb-0.5 text-[10px] uppercase tracking-wide text-slate-400">Occupation</div>
            <div class="text-sm text-slate-700">{{ patient.occupation || '—' }}</div>
          </div>
          <div>
            <div class="mb-0.5 text-[10px] uppercase tracking-wide text-slate-400">Father / Spouse</div>
            <div class="text-sm text-slate-700">{{ patient.fatherSpouseName || '—' }}</div>
          </div>
          <div>
            <div class="mb-0.5 text-[10px] uppercase tracking-wide text-slate-400">Marital Status</div>
            <div class="text-sm text-slate-700">{{ patient.family?.maritalStatus || '—' }}</div>
          </div>
          <div>
            <div class="mb-0.5 text-[10px] uppercase tracking-wide text-slate-400">Registered</div>
            <div class="text-sm text-slate-700">{{ patient.date || '—' }}</div>
          </div>
        </div>
      </div>

      <!-- Assessment History -->
      <div class="rounded-2xl border border-slate-200 bg-white">
        <div class="flex items-center justify-between border-b border-slate-100 px-5 py-4">
          <div>
            <h3 class="font-semibold text-slate-900">Assessment History</h3>
            <p class="text-xs text-slate-400 mt-0.5">{{ (patient.assessmentHistory || []).length }} assessments on record</p>
          </div>
          <button
            @click="router.push(`/assessment/new?patientId=${patient.id}`)"
            class="flex items-center gap-1 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg transition">
            <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M12 5v14M5 12h14"/></svg>
            New
          </button>
        </div>

        <!-- Empty state -->
        <div v-if="!(patient.assessmentHistory || []).length" class="py-12 text-center">
          <svg class="w-10 h-10 text-slate-200 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.2"><path d="M9 12h6m-3-3v6m9-6a9 9 0 1 1-18 0 9 9 0 0 1 18 0z"/></svg>
          <p class="text-sm text-slate-400">No assessments yet.</p>
          <button
            @click="router.push(`/assessment/new?patientId=${patient.id}`)"
            class="mt-3 text-xs text-blue-600 underline">Start first assessment</button>
        </div>

        <!-- Timeline -->
        <div v-else class="divide-y divide-slate-50">
          <div
            v-for="(a, idx) in (patient.assessmentHistory || [])"
            :key="idx"
            class="px-5 py-4 hover:bg-slate-50 cursor-pointer transition-colors group"
            @click="router.push(`/assessment/${patient.id}/result?historyIdx=${idx}`)">

            <div class="flex items-start gap-4">
              <!-- Timeline dot -->
              <div class="flex flex-col items-center mt-1 flex-shrink-0">
                <div :class="[idx === 0 ? 'bg-blue-500' : 'bg-slate-300', 'w-2.5 h-2.5 rounded-full']"/>
                <div v-if="idx < (patient.assessmentHistory || []).length - 1" class="w-px flex-1 bg-slate-200 mt-1 min-h-[24px]"/>
              </div>

              <!-- Content -->
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 flex-wrap">
                  <span class="text-sm font-semibold text-slate-800">{{ a.primaryComplaint || 'Assessment' }}</span>
                  <span v-if="idx === 0" class="text-[10px] bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded font-semibold">Latest</span>
                  <span :class="[riskClasses[a.risk] || 'bg-slate-100 text-slate-600', 'text-[10px] px-1.5 py-0.5 rounded font-semibold']">
                    {{ a.risk }}
                  </span>
                </div>
                <div class="text-xs text-slate-400 mt-0.5">{{ a.date }} · {{ a.time }}</div>

                <!-- AI diagnosis if available -->
                <div v-if="a.aiDiagnosis" class="mt-1.5 text-xs text-slate-600 bg-slate-50 rounded px-2 py-1 inline-block">
                  <span class="text-slate-400 mr-1">Likely:</span> {{ a.aiDiagnosis }}
                </div>

                <!-- Vitals mini-strip -->
                <div v-if="a.vitals" class="flex flex-wrap gap-3 mt-2">
                  <span v-if="a.vitals.bpSystolic" class="text-[10px] text-slate-500">
                    BP {{ a.vitals.bpSystolic }}/{{ a.vitals.bpDiastolic }}
                  </span>
                  <span v-if="a.vitals.heartRate" class="text-[10px] text-slate-500">
                    HR {{ a.vitals.heartRate }}
                  </span>
                  <span v-if="a.vitals.spo2" class="text-[10px] text-slate-500">
                    SpO₂ {{ a.vitals.spo2 }}%
                  </span>
                  <span v-if="a.vitals.temperature" class="text-[10px] text-slate-500">
                    Temp {{ a.vitals.temperature }}°F
                  </span>
                  <span v-if="a.vitals.rbs" class="text-[10px] text-slate-500">
                    RBS {{ a.vitals.rbs }} mg/dL
                  </span>
                </div>
              </div>

              <!-- Arrow -->
              <svg class="w-4 h-4 text-slate-300 group-hover:text-slate-500 transition flex-shrink-0 mt-1" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
            </div>
          </div>
        </div>
      </div>

    </div>
  </AppShell>
</template>
