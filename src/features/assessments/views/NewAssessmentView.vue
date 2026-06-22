<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import AppShell from '@/shared/components/AppShell.vue'
import { usePatientsStore } from '@/features/patients/stores/patients'
import { useAuthStore } from '@/features/auth/stores/auth'
import { useI18n } from '@/i18n'
import { COMPLAINTS_DEF, COMPLAINT_COLOR_MAP } from '@/features/assessments/constants/complaintsDef'

const router = useRouter()
const route  = useRoute()
const store  = usePatientsStore()
const auth   = useAuthStore()
const { t }  = useI18n()

const isEdit    = computed(() => route.name === 'EditAssessment')
const patientId = computed(() => isEdit.value ? Number(route.params.id) : null)
const patient   = computed(() => isEdit.value ? store.getById(patientId.value) : null)

const linkedPatientId = computed(() => route.query.patientId ? Number(route.query.patientId) : null)
const linkedPatient   = computed(() => linkedPatientId.value ? store.getById(linkedPatientId.value) : null)

const isDoctor = computed(() => auth.user?.role === 'Doctor' || auth.user?.role === 'ANM')

// ── Section visibility ────────────────────────────────────────────────────────
const sections = ref({ basic: true, complaints: false, pastHistory: false, familyHistory: false, examination: false })
function toggleSection(key) { sections.value[key] = !sections.value[key] }

// ── Basic Info ────────────────────────────────────────────────────────────────
const form = reactive({
  fullName: '', age: '', gender: '', phone: '', location: '', abhaId: '',
})

// ── Complaints ────────────────────────────────────────────────────────────────
const selectedComplaintIds = ref([])
const complaintDetails     = reactive({})

function blankComplaintDetail() {
  return { onset: '', duration: '', severity: '', symptoms: [], jointsInvolved: '', complaintDescription: '', otherDetails: '' }
}

function toggleComplaint(id) {
  const idx = selectedComplaintIds.value.indexOf(id)
  if (idx >= 0) {
    selectedComplaintIds.value.splice(idx, 1)
    delete complaintDetails[id]
  } else {
    selectedComplaintIds.value.push(id)
    complaintDetails[id] = blankComplaintDetail()
    // Auto-select single-option onset (e.g. wound, animal bite)
    const def = COMPLAINTS_DEF.find(c => c.id === id)
    if (def?.onsetOptions?.length === 1) complaintDetails[id].onset = def.onsetOptions[0]
  }
}

function getComplaintDef(id) { return COMPLAINTS_DEF.find(c => c.id === id) }

// Active AI flags from duration + symptom selections
const activeFlags = computed(() => {
  const flags = []
  for (const id of selectedComplaintIds.value) {
    const def    = getComplaintDef(id)
    const detail = complaintDetails[id]
    if (!def || !detail) continue
    const durOpt = def.durationOptions?.find(d => d.label === detail.duration)
    if (durOpt?.flag) flags.push({ complaint: def.label, message: durOpt.flag, level: durOpt.flagLevel || 'warning' })
    if (def.symptomFlags && detail.symptoms?.length) {
      for (const sym of detail.symptoms) {
        if (def.symptomFlags[sym]) flags.push({ complaint: def.label, ...def.symptomFlags[sym] })
      }
    }
  }
  return flags
})

// ── Past History ──────────────────────────────────────────────────────────────
const pastHistory = reactive({
  hasSimilar: false,
  similarDiagnosis: '',
  similarCount: '',
  similarMedications: '',
  alcohol: { present: false, duration: '', frequency: '', status: '' },
  tobacco: { present: false, duration: '', frequency: '', status: '' },
  conditions: {
    hypertension:    { present: false, diagDuration: '', currentStatus: '', adherence: '' },
    diabetes:        { present: false, diagDuration: '', currentStatus: '', adherence: '', type: '' },
    asthma:          { present: false, diagDuration: '', currentStatus: '', adherence: '' },
    highCholesterol: { present: false, diagDuration: '', currentStatus: '', adherence: '' },
    allergy:         { present: false, allergen: '', diagDuration: '', currentStatus: '', adherence: '' },
    otherDiseases:   [],
  },
  surgeries: '',
})

const newOtherDisease = ref('')
function addOtherDisease() {
  if (!newOtherDisease.value.trim()) return
  pastHistory.conditions.otherDiseases.push({ name: newOtherDisease.value.trim(), diagDuration: '', currentStatus: '', adherence: '' })
  newOtherDisease.value = ''
}
function removeOtherDisease(i) { pastHistory.conditions.otherDiseases.splice(i, 1) }

const DIAG_DURATIONS  = ['< 1 year', '1 - 5 years', '> 5 years']
const STATUSES        = ['Controlled', 'Uncontrolled', 'Unknown']
const ADHERENCES      = ['Regularly taking prescribed medicine', 'Irregularly taking medicine', 'Stopped taking medicine', 'Relying on alternative home remedies']
const ALCOHOL_DURATIONS  = ['< 1 year', '1 - 5 years', '> 5 years']
const ALCOHOL_FREQS      = ['< 2 times a week', '> 2 times a week', 'Daily']
const TOBACCO_FREQS      = ['< 2 per day', '2 - 5 per day', '> 5 per day']

// ── Family History ────────────────────────────────────────────────────────────
const FAMILY_RELATIONS = ['Father', 'Mother', 'Sibling', 'Spouse', 'Child', 'Grandparent', 'Uncle/Aunt']

const familyHistory = reactive({
  sameHouseComplaints: { present: false, complaints: [], duration: '' },
  diseases: {
    hypertension:    { present: false, relations: [] },
    diabetes:        { present: false, relations: [] },
    tb:              { present: false, relations: [] },
    highCholesterol: { present: false, relations: [] },
    thyroid:         { present: false, relations: [] },
    others:          [],
  },
})

const newFamilyOther = reactive({ name: '', relation: '' })
function addFamilyOther() {
  if (!newFamilyOther.name.trim()) return
  familyHistory.diseases.others.push({ name: newFamilyOther.name.trim(), relation: newFamilyOther.relation })
  newFamilyOther.name = ''; newFamilyOther.relation = ''
}
function toggleFamilyRelation(disease, relation) {
  const list = familyHistory.diseases[disease].relations
  const idx  = list.indexOf(relation)
  if (idx >= 0) list.splice(idx, 1)
  else list.push(relation)
}
function toggleSameHouseComplaint(label) {
  const list = familyHistory.sameHouseComplaints.complaints
  const idx  = list.indexOf(label)
  if (idx >= 0) list.splice(idx, 1)
  else list.push(label)
}

