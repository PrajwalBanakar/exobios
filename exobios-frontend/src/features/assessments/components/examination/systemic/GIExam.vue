<script setup>
import RadioGroup from '@/shared/components/forms/RadioGroup.vue'

defineProps({
  // examForm.generalExam.systemicExam.gi — mutated in place.
  exam: { type: Object, required: true },
})

const LC = 'block text-xs font-medium text-slate-600 mb-1.5'

const PRESENT_ABSENT      = ['Present', 'Absent']
const PERCUSSION_OPTIONS  = ['Normal', 'Fluid signs']
const BOWEL_SOUNDS_OPTIONS = ['Normal', 'Increased', 'Decreased', 'Absent']
</script>

<template>
  <div class="space-y-4">
    <div>
      <div class="text-xs font-semibold text-slate-500 mb-2">Inspection</div>
      <div class="space-y-3">
        <div>
          <label :class="LC">Distension</label>
          <RadioGroup v-model="exam.inspection.distension" :options="PRESENT_ABSENT" color="purple"/>
        </div>
        <div>
          <label :class="LC">Scars</label>
          <RadioGroup v-model="exam.inspection.scars" :options="PRESENT_ABSENT" color="purple"/>
        </div>
        <div>
          <label :class="LC">Visible Veins</label>
          <RadioGroup v-model="exam.inspection.visibleVeins" :options="PRESENT_ABSENT" color="purple"/>
        </div>
      </div>
    </div>

    <div>
      <div class="text-xs font-semibold text-slate-500 mb-2">Palpation</div>
      <div class="space-y-3">
        <div>
          <label :class="LC">Tenderness</label>
          <RadioGroup v-model="exam.palpation.tenderness" :options="PRESENT_ABSENT" color="purple"/>
        </div>
        <div>
          <label :class="LC">Organ Enlargement</label>
          <RadioGroup v-model="exam.palpation.organEnlargement" :options="PRESENT_ABSENT" color="purple"/>
        </div>
      </div>
    </div>

    <div>
      <div class="text-xs font-semibold text-slate-500 mb-2">Percussion</div>
      <RadioGroup v-model="exam.percussion.finding" :options="PERCUSSION_OPTIONS" color="purple"/>
    </div>

    <div>
      <div class="text-xs font-semibold text-slate-500 mb-2">Auscultation</div>
      <label :class="LC">Bowel Sounds</label>
      <RadioGroup v-model="exam.auscultation.bowelSounds" :options="BOWEL_SOUNDS_OPTIONS" color="purple"/>
    </div>
  </div>
</template>
