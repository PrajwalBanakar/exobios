<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import AppShell from '@/shared/components/AppShell.vue'
import { usePatientsStore } from '@/features/patients/stores/patients'
import { useI18n } from '@/i18n'

const router = useRouter()
const route  = useRoute()
const store  = usePatientsStore()
const { t }  = useI18n()

const isEdit    = computed(() => route.name === 'EditPatient')
const patientId = computed(() => isEdit.value ? Number(route.params.id) : null)
const existing  = computed(() => isEdit.value ? store.getById(patientId.value) : null)

const form = reactive({
  name: '', dob: '', gender: '', phone: '', occupation: '', abhaId: '', fatherSpouseName: '',
  address: { details: '', village: '', pincode: '', taluk: '', district: '', state: '' },
  family: {
    maritalStatus: '', spouseName: '', spouseAge: '',
    children: [], householdMembers: [],
    fatherName: '', fatherAge: '', motherName: '', motherAge: '',
  },
  photo: '',
})

const calculatedAge = computed(() => {
  if (!form.dob) return null
  const birth = new Date(form.dob)
  const today = new Date()
  let age = today.getFullYear() - birth.getFullYear()
  const m = today.getMonth() - birth.getMonth()
  if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) age--
  return age >= 0 ? age : null
})

const guardianLabel = computed(() =>
  form.family.maritalStatus === 'Married' || form.family.maritalStatus === 'Widowed' ? 'Spouse Name' : "Father's Name"
)

// Pre-fill for edit mode
if (isEdit.value && existing.value) {
  const p = existing.value
  form.name = p.name || ''; form.dob = p.dob || ''; form.gender = p.gender || ''
  form.phone = p.phone || ''; form.occupation = p.occupation || ''
  form.abhaId = p.abhaId || ''; form.fatherSpouseName = p.fatherSpouseName || ''; form.photo = p.photo || ''
  if (p.address) Object.assign(form.address, p.address)
  if (p.family)  Object.assign(form.family,  { ...p.family, children: [...(p.family?.children || [])], householdMembers: [...(p.family?.householdMembers || [])] })
}

// Children list
const newChild  = reactive({ name: '', age: '' })
function addChild() {
  if (!newChild.name.trim()) return
  form.family.children.push({ name: newChild.name.trim(), age: Number(newChild.age) || 0 })
  newChild.name = ''; newChild.age = ''
}
function removeChild(i) { form.family.children.splice(i, 1) }

// Household members
const newMember = reactive({ name: '', relation: '', age: '' })
function addMember() {
  if (!newMember.name.trim()) return
  form.family.householdMembers.push({ name: newMember.name.trim(), relation: newMember.relation, age: Number(newMember.age) || 0 })
  newMember.name = ''; newMember.relation = ''; newMember.age = ''
}
function removeMember(i) { form.family.householdMembers.splice(i, 1) }

// Photo via camera/file
function handlePhoto(e) {
  const file = e.target.files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = (ev) => { form.photo = ev.target.result }
  reader.readAsDataURL(file)
}

const saving = ref(false)
const errors = ref({})

function validate() {
  errors.value = {}
  if (!form.name.trim())                       errors.value.name   = 'Name is required'
  if (!form.dob)                               errors.value.dob    = 'Date of birth is required'
  if (!form.gender)                            errors.value.gender = 'Sex is required'
  if (!form.phone || form.phone.length < 10)  errors.value.phone  = 'Valid 10-digit phone required'
  return Object.keys(errors.value).length === 0
}

async function savePatient() {
  if (!validate()) return
  saving.value = true
  await new Promise(r => setTimeout(r, 300))
  const location = [form.address.village, form.address.district].filter(Boolean).join(', ') || 'Unknown'
  const now      = new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
  const data     = {
    name: form.name.trim(), dob: form.dob, gender: form.gender, phone: form.phone,
    occupation: form.occupation, abhaId: form.abhaId, fatherSpouseName: form.fatherSpouseName, photo: form.photo,
    address: { ...form.address },
    family: { ...form.family, children: [...form.family.children], householdMembers: [...form.family.householdMembers] },
    location, risk: isEdit.value ? (existing.value?.risk || 'Low') : 'Low', date: now,
  }
  if (isEdit.value) {
    store.update(patientId.value, data)
    saving.value = false
    router.push('/patients')
  } else {
    const newId = store.add(data)
    saving.value = false
    // Continue to assessment for this newly registered patient
    router.push(`/assessment/new?patientId=${newId}`)
  }
}

