<script setup>
import { computed } from 'vue'

/**
 * StatusBadge — generic status chip for referrals, teleconsults, devices, sync state.
 * Conveys status via both color and text. Falls back gracefully for unknown values
 * so a status value the caller doesn't recognize still renders (slate, verbatim text)
 * instead of disappearing.
 *
 * Props:
 *   status – the raw status string (e.g. 'Pending', 'Completed', 'Cancelled')
 *   tone   – optional explicit tone override: 'blue' | 'amber' | 'green' | 'red' | 'slate'
 */
const props = defineProps({
  status: { type: String, required: true },
  tone:   { type: String, default: '' },
})

const TONE_MAP = {
  blue:  'bg-blue-50 text-blue-700 border-blue-100',
  amber: 'bg-amber-50 text-amber-700 border-amber-100',
  green: 'bg-green-50 text-green-700 border-green-100',
  red:   'bg-red-50 text-red-700 border-red-100',
  slate: 'bg-slate-100 text-slate-600 border-slate-200',
}

// Default tone inference from common status vocabularies used across the app.
const STATUS_TONE = {
  Pending: 'amber', Scheduled: 'blue', Confirmed: 'blue', Connecting: 'blue',
  Completed: 'green', Confirmed_: 'green', Connected: 'green', Active: 'green', Online: 'green', Synced: 'green', Accepted: 'green',
  Cancelled: 'red', Failed: 'red', Error: 'red', Disconnected: 'red', Offline: 'red',
}

const resolvedTone = computed(() => TONE_MAP[props.tone] || TONE_MAP[STATUS_TONE[props.status]] || TONE_MAP.slate)
const dotTone = computed(() => {
  const key = props.tone || STATUS_TONE[props.status] || 'slate'
  return { blue: 'bg-blue-500', amber: 'bg-amber-500', green: 'bg-green-500', red: 'bg-red-500', slate: 'bg-slate-400' }[key]
})
</script>

<template>
  <span :class="['inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold', resolvedTone]">
    <span :class="['h-1.5 w-1.5 rounded-full', dotTone]"/>
    {{ status }}
  </span>
</template>
