<script setup>
import RadioGroup from '@/shared/components/forms/RadioGroup.vue'

defineProps({
  // examForm.generalExam.doctorGeneralExam — mutated in place (already reactive via the parent's reactive()).
  exam: { type: Object, required: true },
})

const LC  = 'block text-xs font-medium text-slate-600 mb-1.5'
const SEL = 'w-full border border-slate-200 rounded-xl px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500'
const IC  = 'w-full border border-slate-200 rounded-xl px-3 py-2 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500'
const TC  = 'w-full border border-slate-200 rounded-xl px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500'

const CONSCIOUSNESS_OPTIONS = ['Alert', 'Drowsy', 'Confused', 'Unconscious']
const PRESENT_ABSENT        = ['Present', 'Absent']
const GENERAL_SIGNS         = [['pallor', 'Pallor'], ['icterus', 'Icterus'], ['cyanosis', 'Cyanosis'], ['clubbing', 'Clubbing']]
const LYMPH_SITES           = ['Cervical', 'Axillary', 'Inguinal', 'Generalized']
const EDEMA_GRADES          = ['Grade 1', 'Grade 2', 'Grade 3', 'Grade 4']

// GCS-aligned scale — standard Glasgow Coma Scale response options.
const GCS_EYE = [
  { value: '4', label: '4 — Spontaneous' },
  { value: '3', label: '3 — To speech' },
  { value: '2', label: '2 — To pain' },
  { value: '1', label: '1 — None' },
]
const GCS_VERBAL = [
  { value: '5', label: '5 — Oriented' },
  { value: '4', label: '4 — Confused' },
  { value: '3', label: '3 — Inappropriate words' },
  { value: '2', label: '2 — Incomprehensible sounds' },
  { value: '1', label: '1 — None' },
]
const GCS_MOTOR = [
  { value: '6', label: '6 — Obeys commands' },
  { value: '5', label: '5 — Localizes pain' },
  { value: '4', label: '4 — Withdraws from pain' },
  { value: '3', label: '3 — Abnormal flexion' },
  { value: '2', label: '2 — Abnormal extension' },
  { value: '1', label: '1 — None' },
]
</script>

<template>
  <div class="space-y-5">
    <!-- A. Consciousness + GCS -->
    <div>
      <label :class="LC">Consciousness</label>
      <RadioGroup v-model="exam.consciousness.level" :options="CONSCIOUSNESS_OPTIONS" color="blue" columns="flex flex-wrap gap-2"/>

      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-3">
        <div>
          <label :class="LC">GCS — Eye Response</label>
          <select v-model="exam.consciousness.gcs.eye" :class="SEL">
            <option value="">— Select —</option>
            <option v-for="o in GCS_EYE" :key="o.value" :value="o.value">{{ o.label }}</option>
          </select>
        </div>
        <div>
          <label :class="LC">GCS — Verbal Response</label>
          <select v-model="exam.consciousness.gcs.verbal" :class="SEL">
            <option value="">— Select —</option>
            <option v-for="o in GCS_VERBAL" :key="o.value" :value="o.value">{{ o.label }}</option>
          </select>
        </div>
        <div>
          <label :class="LC">GCS — Motor Response</label>
          <select v-model="exam.consciousness.gcs.motor" :class="SEL">
            <option value="">— Select —</option>
            <option v-for="o in GCS_MOTOR" :key="o.value" :value="o.value">{{ o.label }}</option>
          </select>
        </div>
      </div>
    </div>

    <!-- B. General Signs -->
    <div>
      <label :class="LC">General Signs</label>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div v-for="[key, label] in GENERAL_SIGNS" :key="key">
          <div class="text-xs text-slate-500 mb-1">{{ label }}</div>
          <RadioGroup v-model="exam.generalSigns[key]" :options="PRESENT_ABSENT" color="blue" columns="flex gap-2"/>
        </div>
      </div>
    </div>

    <!-- C. Lymphadenopathy -->
    <div class="border border-slate-100 rounded-xl overflow-hidden">
      <label class="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-slate-50 transition">
        <input v-model="exam.lymphadenopathy.present" type="checkbox" class="w-4 h-4 rounded border-slate-300 text-blue-600 accent-blue-600"/>
        <span class="text-sm font-medium text-slate-700 flex-1">Lymphadenopathy Present</span>
      </label>
      <div v-if="exam.lymphadenopathy.present" class="px-4 pb-4 pt-0 space-y-3">
        <div>
          <label :class="LC">Site</label>
          <RadioGroup v-model="exam.lymphadenopathy.site" :options="LYMPH_SITES" color="blue" columns="flex flex-wrap gap-2"/>
        </div>
        <div>
          <label :class="LC">Character</label>
          <input v-model="exam.lymphadenopathy.character" type="text" placeholder="e.g. Tender, mobile, matted" :class="IC" lang="auto"/>
        </div>
      </div>
    </div>

    <!-- D. Edema -->
    <div class="border border-slate-100 rounded-xl overflow-hidden">
      <label class="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-slate-50 transition">
        <input v-model="exam.edema.present" type="checkbox" class="w-4 h-4 rounded border-slate-300 text-blue-600 accent-blue-600"/>
        <span class="text-sm font-medium text-slate-700 flex-1">Edema Present</span>
      </label>
      <div v-if="exam.edema.present" class="px-4 pb-4 pt-0 grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label :class="LC">Site</label>
          <input v-model="exam.edema.site" type="text" placeholder="e.g. Bilateral pedal, facial" :class="IC" lang="auto"/>
        </div>
        <div>
          <label :class="LC">Grade</label>
          <select v-model="exam.edema.grade" :class="SEL">
            <option value="">— Select —</option>
            <option v-for="g in EDEMA_GRADES" :key="g">{{ g }}</option>
          </select>
        </div>
      </div>
    </div>

    <!-- E. Skin Lesions -->
    <div class="border border-slate-100 rounded-xl overflow-hidden">
      <label class="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-slate-50 transition">
        <input v-model="exam.skinLesions.present" type="checkbox" class="w-4 h-4 rounded border-slate-300 text-blue-600 accent-blue-600"/>
        <span class="text-sm font-medium text-slate-700 flex-1">Skin Lesions Present</span>
      </label>
      <div v-if="exam.skinLesions.present" class="px-4 pb-4 pt-0">
        <label :class="LC">Description</label>
        <textarea v-model="exam.skinLesions.description" rows="2" placeholder="Describe skin lesions..." :class="TC" lang="auto"/>
      </div>
    </div>
  </div>
</template>
