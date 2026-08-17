<script setup>
import RadioGroup from '@/shared/components/forms/RadioGroup.vue'

defineProps({
  // examForm.generalExam.systemicExam.cns — mutated in place.
  // CNS follows Mental Status / Motor / Sensory / Reflexes rather than the
  // Inspection/Palpation/Percussion/Auscultation structure used by the other systems.
  exam: { type: Object, required: true },
})

const LC = 'block text-xs font-medium text-slate-600 mb-1.5'

const MENTAL_STATUS_OPTIONS = ['Alert', 'Confused', 'Drowsy']
const POWER_OPTIONS         = ['Normal', 'Reduced', 'Absent']
const TONE_OPTIONS          = ['Normal', 'Increased (Spasticity)', 'Decreased (Hypotonia)']
const NORMAL_ABNORMAL       = ['Normal', 'Abnormal']
</script>

<template>
  <div class="space-y-4">
    <div>
      <label :class="LC">Mental Status</label>
      <RadioGroup v-model="exam.mentalStatus" :options="MENTAL_STATUS_OPTIONS" color="teal"/>
    </div>

    <div>
      <div class="text-xs font-semibold text-slate-500 mb-2">Motor</div>
      <div class="space-y-3">
        <div>
          <label :class="LC">Power</label>
          <RadioGroup v-model="exam.motor.power" :options="POWER_OPTIONS" color="teal"/>
        </div>
        <div>
          <label :class="LC">Tone</label>
          <RadioGroup v-model="exam.motor.tone" :options="TONE_OPTIONS" color="teal"/>
        </div>
      </div>
    </div>

    <div>
      <label :class="LC">Sensory</label>
      <RadioGroup v-model="exam.sensory" :options="NORMAL_ABNORMAL" color="teal"/>
    </div>

    <div>
      <label :class="LC">Reflexes</label>
      <RadioGroup v-model="exam.reflexes" :options="NORMAL_ABNORMAL" color="teal"/>
    </div>
  </div>
</template>
