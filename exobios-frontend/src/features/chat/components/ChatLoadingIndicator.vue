<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const STAGES = ['Searching the Exobios knowledge base...', 'Generating evidence-grounded response...']
const stage = ref(0)
let timer

onMounted(() => {
  timer = setTimeout(() => {
    stage.value = 1
  }, 1100)
})

onUnmounted(() => clearTimeout(timer))
</script>

<template>
  <div class="flex justify-start">
    <div
      role="status"
      aria-live="polite"
      class="flex items-center gap-2.5 rounded-2xl rounded-bl-md border border-slate-200 bg-white px-4 py-3 text-xs font-medium text-slate-500 shadow-sm"
    >
      <span class="flex gap-1">
        <span class="h-1.5 w-1.5 rounded-full bg-blue-400 motion-safe:animate-bounce" style="animation-delay: 0ms" />
        <span class="h-1.5 w-1.5 rounded-full bg-blue-400 motion-safe:animate-bounce" style="animation-delay: 150ms" />
        <span class="h-1.5 w-1.5 rounded-full bg-blue-400 motion-safe:animate-bounce" style="animation-delay: 300ms" />
      </span>
      <span>{{ STAGES[stage] }}</span>
    </div>
  </div>
</template>