// ── Attached Documents ────────────────────────────────────────────────────────
const attachedDocs = ref([])
function handleDocAttach(e) {
  const files = Array.from(e.target.files || [])
  files.forEach(file => {
    const reader = new FileReader()
    reader.onload = (ev) => { attachedDocs.value.push({ name: file.name, size: file.size, data: ev.target.result }) }
    reader.readAsDataURL(file)
  })
}
function removeDoc(i) { attachedDocs.value.splice(i, 1) }

// ── Examination ───────────────────────────────────────────────────────────────
const examForm = reactive({
  height: '', weight: '',
  temperature: '',
  eyeDiscolouration: false, rashes: false, swelling: false, dehydration: false,
  generalOther: '',
  examPhoto: '',
  specificFindings: '',
  systemicExam: '',
  clinicalNotes: '',
})

function handleExamPhoto(e) {
  const file = e.target.files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = (ev) => { examForm.examPhoto = ev.target.result }
  reader.readAsDataURL(file)
}

// ── Vitals ────────────────────────────────────────────────────────────────────
const vitals = reactive({
  bpSystolic: '', bpDiastolic: '',
  heartRate: '', respiratoryRate: '', temperature: '', spo2: '', rbs: '',
})

// ── Draft ─────────────────────────────────────────────────────────────────────
const draftKey    = computed(() => isEdit.value ? `assessment_draft_${patientId.value}` : 'assessment_draft_new')
const savingDraft = ref(false)
const draftSaved  = ref(false)

function buildSnapshot() {
  return {
    form: { ...form },
    complaints: { selected: [...selectedComplaintIds.value], details: JSON.parse(JSON.stringify(complaintDetails)) },
    pastHistory: JSON.parse(JSON.stringify(pastHistory)),
    familyHistory: JSON.parse(JSON.stringify(familyHistory)),
    examForm: { ...examForm }, vitals: { ...vitals },
  }
}

function applySnapshot(d) {
  if (d.form)        Object.assign(form, d.form)
  if (d.complaints?.selected) {
    selectedComplaintIds.value = d.complaints.selected
    if (d.complaints.details) Object.assign(complaintDetails, d.complaints.details)
  }
  if (d.pastHistory)   Object.assign(pastHistory, d.pastHistory)
  if (d.familyHistory) Object.assign(familyHistory, d.familyHistory)
  if (d.examForm)      Object.assign(examForm, d.examForm)
  if (d.vitals)        Object.assign(vitals, d.vitals)
}

onMounted(() => {
  if (isEdit.value && patient.value) {
    const p = patient.value
    form.fullName = p.name || ''; form.age = String(p.age || ''); form.gender = p.gender || ''
    form.phone = p.phone || ''; form.location = p.location || ''; form.abhaId = p.abhaId || ''
    const last = p.assessmentHistory?.[0]
    if (last) {
      if (last.complaints?.selected) {
        selectedComplaintIds.value = last.complaints.selected
        if (last.complaints.details) Object.assign(complaintDetails, last.complaints.details)
      }
      if (last.pastHistory)   Object.assign(pastHistory, last.pastHistory)
      if (last.familyHistory) Object.assign(familyHistory, last.familyHistory)
      if (last.examForm)      Object.assign(examForm, last.examForm)
      if (last.vitals)        Object.assign(vitals, last.vitals)
    }
  } else if (linkedPatient.value) {
    const p = linkedPatient.value
    form.fullName = p.name || ''; form.age = String(p.age || ''); form.gender = p.gender || ''
    form.phone = p.phone || ''
    form.location = [p.address?.village, p.address?.district].filter(Boolean).join(', ') || p.location || ''
    form.abhaId = p.abhaId || ''
    sections.value.basic = false; sections.value.complaints = true
  } else {
    const saved = localStorage.getItem(draftKey.value)
    if (saved) { try { applySnapshot(JSON.parse(saved)) } catch {} }
  }
})

function saveDraft() {
  savingDraft.value = true
  localStorage.setItem(draftKey.value, JSON.stringify(buildSnapshot()))
  setTimeout(() => { savingDraft.value = false; draftSaved.value = true }, 400)
  setTimeout(() => { draftSaved.value = false }, 2200)
}

function saveVersion(id) {
  const key  = `assessment_versions_${id}`
  const prev = JSON.parse(localStorage.getItem(key) || '[]')
  const now  = new Date()
  const ts   = now.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) +
               ', ' + now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true })
  prev.push({ ts, form: { ...form }, vitals: { ...vitals } })
  localStorage.setItem(key, JSON.stringify(prev.slice(-10)))
}

function analyze() {
  const now = new Date()
  const assessmentTime = now.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) +
    ', ' + now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true })
  const primaryComplaint = selectedComplaintIds.value
    .map(id => COMPLAINTS_DEF.find(c => c.id === id)?.label)
    .filter(Boolean)[0] || 'General Assessment'

  const fullData = {
    name: form.fullName, age: Number(form.age), gender: form.gender,
    phone: form.phone, location: form.location, abhaId: form.abhaId, assessmentTime,
    primaryComplaint,
    complaints: { selected: [...selectedComplaintIds.value], details: JSON.parse(JSON.stringify(complaintDetails)) },
    pastHistory: JSON.parse(JSON.stringify(pastHistory)),
    familyHistory: JSON.parse(JSON.stringify(familyHistory)),
    examForm: { ...examForm }, vitals: { ...vitals },
  }
  if (isEdit.value) {
    saveVersion(patientId.value)
    store.addAssessment(patientId.value, fullData)
    localStorage.removeItem(draftKey.value)
    router.push(`/patients/${patientId.value}`)
  } else if (linkedPatientId.value) {
    saveVersion(linkedPatientId.value)
    store.addAssessment(linkedPatientId.value, fullData)
    localStorage.removeItem(draftKey.value)
    router.push(`/patients/${linkedPatientId.value}`)
  } else {
    const newId = store.add(fullData)
    saveVersion(newId)
    localStorage.removeItem(draftKey.value)
    router.push(`/assessment/${newId}/result`)
  }
}

// ── Style constants ───────────────────────────────────────────────────────────
const IC  = 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500'
const TC  = 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none'
const LC  = 'block text-xs font-medium text-gray-600 mb-1.5'
const SEL = ' bg-white'
</script>

