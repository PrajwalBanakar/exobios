<script setup>
import { ref, computed, reactive } from 'vue'
import AppShell from '@/shared/components/AppShell.vue'
import { useReferralsStore } from '@/features/referrals/stores/referrals'
import { useActionPlanStore } from '@/shared/stores/actionPlan'
import { usePatientsStore } from '@/features/patients/stores/patients'
import { HOSPITALS, HOSPITAL_TYPE, getHospitalById } from '@/shared/constants/hospitals'
import { TRANSPORT_OPTIONS } from '@/shared/constants/transport'
import { useI18n } from '@/i18n'

const { t }          = useI18n()
const store          = useReferralsStore()
const actionPlan     = useActionPlanStore()
const patientsStore  = usePatientsStore()

const search     = ref('')
const showModal  = ref(false)
const addSuccess = ref(false)

const form = reactive({ patientName: '', facilityType: HOSPITAL_TYPE.GOVERNMENT, facility: '', transport: '', reason: '', ashaWorker: 'Sunita Devi' })

const filteredFacilities = computed(() => HOSPITALS.filter(h => h.type === form.facilityType))

const filtered = computed(() => {
  if (!search.value.trim()) return store.items
  const q = search.value.toLowerCase()
  return store.items.filter(r =>
    r.patientName.toLowerCase().includes(q) || r.hospital.toLowerCase().includes(q) || r.ashaWorker.toLowerCase().includes(q)
  )
})

// Referrals flagged during an assessment's plan of action but not yet turned into a
// referral record here — reads the same store AIResultView/MeasuresView write to.
const pendingFromAssessments = computed(() => actionPlan.pendingReferrals.map(p => ({
  patientId: p.patientId,
  patientName: patientsStore.getById(p.patientId)?.name || `Patient #${p.patientId}`,
  hospital: getHospitalById(p.hospitalId),
})))

function openModal() {
  form.patientName = ''; form.facilityType = HOSPITAL_TYPE.GOVERNMENT; form.facility = ''; form.transport = ''; form.reason = ''
  showModal.value = true
}

function openModalFromPlan(p) {
  form.patientName = p.patientName
  form.facilityType = p.hospital?.type || HOSPITAL_TYPE.GOVERNMENT
  form.facility = p.hospital?.id || ''
  form.transport = ''
  form.reason = ''
  showModal.value = true
}

function submitReferral() {
  if (!form.patientName.trim() || !form.facility) return
  const hospital = getHospitalById(form.facility)
  store.add({ patientName: form.patientName, hospital: hospital?.name || form.facility, facilityType: form.facilityType, transport: form.transport || 'Private Vehicle', ashaWorker: form.ashaWorker, notes: form.reason })
  showModal.value = false
  addSuccess.value = true
  setTimeout(() => { addSuccess.value = false }, 2500)
}

function sendWhatsApp(r) {
  const msg = encodeURIComponent(`Referral: ${r.patientName} referred to ${r.hospital} via ${r.transport}. Date: ${r.date}`)
  window.open(`https://wa.me/?text=${msg}`, '_blank')
}
</script>

