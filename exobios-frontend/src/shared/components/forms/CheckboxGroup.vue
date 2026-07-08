<script setup>
// Reusable multi-select chip/checkbox list — same visual pattern used for
// complaint symptoms, exam findings, etc. Options may be strings or {value,label}.
const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  options: { type: Array, required: true },
  color: { type: String, default: 'teal' },
  columns: { type: String, default: 'grid-cols-2 sm:grid-cols-3' },
})
const emit = defineEmits(['update:modelValue'])

function optValue(opt) { return typeof opt === 'string' ? opt : opt.value }
function optLabel(opt) { return typeof opt === 'string' ? opt : opt.label }

function toggle(value) {
  const list = [...props.modelValue]
  const idx = list.indexOf(value)
  if (idx >= 0) list.splice(idx, 1)
  else list.push(value)
  emit('update:modelValue', list)
}

const COLOR_MAP = {
  teal:   { selected: 'bg-teal-50 border-teal-300 text-teal-800',     accent: 'accent-teal-600' },
  blue:   { selected: 'bg-blue-50 border-blue-300 text-blue-800',     accent: 'accent-blue-600' },
  red:    { selected: 'bg-red-50 border-red-300 text-red-800',        accent: 'accent-red-600' },
  purple: { selected: 'bg-purple-50 border-purple-300 text-purple-800', accent: 'accent-purple-600' },
  orange: { selected: 'bg-orange-50 border-orange-300 text-orange-800', accent: 'accent-orange-600' },
}
const colorClass = (key) => (COLOR_MAP[props.color] || COLOR_MAP.teal)[key]
</script>

<template>
  <div :class="['grid gap-2', columns]">
    <label v-for="opt in options" :key="optValue(opt)"
      :class="['flex items-center gap-2 px-3 py-2.5 rounded-lg border cursor-pointer transition text-sm',
        modelValue.includes(optValue(opt)) ? colorClass('selected') : 'border-gray-200 text-gray-700 hover:bg-gray-50']">
      <input type="checkbox" :checked="modelValue.includes(optValue(opt))" @change="toggle(optValue(opt))"
        :class="['w-4 h-4 rounded flex-shrink-0', colorClass('accent')]"/>
      <span>{{ optLabel(opt) }}</span>
    </label>
  </div>
</template>
