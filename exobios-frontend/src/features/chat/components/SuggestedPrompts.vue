<script setup>
defineProps({
  prompts: { type: Array, required: true },
})

const emit = defineEmits(['select'])
</script>

<template>
  <div class="grid w-full grid-cols-1 gap-2 sm:grid-cols-2" role="group" aria-label="Suggested questions">
    <button
      v-for="q in prompts"
      :key="q"
      type="button"
      @click="emit('select', q)"
      class="rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-left text-xs font-medium text-slate-700 shadow-sm transition motion-safe:duration-150 hover:border-blue-300 hover:bg-blue-50 hover:text-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/40"
    >
      {{ q }}
    </button>
  </div>
</template>
