<script setup>
import { computed } from 'vue'

/**
 * PatientAvatar — initials avatar used anywhere a patient is listed.
 *
 * Props:
 *   name – full patient name
 *   size – 'sm' | 'md'  (default: 'md')
 */
const props = defineProps({
  name: { type: String, default: '' },
  size: { type: String, default: 'md' },
})

const initials = computed(() =>
  props.name.split(' ').filter(Boolean).map(n => n[0]).join('').slice(0, 2).toUpperCase() || '?'
)

const SIZES = {
  sm: 'w-8 h-8 text-xs',
  md: 'w-10 h-10 text-sm',
  lg: 'w-16 h-16 text-xl',
}
</script>

<template>
  <div :class="['flex flex-shrink-0 items-center justify-center rounded-full bg-blue-50 font-semibold text-blue-600', SIZES[size]]">
    {{ initials }}
  </div>
</template>
