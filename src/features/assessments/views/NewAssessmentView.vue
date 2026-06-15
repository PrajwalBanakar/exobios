<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import AppShell from '@/shared/components/AppShell.vue'
import { usePatientsStore } from '@/features/patients/stores/patients'
import { useAuthStore } from '@/features/auth/stores/auth'
import { useI18n } from '@/i18n'

const router = useRouter()
const route  = useRoute()
const store  = usePatientsStore()
const auth   = useAuthStore()
const { t }  = useI18n()

const isEdit    = computed(() => route.name === 'EditAssessment')
const patientId = computed(() => isEdit.value ? Number(route.params.id) : null)
const patient   = computed(() => isEdit.value ? store.getById(patientId.value) : null)

// When coming from AddPatientView, a registered patient is pre-linked via query param
const linkedPatientId = computed(() => route.query.patientId ? Number(route.query.patientId) : null)
const linkedPatient   = computed(() => linkedPatientId.value ? store.getById(linkedPatientId.value) : null)

// Detect if user is a doctor (more exam fields)
const isDoctor = computed(() => auth.user?.role === 'Doctor' || auth.user?.role === 'ANM')

// ── Section visibility (accordion) ────────────────────────────────────────────
const sections = ref({ basic: true, complaints: false, pastHistory: false, familyHistory: false, examination: false })
function toggleSection(key) { sections.value[key] = !sections.value[key] }

// ── Basic Info ────────────────────────────────────────────────────────────────
const form = reactive({
  fullName: '', age: '', gender: '', phone: '', location: '', village: '', abhaId: '',
})

const calculatedAge = computed(() => {
  // age field may be typed directly or come from DOB
  return form.age ? Number(form.age) : null
})

// ── Chief Complaints (up to 4) ───────────────────────────────────────────────
const ASSOCIATED_SYMPTOMS = [
  'Fever', 'Cough', 'Vomiting', 'Diarrhea', 'Headache',
  'Body Pain', 'Breathlessness', 'Rash', 'Weakness', 'Swelling',
  'Loss of Appetite', 'Abdominal Pain',
]

function blankComplaint() {
  return { complaint: '', onset: '', duration: '', intensity: 5, associatedSymptoms: [] }
}
const complaints = ref([blankComplaint()])

function addComplaint() {
  if (complaints.value.length < 4) complaints.value.push(blankComplaint())
}
function removeComplaint(i) {
  if (complaints.value.length > 1) complaints.value.splice(i, 1)
}

// ── Past History ─────────────────────────────────────────────────────────────
const pastHistory = reactive({
  similarComplaints: false,
  similarDetails: '',
  conditions: {
    hypertension:    { present: false, since: '', medications: '' },
    diabetes:        { present: false, type: '', medications: '' },
    asthma:          { present: false, medications: '' },
    highCholesterol: { present: false, medications: '' },
    allergy:         { present: false, allergen: '', medications: '' },
    otherDiseases:   [],
  },
  surgeries:   '',
})

const newOtherDisease = ref('')
function addOtherDisease() {
  if (!newOtherDisease.value.trim()) return
  pastHistory.conditions.otherDiseases.push({ name: newOtherDisease.value.trim(), medications: '' })
  newOtherDisease.value = ''
}
function removeOtherDisease(i) { pastHistory.conditions.otherDiseases.splice(i, 1) }

// ── Family History ────────────────────────────────────────────────────────────
const FAMILY_RELATIONS = ['Father', 'Mother', 'Sibling', 'Spouse', 'Child', 'Grandparent', 'Uncle/Aunt']