const IC = 'w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500'
const LC = 'block text-xs font-medium text-gray-600 mb-1.5'
</script>

<template>
  <AppShell>
    <template #page-title>{{ isEdit ? 'Edit Patient' : 'Register Patient' }}</template>
    <template #page-subtitle>{{ isEdit ? 'Update patient information' : 'Add a new patient record' }}</template>

    <div class="p-4 md:p-6">
      <button @click="router.back()" class="flex items-center gap-1.5 text-sm text-blue-600 hover:underline mb-5">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 5l-7 7 7 7"/></svg>
        Back
      </button>

      <div class="max-w-3xl space-y-5">

        <!-- SECTION 1: Personal Information -->
        <div class="bg-white rounded-xl border border-gray-100 shadow-sm">
          <div class="flex items-center gap-3 px-5 py-4 border-b border-gray-100">
            <div class="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
              <span class="text-sm font-bold text-blue-600">1</span>
            </div>
            <div>
              <h2 class="font-semibold text-gray-800">Personal Information</h2>
              <p class="text-xs text-gray-400">Basic identification details</p>
            </div>
          </div>
          <div class="px-5 py-5 space-y-4">
            <!-- Photo + Name -->
            <div class="flex items-start gap-5">
              <div class="flex-shrink-0 text-center">
                <label class="cursor-pointer group" title="Tap to capture or upload photo">
                  <div class="w-20 h-20 rounded-full bg-gray-100 border-2 border-dashed border-gray-300 group-hover:border-blue-400 flex items-center justify-center overflow-hidden transition">
                    <img v-if="form.photo" :src="form.photo" class="w-full h-full object-cover rounded-full"/>
                    <div v-else class="text-center p-2">
                      <svg class="w-6 h-6 text-gray-300 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="8" r="4"/><path d="M3 20c0-4 3.582-7 8-7h2c4.418 0 8 3 8 7"/></svg>
                      <span class="text-[9px] text-gray-400 mt-1 block leading-tight">Tap to<br>add photo</span>
                    </div>
                  </div>
                  <input type="file" accept="image/*" capture="environment" class="hidden" @change="handlePhoto"/>
                </label>
              </div>
              <div class="flex-1 space-y-3">
                <div>
                  <label :class="LC">Full Name <span class="text-red-500">*</span></label>
                  <input v-model="form.name" type="text" placeholder="Patient's full name" :class="IC + (errors.name ? ' border-red-300 ring-1 ring-red-300' : '')"/>
                  <p v-if="errors.name" class="text-red-500 text-xs mt-1">{{ errors.name }}</p>
                </div>
                <div class="grid grid-cols-2 gap-3">
                  <div>
                    <label :class="LC">Date of Birth <span class="text-red-500">*</span></label>
                    <input v-model="form.dob" type="date" :class="IC + (errors.dob ? ' border-red-300' : '')"/>
                    <p v-if="calculatedAge !== null" class="text-xs text-blue-600 mt-1 font-medium">Age: {{ calculatedAge }} years</p>
                    <p v-if="errors.dob" class="text-red-500 text-xs mt-1">{{ errors.dob }}</p>
                  </div>
                  <div>
                    <label :class="LC">Sex <span class="text-red-500">*</span></label>
                    <select v-model="form.gender" :class="IC + ' bg-white' + (errors.gender ? ' border-red-300' : '')">
                      <option value="">— Select —</option>
                      <option value="Male">Male</option>
                      <option value="Female">Female</option>
                      <option value="Other">Other</option>
                    </select>
                    <p v-if="errors.gender" class="text-red-500 text-xs mt-1">{{ errors.gender }}</p>
                  </div>
                </div>
              </div>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <label :class="LC">Phone Number <span class="text-red-500">*</span></label>
                <input v-model="form.phone" type="tel" maxlength="10" placeholder="10-digit number" :class="IC + (errors.phone ? ' border-red-300' : '')"/>
                <p v-if="errors.phone" class="text-red-500 text-xs mt-1">{{ errors.phone }}</p>
              </div>
              <div>
                <label :class="LC">Occupation</label>
                <input v-model="form.occupation" type="text" placeholder="e.g. Farmer, Teacher, Homemaker" :class="IC"/>
              </div>
              <div>
                <label :class="LC">{{ guardianLabel }}</label>
                <input v-model="form.fatherSpouseName" type="text" :placeholder="guardianLabel" :class="IC"/>
              </div>
              <div>
                <label :class="LC">ABHA ID</label>
                <input v-model="form.abhaId" type="text" placeholder="12-XXXX-XXXX-XXXX" :class="IC"/>
              </div>
            </div>
          </div>
        </div>

        <!-- SECTION 2: Address -->
        <div class="bg-white rounded-xl border border-gray-100 shadow-sm">
          <div class="flex items-center gap-3 px-5 py-4 border-b border-gray-100">
            <div class="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center flex-shrink-0">
              <span class="text-sm font-bold text-purple-600">2</span>
            </div>
            <div>
              <h2 class="font-semibold text-gray-800">Address</h2>
              <p class="text-xs text-gray-400">Patient's residential address</p>
            </div>
          </div>
          <div class="px-5 py-5 space-y-3">
            <div>
              <label :class="LC">House / Door Details</label>
              <input v-model="form.address.details" type="text" placeholder="House No., Street, Landmark" :class="IC"/>
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label :class="LC">Village / Town</label>
                <input v-model="form.address.village" type="text" placeholder="Village or town name" :class="IC"/>
              </div>
              <div>
                <label :class="LC">Pincode</label>
                <input v-model="form.address.pincode" type="text" maxlength="6" placeholder="6-digit pincode" :class="IC"/>
              </div>
              <div>
                <label :class="LC">Taluk / Block</label>
                <input v-model="form.address.taluk" type="text" placeholder="Taluk or Block" :class="IC"/>
              </div>
              <div>
                <label :class="LC">District</label>
                <input v-model="form.address.district" type="text" placeholder="District name" :class="IC"/>
              </div>
              <div class="col-span-2">
                <label :class="LC">State</label>
                <input v-model="form.address.state" type="text" placeholder="State" :class="IC"/>
              </div>
            </div>
          </div>
        </div>

        <!-- SECTION 3: Family Details -->
        <div class="bg-white rounded-xl border border-gray-100 shadow-sm">
          <div class="flex items-center gap-3 px-5 py-4 border-b border-gray-100">
            <div class="w-8 h-8 rounded-full bg-teal-100 flex items-center justify-center flex-shrink-0">
              <span class="text-sm font-bold text-teal-600">3</span>
            </div>
            <div>
              <h2 class="font-semibold text-gray-800">Family Details</h2>
              <p class="text-xs text-gray-400">Marital status, spouse, children, and household</p>
            </div>
          </div>
          <div class="px-5 py-5 space-y-4">
            <!-- Marital status chips -->
            <div>
              <label :class="LC">Marital Status</label>
              <div class="flex flex-wrap gap-2">
                <button v-for="opt in ['Married', 'Unmarried', 'Widowed', 'Divorced']" :key="opt"
                  type="button"
                  :class="['px-4 py-2 rounded-lg text-sm border transition', form.family.maritalStatus === opt ? 'bg-blue-600 text-white border-blue-600' : 'border-gray-200 text-gray-600 hover:border-blue-300 bg-white']"
                  @click="form.family.maritalStatus = opt">
                  {{ opt }}
                </button>
              </div>
            </div>

            <!-- Married / Widowed fields -->
            <template v-if="form.family.maritalStatus === 'Married' || form.family.maritalStatus === 'Widowed'">
              <div class="grid grid-cols-2 gap-3 p-4 bg-blue-50/40 rounded-xl border border-blue-100">
                <div>
                  <label :class="LC">Spouse Name</label>
                  <input v-model="form.family.spouseName" type="text" placeholder="Spouse's full name" :class="IC"/>
                </div>
                <div>
                  <label :class="LC">Spouse Age</label>
                  <input v-model="form.family.spouseAge" type="number" min="0" max="120" placeholder="Age" :class="IC"/>
                </div>
              </div>

              <!-- Children -->
              <div>
                <label :class="LC">Children</label>
                <div class="space-y-2 mb-2">
                  <div v-for="(c, i) in form.family.children" :key="i"
                    class="flex items-center gap-2 bg-gray-50 rounded-lg px-3 py-2 text-sm">
                    <span class="text-xs text-gray-500 font-semibold w-5">{{ i + 1 }}.</span>
                    <span class="flex-1 text-gray-700">{{ c.name }}</span>
                    <span class="text-gray-400 text-xs">{{ c.age }} yrs</span>
                    <button type="button" @click="removeChild(i)" class="ml-2 text-red-400 hover:text-red-600">
                      <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M18 6 6 18M6 6l12 12"/></svg>
                    </button>
                  </div>
                </div>
                <div class="flex gap-2">
                  <input v-model="newChild.name" type="text" placeholder="Child's name" :class="IC"/>
                  <input v-model="newChild.age" type="number" min="0" max="30" placeholder="Age" class="w-20 border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"/>
                  <button type="button" @click="addChild" class="px-3 py-2 bg-blue-50 text-blue-600 text-sm rounded-lg hover:bg-blue-100 transition flex-shrink-0 font-medium">+ Add</button>
                </div>
              </div>
            </template>

            <!-- Unmarried fields -->
            <template v-if="form.family.maritalStatus === 'Unmarried'">
              <div class="grid grid-cols-2 gap-3 p-4 bg-purple-50/40 rounded-xl border border-purple-100">
                <div>
                  <label :class="LC">Father's Name</label>
                  <input v-model="form.family.fatherName" type="text" placeholder="Father's name" :class="IC"/>
                </div>
                <div>
                  <label :class="LC">Father's Age</label>
                  <input v-model="form.family.fatherAge" type="number" min="0" placeholder="Age" :class="IC"/>
                </div>
                <div>
                  <label :class="LC">Mother's Name</label>
                  <input v-model="form.family.motherName" type="text" placeholder="Mother's name" :class="IC"/>
                </div>
                <div>
                  <label :class="LC">Mother's Age</label>
                  <input v-model="form.family.motherAge" type="number" min="0" placeholder="Age" :class="IC"/>
                </div>
              </div>
            </template>

            <!-- Household Members -->
            <div>
              <label :class="LC">Other Household Members <span class="text-gray-400 font-normal">(optional)</span></label>
              <div class="space-y-2 mb-2">
                <div v-for="(m, i) in form.family.householdMembers" :key="i"
                  class="flex items-center gap-2 bg-gray-50 rounded-lg px-3 py-2 text-sm">
                  <span class="flex-1 text-gray-700">{{ m.name }} <span class="text-gray-400">({{ m.relation }}, {{ m.age }} yrs)</span></span>
                  <button type="button" @click="removeMember(i)" class="text-red-400 hover:text-red-600">
                    <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M18 6 6 18M6 6l12 12"/></svg>
                  </button>
                </div>
              </div>
              <div class="grid grid-cols-3 gap-2">
                <input v-model="newMember.name" type="text" placeholder="Name" :class="IC"/>
                <input v-model="newMember.relation" type="text" placeholder="Relation (e.g. Uncle)" :class="IC"/>
                <div class="flex gap-2">
                  <input v-model="newMember.age" type="number" min="0" placeholder="Age" class="flex-1 border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"/>
                  <button type="button" @click="addMember" class="px-3 py-2 bg-blue-50 text-blue-600 text-sm rounded-lg hover:bg-blue-100 transition font-medium">+</button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Bottom action bar -->
        <div class="flex items-center justify-end gap-3 py-2">
          <button type="button" @click="router.back()" class="px-5 py-2.5 border border-gray-200 text-gray-600 text-sm font-medium rounded-lg hover:bg-gray-50 transition">
            Cancel
          </button>
          <button type="button" @click="savePatient" :disabled="saving"
            class="flex items-center gap-2 px-8 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white text-sm font-semibold rounded-lg transition">
            <svg v-if="saving" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 0 1 8-8v8H4z"/>
            </svg>
            {{ isEdit ? 'Save Changes' : 'Register Patient' }}
          </button>
        </div>
      </div>
    </div>
  </AppShell>
</template>
