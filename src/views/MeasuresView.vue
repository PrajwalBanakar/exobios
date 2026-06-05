<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '../components/AppShell.vue'

const router = useRouter()

const aiActions = [
  'Give Paracetamol 650mg',
  'Ensure plenty of fluids',
  'ORS if loose motions',
  'Rest and monitor temperature',
  'Monitor for red flags',
]

const implemented = reactive({
  'Give Paracetamol 650mg':     { yes: true,  no: false, note: 'Given at 10:35 AM' },
  'ORS if loose motions':       { yes: true,  no: false, note: '1 sachet administered' },
  'Ensure plenty of fluids':    { yes: true,  no: false, note: 'Family informed' },
  'Rest and monitor temperature':{ yes: true, no: false, note: 'Patient at home' },
  'Monitor for red flags':      { yes: true,  no: false, note: 'Recheck after 1 hour' },
})

const additional = reactive({
  'Tepid sponging':    true,
  'Blood sugar checked': true,
  'BP checked':        true,
  'Oxygen given':      false,
  'Wound dressing':    false,
  'First aid provided': true,
  'Ambulance called':  true,
  'Doctor contacted':  false,
  'Family educated':   true,
  'Referral slip issued': true,
  'Other':             false,
})

const patientResponse = ref('Improved')
const responseOptions = ['Improved', 'Stable', 'No Change', 'Deteriorating', 'Emergency']
const responseColors = {
  Improved: 'border-green-500 bg-green-50 text-green-600',
  Stable: 'border-blue-300 bg-blue-50 text-blue-500',
  'No Change': 'border-gray-300 bg-gray-50 text-gray-500',
  Deteriorating: 'border-orange-400 bg-orange-50 text-orange-500',
  Emergency: 'border-red-500 bg-red-50 text-red-500',
}

const referral = reactive({
  required: 'yes',
  center: 'Rampur Community Health Center',
  time: '16 May 2025, 10:50 AM',
  transport: 'Ambulance',
})

const teleconsult = reactive({
  done: 'yes',
  doctor: 'Dr. Anjali Sharma',
  time: '16 May 2025, 10:42 AM',
  advice: 'Continue paracetamol. Monitor temperature. Increase fluid intake. Refer if fever persists > 48 hrs or condition worsens.',
})

const outcome = ref(`Patient presented with fever 101°F.
Paracetamol 650mg given at 10:35 AM.
ORS 1 sachet administered and plenty of fluids advised.
Tepid sponging done and family educated about hydration and monitoring.
Referred to Rampur Community Health Center due to high-risk assessment.`)

const timeline = [
  { time: '10:20 AM', label: 'Assessment Completed',          done: true },
  { time: '10:21 AM', label: 'AI Recommendation Generated',   done: true },
  { time: '10:35 AM', label: 'Paracetamol Given',             done: true },
  { time: '10:37 AM', label: 'ORS Administered',              done: true },
  { time: '10:42 AM', label: 'Doctor Consulted (Teleconsultation)', done: true },
  { time: '10:50 AM', label: 'Referral Issued',               done: true },
  { time: '11:00 AM', label: 'Patient Referred',              done: false },
]
</script>

