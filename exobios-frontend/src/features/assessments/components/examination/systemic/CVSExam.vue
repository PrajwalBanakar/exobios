<script setup>
import RadioGroup from '@/shared/components/forms/RadioGroup.vue'
import CheckboxGroup from '@/shared/components/forms/CheckboxGroup.vue'

defineProps({
  // examForm.generalExam.systemicExam.cvs — mutated in place.
  exam: { type: Object, required: true },
})

const LC = 'block text-xs font-medium text-slate-600 mb-1.5'

const PRESENT_ABSENT       = ['Present', 'Absent']
const APEX_BEAT_OPTIONS    = ['Normal', 'Displaced', 'Not palpable']
const AUSCULTATION_OPTIONS = ['Normal heart sounds', 'Murmur', 'Added sounds']
</script>

<template>
  <div class="space-y-4">
    <div>
      <div class="text-xs font-semibold text-slate-500 mb-2">Inspection</div>
      <div class="space-y-3">
        <div>
          <label :class="LC">Precordial Bulge</label>
          <RadioGroup v-model="exam.inspection.precordialBulge" :options="PRESENT_ABSENT" color="red"/>
        </div>
        <div>
          <label :class="LC">Visible Pulsations</label>
          <RadioGroup v-model="exam.inspection.visiblePulsations" :options="PRESENT_ABSENT" color="red"/>
        </div>
      </div>
    </div>

    <div>
      <div class="text-xs font-semibold text-slate-500 mb-2">Palpation</div>
      <div class="space-y-3">
        <div>
          <label :class="LC">Apex Beat</label>
          <RadioGroup v-model="exam.palpation.apexBeat" :options="APEX_BEAT_OPTIONS" color="red"/>
        </div>
        <div>
          <label :class="LC">Thrills</label>
          <RadioGroup v-model="exam.palpation.thrills" :options="PRESENT_ABSENT" color="red"/>
        </div>
      </div>
    </div>

    <div>
      <div class="text-xs font-semibold text-slate-500 mb-2">Auscultation</div>
      <CheckboxGroup v-model="exam.auscultation.findings" :options="AUSCULTATION_OPTIONS" color="red" columns="grid-cols-1 sm:grid-cols-3"/>
    </div>
  </div>
</template>
