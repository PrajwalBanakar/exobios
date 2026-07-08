<script setup>
import CheckboxGroup from '@/shared/components/forms/CheckboxGroup.vue'

defineProps({
  // examForm.generalExam.paramedicExam — mutated in place (already reactive via the parent's reactive()).
  exam: { type: Object, required: true },
})

const LC = 'block text-xs font-medium text-gray-600 mb-1.5'

const GENERAL_APPEARANCE_OPTIONS = ['Conscious', 'Oriented', 'Comfortable', 'Distressed', 'Weak']
const EYES_OPTIONS               = ['Pallor', 'Icterus', 'Redness', 'Discharge']
const SKIN_MUCOSA_OPTIONS        = ['Rash', 'Cyanosis', 'Dehydration signs']
const EXTREMITIES_OPTIONS        = ['Edema', 'Injury', 'Deformity']
</script>

<template>
  <div class="space-y-5">
    <div>
      <label :class="LC">General Appearance</label>
      <CheckboxGroup v-model="exam.generalAppearance" :options="GENERAL_APPEARANCE_OPTIONS" color="teal" columns="grid-cols-2 sm:grid-cols-3"/>
    </div>

    <div>
      <label :class="LC">Eyes</label>
      <CheckboxGroup v-model="exam.eyes" :options="EYES_OPTIONS" color="teal" columns="grid-cols-2 sm:grid-cols-4"/>
    </div>

    <div>
      <label :class="LC">Skin / Mucosa</label>
      <CheckboxGroup v-model="exam.skinMucosa" :options="SKIN_MUCOSA_OPTIONS" color="teal" columns="grid-cols-1 sm:grid-cols-3"/>
    </div>

    <div>
      <label :class="LC">Extremities</label>
      <CheckboxGroup v-model="exam.extremities" :options="EXTREMITIES_OPTIONS" color="teal" columns="grid-cols-1 sm:grid-cols-3"/>
    </div>

    <div class="border border-gray-100 rounded-xl overflow-hidden">
      <label class="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-gray-50 transition">
        <input v-model="exam.visibleInjuries.present" type="checkbox" class="w-4 h-4 rounded border-gray-300 text-teal-600 accent-teal-600"/>
        <span class="text-sm font-medium text-gray-700 flex-1">Visible Injuries Present</span>
      </label>
      <div v-if="exam.visibleInjuries.present" class="px-4 pb-4 pt-0">
        <label :class="LC">Description</label>
        <textarea v-model="exam.visibleInjuries.description" rows="2" placeholder="Describe visible injuries..."
          class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-teal-500" lang="auto"/>
      </div>
    </div>
  </div>
</template>
