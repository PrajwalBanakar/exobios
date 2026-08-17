<script setup>
import RadioGroup from '@/shared/components/forms/RadioGroup.vue'
import CheckboxGroup from '@/shared/components/forms/CheckboxGroup.vue'

defineProps({
  // examForm.generalExam.systemicExam.respiratory — mutated in place.
  exam: { type: Object, required: true },
})

const LC = 'block text-xs font-medium text-slate-600 mb-1.5'

const CHEST_MOVEMENT_OPTIONS   = ['Normal', 'Reduced', 'Paradoxical']
const RESP_EFFORT_OPTIONS      = ['Normal', 'Labored', 'Use of accessory muscles']
const SYMMETRY_OPTIONS         = ['Symmetrical', 'Asymmetrical']
const TRACHEAL_POSITION_OPTIONS = ['Midline', 'Deviated Left', 'Deviated Right']
const CHEST_EXPANSION_OPTIONS  = ['Normal', 'Reduced Left', 'Reduced Right', 'Reduced Bilateral']
const PERCUSSION_OPTIONS       = ['Normal', 'Dull', 'Hyper-resonant']
const AUSCULTATION_OPTIONS     = ['Normal breath sounds', 'Wheeze', 'Crackles', 'Reduced air entry']
</script>

<template>
  <div class="space-y-4">
    <div>
      <div class="text-xs font-semibold text-slate-500 mb-2">Inspection</div>
      <div class="space-y-3">
        <div>
          <label :class="LC">Chest Movement</label>
          <RadioGroup v-model="exam.inspection.chestMovement" :options="CHEST_MOVEMENT_OPTIONS" color="blue"/>
        </div>
        <div>
          <label :class="LC">Respiratory Effort</label>
          <RadioGroup v-model="exam.inspection.respiratoryEffort" :options="RESP_EFFORT_OPTIONS" color="blue"/>
        </div>
        <div>
          <label :class="LC">Symmetry</label>
          <RadioGroup v-model="exam.inspection.symmetry" :options="SYMMETRY_OPTIONS" color="blue"/>
        </div>
      </div>
    </div>

    <div>
      <div class="text-xs font-semibold text-slate-500 mb-2">Palpation</div>
      <div class="space-y-3">
        <div>
          <label :class="LC">Tracheal Position</label>
          <RadioGroup v-model="exam.palpation.trachealPosition" :options="TRACHEAL_POSITION_OPTIONS" color="blue"/>
        </div>
        <div>
          <label :class="LC">Chest Expansion</label>
          <RadioGroup v-model="exam.palpation.chestExpansion" :options="CHEST_EXPANSION_OPTIONS" color="blue"/>
        </div>
      </div>
    </div>

    <div>
      <div class="text-xs font-semibold text-slate-500 mb-2">Percussion</div>
      <RadioGroup v-model="exam.percussion.finding" :options="PERCUSSION_OPTIONS" color="blue"/>
    </div>

    <div>
      <div class="text-xs font-semibold text-slate-500 mb-2">Auscultation</div>
      <CheckboxGroup v-model="exam.auscultation.findings" :options="AUSCULTATION_OPTIONS" color="blue" columns="grid-cols-2"/>
    </div>
  </div>
</template>
