<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import AppShell from '@/shared/components/AppShell.vue'
import { usePatientsStore } from '@/features/patients/stores/patients'
import { useReferralsStore } from '@/features/referrals/stores/referrals'
import { useTeleconsultStore } from '@/features/teleconsult/stores/teleconsult'
import { useAuthStore } from '@/features/auth/stores/auth'

const router           = useRouter()
const route            = useRoute()
const store            = usePatientsStore()
const referralsStore   = useReferralsStore()
const teleconsultStore = useTeleconsultStore()
const auth             = useAuthStore()

const patientId = computed(() => Number(route.params.id))
const patient   = computed(() => store.getById(patientId.value) || { name: 'Unknown', id: patientId.value, age: '—', gender: '—', location: '—', risk: '—' })

const aiActions = [
  'Give Paracetamol 650mg',
  'Ensure plenty of fluids',
  'ORS if loose motions',
  'Rest and monitor temperature',
  'Monitor for red flags',
]

const implemented = reactive(Object.fromEntries(aiActions.map(a => [a, { yes: false, no: false, note: '' }])))

const additional = reactive({
  'Tepid sponging':      false, 'Blood sugar checked': false, 'BP checked':          false,
  'Oxygen given':        false, 'Wound dressing':      false, 'First aid provided':  false,
  'Ambulance called':    false, 'Doctor contacted':    false, 'Family educated':     false,
  'Referral slip issued':false, 'Other':               false,
})

const patientResponse = ref('Stable')
const responseOptions = ['Improved', 'Stable', 'No Change', 'Deteriorating', 'Emergency']
const responseColors  = {
  Improved:      'border-green-500 bg-green-50 text-green-600',
  Stable:        'border-blue-300 bg-blue-50 text-blue-500',
  'No Change':   'border-gray-300 bg-gray-50 text-gray-500',
  Deteriorating: 'border-orange-400 bg-orange-50 text-orange-500',
  Emergency:     'border-red-500 bg-red-50 text-red-500',
}

const referral    = reactive({ required: 'no', center: 'Rampur Community Health Center', time: '', transport: 'Ambulance' })
const teleconsult = reactive({ done: 'no', doctor: 'Dr. Anjali Sharma', time: '', advice: '' })
const outcome     = ref('')

// Evidence upload
const evidenceSlots = [
  { key: 'photo',    label: 'Patient Photo',    accept: 'image/*' },
  { key: 'meds',     label: 'Medication Given', accept: 'image/*' },
  { key: 'referral', label: 'Referral Slip',    accept: 'image/*,.pdf' },
  { key: 'reports',  label: 'Test Reports',     accept: 'image/*,.pdf' },
  { key: 'other',    label: 'Other Documents',  accept: '*' },
]
const evidenceFiles = reactive(Object.fromEntries(evidenceSlots.map(s => [s.key, null])))
const fileInputRefs = ref({})

function triggerUpload(key)       { fileInputRefs.value[key]?.click() }
function removeFile(key)          { evidenceFiles[key] = null; if (fileInputRefs.value[key]) fileInputRefs.value[key].value = '' }
function handleFileChange(key, e) { const file = e.target.files[0]; if (file) evidenceFiles[key] = file }

// Draft persistence
const draftKey  = computed(() => `measures_draft_${patientId.value}`)
const draftSaved = ref(false)

function buildSnapshot() {
  return {
    implemented: JSON.parse(JSON.stringify(implemented)),
    additional:  JSON.parse(JSON.stringify(additional)),
    patientResponse: patientResponse.value,
    referral:    JSON.parse(JSON.stringify(referral)),
    teleconsult: JSON.parse(JSON.stringify(teleconsult)),
    outcome:     outcome.value,
  }
}

function saveDraft() {
  localStorage.setItem(draftKey.value, JSON.stringify(buildSnapshot()))
  draftSaved.value = true
  setTimeout(() => { draftSaved.value = false }, 2200)
}

function loadDraft() {
  try {
    const d = JSON.parse(localStorage.getItem(draftKey.value) || 'null')
    if (!d) return
    Object.assign(implemented, d.implemented)
    Object.assign(additional,  d.additional)
    patientResponse.value = d.patientResponse
    Object.assign(referral,    d.referral)
    Object.assign(teleconsult, d.teleconsult)
    outcome.value = d.outcome
  } catch {}
}

onMounted(loadDraft)

const submitting = ref(false)
const submitted  = ref(false)