<template>
  <AppShell>
    <template #page-title>{{ t('referrals.title') }}</template>
    <template #page-subtitle>{{ t('referrals.subtitle') }}</template>

    <template #topbar-left>
      <div class="flex items-center gap-3">
        <div class="relative hidden md:block">
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
          <input v-model="search" type="text" :placeholder="t('referrals.searchPlaceholder')"
            class="pl-9 pr-4 py-2 text-sm border border-gray-200 rounded-lg bg-gray-50 w-64 focus:outline-none focus:ring-2 focus:ring-blue-500"/>
        </div>
      </div>
    </template>

    <div class="p-4 md:p-6 space-y-5">

      <transition enter-active-class="transition-all duration-300" enter-from-class="opacity-0 -translate-y-2" leave-active-class="transition-all duration-200" leave-to-class="opacity-0">
        <div v-if="addSuccess" class="bg-green-50 border border-green-200 text-green-700 rounded-xl px-5 py-3 flex items-center gap-2 font-medium text-sm">
          <svg class="w-5 h-5 text-green-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg>
          {{ t('referrals.addSuccess') }}
        </div>
      </transition>

      <!-- Referrals flagged during an assessment's plan of action, not yet recorded here -->
      <div v-if="pendingFromAssessments.length" class="bg-amber-50 border border-amber-200 rounded-xl px-5 py-3 space-y-2">
        <h3 class="text-sm font-semibold text-amber-800">Pending Referrals From Assessments</h3>
        <div v-for="p in pendingFromAssessments" :key="p.patientId" class="flex items-center justify-between gap-3 text-sm">
          <span class="text-amber-700">{{ p.patientName }} → {{ p.hospital?.name || 'Hospital not selected' }}</span>
          <button @click="openModalFromPlan(p)" class="text-xs text-blue-600 hover:underline font-semibold flex-shrink-0">Create Referral Record</button>
        </div>
      </div>

      <div class="bg-white rounded-xl border border-gray-100 shadow-sm">
        <div class="flex items-center justify-between px-5 py-4 border-b border-gray-100 gap-3 flex-wrap">
          <h2 class="font-semibold text-gray-900">{{ t('referrals.title') }}</h2>
          <button @click="openModal" class="flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-lg transition">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M12 5v14M5 12h14"/></svg>
            {{ t('referrals.newReferral') }}
          </button>
        </div>

        <div v-if="filtered.length === 0" class="py-16 text-center">
          <svg class="w-12 h-12 text-gray-200 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
          <p class="text-sm text-gray-500">{{ t('referrals.noReferrals') }}</p>
        </div>

        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-gray-100 bg-gray-50/50">
                <th class="text-left text-xs font-semibold text-gray-500 px-5 py-3">{{ t('referrals.patient') }}</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">{{ t('referrals.hospital') }}</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">{{ t('referrals.clinicType') }}</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">{{ t('referrals.ashaWorker') }}</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">{{ t('referrals.transport') }}</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">{{ t('common.date') }}</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">{{ t('common.actions') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in filtered" :key="r.id" class="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                <td class="px-5 py-3.5">
                  <div class="flex items-center gap-2.5">
                    <div class="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-xs font-semibold text-blue-600 flex-shrink-0">
                      {{ r.patientName.split(' ').map(n=>n[0]).join('').slice(0,2).toUpperCase() }}
                    </div>
                    <div>
                      <div class="font-medium text-gray-800">{{ r.patientName }}</div>
                      <div v-if="r.notes" class="text-[10px] text-gray-400 truncate max-w-[140px]">{{ r.notes }}</div>
                    </div>
                  </div>
                </td>
                <td class="px-4 py-3.5">
                  <div class="flex items-center gap-1.5">
                    <svg class="w-3.5 h-3.5 text-gray-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/></svg>
                    <span class="text-sm text-gray-700">{{ r.hospital }}</span>
                  </div>
                </td>
                <td class="px-4 py-3.5">
                  <span :class="[r.facilityType === 'Private' ? 'bg-purple-100 text-purple-600' : 'bg-green-100 text-green-700', 'px-2 py-0.5 text-xs font-medium rounded']">
                    {{ r.facilityType === 'Private' ? t('referrals.private') : t('referrals.government') }}
                  </span>
                </td>
                <td class="px-4 py-3.5 text-gray-600 text-sm">{{ r.ashaWorker }}</td>
                <td class="px-4 py-3.5"><span class="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded font-medium">{{ r.transport }}</span></td>
                <td class="px-4 py-3.5 text-gray-500 text-xs">{{ r.date }}</td>
                <td class="px-4 py-3.5">
                  <button @click="sendWhatsApp(r)" class="flex items-center gap-1 text-xs text-green-600 hover:underline border border-green-200 px-2.5 py-1 rounded-lg hover:bg-green-50 transition">
                    <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893A11.821 11.821 0 0020.885 3.488"/></svg>
                    WhatsApp
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="px-5 py-3 text-xs text-gray-400 border-t border-gray-50">
          {{ t('common.showing') }} {{ filtered.length }} {{ t('common.of') }} {{ store.items.length }} {{ t('referrals.title').toLowerCase() }}
        </div>
      </div>
    </div>

    <!-- New Referral Modal -->
    <teleport to="body">
      <div v-if="showModal" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" @click.self="showModal=false">
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-lg">
          <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
            <h3 class="font-semibold text-gray-900 text-lg">{{ t('referrals.newReferral') }}</h3>
            <button @click="showModal=false" class="text-gray-400 hover:text-gray-600 p-1" aria-label="Close">
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18M6 6l12 12"/></svg>
            </button>
          </div>
          <div class="px-6 py-5 space-y-4">
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1.5">{{ t('referrals.patient') }} <span class="text-red-500">*</span></label>
              <input v-model="form.patientName" type="text" :placeholder="t('referrals.patient')" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"/>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1.5">{{ t('referrals.facilityType') }}</label>
              <div class="flex gap-2">
                <button v-for="type in [HOSPITAL_TYPE.GOVERNMENT, HOSPITAL_TYPE.PRIVATE]" :key="type"
                  :class="['flex-1 py-2 rounded-lg text-sm font-medium border transition', form.facilityType === type ? 'bg-blue-600 text-white border-blue-600' : 'border-gray-200 text-gray-600 hover:border-blue-300']"
                  @click="form.facilityType = type; form.facility = ''">
                  {{ type === HOSPITAL_TYPE.GOVERNMENT ? t('referrals.government') : t('referrals.private') }}
                </button>
              </div>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1.5">{{ t('referrals.facility') }} <span class="text-red-500">*</span></label>
              <select v-model="form.facility" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white">
                <option value="">{{ t('referrals.selectFacility') }}</option>
                <option v-for="f in filteredFacilities" :key="f.id" :value="f.id">{{ f.name }}</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1.5">{{ t('referrals.transport') }}</label>
              <select v-model="form.transport" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white">
                <option value="">{{ t('referrals.selectTransport') }}</option>
                <option v-for="opt in TRANSPORT_OPTIONS" :key="opt" :value="opt">{{ opt }}</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1.5">{{ t('referrals.reason') }}</label>
              <textarea v-model="form.reason" rows="2" :placeholder="t('referrals.reasonPlaceholder')" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"/>
            </div>
          </div>
          <div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-100">
            <button @click="showModal=false" class="px-4 py-2 text-sm border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50 transition">{{ t('common.cancel') }}</button>
            <button @click="submitReferral" :disabled="!form.patientName.trim() || !form.facility"
              class="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed">
              {{ t('common.submit') }}
            </button>
          </div>
        </div>
      </div>
    </teleport>
  </AppShell>
</template>
