<script setup>
import { ref, computed, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import AppShell from '@/shared/components/AppShell.vue'
import { usePatientsStore } from '@/features/patients/stores/patients'
import { useAuthStore } from '@/features/auth/stores/auth'
import { useActionPlanStore } from '@/shared/stores/actionPlan'
import { HOSPITALS, sortByDistance } from '@/shared/constants/hospitals'
import { DOCTOR_TIER, getDoctorsByTier } from '@/shared/constants/doctors'
import { computeActiveFlags } from '@/features/assessments/constants/complaintsDef'
import { MOCK_DIFFERENTIAL_DIAGNOSIS } from '@/features/assessments/constants/mockDiagnosis'
import { useI18n } from '@/i18n'
import RiskBadge from '@/shared/components/RiskBadge.vue'
import { formatPatientId } from '@/shared/utils/format'

const router     = useRouter()
const route      = useRoute()
const store      = usePatientsStore()
const auth       = useAuthStore()
const actionPlan = useActionPlanStore()
const { t }      = useI18n()
const patientId   = computed(() => Number(route.params.id))
const historyIdx  = computed(() => route.query.historyIdx !== undefined ? Number(route.query.historyIdx) : 0)
const patient     = computed(() => store.getById(patientId.value) || {
  name: 'Unknown', id: patientId.value, age: '—', gender: '—', location: '—',
})
// The specific assessment being viewed (defaults to latest)
const assessment  = computed(() => {
  const history = patient.value?.assessmentHistory || []
  return history[historyIdx.value] || null
})

// ── Differential Diagnosis ──────────────────────────────────────────────────
// The ranked probability list and narrative summary only exist for the seeded demo
// records today — the live assessment flow (NewAssessmentView) doesn't yet call a
// real AI/FastAPI endpoint, so a freshly submitted assessment has no aiDiagnosis on
// it. Rather than showing the same mock Dengue analysis for every patient, this page
// only renders AI output when the assessment actually carries it, and shows an
// honest "pending" state otherwise. (Backend dependency: wiring the AI service into
// the assessment-submission flow so every assessment gets real analysis.)
const hasAiData = computed(() => !!assessment.value?.aiDiagnosis)
const conditions = MOCK_DIFFERENTIAL_DIAGNOSIS
const aiSummary  = computed(() => assessment.value?.aiSummary || '')

// ── Warning Signs — derived from the same AI flags NewAssessmentView computes,
// re-applied here to the saved assessment's complaints (no new flag logic). ───────
const activeFlags = computed(() => computeActiveFlags(assessment.value?.complaints?.selected, assessment.value?.complaints?.details))

// ── Plan of Action — Immediate Measures (role-based) ──────────────────────
const PARAMEDIC_IMMEDIATE_MEASURES = [
  'Administer Paracetamol 650mg for fever relief',
  'Ensure adequate oral hydration (ORS / fluids)',
  'Monitor temperature and platelet count',
  'Rest and avoid NSAIDs / Aspirin',
  'Advise patient on warning signs requiring immediate referral',
]
const DOCTOR_IMMEDIATE_MEASURES = [
  'Assess hydration/perfusion status and start IV fluids if indicated',
  'Order confirmatory investigations (e.g. NS1/CBC/platelet count)',
  'Initiate symptomatic and supportive treatment per clinical protocol',
  'Closely monitor vitals and evolving warning signs',
  'Document clinical findings, working diagnosis, and management plan',
]
const immediateMeasures = computed(() => auth.isDoctor ? DOCTOR_IMMEDIATE_MEASURES : PARAMEDIC_IMMEDIATE_MEASURES)

// Referral decision: 'undecided' | 'yes' | 'no'
const referralDecision = ref('undecided')

// Nearby hospitals — sourced from the shared hospitals directory, closest first
// (Government hospitals are highlighted in the template, not hardcoded here).
const hospitals = sortByDistance(HOSPITALS).slice(0, 4)

// Teleconsult doctor tier follows role: Paramedic sees general doctors, Doctor sees specialists.
const doctors = computed(() => getDoctorsByTier(auth.isDoctor ? DOCTOR_TIER.SPECIALIST : DOCTOR_TIER.GENERAL))

function callAmbulance() { window.location.href = 'tel:108' }
function callNumber(n)   { window.location.href = `tel:${n}` }
function openMap(addr)   { window.open(`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(addr)}`, '_blank') }
function startVideo()    { window.open('https://meet.google.com/new', '_blank') }

// ── AI Chatbot ─────────────────────────────────────────────────────────────
const chatOpen    = ref(false)
const chatInput   = ref('')
const chatHistory = ref([
  { role: 'ai', text: 'Hello! I\'m the Exobios AI assistant. Ask me anything about this patient\'s diagnosis or next steps.' },
])

const chatLoading = ref(false)
function sendChat() {
  const msg = chatInput.value.trim()
  if (!msg) return
  chatHistory.value.push({ role: 'user', text: msg })
  chatInput.value = ''
  chatLoading.value = true
  setTimeout(() => {
    chatHistory.value.push({ role: 'ai', text: 'Based on the current assessment, I recommend ensuring the patient is well-hydrated and monitored for warning signs like persistent vomiting, severe abdominal pain, or bleeding. A Dengue NS1 antigen test would confirm the diagnosis.' })
    chatLoading.value = false
  }, 1200)
}

// ── Action Taken ───────────────────────────────────────────────────────────
const actionTaken = reactive({
  measures: immediateMeasures.value.map(() => false),
  referralHospital: '',
  ambulanceCalled: false,
  teleconsultDoctor: '',
  teleconsultNotes: '',
  additionalNotes: '',
})

const actionSubmitted = ref(false)
function submitAction() {
  actionSubmitted.value = true

  // Write the plan of action to the shared store so MeasuresView (and eventually
  // ReferralsView) read the same decision instead of re-capturing it independently.
  actionPlan.setImmediateMeasures(patientId.value, immediateMeasures.value.map((label, i) => ({ label, done: actionTaken.measures[i] })))
  actionPlan.setReferral(patientId.value, {
    hospitalId: actionTaken.referralHospital || null,
    status: referralDecision.value === 'undecided' ? '' : referralDecision.value,
  })
  actionPlan.setTeleconsult(patientId.value, {
    doctorId: actionTaken.teleconsultDoctor || null,
    status: actionTaken.teleconsultDoctor ? 'yes' : '',
  })
  actionPlan.setNotes(patientId.value, actionTaken.additionalNotes)

  setTimeout(() => { actionSubmitted.value = false }, 3000)
}

// ── Clinical Annotation ───────────────────────────────────────────────────
const annotationKey     = computed(() => `annotation_${patientId.value}`)
const annotation        = ref(localStorage.getItem(annotationKey.value) || '')
const editingAnnotation = ref(false)
const annotationDraft   = ref('')
function startEditAnnotation() { annotationDraft.value = annotation.value; editingAnnotation.value = true }
function saveAnnotation()      { annotation.value = annotationDraft.value; localStorage.setItem(annotationKey.value, annotation.value); editingAnnotation.value = false }

// ── Version History ───────────────────────────────────────────────────────
const versionHistory = computed(() => {
  try { return JSON.parse(localStorage.getItem(`assessment_versions_${patientId.value}`) || '[]').reverse() }
  catch { return [] }
})

// ── Share ─────────────────────────────────────────────────────────────────
function sendWhatsApp(p) {
  const msg = encodeURIComponent(`Patient: ${p.name}, Age: ${p.age}/${p.gender}, Location: ${p.address?.village || p.location || '—'}. Assessed at ${p.assessmentTime || p.date}.`)
  window.open(`https://wa.me/?text=${msg}`, '_blank')
}
function sendEmail(p) {
  const subject = encodeURIComponent(`Patient Assessment — ${p.name}`)
  const body    = encodeURIComponent(`Patient: ${p.name}\nAge/Gender: ${p.age}/${p.gender}\nLocation: ${p.address?.village || p.location || '—'}\nAssessment Time: ${p.assessmentTime || p.date}`)
  window.open(`mailto:?subject=${subject}&body=${body}`)
}
function printResult() { window.print() }
</script>

<template>
  <AppShell>
    <template #page-title>{{ t('result.title') }}</template>
    <template #page-subtitle>{{ t('result.subtitle') }}</template>

    <div class="p-4 md:p-6 space-y-5">

      <!-- Patient header strip -->
      <div class="bg-white rounded-xl border border-slate-100 shadow-sm px-5 py-4 flex items-center gap-5 flex-wrap">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 rounded-full bg-blue-100 flex items-center justify-center">
            <svg class="w-5 h-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
          </div>
          <div>
            <div class="text-xs text-slate-500">{{ t('result.patientName') }}</div>
            <div class="text-sm font-semibold text-slate-800">{{ patient.name }}</div>
          </div>
        </div>
        <div><div class="text-xs text-slate-500">Patient ID</div><div class="text-sm font-semibold text-slate-800">{{ formatPatientId(patientId) }}</div></div>
        <div><div class="text-xs text-slate-500">{{ t('result.ageGender') }}</div><div class="text-sm font-semibold text-slate-800">{{ patient.age }} / {{ patient.gender }}</div></div>
        <div><div class="text-xs text-slate-500">{{ t('result.location') }}</div><div class="text-sm font-semibold text-slate-800">{{ patient.address?.village || patient.location || '—' }}</div></div>
        <!-- Show which assessment this is -->
        <div v-if="assessment">
          <div class="text-xs text-slate-500">Assessment Date</div>
          <div class="text-sm font-semibold text-slate-800">{{ assessment.date }}, {{ assessment.time }}</div>
        </div>
        <div v-if="(patient.assessmentHistory || []).length > 1" class="text-xs">
          <div class="text-slate-400 mb-0.5">Viewing</div>
          <div class="font-semibold text-blue-600">
            {{ historyIdx === 0 ? 'Latest' : `#${historyIdx + 1} of ${patient.assessmentHistory.length}` }}
          </div>
        </div>
        <div class="ml-auto flex items-center gap-2 flex-wrap">
          <button @click="router.push(`/patients/${patientId}`)" class="flex items-center gap-1.5 px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-600 text-xs font-medium rounded-xl transition">
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 5l-7 7 7 7"/></svg>
            All Assessments
          </button>
          <button @click="router.push(`/assessment/new?patientId=${patientId}`)" class="flex items-center gap-1.5 px-3 py-2 border border-slate-200 text-slate-600 text-xs font-medium rounded-xl hover:bg-slate-50 transition">
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M12 5v14M5 12h14"/></svg>
            New Assessment
          </button>
          <button @click="printResult" class="flex items-center gap-1.5 px-3 py-2 border border-slate-200 text-slate-600 text-xs font-medium rounded-xl hover:bg-slate-50 transition">
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>
            Print
          </button>
        </div>
      </div>

      <!-- Historical assessment banner (not viewing latest) -->
      <div v-if="historyIdx > 0" class="bg-amber-50 border border-amber-200 rounded-xl px-4 py-2.5 flex items-center gap-3 text-sm">
        <svg class="w-4 h-4 text-amber-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
        <span class="text-amber-700">Viewing historical assessment from <strong>{{ assessment?.date }}</strong>.</span>
        <button @click="router.push(`/assessment/${patientId}/result`)" class="ml-auto text-xs text-amber-700 underline font-semibold whitespace-nowrap">View Latest →</button>
      </div>

      <!-- ── SECTION 1: Differential Diagnosis ── -->
      <div class="bg-white rounded-xl border border-slate-100 shadow-sm p-5">
        <div class="flex items-center justify-between mb-1">
          <h2 class="font-semibold text-slate-900 flex items-center gap-2">
            <svg class="w-5 h-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
            Differential Diagnosis
            <span class="text-xs font-normal text-blue-500">AI Analysis</span>
          </h2>
          <RiskBadge v-if="assessment?.risk" :risk="assessment.risk"/>
        </div>

        <!-- Decision-support disclaimer -->
        <div class="flex items-start gap-2 text-xs text-blue-700 bg-blue-50 border border-blue-100 rounded-xl px-3.5 py-2.5 mt-3">
          <svg class="w-4 h-4 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
          <span>AI-generated decision support — intended to assist, not replace, clinical judgment. Confirm findings before acting.</span>
        </div>

        <template v-if="hasAiData">
          <!-- AI brief summary -->
          <p v-if="aiSummary" class="text-sm text-slate-600 leading-relaxed mb-5 bg-slate-50 border border-slate-100 rounded-xl px-4 py-3 mt-3">
            {{ aiSummary }}
          </p>

          <!-- Probability bars -->
          <div class="space-y-3">
            <div v-for="(c, i) in conditions" :key="c.name" class="flex items-center gap-3">
              <span class="text-xs font-bold text-slate-500 w-4">{{ i + 1 }}.</span>
              <div class="flex-1">
                <div class="flex justify-between text-xs mb-1">
                  <span :class="['font-semibold', i === 0 ? 'text-red-600' : 'text-slate-700']">{{ c.name }}</span>
                  <span class="font-bold text-slate-700">{{ c.pct }}%</span>
                </div>
                <div class="h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div :class="['h-full rounded-full transition-all duration-700', c.color]" :style="`width:${c.pct}%`"/>
                </div>
              </div>
            </div>
          </div>

          <button @click="router.push(`/assessment/${patientId}/analysis`)"
            class="text-xs text-blue-600 hover:underline mt-4 flex items-center gap-1">
            View Full Differential Analysis
            <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
          </button>
        </template>

        <!-- Honest empty state — no fabricated diagnosis when the assessment has no real AI output -->
        <div v-else class="mt-4 flex flex-col items-center rounded-xl border border-dashed border-slate-200 py-10 text-center">
          <svg class="w-10 h-10 text-slate-300 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.3"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          <p class="text-sm font-medium text-slate-600">AI analysis pending</p>
          <p class="text-xs text-slate-400 max-w-sm mt-1">This assessment hasn't been scored by the AI service yet. Use your clinical judgment and the recorded complaints, history and vitals below to decide next steps.</p>
        </div>
      </div>

      <!-- ── SECTION 2: AI Chatbot ── -->
      <div class="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden">
        <button class="w-full flex items-center justify-between px-5 py-4" @click="chatOpen = !chatOpen">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center">
              <svg class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
            </div>
            <div>
              <div class="font-semibold text-slate-800 text-sm">Ask AI for Clarification</div>
              <div class="text-xs text-slate-400">Get detailed explanation or ask follow-up questions</div>
            </div>
          </div>
          <svg :class="['w-5 h-5 text-slate-400 transition-transform', chatOpen ? 'rotate-180' : '']" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M19 9l-7 7-7-7"/></svg>
        </button>

        <div v-if="chatOpen" class="border-t border-slate-100">
          <!-- Chat history -->
          <div class="h-52 overflow-y-auto px-4 py-3 space-y-3 bg-slate-50/40">
            <div v-for="(msg, i) in chatHistory" :key="i"
              :class="['flex', msg.role === 'user' ? 'justify-end' : 'justify-start']">
              <div :class="['max-w-[80%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed', msg.role === 'user' ? 'bg-blue-600 text-white rounded-tr-sm' : 'bg-white border border-slate-100 text-slate-700 rounded-tl-sm shadow-sm']">
                {{ msg.text }}
              </div>
            </div>
            <div v-if="chatLoading" class="flex justify-start">
              <div class="bg-white border border-slate-100 shadow-sm px-4 py-3 rounded-2xl rounded-tl-sm">
                <div class="flex gap-1">
                  <span v-for="n in 3" :key="n" :style="`animation-delay:${n*0.15}s`" class="w-2 h-2 bg-blue-400 rounded-full animate-bounce"/>
                </div>
              </div>
            </div>
          </div>
          <!-- Chat input -->
          <div class="flex items-center gap-2 px-4 py-3 border-t border-slate-100">
            <input v-model="chatInput" type="text" placeholder="Ask about diagnosis, treatment, or next steps..." @keyup.enter="sendChat"
              class="flex-1 border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"/>
            <button @click="sendChat" :disabled="!chatInput.trim() || chatLoading"
              class="flex items-center justify-center w-10 h-10 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-xl transition">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
            </button>
          </div>
        </div>
      </div>

      <!-- ── SECTION 3: Plan of Action ── -->
      <div class="bg-white rounded-xl border border-slate-100 shadow-sm p-5">
        <h2 class="font-semibold text-slate-900 mb-4 flex items-center gap-2">
          <svg class="w-5 h-5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
          Plan of Action
          <span class="text-[10px] font-medium px-2 py-0.5 rounded-full bg-teal-50 text-teal-600 border border-teal-200">
            {{ auth.isDoctor ? 'Doctor Module' : 'Paramedic Module' }}
          </span>
        </h2>

        <!-- Immediate Measures -->
        <div class="mb-5">
          <h3 class="text-sm font-semibold text-slate-700 mb-3">Immediate Measures</h3>
          <ul class="space-y-2.5">
            <li v-for="(a, i) in immediateMeasures" :key="i" class="flex items-center gap-3">
              <div class="w-6 h-6 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
                <span class="text-xs font-bold text-green-700">{{ i + 1 }}</span>
              </div>
              <span class="text-sm text-slate-700">{{ a }}</span>
            </li>
          </ul>
        </div>

        <!-- Warning Signs — derived from the assessment's own AI flags (TB, cardiac, snakebite, meningitis, etc.) -->
        <div :class="['border rounded-xl p-4 mb-5', activeFlags.length ? 'bg-red-50/60 border-red-100' : 'bg-green-50/60 border-green-100']">
          <h3 :class="['text-sm font-semibold mb-2 flex items-center gap-2', activeFlags.length ? 'text-red-700' : 'text-green-700']">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
            Warning Signs
          </h3>
          <ul v-if="activeFlags.length" class="space-y-1.5">
            <li v-for="(flag, i) in activeFlags" :key="i"
              class="flex items-start gap-2 text-sm" :class="flag.level === 'critical' ? 'text-red-700' : 'text-orange-700'">
              <span :class="['w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0', flag.level === 'critical' ? 'bg-red-500' : 'bg-orange-500']"/>
              <span><span class="font-semibold">{{ flag.complaint }}:</span> {{ flag.message }}</span>
            </li>
          </ul>
          <p v-else class="text-sm text-green-700">No immediate warning signs detected</p>
        </div>

        <!-- Referral Required Decision -->
        <div>
          <h3 class="text-sm font-semibold text-slate-700 mb-3">Referral Required?</h3>
          <div class="flex gap-3 flex-wrap">
            <button v-for="opt in [
              { val: 'yes',     label: 'Yes — Refer',          cls: 'border-red-400 bg-red-50 text-red-700' },
              { val: 'no',      label: 'No — Manage Here',     cls: 'border-green-400 bg-green-50 text-green-700' },
            ]" :key="opt.val"
              :class="['px-5 py-2.5 rounded-xl border-2 text-sm font-semibold transition', referralDecision === opt.val ? opt.cls + ' ring-2 ring-offset-1 ring-blue-400' : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300']"
              @click="referralDecision = opt.val">
              {{ opt.label }}
            </button>
          </div>

          <!-- REFERRAL = YES: Hospitals + Ambulance -->
          <div v-if="referralDecision === 'yes'" class="mt-4 space-y-3">
            <!-- Call Ambulance -->
            <button @click="callAmbulance"
              class="w-full flex items-center justify-center gap-3 py-4 bg-red-600 hover:bg-red-700 text-white font-bold rounded-xl transition text-base animate-pulse-slow">
              <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><rect x="1" y="3" width="15" height="13" rx="2"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg>
              Call Ambulance — Dial 108
            </button>

            <!-- Nearby Hospitals (ordered by distance, govt first) -->
            <div>
              <div class="flex items-center justify-between mb-2">
                <h4 class="text-xs font-semibold text-slate-600 uppercase tracking-wide">Nearby Hospitals</h4>
                <button @click="openMap('hospitals near ' + (patient.address?.village || patient.location))" class="text-xs text-blue-600 hover:underline flex items-center gap-1">
                  View on Map
                  <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
                </button>
              </div>
              <div class="space-y-2.5">
                <div v-for="(h, i) in hospitals" :key="h.id"
                  :class="['flex items-center gap-3 rounded-xl border p-3', h.govt ? 'border-green-200 bg-green-50/50' : 'border-slate-100 bg-white']">
                  <div :class="['w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 text-white text-xs font-bold', h.govt ? 'bg-green-600' : 'bg-slate-600']">
                    {{ i + 1 }}
                  </div>
                  <div class="flex-1 min-w-0">
                    <div class="text-sm font-medium text-slate-800 truncate">{{ h.name }}</div>
                    <div class="flex items-center gap-2 mt-0.5">
                      <span :class="['text-xs px-2 py-0.5 rounded font-semibold', h.govt ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-600']">{{ h.type }}</span>
                      <span v-if="h.govt" class="text-xs text-green-600 font-medium">★ Recommended</span>
                    </div>
                  </div>
                  <div class="flex items-center gap-2 flex-shrink-0">
                    <span class="text-xs text-slate-500 font-medium">{{ h.distance }}</span>
                    <button @click="openMap(h.location)" class="w-7 h-7 rounded-full bg-blue-50 flex items-center justify-center hover:bg-blue-100 transition" title="View on map">
                      <svg class="w-3.5 h-3.5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
                    </button>
                    <button @click="callNumber(h.phone)" class="w-7 h-7 rounded-full bg-green-100 flex items-center justify-center hover:bg-green-200 transition" title="Call hospital">
                      <svg class="w-3.5 h-3.5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 13a19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 3.6 2.18h3a2 2 0 0 1 2 1.72c.1.96.32 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- REFERRAL = NO: Teleconsultation -->
          <div v-else-if="referralDecision === 'no'" class="mt-4">
            <h4 class="text-xs font-semibold text-slate-600 uppercase tracking-wide mb-2">{{ auth.isDoctor ? 'Available Specialist Doctors' : 'Available Doctors' }}</h4>
            <div class="space-y-2.5">
              <div v-for="d in doctors" :key="d.id"
                :class="['border rounded-xl p-3 flex items-center gap-3', d.available ? 'border-slate-100' : 'border-slate-100 opacity-60']">
                <div class="w-9 h-9 rounded-full bg-amber-100 flex items-center justify-center flex-shrink-0">
                  <svg class="w-4 h-4 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                </div>
                <div class="flex-1 min-w-0">
                  <div class="text-sm font-semibold text-slate-800">{{ d.name }}</div>
                  <div class="text-xs text-slate-500">{{ d.specialization }}</div>
                  <div class="flex items-center gap-1 mt-0.5">
                    <span :class="['w-1.5 h-1.5 rounded-full', d.available ? 'bg-green-500' : 'bg-slate-300']"/>
                    <span :class="['text-xs font-medium', d.available ? 'text-green-600' : 'text-slate-400']">{{ d.available ? 'Available' : 'Busy' }}</span>
                  </div>
                </div>
                <div v-if="d.available" class="flex items-center gap-2">
                  <button @click="callNumber(d.phone)" class="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center hover:bg-green-200 transition" title="Voice call">
                    <svg class="w-4 h-4 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 13a19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 3.6 2.18h3a2 2 0 0 1 2 1.72c.1.96.32 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
                  </button>
                  <button @click="startVideo()" class="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center hover:bg-blue-200 transition" title="Video call via Google Meet">
                    <svg class="w-4 h-4 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2"/></svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ── SECTION 4: Action Taken ── -->
      <div class="bg-white rounded-xl border border-slate-100 shadow-sm p-5">
        <h2 class="font-semibold text-slate-900 mb-4 flex items-center gap-2">
          <svg class="w-5 h-5 text-teal-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
          Action Taken
          <span class="text-xs font-normal text-slate-400">Record what was done</span>
        </h2>

        <transition enter-active-class="transition duration-300" enter-from-class="opacity-0 -translate-y-2">
          <div v-if="actionSubmitted" class="mb-4 px-4 py-3 bg-green-50 border border-green-200 text-green-700 rounded-xl text-sm flex items-center gap-2">
            <svg class="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M20 6L9 17l-5-5"/></svg>
            Actions recorded successfully.
          </div>
        </transition>

        <!-- Immediate measures taken -->
        <div class="mb-5">
          <h3 class="text-sm font-semibold text-slate-700 mb-3">Immediate Measures Implemented</h3>
          <div class="space-y-2">
            <label v-for="(a, i) in immediateMeasures" :key="i"
              class="flex items-center gap-3 px-3 py-2.5 rounded-xl cursor-pointer hover:bg-teal-50 transition"
              :class="actionTaken.measures[i] ? 'bg-teal-50 border border-teal-100' : 'bg-slate-50'">
              <input v-model="actionTaken.measures[i]" type="checkbox" class="w-4 h-4 rounded border-slate-300 text-teal-600 focus:ring-teal-500"/>
              <span :class="['text-sm', actionTaken.measures[i] ? 'text-teal-700 line-through decoration-teal-400' : 'text-slate-700']">{{ a }}</span>
            </label>
          </div>
        </div>

        <!-- Referral action details (if referral = yes) -->
        <div v-if="referralDecision === 'yes'" class="mb-5 p-4 bg-red-50/40 border border-red-100 rounded-xl space-y-3">
          <h3 class="text-sm font-semibold text-red-700">Referral Details</h3>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-medium text-slate-600 mb-1.5">Hospital Referred To</label>
              <select v-model="actionTaken.referralHospital"
                class="w-full border border-slate-200 rounded-xl px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="">— Select —</option>
                <option v-for="h in hospitals" :key="h.id" :value="h.id">{{ h.name }}</option>
              </select>
            </div>
            <div class="flex items-end">
              <label class="flex items-center gap-2 cursor-pointer text-sm text-slate-700">
                <input v-model="actionTaken.ambulanceCalled" type="checkbox" class="w-4 h-4 rounded border-slate-300 text-red-600"/>
                Ambulance (108) called
              </label>
            </div>
          </div>
        </div>

        <!-- Teleconsult action details (if no) -->
        <div v-if="referralDecision === 'no'" class="mb-5 p-4 bg-blue-50/40 border border-blue-100 rounded-xl space-y-3">
          <h3 class="text-sm font-semibold text-blue-700">Teleconsultation Details</h3>
          <div>
            <label class="block text-xs font-medium text-slate-600 mb-1.5">Doctor Consulted</label>
            <select v-model="actionTaken.teleconsultDoctor"
              class="w-full border border-slate-200 rounded-xl px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500">
              <option value="">— Select —</option>
              <option v-for="d in doctors.filter(d => d.available)" :key="d.id" :value="d.id">{{ d.name }}</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-medium text-slate-600 mb-1.5">Doctor's Advice / Instructions</label>
            <textarea v-model="actionTaken.teleconsultNotes" rows="2" placeholder="Note the advice given by the doctor..."
              class="w-full border border-slate-200 rounded-xl px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500" lang="auto"/>
          </div>
        </div>

        <!-- Additional notes -->
        <div class="mb-4">
          <label class="block text-xs font-medium text-slate-600 mb-1.5">Additional Notes</label>
          <textarea v-model="actionTaken.additionalNotes" rows="2" placeholder="Any other observations or actions taken..."
            class="w-full border border-slate-200 rounded-xl px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500" lang="auto"/>
        </div>

        <button @click="submitAction"
          class="flex items-center gap-2 px-6 py-2.5 bg-teal-600 hover:bg-teal-700 text-white text-sm font-semibold rounded-xl transition">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M20 6L9 17l-5-5"/></svg>
          Save Action Record
        </button>
      </div>

      <!-- ── Annotation + Version History ── -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div class="bg-white rounded-xl border border-slate-100 shadow-sm p-5">
          <div class="flex items-center justify-between mb-3">
            <h3 class="font-semibold text-slate-800 text-sm flex items-center gap-2">
              <svg class="w-4 h-4 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5z"/></svg>
              {{ t('annotation.label') }}
            </h3>
            <button v-if="!editingAnnotation" @click="startEditAnnotation"
              class="text-xs text-blue-600 border border-blue-200 px-2.5 py-1 rounded-xl hover:bg-blue-50 transition">
              {{ annotation ? t('annotation.edit') : t('common.add') }}
            </button>
          </div>
          <div v-if="!editingAnnotation">
            <p v-if="annotation" class="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">{{ annotation }}</p>
            <p v-else class="text-sm text-slate-400 italic">{{ t('annotation.add') }}</p>
          </div>
          <div v-else class="space-y-2">
            <textarea v-model="annotationDraft" rows="4" :placeholder="t('annotation.add')"
              class="w-full border border-slate-200 rounded-xl px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500" lang="auto"/>
            <div class="flex gap-2 justify-end">
              <button @click="editingAnnotation = false" class="px-3 py-1.5 text-xs border border-slate-200 text-slate-600 rounded-xl hover:bg-slate-50">{{ t('common.cancel') }}</button>
              <button @click="saveAnnotation" class="px-3 py-1.5 text-xs bg-blue-600 text-white rounded-xl hover:bg-blue-700">{{ t('annotation.save') }}</button>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl border border-slate-100 shadow-sm p-5">
          <h3 class="font-semibold text-slate-800 text-sm flex items-center gap-2 mb-3">
            <svg class="w-4 h-4 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M12 7v5l4 2"/></svg>
            {{ t('version.history') }}
          </h3>
          <div v-if="versionHistory.length === 0" class="text-xs text-slate-400 italic">{{ t('version.noHistory') }}</div>
          <div v-else class="space-y-2 max-h-40 overflow-y-auto">
            <div v-for="(v, i) in versionHistory" :key="i" class="flex items-center justify-between bg-slate-50 rounded-xl px-3 py-2">
              <div>
                <div class="text-xs font-medium text-slate-700">{{ v.ts }}</div>
                <div class="text-[10px] text-slate-400">{{ i === 0 ? t('version.current') : `v${versionHistory.length - i}` }}</div>
              </div>
              <span v-if="i === 0" class="text-[10px] px-2 py-0.5 bg-blue-100 text-blue-600 rounded font-semibold">{{ t('version.current') }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Share panel -->
      <div class="bg-white rounded-xl border border-slate-100 shadow-sm px-5 py-4 flex items-center gap-3 flex-wrap">
        <span class="text-sm font-medium text-slate-700">{{ t('notif.channel') }}:</span>
        <button @click="sendWhatsApp(patient)"
          class="flex items-center gap-2 px-4 py-2 bg-green-500 hover:bg-green-600 text-white text-xs font-semibold rounded-xl transition">
          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893A11.821 11.821 0 0020.885 3.488"/></svg>
          {{ t('notif.sendWhatsapp') }}
        </button>
        <button @click="sendEmail(patient)"
          class="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-xl transition">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
          {{ t('notif.sendEmail') }}
        </button>
      </div>

      <!-- Disclaimer + proceed -->
      <div class="flex items-center justify-between flex-wrap gap-3">
        <div class="flex items-center gap-2 text-xs text-blue-600 bg-blue-50 border border-blue-100 rounded-xl px-4 py-2.5">
          <svg class="w-4 h-4 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm1 15h-2v-6h2zm0-8h-2V7h2z"/></svg>
          AI-generated analysis. A qualified healthcare professional should review before final diagnosis.
        </div>
        <button @click="router.push(`/assessment/${patientId}/measures`)"
          class="flex items-center gap-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-xl transition flex-shrink-0">
          {{ t('result.recordMeasures') }}
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
        </button>
      </div>
    </div>
  </AppShell>
</template>