const familyHistory = reactive({
  similarComplaints: false,
  similarDetails: '',
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
  // Both roles
  height: '', weight: '',
  temperature: '',
  eyeDiscolouration: false, rashes: false, swelling: false, dehydration: false,
  generalOther: '',
  examPhoto: '',
  // Doctor-only
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

// ── Draft save / load ─────────────────────────────────────────────────────────
const draftKey    = computed(() => isEdit.value ? `assessment_draft_${patientId.value}` : 'assessment_draft_new')
const savingDraft = ref(false)
const draftSaved  = ref(false)

onMounted(() => {
  if (isEdit.value && patient.value) {
    const p = patient.value
    form.fullName = p.name || ''; form.age = String(p.age || ''); form.gender = p.gender || ''
    form.phone = p.phone || ''; form.location = p.location || ''; form.abhaId = p.abhaId || ''
    if (p.complaints)    complaints.value = p.complaints
    if (p.pastHistory)   Object.assign(pastHistory, p.pastHistory)
    if (p.familyHistory) Object.assign(familyHistory, p.familyHistory)
    if (p.examForm)      Object.assign(examForm, p.examForm)
    if (p.vitals)        Object.assign(vitals, p.vitals)
  } else if (linkedPatient.value) {
    // Patient was just registered — pre-fill read-only info and jump straight to complaints
    const p = linkedPatient.value
    form.fullName = p.name || ''; form.age = String(p.age || ''); form.gender = p.gender || ''
    form.phone = p.phone || ''
    form.location = [p.address?.village, p.address?.district].filter(Boolean).join(', ') || p.location || ''
    form.abhaId = p.abhaId || ''
    // Open complaints section immediately — patient info is already registered
    sections.value.basic = false
    sections.value.complaints = true
  } else {
    const saved = localStorage.getItem(draftKey.value)
    if (saved) {
      try {
        const d = JSON.parse(saved)
        if (d.form)          Object.assign(form, d.form)
        if (d.complaints)    complaints.value = d.complaints
        if (d.pastHistory)   Object.assign(pastHistory, d.pastHistory)
        if (d.familyHistory) Object.assign(familyHistory, d.familyHistory)
        if (d.examForm)      Object.assign(examForm, d.examForm)
        if (d.vitals)        Object.assign(vitals, d.vitals)
      } catch {}
    }
  }
})

function saveDraft() {
  savingDraft.value = true
  localStorage.setItem(draftKey.value, JSON.stringify({
    form: { ...form }, complaints: complaints.value,
    pastHistory: JSON.parse(JSON.stringify(pastHistory)),
    familyHistory: JSON.parse(JSON.stringify(familyHistory)),
    examForm: { ...examForm }, vitals: { ...vitals },
  }))
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
  const fullData = {
    name: form.fullName, age: Number(form.age), gender: form.gender,
    phone: form.phone, location: form.location, abhaId: form.abhaId, assessmentTime,
    complaints: complaints.value,
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
    // Patient already registered — append as a new assessment entry in their history
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

const IC  = 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500'
const TC  = 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none'
const LC  = 'block text-xs font-medium text-gray-600 mb-1.5'
const CHK = 'w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500'
</script>

<template>
  <AppShell>
    <template #page-title>{{ isEdit ? t('assessment.edit') : t('assessment.new') }}</template>
    <template #page-subtitle>{{ isEdit ? patient?.name || '' : linkedPatient ? linkedPatient.name : 'Patient complaint, history, and examination' }}</template>

    <div class="p-4 md:p-6">
      <button @click="router.back()" class="flex items-center gap-1.5 text-sm text-blue-600 hover:underline mb-5">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 5l-7 7 7 7"/></svg>
        {{ t('common.back') }}
      </button>

      <!-- Registered-patient banner: shown when coming from AddPatientView -->
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

      <div class="flex gap-6">
        <!-- ── Left: Form sections ── -->
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

          <!-- ①  Basic Patient Info -->
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
                  <select v-model="form.gender" :class="IC + ' bg-white'">
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
              <div class="grid grid-cols-2 lg:grid-cols-3 gap-4">
                <div class="col-span-2 lg:col-span-1">
                  <label :class="LC">{{ t('assessment.location') }}</label>
                  <input v-model="form.location" type="text" :placeholder="t('assessment.location')" :class="IC" lang="auto"/>
                </div>
                <div>
                  <label :class="LC">{{ t('assessment.village') }}</label>
                  <input v-model="form.village" type="text" placeholder="Village name" :class="IC" lang="auto"/>
                </div>
                <div>
                  <label :class="LC">{{ t('assessment.abhaId') }}</label>
                  <input v-model="form.abhaId" type="text" placeholder="12-XXXX-XXXX-XXXX" :class="IC"/>
                </div>
              </div>
            </div>
          </div>

          <!-- ②  Chief Complaints -->
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
            <button class="w-full flex items-center justify-between px-5 py-4" @click="toggleSection('complaints')">
              <div class="flex items-center gap-3">
                <svg class="w-5 h-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
                <span class="font-semibold text-gray-800">Chief Complaints</span>
                <span class="text-xs bg-red-100 text-red-600 px-2 py-0.5 rounded-full font-medium">Up to 4</span>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-xs text-gray-400">{{ complaints.length }} added</span>
                <svg :class="['w-5 h-5 text-gray-400 transition-transform', sections.complaints ? 'rotate-180' : '']" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M19 9l-7 7-7-7"/></svg>
              </div>
            </button>
            <div v-if="sections.complaints" class="px-5 pb-5 space-y-4">
              <div v-for="(c, i) in complaints" :key="i" class="border border-gray-100 rounded-xl p-4 space-y-3 bg-gray-50/50">
                <div class="flex items-center justify-between mb-2">
                  <span class="text-xs font-semibold text-red-600 bg-red-50 px-2 py-1 rounded-full">Complaint {{ i + 1 }}</span>
                  <button v-if="complaints.length > 1" @click="removeComplaint(i)"
                    class="text-gray-400 hover:text-red-500 transition p-1">
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18M6 6l12 12"/></svg>
                  </button>
                </div>

                <div>
                  <label :class="LC">Chief Complaint <span class="text-red-500">*</span></label>
                  <textarea v-model="c.complaint" rows="2" placeholder="Describe the main complaint in patient's words" :class="TC" lang="auto"/>
                </div>

                <div class="grid grid-cols-3 gap-3">
                  <div>
                    <label :class="LC">Onset</label>
                    <input v-model="c.onset" type="text" placeholder="e.g. Sudden, Gradual" :class="IC" lang="auto"/>
                  </div>
                  <div>
                    <label :class="LC">Duration</label>
                    <input v-model="c.duration" type="text" placeholder="e.g. 3 days, 2 weeks" :class="IC" lang="auto"/>
                  </div>
                  <div>
                    <label :class="LC">Intensity (1–10): <span class="font-bold text-red-600">{{ c.intensity }}</span></label>
                    <input v-model.number="c.intensity" type="range" min="1" max="10" class="w-full accent-red-500 mt-2"/>
                    <div class="flex justify-between text-[10px] text-gray-400 mt-0.5"><span>Mild</span><span>Severe</span></div>
                  </div>
                </div>

                <div>
                  <label :class="LC">Associated Symptoms</label>
                  <div class="grid grid-cols-3 sm:grid-cols-4 gap-2">
                    <label v-for="sym in ASSOCIATED_SYMPTOMS" :key="sym"
                      class="flex items-center gap-1.5 text-xs text-gray-700 cursor-pointer hover:bg-red-50 rounded-lg px-2 py-1.5 transition">
                      <input v-model="c.associatedSymptoms" type="checkbox" :value="sym" :class="CHK"/>
                      {{ sym }}
                    </label>
                  </div>
                </div>
              </div>

              <button v-if="complaints.length < 4" @click="addComplaint"
                class="w-full flex items-center justify-center gap-2 py-3 border-2 border-dashed border-gray-200 rounded-xl text-sm text-gray-500 hover:border-blue-300 hover:text-blue-600 transition">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M12 5v14M5 12h14"/></svg>
                Add Another Complaint
              </button>
            </div>
          </div>

          <!-- ③  Past History -->
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
            <button class="w-full flex items-center justify-between px-5 py-4" @click="toggleSection('pastHistory')">
              <div class="flex items-center gap-3">
                <svg class="w-5 h-5 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                <span class="font-semibold text-gray-800">Past History</span>
              </div>
              <svg :class="['w-5 h-5 text-gray-400 transition-transform', sections.pastHistory ? 'rotate-180' : '']" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M19 9l-7 7-7-7"/></svg>
            </button>
            <div v-if="sections.pastHistory" class="px-5 pb-5 space-y-4">
              <!-- Similar complaints -->
              <div class="p-4 bg-orange-50/40 border border-orange-100 rounded-xl">
                <label class="flex items-center gap-3 cursor-pointer">
                  <input v-model="pastHistory.similarComplaints" type="checkbox" :class="CHK"/>
                  <span class="text-sm font-medium text-gray-700">History of similar complaints in the past</span>
                </label>
                <div v-if="pastHistory.similarComplaints" class="mt-3">
                  <textarea v-model="pastHistory.similarDetails" rows="2" placeholder="Describe when, how often, any diagnosis received..." :class="TC" lang="auto"/>
                </div>
              </div>

              <!-- Known conditions -->
              <div>
                <h4 class="text-sm font-semibold text-gray-700 mb-3">Known Conditions</h4>
                <div class="space-y-3">
                  <!-- Hypertension -->
                  <div class="border border-gray-100 rounded-xl overflow-hidden">
                    <label class="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-gray-50 transition">
                      <input v-model="pastHistory.conditions.hypertension.present" type="checkbox" :class="CHK"/>
                      <span class="text-sm font-medium text-gray-700 flex-1">Hypertension (High Blood Pressure)</span>
                    </label>
                    <div v-if="pastHistory.conditions.hypertension.present" class="px-4 pb-3 pt-0 grid grid-cols-2 gap-3">
                      <div><label :class="LC">Since when</label><input v-model="pastHistory.conditions.hypertension.since" type="text" placeholder="e.g. 5 years" :class="IC" lang="auto"/></div>
                      <div><label :class="LC">Medications</label><input v-model="pastHistory.conditions.hypertension.medications" type="text" placeholder="Drug name, dose" :class="IC" lang="auto"/></div>
                    </div>
                  </div>

                  <!-- Diabetes -->
                  <div class="border border-gray-100 rounded-xl overflow-hidden">
                    <label class="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-gray-50 transition">
                      <input v-model="pastHistory.conditions.diabetes.present" type="checkbox" :class="CHK"/>
                      <span class="text-sm font-medium text-gray-700 flex-1">Diabetes Mellitus</span>
                    </label>
                    <div v-if="pastHistory.conditions.diabetes.present" class="px-4 pb-3 pt-0 grid grid-cols-2 gap-3">
                      <div><label :class="LC">Type</label>
                        <select v-model="pastHistory.conditions.diabetes.type" :class="IC + ' bg-white'">
                          <option value="">—</option><option>Type 1</option><option>Type 2</option><option>Gestational</option>
                        </select>
                      </div>
                      <div><label :class="LC">Medications</label><input v-model="pastHistory.conditions.diabetes.medications" type="text" placeholder="e.g. Metformin 500mg" :class="IC" lang="auto"/></div>
                    </div>
                  </div>

                  <!-- Asthma -->
                  <div class="border border-gray-100 rounded-xl overflow-hidden">
                    <label class="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-gray-50 transition">
                      <input v-model="pastHistory.conditions.asthma.present" type="checkbox" :class="CHK"/>
                      <span class="text-sm font-medium text-gray-700 flex-1">Asthma / Respiratory illness</span>
                    </label>
                    <div v-if="pastHistory.conditions.asthma.present" class="px-4 pb-3 pt-0">
                      <label :class="LC">Medications / Inhalers</label>
                      <input v-model="pastHistory.conditions.asthma.medications" type="text" placeholder="e.g. Salbutamol inhaler" :class="IC" lang="auto"/>
                    </div>
                  </div>

                  <!-- High Cholesterol -->
                  <div class="border border-gray-100 rounded-xl overflow-hidden">
                    <label class="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-gray-50 transition">
                      <input v-model="pastHistory.conditions.highCholesterol.present" type="checkbox" :class="CHK"/>
                      <span class="text-sm font-medium text-gray-700 flex-1">High Cholesterol (Dyslipidaemia)</span>
                    </label>
                    <div v-if="pastHistory.conditions.highCholesterol.present" class="px-4 pb-3 pt-0">
                      <label :class="LC">Medications</label>
                      <input v-model="pastHistory.conditions.highCholesterol.medications" type="text" placeholder="e.g. Atorvastatin 10mg" :class="IC" lang="auto"/>
                    </div>
                  </div>

                  <!-- Allergy -->
                  <div class="border border-gray-100 rounded-xl overflow-hidden">
                    <label class="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-gray-50 transition">
                      <input v-model="pastHistory.conditions.allergy.present" type="checkbox" :class="CHK"/>
                      <span class="text-sm font-medium text-gray-700 flex-1">Known Allergies</span>
                    </label>
                    <div v-if="pastHistory.conditions.allergy.present" class="px-4 pb-3 pt-0 grid grid-cols-2 gap-3">
                      <div><label :class="LC">Allergen</label><input v-model="pastHistory.conditions.allergy.allergen" type="text" placeholder="e.g. Penicillin, dust" :class="IC" lang="auto"/></div>
                      <div><label :class="LC">Medications / Precautions</label><input v-model="pastHistory.conditions.allergy.medications" type="text" placeholder="Antihistamines, avoid X" :class="IC" lang="auto"/></div>
                    </div>
                  </div>

                  <!-- Other diseases -->
                  <div class="border border-gray-100 rounded-xl overflow-hidden p-4">
                    <label :class="LC">Other Diseases / Conditions</label>
                    <div class="space-y-2 mb-2">
                      <div v-for="(d, i) in pastHistory.conditions.otherDiseases" :key="i" class="flex items-center gap-2 bg-gray-50 rounded-lg px-3 py-2">
                        <span class="text-sm text-gray-700 flex-1">{{ d.name }}</span>
                        <input v-model="d.medications" type="text" placeholder="Medications" class="flex-1 border border-gray-200 rounded px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-blue-400" lang="auto"/>
                        <button @click="removeOtherDisease(i)" class="text-red-400 hover:text-red-600">
                          <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M18 6 6 18M6 6l12 12"/></svg>
                        </button>
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

          <!-- ④  Family History + Documents -->
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
            <button class="w-full flex items-center justify-between px-5 py-4" @click="toggleSection('familyHistory')">
              <div class="flex items-center gap-3">
                <svg class="w-5 h-5 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></svg>
                <span class="font-semibold text-gray-800">Family History &amp; Documents</span>
              </div>
              <svg :class="['w-5 h-5 text-gray-400 transition-transform', sections.familyHistory ? 'rotate-180' : '']" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M19 9l-7 7-7-7"/></svg>
            </button>
            <div v-if="sections.familyHistory" class="px-5 pb-5 space-y-4">
              <!-- Similar in family -->
              <div class="p-4 bg-purple-50/40 border border-purple-100 rounded-xl">
                <label class="flex items-center gap-3 cursor-pointer">
                  <input v-model="familyHistory.similarComplaints" type="checkbox" :class="CHK"/>
                  <span class="text-sm font-medium text-gray-700">Similar complaints seen in family members</span>
                </label>
                <div v-if="familyHistory.similarComplaints" class="mt-3">
                  <textarea v-model="familyHistory.similarDetails" rows="2" placeholder="Who, what complaint, when..." :class="TC" lang="auto"/>
                </div>
              </div>

              <!-- Major family diseases -->
              <div>
                <h4 class="text-sm font-semibold text-gray-700 mb-3">Major Diseases in Family</h4>
                <div class="space-y-3">
                  <div v-for="[key, label] in [
                    ['hypertension','Hypertension'],['diabetes','Diabetes'],['tb','Tuberculosis (TB)'],
                    ['highCholesterol','High Cholesterol'],['thyroid','Thyroid Disease'],
                  ]" :key="key" class="border border-gray-100 rounded-xl overflow-hidden">
                    <label class="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-gray-50 transition">
                      <input v-model="familyHistory.diseases[key].present" type="checkbox" :class="CHK"/>
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
                      <select v-model="newFamilyOther.relation" :class="IC + ' bg-white w-36'">
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
                <label :class="LC">Attach Documents (Lab reports, prescriptions, photos)</label>
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

          <!-- ⑤  Examination + Vitals -->
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

              <!-- General Examination (all roles) -->
              <div>
                <h4 class="text-sm font-semibold text-gray-700 mb-3">General Examination</h4>
                <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-3">
                  <label v-for="field in [
                    { key: 'eyeDiscolouration', label: 'Eye Discolouration' },
                    { key: 'rashes', label: 'Skin Rashes' },
                    { key: 'swelling', label: 'Swelling / Oedema' },
                    { key: 'dehydration', label: 'Dehydration' },
                  ]" :key="field.key"
                    class="flex items-center gap-2 bg-gray-50 rounded-lg px-3 py-2 cursor-pointer hover:bg-teal-50 transition text-sm">
                    <input v-model="examForm[field.key]" type="checkbox" :class="CHK"/>
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

              <!-- Photo capture -->
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
                  <!-- BP -->
                  <div class="col-span-2 sm:col-span-1">
                    <label :class="LC">Blood Pressure (mmHg)</label>
                    <div class="flex items-center gap-2">
                      <input v-model="vitals.bpSystolic" type="number" placeholder="Systolic" class="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"/>
                      <span class="text-gray-400 font-semibold">/</span>
                      <input v-model="vitals.bpDiastolic" type="number" placeholder="Diastolic" class="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"/>
                    </div>
                  </div>

                  <div v-for="f in [
                    { key: 'heartRate',       label: 'Heart Rate',         unit: 'BPM',    ph: '72' },
                    { key: 'respiratoryRate', label: 'Respiratory Rate',   unit: '/min',   ph: '18' },
                    { key: 'temperature',     label: 'Temperature',        unit: '°F',     ph: '98.6' },
                    { key: 'spo2',            label: 'O₂ Saturation',     unit: '%',      ph: '98' },
                    { key: 'rbs',             label: 'Blood Glucose (RBS)',unit: 'mg/dL',  ph: '110' },
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
          <!-- Vitals live preview -->
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-4 sticky top-4">
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

          <!-- AI Assistant hint -->
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
            <div class="flex items-center gap-2 mb-2">
              <svg class="w-4 h-4 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
              <h3 class="font-semibold text-gray-800 text-sm">AI Assistant</h3>
            </div>
            <p class="text-xs text-gray-400 mb-3">Fill in the assessment and click Analyze to get AI-powered clinical suggestions.</p>
            <div class="text-xs text-blue-600 bg-blue-50 rounded-lg px-3 py-2">
              The AI will analyze complaints, history, examination, and vitals together.
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