async function submitMeasures() {
  submitting.value = true
  try {
    await new Promise(r => setTimeout(r, 800))
    const workerName = auth.user?.name || 'ASHA Worker'
    if (referral.required === 'yes' && referral.center) {
      referralsStore.add({
        patientId: patientId.value, patientName: patient.value.name,
        hospital: referral.center, transport: referral.transport,
        ashaWorker: workerName, notes: outcome.value.slice(0, 80),
      })
    }
    if (teleconsult.done === 'yes' && teleconsult.doctor) {
      teleconsultStore.add({
        patientId: patientId.value, patientName: patient.value.name,
        doctor: teleconsult.doctor, spec: 'General Physician',
        ashaWorker: workerName, advice: teleconsult.advice,
        status: 'Completed', duration: teleconsult.time ? 15 : null,
      })
    }
    localStorage.removeItem(draftKey.value)
    submitted.value = true
    setTimeout(() => router.push('/dashboard'), 2000)
  } catch {
    // submit failed silently — keep form open
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <AppShell>
    <template #page-title>Measures Implemented</template>
    <template #page-subtitle>Record the measures and actions implemented for the patient.</template>

    <!-- Success overlay -->
    <div v-if="submitted" class="fixed inset-0 bg-black/40 z-50 flex items-center justify-center">
      <div class="bg-white rounded-2xl shadow-2xl px-10 py-8 flex flex-col items-center gap-4 max-w-xs w-full mx-4">
        <div class="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center">
          <svg class="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M20 6L9 17l-5-5"/></svg>
        </div>
        <h3 class="text-lg font-bold text-gray-800">Measures Submitted!</h3>
        <p class="text-sm text-gray-500 text-center">Patient measures have been recorded successfully. Returning to dashboard…</p>
      </div>
    </div>

    <div class="p-4 md:p-6 space-y-5">
      <button @click="router.push('/dashboard')" class="flex items-center gap-1.5 text-sm text-blue-600 hover:underline">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 5l-7 7 7 7"/></svg>
        Back to Dashboard
      </button>

      <!-- Patient strip -->
      <div class="bg-white rounded-xl border border-gray-100 shadow-sm px-5 py-3 flex items-center gap-5 flex-wrap text-xs">
        <div><div class="text-gray-500 mb-0.5">Patient Name</div><div class="font-semibold text-gray-800">{{ patient.name }}</div></div>
        <div><div class="text-gray-500 mb-0.5">Patient ID</div><div class="font-semibold text-gray-800">PT-2025-{{ String(patientId).padStart(6,'0') }}</div></div>
        <div><div class="text-gray-500 mb-0.5">Age / Gender</div><div class="font-semibold text-gray-800">{{ patient.age }} / {{ patient.gender }}</div></div>
        <div><div class="text-gray-500 mb-0.5">Location</div><div class="font-semibold text-gray-800">{{ patient.location }}</div></div>
        <div>
          <div class="text-gray-500 mb-0.5">Risk Level</div>
          <div class="flex items-center gap-1">
            <span :class="['w-2 h-2 rounded-full', patient.risk === 'High' ? 'bg-red-500' : patient.risk === 'Moderate' ? 'bg-orange-400' : 'bg-green-500']"/>
            <span :class="['font-semibold', patient.risk === 'High' ? 'text-red-600' : patient.risk === 'Moderate' ? 'text-orange-500' : 'text-green-600']">{{ patient.risk }} Risk</span>
          </div>
        </div>
        <div><div class="text-gray-500 mb-0.5">Assessment Time</div><div class="font-semibold text-gray-800">{{ patient.assessmentTime || patient.date || '—' }}</div></div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <!-- Col 1: AI Recommended + Additional -->
        <div class="space-y-4">
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
            <h3 class="font-semibold text-gray-800 text-sm mb-3">
              1. AI Recommended Actions
              <span class="text-xs text-blue-500 font-normal">(From Assessment)</span>
            </h3>
            <ul class="space-y-2.5">
              <li v-for="a in aiActions" :key="a" class="flex items-center gap-2">
                <div class="w-5 h-5 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
                  <svg class="w-3 h-3 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path d="M20 6L9 17l-5-5"/></svg>
                </div>
                <span class="text-xs text-gray-700">{{ a }}</span>
              </li>
            </ul>
          </div>

          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
            <h3 class="font-semibold text-gray-800 text-sm mb-3">3. Additional Measures Taken</h3>
            <div class="grid grid-cols-2 gap-x-4 gap-y-2">
              <label v-for="(val, key) in additional" :key="key" class="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" v-model="additional[key]" class="w-3.5 h-3.5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"/>
                <span class="text-xs text-gray-700">{{ key }}</span>
              </label>
            </div>
            <input v-if="additional['Other']" type="text" placeholder="Please specify"
              class="w-full mt-2 border border-gray-200 rounded-lg px-2.5 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"/>
          </div>
        </div>

        <!-- Col 2: Actions Implemented + Evidence + Outcome -->
        <div class="space-y-4">
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
            <h3 class="font-semibold text-gray-800 text-sm mb-3">2. Actions Actually Implemented</h3>
            <div class="space-y-3">
              <div class="grid grid-cols-[1fr_auto_auto_1fr] gap-2 text-xs font-semibold text-gray-500 border-b border-gray-100 pb-2">
                <span>Action</span><span class="text-center col-span-2">Done?</span><span>Notes</span>
              </div>
              <div v-for="(imp, action) in implemented" :key="action" class="grid grid-cols-[1fr_auto_auto_1fr] gap-2 items-center text-xs">
                <span class="text-gray-700 text-[11px] leading-tight">{{ action }}</span>
                <label class="flex items-center gap-1 cursor-pointer">
                  <input type="checkbox" v-model="imp.yes" class="w-3 h-3 text-green-600 focus:ring-green-500"/>
                  <span class="text-green-600">Yes</span>
                </label>
                <label class="flex items-center gap-1 cursor-pointer">
                  <input type="checkbox" v-model="imp.no" class="w-3 h-3 text-red-500 focus:ring-red-500"/>
                  <span class="text-red-500">No</span>
                </label>
                <input v-model="imp.note" type="text" placeholder="Time, details…"
                  class="flex-1 border border-gray-200 rounded px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"/>
              </div>
            </div>
          </div>

          <!-- Evidence upload -->
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
            <h3 class="font-semibold text-gray-800 text-sm mb-3">7. Evidence Upload</h3>
            <div class="grid grid-cols-5 gap-2">
              <div v-for="slot in evidenceSlots" :key="slot.key" class="text-center">
                <input :ref="el => fileInputRefs[slot.key] = el" type="file" :accept="slot.accept" class="hidden" @change="handleFileChange(slot.key, $event)"/>
                <div v-if="!evidenceFiles[slot.key]"
                  @click="triggerUpload(slot.key)"
                  class="border border-dashed border-gray-200 rounded-lg p-2 hover:border-blue-400 transition cursor-pointer bg-gray-50 hover:bg-blue-50">
                  <svg class="w-5 h-5 text-blue-400 mx-auto mb-1" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>
                  <div class="text-[9px] text-gray-500 leading-tight">{{ slot.label }}</div>
                </div>
                <div v-else class="border border-green-200 bg-green-50 rounded-lg p-2 relative">
                  <svg class="w-5 h-5 text-green-500 mx-auto mb-1" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                  <div class="text-[9px] text-green-600 leading-tight truncate">{{ evidenceFiles[slot.key].name.slice(0,12) }}</div>
                  <button @click="removeFile(slot.key)" class="absolute -top-1.5 -right-1.5 w-4 h-4 bg-red-500 text-white rounded-full flex items-center justify-center text-[9px] hover:bg-red-600">×</button>
                </div>
              </div>
            </div>
          </div>

          <!-- Outcome summary -->
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
            <h3 class="font-semibold text-gray-800 text-sm mb-3">8. Outcome Summary <span class="text-red-500">*</span></h3>
            <textarea v-model="outcome" rows="5" maxlength="1000" placeholder="Describe the outcome and observations…"
              class="w-full border border-gray-200 rounded-lg px-3 py-2 text-xs text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"/>
            <div class="text-right text-xs text-gray-400 mt-1">{{ outcome.length }} / 1000</div>
          </div>
        </div>

        <!-- Col 3: Patient Response + Referral + Teleconsult -->
        <div class="space-y-4">
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
            <h3 class="font-semibold text-gray-800 text-sm mb-3">4. Patient Response</h3>
            <div class="grid grid-cols-2 gap-2">
              <button v-for="r in responseOptions" :key="r"
                :class="['px-2 py-2 border rounded-lg text-xs font-medium transition text-center',
                  patientResponse === r ? responseColors[r] + ' border-2' : 'border-gray-200 text-gray-500 hover:border-gray-300']"
                @click="patientResponse = r">
                {{ r }}
              </button>
            </div>
          </div>

          <!-- Referral status -->
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
            <h3 class="font-semibold text-gray-800 text-sm mb-3">5. Referral Status</h3>
            <div class="space-y-3 text-xs">
              <div class="flex items-center gap-4">
                <span class="text-gray-600">Referral Required?</span>
                <label class="flex items-center gap-1.5 cursor-pointer"><input type="radio" v-model="referral.required" value="yes" class="text-blue-600"/><span>Yes</span></label>
                <label class="flex items-center gap-1.5 cursor-pointer"><input type="radio" v-model="referral.required" value="no"  class="text-blue-600"/><span>No</span></label>
              </div>
              <div v-if="referral.required === 'yes'" class="space-y-2.5">
                <div>
                  <label class="block text-gray-600 mb-1">Referral Center <span class="text-red-500">*</span></label>
                  <select v-model="referral.center" class="w-full border border-gray-200 rounded-lg px-2.5 py-1.5 text-xs bg-white focus:outline-none focus:ring-1 focus:ring-blue-500">
                    <option>Rampur Community Health Center</option>
                    <option>Sharma Hospital</option>
                    <option>City Care Hospital</option>
                  </select>
                </div>
                <div>
                  <label class="block text-gray-600 mb-1">Referral Time <span class="text-red-500">*</span></label>
                  <input v-model="referral.time" type="datetime-local" class="w-full border border-gray-200 rounded-lg px-2.5 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"/>
                </div>
                <div>
                  <label class="block text-gray-600 mb-1">Transport <span class="text-red-500">*</span></label>
                  <div class="flex gap-3 flex-wrap">
                    <label v-for="opt in ['Ambulance','Private Vehicle','Govt. Vehicle','Walking']" :key="opt" class="flex items-center gap-1.5 cursor-pointer">
                      <input type="radio" v-model="referral.transport" :value="opt" class="text-blue-600"/>
                      <span class="text-xs">{{ opt }}</span>
                    </label>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Teleconsultation -->
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
            <h3 class="font-semibold text-gray-800 text-sm mb-3">6. Teleconsultation</h3>
            <div class="space-y-2.5 text-xs">
              <div class="flex items-center gap-4">
                <span class="text-gray-600">Teleconsultation Done?</span>
                <label class="flex items-center gap-1.5 cursor-pointer"><input type="radio" v-model="teleconsult.done" value="yes" class="text-blue-600"/><span>Yes</span></label>
                <label class="flex items-center gap-1.5 cursor-pointer"><input type="radio" v-model="teleconsult.done" value="no"  class="text-blue-600"/><span>No</span></label>
              </div>
              <div v-if="teleconsult.done === 'yes'" class="space-y-2.5">
                <div>
                  <label class="block text-gray-600 mb-1">Doctor Name</label>
                  <select v-model="teleconsult.doctor" class="w-full border border-gray-200 rounded-lg px-2.5 py-1.5 text-xs bg-white focus:outline-none focus:ring-1 focus:ring-blue-500">
                    <option>Dr. Anjali Sharma</option>
                    <option>Dr. Vivek Singh</option>
                    <option>Dr. Neha Verma</option>
                  </select>
                </div>
                <div>
                  <label class="block text-gray-600 mb-1">Consultation Time</label>
                  <input v-model="teleconsult.time" type="datetime-local" class="w-full border border-gray-200 rounded-lg px-2.5 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"/>
                </div>
                <div>
                  <label class="block text-gray-600 mb-1">Advice Given</label>
                  <textarea v-model="teleconsult.advice" rows="4" placeholder="Doctor's advice and instructions…"
                    class="w-full border border-gray-200 rounded-lg px-2.5 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none"/>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Bottom actions -->
      <div class="flex items-center justify-between pt-4 border-t border-gray-200">
        <div class="flex items-center gap-3">
          <button @click="router.back()" class="px-5 py-2.5 border border-gray-200 text-gray-600 text-sm font-medium rounded-lg hover:bg-gray-50 transition">Cancel</button>
          <button @click="saveDraft" class="flex items-center gap-2 px-5 py-2.5 border border-blue-200 text-blue-600 text-sm font-medium rounded-lg hover:bg-blue-50 transition">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
            {{ draftSaved ? 'Draft Saved!' : 'Save Draft' }}
          </button>
        </div>
        <button @click="submitMeasures" :disabled="submitting"
          class="flex items-center gap-2 px-8 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white text-sm font-semibold rounded-lg transition">
          <svg v-if="submitting" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 0 1 8-8v8H4z"/></svg>
          {{ submitting ? 'Submitting…' : 'Submit Measures' }}
          <svg v-if="!submitting" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
        </button>
      </div>
    </div>
  </AppShell>
</template>
