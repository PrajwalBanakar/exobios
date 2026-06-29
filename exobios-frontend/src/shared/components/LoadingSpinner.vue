<script setup>
defineProps({
  size:    { type: String, default: 'md' }, // sm | md | lg
  color:   { type: String, default: 'blue' },
  message: { type: String, default: '' },
})
</script>

<template>
  <div class="flex flex-col items-center justify-center gap-3">
    <svg
      :class="[
        'animate-spin',
        size === 'sm' ? 'w-4 h-4' : size === 'lg' ? 'w-10 h-10' : 'w-6 h-6',
        color === 'white' ? 'text-white' : color === 'gray' ? 'text-gray-400' : 'text-blue-600',
      ]"
      fill="none" viewBox="0 0 24 24"
    >
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 0 1 8-8v8H4z"/>
    </svg>
    <p v-if="message" :class="['text-sm', color === 'white' ? 'text-white/80' : 'text-gray-500']">{{ message }}</p>
  </div>
</template>