<template>
  <AppShell>
    <template #page-title>{{ isEdit ? t('assessment.edit') : t('assessment.new') }}</template>
    <template #page-subtitle>{{ isEdit ? (patient?.name || '') : linkedPatient ? linkedPatient.name : 'Patient complaint, history & examination' }}</template>

    <div class="p-4 md:p-6">
      <button @click="router.back()" class="flex items-center gap-1.5 text-sm text-blue-600 hover:underline mb-5">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 5l-7 7 7 7"/></svg>
        {{ t('common.back') }}
      </button>

      <!-- Linked patient banner -->
      <div v-if="linkedPatient" class="mb-4 bg-green-50 border border-green-200 rounded-xl px-5 py-3.5 flex items-center gap-4 flex-wrap">
        <div class="w-9 h-9 rounded-full bg-green-100 flex items-center justify-center text-sm font-bold text-green-700 flex-shrink-0">
          {{ linkedPatient.name.split(' ').map(n=>n[0]).join('').slice(0,2).toUpperCase() }}
        </div>
        <div class="flex-1 min-w-0">
          <div class="text-xs text-green-600 font-semibold uppercase tracking-wide mb-0.5">Patient Registered</div>
          <div class="text-sm font-semibold text-gray-800">{{ linkedPatient.name }} · {{ linkedPatient.age }} yrs · {{ linkedPatient.gender }}</div>
          <div class="text-xs text-gray-500">{{ linkedPatient.phone }} · {{ linkedPatient.address?.village || linkedPatient.location }}</div>
        </div>
        <button @click="router.push('/patients')" class="text-xs text-green-700 underline">View All Patients</button>
      </div>

      <!-- AI flags banner -->
      <div v-if="activeFlags.length" class="mb-4 space-y-2">
        <div v-for="(flag, i) in activeFlags" :key="i"
          :class="['flex items-start gap-3 px-4 py-3 rounded-xl border text-sm font-medium',
            flag.level === 'critical'
              ? 'bg-red-50 border-red-300 text-red-800'
              : 'bg-yellow-50 border-yellow-300 text-yellow-800']">
          <svg class="w-4 h-4 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path d="M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
          </svg>
          <span><span class="font-semibold">{{ flag.complaint }}:</span> {{ flag.message }}</span>
        </div>
      </div>

      <div class="flex gap-6">
        <!-- ── Left: form sections ── -->
        <div class="flex-1 min-w-0 space-y-4">

          <!-- Header strip -->
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm px-5 py-4 flex items-center gap-6 flex-wrap">
            <div class="flex items-center gap-3">
              <div class="w-9 h-9 rounded-full bg-blue-100 flex items-center justify-center">
                <svg class="w-5 h-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
              </div>
              <div>
                <div class="text-xs text-gray-500">Patient ID</div>
                <div class="text-sm font-semibold text-gray-800">
                  {{ isEdit ? `PT-2025-${String(patientId).padStart(6,'0')}` : linkedPatientId ? `PT-2025-${String(linkedPatientId).padStart(6,'0')}` : 'Auto-assigned on save' }}
                </div>
              </div>
            </div>
            <div class="ml-auto text-right text-xs text-gray-500">
              <div class="font-medium text-gray-700">Date &amp; Time</div>
              <div>{{ new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) }}, {{ new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true }) }}</div>
            </div>
            <div class="text-right text-xs">
              <div class="text-gray-500 mb-1">Type</div>
              <span class="px-2.5 py-1 bg-blue-50 text-blue-600 border border-blue-200 text-xs font-medium rounded-md">{{ isEdit ? 'Edit' : 'New' }}</span>
            </div>
          </div>

          <!-- ① Basic Patient Info -->
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
            <button class="w-full flex items-center justify-between px-5 py-4" @click="toggleSection('basic')">
              <div class="flex items-center gap-3">
                <svg class="w-5 h-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                <span class="font-semibold text-gray-800">{{ t('assessment.basicInfo') }}</span>
              </div>
              <svg :class="['w-5 h-5 text-gray-400 transition-transform', sections.basic ? 'rotate-180' : '']" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M19 9l-7 7-7-7"/></svg>
            </button>
            <div v-if="sections.basic" class="px-5 pb-5 space-y-4">
              <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <div class="col-span-2 lg:col-span-1">
                  <label :class="LC">{{ t('assessment.fullName') }} <span class="text-red-500">*</span></label>
                  <input v-model="form.fullName" type="text" :placeholder="t('assessment.fullName')" :class="IC" lang="auto"/>
                </div>
                <div>
                  <label :class="LC">{{ t('assessment.age') }} <span class="text-red-500">*</span></label>
                  <input v-model="form.age" type="number" min="0" max="120" placeholder="Years" :class="IC"/>
                </div>
                <div>
                  <label :class="LC">{{ t('assessment.gender') }} <span class="text-red-500">*</span></label>
                  <select v-model="form.gender" :class="IC + SEL">
                    <option value="">—</option>
                    <option value="Male">{{ t('assessment.genderMale') }}</option>
                    <option value="Female">{{ t('assessment.genderFemale') }}</option>
                    <option value="Other">{{ t('assessment.genderOther') }}</option>
                  </select>
                </div>
                <div>
                  <label :class="LC">{{ t('assessment.phone') }}</label>
                  <input v-model="form.phone" type="tel" maxlength="10" placeholder="10-digit" :class="IC"/>
                </div>
              </div>
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label :class="LC">{{ t('assessment.location') }}</label>
                  <input v-model="form.location" type="text" :placeholder="t('assessment.location')" :class="IC" lang="auto"/>
                </div>
                <div>
                  <label :class="LC">{{ t('assessment.abhaId') }}</label>
                  <input v-model="form.abhaId" type="text" placeholder="12-XXXX-XXXX-XXXX" :class="IC"/>
                </div>
              </div>
            </div>
          </div>

          <!-- ② Chief Complaints -->
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
            <button class="w-full flex items-center justify-between px-5 py-4" @click="toggleSection('complaints')">
              <div class="flex items-center gap-3">
                <svg class="w-5 h-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
                <span class="font-semibold text-gray-800">Patient Complaints</span>
                <span class="text-xs bg-red-100 text-red-600 px-2 py-0.5 rounded-full font-medium">Select all that apply</span>
              </div>
              <div class="flex items-center gap-2">
                <span v-if="selectedComplaintIds.length" class="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full font-semibold">{{ selectedComplaintIds.length }} selected</span>
                <svg :class="['w-5 h-5 text-gray-400 transition-transform', sections.complaints ? 'rotate-180' : '']" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M19 9l-7 7-7-7"/></svg>
              </div>
            </button>

            <div v-if="sections.complaints" class="px-5 pb-5 space-y-5">
              <!-- Complaint selector grid -->
              <div>
                <p class="text-xs text-gray-500 mb-3">Tap a complaint to select it. Selected complaints expand for detailed assessment below.</p>
                <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
                  <button
                    v-for="def in COMPLAINTS_DEF" :key="def.id"
                    type="button"
                    @click="toggleComplaint(def.id)"
                    :class="['flex items-center gap-2 px-3 py-2.5 rounded-xl border text-left transition text-sm font-medium',
                      selectedComplaintIds.includes(def.id)
                        ? (COMPLAINT_COLOR_MAP[def.color]?.selected + ' ' + COMPLAINT_COLOR_MAP[def.color]?.text)
                        : 'border-gray-200 text-gray-700 hover:bg-gray-50']">
                    <span :class="['w-2 h-2 rounded-full flex-shrink-0', selectedComplaintIds.includes(def.id) ? 'bg-current' : 'bg-gray-300']"></span>
                    {{ def.label }}
                  </button>
                </div>
              </div>

              <!-- Detail panels for each selected complaint -->
              <div v-if="selectedComplaintIds.length" class="space-y-4">
                <div class="text-xs font-semibold text-gray-500 uppercase tracking-wide border-t border-gray-100 pt-4">Complaint Details</div>

                <div v-for="id in selectedComplaintIds" :key="id"
                  :class="['border rounded-xl overflow-hidden', COMPLAINT_COLOR_MAP[getComplaintDef(id)?.color]?.border]">
                  <!-- Panel header -->
                  <div :class="['px-4 py-3 flex items-center gap-2', COMPLAINT_COLOR_MAP[getComplaintDef(id)?.color]?.bg]">
                    <span :class="['text-sm font-semibold', COMPLAINT_COLOR_MAP[getComplaintDef(id)?.color]?.text]">{{ getComplaintDef(id)?.label }}</span>
                    <button @click="toggleComplaint(id)" class="ml-auto text-gray-400 hover:text-red-500 transition">
                      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18M6 6l12 12"/></svg>
                    </button>
                  </div>

                  <div class="px-4 py-4 bg-white space-y-4">
                    <!-- Open-ended description (complaint #19) -->
                    <div v-if="getComplaintDef(id)?.isOpenEnded">
                      <label :class="LC">Describe the complaint <span class="text-red-500">*</span></label>
                      <textarea v-model="complaintDetails[id].complaintDescription" rows="2" placeholder="Describe the complaint in the patient's own words..." :class="TC" lang="auto"/>
                    </div>

                    <!-- Onset -->
                    <div v-if="(getComplaintDef(id)?.onsetOptions?.length || 0) > 1">
                      <label :class="LC">Onset</label>
                      <div class="flex flex-wrap gap-2">
                        <label v-for="opt in getComplaintDef(id).onsetOptions" :key="opt"
                          :class="['flex items-center gap-2 px-3 py-2 rounded-lg border cursor-pointer transition text-sm',
                            complaintDetails[id].onset === opt ? 'bg-blue-50 border-blue-400 text-blue-800' : 'border-gray-200 text-gray-700 hover:bg-gray-50']">
                          <input type="radio" v-model="complaintDetails[id].onset" :value="opt" class="w-3.5 h-3.5 text-blue-600 accent-blue-600"/>
                          {{ opt }}
                        </label>
                      </div>
                    </div>
                    <div v-else-if="(getComplaintDef(id)?.onsetOptions?.length || 0) === 1">
                      <label :class="LC">Onset</label>
                      <span class="text-sm text-gray-700 bg-gray-50 px-3 py-2 rounded-lg border border-gray-200 inline-block">{{ getComplaintDef(id).onsetOptions[0] }}</span>
                    </div>

                    <!-- Duration -->
                    <div>
                      <label :class="LC">Duration</label>
                      <div class="flex flex-wrap gap-2">
                        <label v-for="opt in getComplaintDef(id)?.durationOptions" :key="opt.label"
                          :class="['flex items-center gap-2 px-3 py-2 rounded-lg border cursor-pointer transition text-sm',
                            complaintDetails[id].duration === opt.label ? 'bg-blue-50 border-blue-400 text-blue-800' : 'border-gray-200 text-gray-700 hover:bg-gray-50']">
                          <input type="radio" v-model="complaintDetails[id].duration" :value="opt.label" class="w-3.5 h-3.5 text-blue-600 accent-blue-600"/>
                          <span>{{ opt.label }}</span>
                          <span v-if="opt.flag" class="text-[10px] bg-yellow-100 text-yellow-700 px-1.5 py-0.5 rounded font-medium">AI Flag</span>
                        </label>
                      </div>
                    </div>

                    <!-- Severity -->
                    <div>
                      <label :class="LC">Severity</label>
                      <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
                        <label v-for="opt in getComplaintDef(id)?.severityOptions" :key="opt.label"
                          :class="['flex items-start gap-2 p-3 rounded-lg border cursor-pointer transition',
                            complaintDetails[id].severity === opt.label
                              ? (opt.label === 'Severe' ? 'bg-red-50 border-red-400' : opt.label === 'Moderate' ? 'bg-yellow-50 border-yellow-400' : 'bg-green-50 border-green-400')
                              : 'border-gray-200 hover:bg-gray-50']">
                          <input type="radio" v-model="complaintDetails[id].severity" :value="opt.label"
                            :class="['w-3.5 h-3.5 mt-0.5 flex-shrink-0', opt.label === 'Severe' ? 'accent-red-600' : opt.label === 'Moderate' ? 'accent-yellow-600' : 'accent-green-600']"/>
                          <div>
                            <div :class="['text-sm font-semibold', opt.label === 'Severe' ? 'text-red-700' : opt.label === 'Moderate' ? 'text-yellow-700' : 'text-green-700']">{{ opt.label }}</div>
                            <div v-if="opt.description" class="text-xs text-gray-500 mt-0.5">{{ opt.description }}</div>
                          </div>
                        </label>
                      </div>
                    </div>

                    <!-- Associated Symptoms -->
                    <div v-if="getComplaintDef(id)?.symptoms?.length">
                      <label :class="LC">Associated Symptoms</label>
                      <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        <label v-for="sym in getComplaintDef(id).symptoms" :key="sym"
                          :class="['flex items-start gap-2 px-3 py-2.5 rounded-lg border cursor-pointer transition text-sm',
                            complaintDetails[id].symptoms?.includes(sym)
                              ? 'bg-blue-50 border-blue-300 text-blue-800'
                              : 'border-gray-200 text-gray-700 hover:bg-gray-50']">
                          <input type="checkbox" v-model="complaintDetails[id].symptoms" :value="sym" class="w-4 h-4 rounded text-blue-600 accent-blue-600 mt-0.5 flex-shrink-0"/>
                          <span>{{ sym }}</span>
                        </label>
                      </div>
                    </div>

                    <!-- Joints involved (body aches) -->
                    <div v-if="getComplaintDef(id)?.hasJointsField">
                      <label :class="LC">Joints Involved (describe)</label>
                      <input v-model="complaintDetails[id].jointsInvolved" type="text" placeholder="e.g. Both knees, right shoulder, lower back" :class="IC" lang="auto"/>
                    </div>

                    <!-- Other details (open-ended) -->
                    <div v-if="getComplaintDef(id)?.isOpenEnded">
                      <label :class="LC">Additional Details</label>
                      <textarea v-model="complaintDetails[id].otherDetails" rows="2" placeholder="Any additional details about this complaint..." :class="TC" lang="auto"/>
                    </div>
                  </div>
                </div>
              </div>

              <div v-if="!selectedComplaintIds.length" class="text-center py-8 text-gray-400 text-sm border-2 border-dashed border-gray-200 rounded-xl">
                No complaints selected. Tap complaint cards above to begin.
              </div>
            </div>
          </div>

          <!-- ③ Past History -->
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
            <button class="w-full flex items-center justify-between px-5 py-4" @click="toggleSection('pastHistory')">
              <div class="flex items-center gap-3">
                <svg class="w-5 h-5 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                <span class="font-semibold text-gray-800">Past History</span>
              </div>
              <svg :class="['w-5 h-5 text-gray-400 transition-transform', sections.pastHistory ? 'rotate-180' : '']" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M19 9l-7 7-7-7"/></svg>
            </button>
            <div v-if="sections.pastHistory" class="px-5 pb-5 space-y-5">

              <!-- Similar complaints in past 2 years -->
              <div class="p-4 bg-orange-50/40 border border-orange-100 rounded-xl space-y-3">
                <label class="flex items-center gap-3 cursor-pointer">
                  <input v-model="pastHistory.hasSimilar" type="checkbox" class="w-4 h-4 rounded border-gray-300 text-blue-600 accent-blue-600"/>
                  <span class="text-sm font-medium text-gray-700">History of similar complaints in the past 2 years</span>
                </label>
                <div v-if="pastHistory.hasSimilar" class="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
                  <div>
                    <label :class="LC">Any diagnosis known</label>
                    <input v-model="pastHistory.similarDiagnosis" type="text" placeholder="e.g. Dengue, Typhoid" :class="IC" lang="auto"/>
                  </div>
                  <div>
                    <label :class="LC">How many times</label>
                    <input v-model="pastHistory.similarCount" type="text" placeholder="e.g. Once, 3 times" :class="IC"/>
                  </div>
                  <div>
                    <label :class="LC">Medications / treatment taken</label>
                    <input v-model="pastHistory.similarMedications" type="text" placeholder="e.g. Paracetamol, hospitalized" :class="IC" lang="auto"/>
                  </div>
                </div>
              </div>

              <!-- Alcohol -->
              <div class="border border-gray-100 rounded-xl overflow-hidden">
                <label class="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-gray-50 transition">
                  <input v-model="pastHistory.alcohol.present" type="checkbox" class="w-4 h-4 rounded border-gray-300 text-blue-600 accent-blue-600"/>
                  <span class="text-sm font-medium text-gray-700 flex-1">History of Alcohol consumption</span>
                </label>
                <div v-if="pastHistory.alcohol.present" class="px-4 pb-4 pt-0 grid grid-cols-3 gap-3">
                  <div>
                    <label :class="LC">Duration</label>
                    <select v-model="pastHistory.alcohol.duration" :class="IC + SEL">
                      <option value="">— Select —</option>
                      <option v-for="d in ALCOHOL_DURATIONS" :key="d">{{ d }}</option>
                    </select>
                  </div>
                  <div>
                    <label :class="LC">Frequency</label>
                    <select v-model="pastHistory.alcohol.frequency" :class="IC + SEL">
                      <option value="">— Select —</option>
                      <option v-for="f in ALCOHOL_FREQS" :key="f">{{ f }}</option>
                    </select>
                  </div>
                  <div>
                    <label :class="LC">Current Status</label>
                    <select v-model="pastHistory.alcohol.status" :class="IC + SEL">
                      <option value="">— Select —</option>
                      <option>Continuing</option>
                      <option>Quit</option>
                    </select>
                  </div>
                </div>
              </div>

              <!-- Tobacco -->
              <div class="border border-gray-100 rounded-xl overflow-hidden">
                <label class="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-gray-50 transition">
                  <input v-model="pastHistory.tobacco.present" type="checkbox" class="w-4 h-4 rounded border-gray-300 text-blue-600 accent-blue-600"/>
                  <span class="text-sm font-medium text-gray-700 flex-1">History of Tobacco consumption</span>
                </label>
                <div v-if="pastHistory.tobacco.present" class="px-4 pb-4 pt-0 grid grid-cols-3 gap-3">
                  <div>
                    <label :class="LC">Duration</label>
                    <select v-model="pastHistory.tobacco.duration" :class="IC + SEL">
                      <option value="">— Select —</option>
                      <option v-for="d in ALCOHOL_DURATIONS" :key="d">{{ d }}</option>
                    </select>
                  </div>
                  <div>
                    <label :class="LC">Frequency</label>
                    <select v-model="pastHistory.tobacco.frequency" :class="IC + SEL">
                      <option value="">— Select —</option>
                      <option v-for="f in TOBACCO_FREQS" :key="f">{{ f }}</option>
                    </select>
                  </div>
                  <div>
                    <label :class="LC">Current Status</label>
                    <select v-model="pastHistory.tobacco.status" :class="IC + SEL">
                      <option value="">— Select —</option>
                      <option>Continuing</option>
                      <option>Quit</option>
                    </select>
                  </div>
                </div>
              </div>

              <!-- Known Conditions -->
              <div>
                <h4 class="text-sm font-semibold text-gray-700 mb-3">Known Conditions</h4>
                <div class="space-y-3">
                  <!-- Reusable condition sub-fields template -->
                  <template v-for="[key, label] in [
                    ['hypertension', 'Hypertension (High Blood Pressure)'],
                    ['diabetes',     'Diabetes Mellitus'],
                    ['asthma',       'Asthma / Respiratory illness'],
                    ['highCholesterol', 'High Cholesterol (Dyslipidaemia)'],
                    ['allergy',      'Known Allergies'],
                  ]" :key="key">
                    <div class="border border-gray-100 rounded-xl overflow-hidden">
                      <label class="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-gray-50 transition">
                        <input v-model="pastHistory.conditions[key].present" type="checkbox" class="w-4 h-4 rounded border-gray-300 text-blue-600 accent-blue-600"/>
                        <span class="text-sm font-medium text-gray-700 flex-1">{{ label }}</span>
                      </label>
                      <div v-if="pastHistory.conditions[key].present" class="px-4 pb-4 pt-1 space-y-3">
                        <!-- Diabetes type -->
                        <div v-if="key === 'diabetes'" class="grid grid-cols-2 gap-3">
                          <div>
                            <label :class="LC">Type</label>
                            <select v-model="pastHistory.conditions.diabetes.type" :class="IC + SEL">
                              <option value="">—</option><option>Type 1</option><option>Type 2</option><option>Gestational</option>
                            </select>
                          </div>
                        </div>
                        <!-- Allergy allergen -->
                        <div v-if="key === 'allergy'">
                          <label :class="LC">Allergen</label>
                          <input v-model="pastHistory.conditions.allergy.allergen" type="text" placeholder="e.g. Penicillin, dust, peanuts" :class="IC" lang="auto"/>
                        </div>
                        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
                          <div>
                            <label :class="LC">Duration of diagnosis</label>
                            <select v-model="pastHistory.conditions[key].diagDuration" :class="IC + SEL">
                              <option value="">— Select —</option>
                              <option v-for="d in DIAG_DURATIONS" :key="d">{{ d }}</option>
                            </select>
                          </div>
                          <div>
                            <label :class="LC">Current status</label>
                            <select v-model="pastHistory.conditions[key].currentStatus" :class="IC + SEL">
                              <option value="">— Select —</option>
                              <option v-for="s in STATUSES" :key="s">{{ s }}</option>
                            </select>
                          </div>
                          <div>
                            <label :class="LC">Medication adherence</label>
                            <select v-model="pastHistory.conditions[key].adherence" :class="IC + SEL">
                              <option value="">— Select —</option>
                              <option v-for="a in ADHERENCES" :key="a">{{ a }}</option>
                            </select>
                          </div>
                        </div>
                      </div>
                    </div>
                  </template>

                  <!-- Other diseases -->
                  <div class="border border-gray-100 rounded-xl overflow-hidden p-4">
                    <label :class="LC">Other Diseases / Conditions</label>
                    <div class="space-y-2 mb-2">
                      <div v-for="(d, i) in pastHistory.conditions.otherDiseases" :key="i" class="border border-gray-100 rounded-lg p-3 bg-gray-50/50 space-y-2">
                        <div class="flex items-center gap-2">
                          <span class="text-sm font-medium text-gray-700 flex-1">{{ d.name }}</span>
                          <button @click="removeOtherDisease(i)" class="text-red-400 hover:text-red-600">
                            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M18 6 6 18M6 6l12 12"/></svg>
                          </button>
                        </div>
                        <div class="grid grid-cols-3 gap-2">
                          <div>
                            <label :class="LC">Duration of diagnosis</label>
                            <select v-model="d.diagDuration" :class="IC + SEL">
                              <option value="">— Select —</option>
                              <option v-for="dur in DIAG_DURATIONS" :key="dur">{{ dur }}</option>
                            </select>
                          </div>
                          <div>
                            <label :class="LC">Current status</label>
                            <select v-model="d.currentStatus" :class="IC + SEL">
                              <option value="">— Select —</option>
                              <option v-for="s in STATUSES" :key="s">{{ s }}</option>
                            </select>
                          </div>
                          <div>
                            <label :class="LC">Medication adherence</label>
                            <select v-model="d.adherence" :class="IC + SEL">
                              <option value="">— Select —</option>
                              <option v-for="a in ADHERENCES" :key="a">{{ a }}</option>
                            </select>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div class="flex gap-2">
                      <input v-model="newOtherDisease" type="text" placeholder="Disease name" :class="IC" lang="auto" @keyup.enter="addOtherDisease"/>
                      <button @click="addOtherDisease" class="px-3 py-2 bg-orange-50 text-orange-600 text-sm rounded-lg hover:bg-orange-100 transition flex-shrink-0 font-medium">+ Add</button>
                    </div>
                  </div>
                </div>
              </div>

              <div>
                <label :class="LC">Past Surgeries / Hospitalisations</label>
                <textarea v-model="pastHistory.surgeries" rows="2" placeholder="Mention any surgeries or hospitalisations" :class="TC" lang="auto"/>
              </div>
            </div>
          </div>

          <!-- ④ Family History + Documents -->
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
            <button class="w-full flex items-center justify-between px-5 py-4" @click="toggleSection('familyHistory')">
              <div class="flex items-center gap-3">
                <svg class="w-5 h-5 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></svg>
                <span class="font-semibold text-gray-800">Family History &amp; Documents</span>
              </div>
              <svg :class="['w-5 h-5 text-gray-400 transition-transform', sections.familyHistory ? 'rotate-180' : '']" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M19 9l-7 7-7-7"/></svg>
            </button>
            <div v-if="sections.familyHistory" class="px-5 pb-5 space-y-4">

              <!-- Same-house complaints -->
              <div class="p-4 bg-purple-50/40 border border-purple-100 rounded-xl space-y-3">
                <label class="flex items-center gap-3 cursor-pointer">
                  <input v-model="familyHistory.sameHouseComplaints.present" type="checkbox" class="w-4 h-4 rounded border-gray-300 text-blue-600 accent-blue-600"/>
                  <span class="text-sm font-medium text-gray-700">Similar complaints in other family members residing in the same house</span>
                </label>
                <div v-if="familyHistory.sameHouseComplaints.present" class="space-y-3">
                  <div>
                    <label :class="LC">Which complaints <span class="text-gray-400 font-normal">(select all that apply)</span></label>
                    <div class="grid grid-cols-2 sm:grid-cols-3 gap-2 mt-1">
                      <label v-for="def in COMPLAINTS_DEF.filter(c => !c.isOpenEnded)" :key="def.id"
                        :class="['flex items-center gap-2 px-3 py-2 rounded-lg border cursor-pointer transition text-xs',
                          familyHistory.sameHouseComplaints.complaints.includes(def.label)
                            ? 'bg-purple-50 border-purple-300 text-purple-800'
                            : 'border-gray-200 text-gray-700 hover:bg-gray-50']">
                        <input type="checkbox" :checked="familyHistory.sameHouseComplaints.complaints.includes(def.label)" @change="toggleSameHouseComplaint(def.label)" class="w-3.5 h-3.5 rounded accent-purple-600"/>
                        {{ def.label }}
                      </label>
                    </div>
                  </div>
                  <div class="w-40">
                    <label :class="LC">Duration</label>
                    <select v-model="familyHistory.sameHouseComplaints.duration" :class="IC + SEL">
                      <option value="">— Select —</option>
                      <option>< 1 day</option>
                      <option>1 - 5 days</option>
                      <option>> 5 days</option>
                    </select>
                  </div>
                </div>
              </div>

              <!-- Major family diseases -->
              <div>
                <h4 class="text-sm font-semibold text-gray-700 mb-3">Major Diseases in Immediate Family</h4>
                <div class="space-y-3">
                  <div v-for="[key, label] in [
                    ['hypertension','Hypertension'],['diabetes','Diabetes'],['tb','Tuberculosis (TB)'],
                    ['highCholesterol','High Cholesterol'],['thyroid','Thyroid Disease'],
                  ]" :key="key" class="border border-gray-100 rounded-xl overflow-hidden">
                    <label class="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-gray-50 transition">
                      <input v-model="familyHistory.diseases[key].present" type="checkbox" class="w-4 h-4 rounded border-gray-300 text-blue-600 accent-blue-600"/>
                      <span class="text-sm font-medium text-gray-700 flex-1">{{ label }}</span>
                    </label>
                    <div v-if="familyHistory.diseases[key].present" class="px-4 pb-3 pt-0">
                      <label :class="LC">Affected family members</label>
                      <div class="flex flex-wrap gap-2">
                        <button v-for="rel in FAMILY_RELATIONS" :key="rel" type="button"
                          :class="['px-3 py-1.5 rounded-lg text-xs border transition', familyHistory.diseases[key].relations.includes(rel) ? 'bg-purple-600 text-white border-purple-600' : 'border-gray-200 text-gray-600 hover:border-purple-300 bg-white']"
                          @click="toggleFamilyRelation(key, rel)">
                          {{ rel }}
                        </button>
                      </div>
                    </div>
                  </div>

                  <!-- Other family diseases -->
                  <div class="border border-gray-100 rounded-xl p-4">
                    <label :class="LC">Other Diseases in Family</label>
                    <div class="space-y-2 mb-2">
                      <div v-for="(d, i) in familyHistory.diseases.others" :key="i" class="flex items-center gap-2 bg-gray-50 rounded-lg px-3 py-2 text-sm">
                        <span class="flex-1 text-gray-700">{{ d.name }}</span>
                        <span class="text-gray-400 text-xs">{{ d.relation }}</span>
                        <button @click="familyHistory.diseases.others.splice(i,1)" class="text-red-400 hover:text-red-600">
                          <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M18 6 6 18M6 6l12 12"/></svg>
                        </button>
                      </div>
                    </div>
                    <div class="flex gap-2">
                      <input v-model="newFamilyOther.name" type="text" placeholder="Disease name" :class="IC" lang="auto"/>
                      <select v-model="newFamilyOther.relation" :class="IC + SEL + ' w-36'">
                        <option value="">Relation</option>
                        <option v-for="r in FAMILY_RELATIONS" :key="r" :value="r">{{ r }}</option>
                      </select>
                      <button @click="addFamilyOther" class="px-3 py-2 bg-purple-50 text-purple-600 text-sm rounded-lg hover:bg-purple-100 transition flex-shrink-0 font-medium">+ Add</button>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Attach Documents -->
              <div>
                <label :class="LC">Attach Documents (lab reports, prescriptions, photos)</label>
                <div class="space-y-2 mb-2">
                  <div v-for="(doc, i) in attachedDocs" :key="i"
                    class="flex items-center gap-3 bg-blue-50 border border-blue-100 rounded-lg px-3 py-2">
                    <svg class="w-4 h-4 text-blue-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                    <span class="text-sm text-gray-700 flex-1 truncate">{{ doc.name }}</span>
                    <span class="text-xs text-gray-400">{{ (doc.size / 1024).toFixed(1) }} KB</span>
                    <button @click="removeDoc(i)" class="text-red-400 hover:text-red-600">
                      <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M18 6 6 18M6 6l12 12"/></svg>
                    </button>
                  </div>
                </div>
                <label class="cursor-pointer flex items-center gap-2 px-4 py-3 border-2 border-dashed border-gray-200 rounded-xl hover:border-blue-300 hover:bg-blue-50/30 transition">
                  <svg class="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                  <span class="text-sm text-gray-500">Click to attach photos or PDF documents</span>
                  <input type="file" accept="image/*,application/pdf" multiple class="hidden" @change="handleDocAttach" capture="environment"/>
                </label>
              </div>
            </div>
          </div>

          <!-- ⑤ Examination + Vitals -->
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
            <button class="w-full flex items-center justify-between px-5 py-4" @click="toggleSection('examination')">
              <div class="flex items-center gap-3">
                <svg class="w-5 h-5 text-teal-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
                <span class="font-semibold text-gray-800">Examination &amp; Vitals</span>
                <span v-if="isDoctor" class="text-[10px] bg-blue-100 text-blue-600 px-2 py-0.5 rounded-full font-medium">Doctor</span>
                <span v-else class="text-[10px] bg-teal-100 text-teal-600 px-2 py-0.5 rounded-full font-medium">ASHA / ANM</span>
              </div>
              <svg :class="['w-5 h-5 text-gray-400 transition-transform', sections.examination ? 'rotate-180' : '']" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M19 9l-7 7-7-7"/></svg>
            </button>
            <div v-if="sections.examination" class="px-5 pb-5 space-y-5">

              <!-- Anthropometry -->
              <div>
                <h4 class="text-sm font-semibold text-gray-700 mb-3">Anthropometry</h4>
                <div class="grid grid-cols-2 gap-4">
                  <div>
                    <label :class="LC">Height (cm)</label>
                    <input v-model="examForm.height" type="number" placeholder="e.g. 165" :class="IC"/>
                  </div>
                  <div>
                    <label :class="LC">Weight (kg)</label>
                    <input v-model="examForm.weight" type="number" placeholder="e.g. 60" :class="IC"/>
                  </div>
                </div>
              </div>

              <!-- General Examination -->
              <div>
                <h4 class="text-sm font-semibold text-gray-700 mb-3">General Examination</h4>
                <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-3">
                  <label v-for="field in [
                    { key: 'eyeDiscolouration', label: 'Eye Discolouration' },
                    { key: 'rashes',            label: 'Skin Rashes' },
                    { key: 'swelling',          label: 'Swelling / Oedema' },
                    { key: 'dehydration',       label: 'Dehydration' },
                  ]" :key="field.key"
                    :class="['flex items-center gap-2 rounded-lg px-3 py-2.5 cursor-pointer transition text-sm border',
                      examForm[field.key] ? 'bg-teal-50 border-teal-300' : 'bg-gray-50 border-gray-200 hover:bg-teal-50/40']">
                    <input v-model="examForm[field.key]" type="checkbox" class="w-4 h-4 rounded text-teal-600 accent-teal-600"/>
                    <span class="text-gray-700 text-xs">{{ field.label }}</span>
                  </label>
                </div>
                <div>
                  <label :class="LC">Other General Findings</label>
                  <textarea v-model="examForm.generalOther" rows="2" placeholder="Pallor, icterus, cyanosis, other observations..." :class="TC" lang="auto"/>
                </div>
              </div>

              <!-- Doctor-only: Specific Examination -->
              <template v-if="isDoctor">
                <div>
                  <h4 class="text-sm font-semibold text-gray-700 mb-3">Specific / Systemic Examination</h4>
                  <div class="space-y-3">
                    <div>
                      <label :class="LC">Systemic Examination</label>
                      <textarea v-model="examForm.systemicExam" rows="3" placeholder="CVS, Respiratory, Abdomen, CNS..." :class="TC" lang="auto"/>
                    </div>
                    <div>
                      <label :class="LC">Specific Findings / Remarks</label>
                      <textarea v-model="examForm.specificFindings" rows="2" placeholder="Any specific clinical findings..." :class="TC" lang="auto"/>
                    </div>
                  </div>
                </div>
              </template>

              <!-- Exam Photo -->
              <div>
                <label :class="LC">Examination Photo (optional)</label>
                <div class="flex items-center gap-4">
                  <label class="cursor-pointer">
                    <div class="w-20 h-20 rounded-xl bg-gray-50 border-2 border-dashed border-gray-200 hover:border-teal-400 flex items-center justify-center overflow-hidden transition">
                      <img v-if="examForm.examPhoto" :src="examForm.examPhoto" class="w-full h-full object-cover rounded-xl"/>
                      <svg v-else class="w-6 h-6 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>
                    </div>
                    <input type="file" accept="image/*" capture="environment" class="hidden" @change="handleExamPhoto"/>
                  </label>
                  <p class="text-xs text-gray-400">Tap to capture using camera</p>
                </div>
              </div>

              <!-- Vital Parameters -->
              <div>
                <h4 class="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                  <svg class="w-4 h-4 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
                  Vital Parameters
                </h4>
                <div class="grid grid-cols-2 sm:grid-cols-3 gap-4">
                  <div class="col-span-2 sm:col-span-1">
                    <label :class="LC">Blood Pressure (mmHg)</label>
                    <div class="flex items-center gap-2">
                      <input v-model="vitals.bpSystolic" type="number" placeholder="Systolic" class="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"/>
                      <span class="text-gray-400 font-semibold">/</span>
                      <input v-model="vitals.bpDiastolic" type="number" placeholder="Diastolic" class="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"/>
                    </div>
                  </div>
                  <div v-for="f in [
                    { key: 'heartRate',       label: 'Heart Rate',          unit: 'BPM',   ph: '72' },
                    { key: 'respiratoryRate', label: 'Respiratory Rate',    unit: '/min',  ph: '18' },
                    { key: 'temperature',     label: 'Temperature',         unit: '°F',    ph: '98.6' },
                    { key: 'spo2',            label: 'O₂ Saturation',      unit: '%',     ph: '98' },
                    { key: 'rbs',             label: 'Blood Glucose (RBS)', unit: 'mg/dL', ph: '110' },
                  ]" :key="f.key">
                    <div>
                      <label :class="LC">{{ f.label }} <span class="text-gray-400 font-normal">({{ f.unit }})</span></label>
                      <input v-model="vitals[f.key]" type="number" :placeholder="f.ph" :class="IC"/>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ── Right: Sidebar ── -->
        <div class="w-64 flex-shrink-0 space-y-4 hidden lg:block">
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-4 sticky top-4 space-y-4">
            <!-- Vitals preview -->
            <div>
              <div class="flex items-center gap-2 mb-3">
                <svg class="w-4 h-4 text-teal-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
                <h3 class="font-semibold text-gray-800 text-sm">Vitals Summary</h3>
              </div>
              <div class="space-y-2">
                <div v-for="[label, val, unit] in [
                  ['BP', vitals.bpSystolic && vitals.bpDiastolic ? vitals.bpSystolic+'/'+vitals.bpDiastolic : '—', 'mmHg'],
                  ['HR', vitals.heartRate || '—', 'BPM'],
                  ['RR', vitals.respiratoryRate || '—', '/min'],
                  ['Temp', vitals.temperature || '—', '°F'],
                  ['SpO₂', vitals.spo2 || '—', '%'],
                  ['RBS', vitals.rbs || '—', 'mg/dL'],
                ]" :key="label" class="flex items-center justify-between text-xs">
                  <span class="text-gray-500">{{ label }}</span>
                  <span class="font-semibold text-gray-800">{{ val }} <span class="font-normal text-gray-400">{{ unit }}</span></span>
                </div>
              </div>
            </div>

            <!-- Complaints summary -->
            <div v-if="selectedComplaintIds.length" class="border-t border-gray-100 pt-4">
              <div class="text-xs font-semibold text-gray-500 mb-2">Complaints ({{ selectedComplaintIds.length }})</div>
              <div class="flex flex-wrap gap-1.5">
                <span v-for="id in selectedComplaintIds" :key="id"
                  :class="['text-[11px] px-2 py-1 rounded-full font-medium', COMPLAINT_COLOR_MAP[getComplaintDef(id)?.color]?.badge]">
                  {{ getComplaintDef(id)?.label }}
                </span>
              </div>
            </div>

            <!-- AI Flags summary -->
            <div v-if="activeFlags.length" class="border-t border-gray-100 pt-4">
              <div class="text-xs font-semibold text-red-600 mb-2">AI Flags ({{ activeFlags.length }})</div>
              <div class="space-y-1.5">
                <div v-for="(flag, i) in activeFlags" :key="i"
                  :class="['text-[11px] px-2 py-1.5 rounded-lg', flag.level === 'critical' ? 'bg-red-50 text-red-700' : 'bg-yellow-50 text-yellow-700']">
                  {{ flag.message }}
                </div>
              </div>
            </div>

            <!-- AI hint -->
            <div class="border-t border-gray-100 pt-4">
              <div class="flex items-center gap-2 mb-2">
                <svg class="w-4 h-4 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                <h3 class="font-semibold text-gray-800 text-sm">AI Assistant</h3>
              </div>
              <p class="text-xs text-gray-400">Fill in the assessment and click Analyze to get AI-powered clinical suggestions.</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Bottom action bar -->
      <div class="flex items-center justify-between mt-6 pt-4 border-t border-gray-200">
        <div class="flex items-center gap-3">
          <button @click="router.back()" class="px-5 py-2.5 border border-gray-200 text-gray-600 text-sm font-medium rounded-lg hover:bg-gray-50 transition">{{ t('common.cancel') }}</button>
          <button @click="saveDraft"
            class="flex items-center gap-2 px-5 py-2.5 border border-blue-200 text-blue-600 text-sm font-medium rounded-lg hover:bg-blue-50 transition">
            <svg v-if="savingDraft" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 0 1 8-8v8H4z"/></svg>
            <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/></svg>
            {{ draftSaved ? t('common.draftSaved') : t('common.saveDraft') }}
          </button>
        </div>
        <button @click="analyze"
          class="flex items-center gap-2 px-8 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-lg transition">
          {{ t('common.analyze') }}
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
        </button>
      </div>
    </div>
  </AppShell>
</template>
