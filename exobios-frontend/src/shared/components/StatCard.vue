<script setup>
/**
 * StatCard — KPI summary card for dashboards.
 *
 * Props:
 *   label     – metric name (e.g. "Total Patients")
 *   value     – headline number
 *   tone      – 'blue' | 'red' | 'amber' | 'green'  (default: 'blue')
 *   secondary – short contextual line shown below the value, if available
 *
 * Slot:
 *   icon – the metric's icon markup
 */
defineProps({
  label:     { type: String, required: true },
  value:     { type: [String, Number], required: true },
  tone:      { type: String, default: 'blue' },
  secondary: { type: String, default: '' },
})

const TONES = {
  blue:  { bg: 'bg-blue-50',  text: 'text-blue-600'  },
  red:   { bg: 'bg-red-50',   text: 'text-red-600'   },
  amber: { bg: 'bg-amber-50', text: 'text-amber-600' },
  green: { bg: 'bg-green-50', text: 'text-green-600' },
}
</script>

<template>
  <div class="rounded-2xl border border-slate-200 bg-white p-5">
    <div :class="['flex h-11 w-11 items-center justify-center rounded-xl', TONES[tone].bg, TONES[tone].text]">
      <slot name="icon" />
    </div>
    <div class="mt-4 text-2xl font-bold text-slate-900">{{ value }}</div>
    <div class="mt-0.5 text-sm text-slate-500">{{ label }}</div>
    <div v-if="secondary" :class="['mt-2 text-xs font-medium', TONES[tone].text]">{{ secondary }}</div>
  </div>
</template>