<template>
  <AppShell>
    <template #page-title>Measures Implemented by Enabler</template>
    <template #page-subtitle>Record the measures and actions implemented for the patient.</template>

    <div class="p-6 space-y-5">
      <!-- Patient strip -->
      <div class="bg-white rounded-xl border border-gray-100 shadow-sm px-5 py-3 flex items-center gap-5 flex-wrap text-xs">
        <div>
          <div class="text-gray-500 mb-0.5">Patient Name</div>
          <div class="font-semibold text-gray-800">Ramesh Kumar</div>
        </div>
        <div>
          <div class="text-gray-500 mb-0.5">Patient ID</div>
          <div class="font-semibold text-gray-800">PT-2025-000123</div>
        </div>
        <div>
          <div class="text-gray-500 mb-0.5">Age / Gender</div>
          <div class="font-semibold text-gray-800">45 / Male</div>
        </div>
        <div>
          <div class="text-gray-500 mb-0.5">Location</div>
          <div class="font-semibold text-gray-800">Rampur, Uttar Pradesh - 244901</div>
        </div>
        <div>
          <div class="text-gray-500 mb-0.5">Risk Level</div>
          <div class="flex items-center gap-1">
            <span class="w-2 h-2 rounded-full bg-red-500"></span>
            <span class="font-semibold text-red-600">High Risk</span>
          </div>
        </div>
        <div>
          <div class="text-gray-500 mb-0.5">Assessment Time</div>
          <div class="font-semibold text-gray-800">16 May 2025, 10:20 AM</div>
        </div>
        <div>
          <div class="text-gray-500 mb-0.5">Implementation Time</div>
          <div class="font-semibold text-gray-800">16 May 2025, 10:30 AM <span class="text-gray-400">(Auto)</span></div>
        </div>
      </div>

      <div class="grid grid-cols-3 gap-5">
        <!-- Col 1: AI Actions + Additional -->
        <div class="space-y-4">
          <!-- AI Recommended -->
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
            <h3 class="font-semibold text-gray-800 text-sm mb-3">
              1. AI Recommended Actions
              <span class="text-xs text-blue-500 font-normal">(From Previous Assessment)</span>
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

          <!-- Additional Measures -->
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
            <h3 class="font-semibold text-gray-800 text-sm mb-3">3. Additional Measures Taken</h3>
            <div class="grid grid-cols-2 gap-x-4 gap-y-2">
              <label v-for="(val, key) in additional" :key="key"
                class="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" v-model="additional[key]"
                  class="w-3.5 h-3.5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"/>
                <span class="text-xs text-gray-700">{{ key }}</span>
              </label>
            </div>
            <input v-if="additional['Other']" type="text" placeholder="Please specify"
              class="w-full mt-2 border border-gray-200 rounded-lg px-2.5 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"/>
          </div>
        </div>

        <!-- Col 2: Actions Implemented + Evidence + Outcome + Timeline -->
        <div class="space-y-4">
          <!-- Actions Implemented -->
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
            <h3 class="font-semibold text-gray-800 text-sm mb-3">2. Actions Actually Implemented</h3>
            <div class="space-y-3">
              <div class="grid grid-cols-[1fr_auto_auto_1fr] gap-2 text-xs font-semibold text-gray-500 border-b border-gray-100 pb-2">
                <span>Recommended Action</span>
                <span class="text-center col-span-2">Implemented?</span>
                <span>Notes (Time, Details)</span>
              </div>
              <div v-for="(imp, action) in implemented" :key="action" class="grid grid-cols-[1fr_auto_auto_1fr] gap-2 items-center text-xs">
                <span class="text-gray-700">{{ action }}</span>
                <label class="flex items-center gap-1 cursor-pointer">
                  <input type="checkbox" v-model="imp.yes" class="w-3 h-3 text-blue-600 focus:ring-blue-500"/>
                  <span>Yes</span>
                </label>
                <label class="flex items-center gap-1 cursor-pointer">
                  <input type="checkbox" v-model="imp.no" class="w-3 h-3 text-blue-600 focus:ring-blue-500"/>
                  <span>No</span>
                </label>
                <div class="flex items-center gap-1">
                  <input v-model="imp.note" type="text" class="flex-1 border border-gray-200 rounded px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"/>
                  <button class="text-gray-400 hover:text-blue-500 flex-shrink-0">
                    <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Evidence Upload -->
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
            <h3 class="font-semibold text-gray-800 text-sm mb-3">7. Evidence Upload</h3>
            <div class="grid grid-cols-5 gap-2">
              <div v-for="slot in ['Patient Photo','Medication Given','Referral Slip','Test Reports','Other Documents']"
                :key="slot" class="text-center">
                <div class="border border-dashed border-gray-200 rounded-lg p-2 hover:border-blue-400 transition cursor-pointer bg-gray-50 hover:bg-blue-50">
                  <svg class="w-5 h-5 text-blue-400 mx-auto mb-1" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                    <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>
                    <circle cx="12" cy="13" r="4"/>
                  </svg>
                  <div class="text-[9px] text-gray-500 leading-tight">{{ slot }}</div>
                  <div class="text-[8px] text-gray-400 mt-0.5">JPG, PNG<br>Max 5MB</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Outcome Summary -->
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
            <h3 class="font-semibold text-gray-800 text-sm mb-3">8. Outcome Summary <span class="text-red-500">*</span></h3>
            <textarea v-model="outcome" rows="5" maxlength="1000"
              class="w-full border border-gray-200 rounded-lg px-3 py-2 text-xs text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"></textarea>
            <div class="text-right text-xs text-gray-400 mt-1">{{ outcome.length }} / 1000</div>
          </div>

          <!-- Timeline -->
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
            <h3 class="font-semibold text-gray-800 text-sm mb-3">9. Implementation Timeline
              <span class="text-xs text-blue-500 font-normal">(Auto Generated)</span>
            </h3>
            <div class="space-y-2">
              <div v-for="t in timeline" :key="t.time" class="flex items-center gap-3 text-xs">
                <div :class="['w-4 h-4 rounded-full flex items-center justify-center flex-shrink-0', t.done ? 'bg-green-500' : 'bg-gray-200']">
                  <svg v-if="t.done" class="w-2.5 h-2.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path d="M20 6L9 17l-5-5"/></svg>
                  <div v-else class="w-2 h-2 rounded-full bg-gray-400"></div>
                </div>
                <span class="text-gray-500 w-16 flex-shrink-0">{{ t.time }}</span>
                <span :class="t.done ? 'text-gray-700' : 'text-gray-400'">{{ t.label }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Col 3: Patient Response + Referral + Teleconsultation -->
        <div class="space-y-4">
          <!-- Patient Response -->
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
            <h3 class="font-semibold text-gray-800 text-sm mb-3">4. Patient Response</h3>
            <div class="flex gap-2 flex-wrap">
              <button v-for="r in responseOptions" :key="r"
                :class="['px-2.5 py-2 border rounded-lg text-xs font-medium transition flex-1 min-w-0',
                  patientResponse === r ? responseColors[r] + ' border-2' : 'border-gray-200 text-gray-500 hover:border-gray-300']"
                @click="patientResponse = r">
                {{ r }}
              </button>
            </div>
          </div>

          <!-- Referral Status -->
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
            <h3 class="font-semibold text-gray-800 text-sm mb-3">5. Referral Status</h3>
            <div class="space-y-3 text-xs">
              <div class="flex items-center gap-4">
                <span class="text-gray-600">Referral Required?</span>
                <label class="flex items-center gap-1.5 cursor-pointer">
                  <input type="radio" v-model="referral.required" value="yes" class="text-blue-600"/>
                  <span>Yes</span>
                </label>
                <label class="flex items-center gap-1.5 cursor-pointer">
                  <input type="radio" v-model="referral.required" value="no" class="text-blue-600"/>
                  <span>No</span>
                </label>
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
                  <input v-model="referral.time" type="text" class="w-full border border-gray-200 rounded-lg px-2.5 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"/>
                </div>
                <div>
                  <label class="block text-gray-600 mb-1">Transport <span class="text-red-500">*</span></label>
                  <div class="flex gap-3 flex-wrap">
                    <label v-for="t in ['Ambulance','Private Vehicle','Government Vehicle','Walking']" :key="t"
                      class="flex items-center gap-1.5 cursor-pointer">
                      <input type="radio" v-model="referral.transport" :value="t" class="text-blue-600"/>
                      <span class="text-xs">{{ t }}</span>
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
                <label class="flex items-center gap-1.5 cursor-pointer">
                  <input type="radio" v-model="teleconsult.done" value="yes" class="text-blue-600"/>
                  <span>Yes</span>
                </label>
                <label class="flex items-center gap-1.5 cursor-pointer">
                  <input type="radio" v-model="teleconsult.done" value="no" class="text-blue-600"/>
                  <span>No</span>
                </label>
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
                  <input v-model="teleconsult.time" type="text" class="w-full border border-gray-200 rounded-lg px-2.5 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"/>
                </div>
                <div>
                  <label class="block text-gray-600 mb-1">Advice Given</label>
                  <textarea v-model="teleconsult.advice" rows="4"
                    class="w-full border border-gray-200 rounded-lg px-2.5 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none"></textarea>
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
          <button class="flex items-center gap-2 px-5 py-2.5 border border-blue-200 text-blue-600 text-sm font-medium rounded-lg hover:bg-blue-50 transition">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
              <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/>
            </svg>
            Save Draft
          </button>
        </div>
        <button @click="router.push('/dashboard')"
          class="flex items-center gap-2 px-8 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-lg transition">
          Submit Measures
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
        </button>
      </div>
    </div>
  </AppShell>
</template>
