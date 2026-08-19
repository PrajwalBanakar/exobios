<script setup>
import SuggestedPrompts from './SuggestedPrompts.vue'

defineProps({
  prompts: { type: Array, required: true },
})

const emit = defineEmits(['select-prompt'])
</script>

<template>
  <div class="flex h-full flex-col items-center justify-center px-2 py-6 text-center">
    <div class="mb-3 flex h-11 w-11 items-center justify-center rounded-2xl bg-blue-50 ring-1 ring-blue-100">
      <svg class="h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.6">
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          d="M8.625 12a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H8.25m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H12m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 0 1-2.555-.337A5.972 5.972 0 0 1 5.41 20.97a5.969 5.969 0 0 1-.474-.065 4.48 4.48 0 0 0 .978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25Z"
        />
      </svg>
    </div>
    <h4 class="text-sm font-semibold text-navy-900">Ask Exobios AI</h4>
    <p class="mx-auto mt-1 max-w-xs text-xs text-slate-500 sm:text-sm">
      Ask a question from the currently available medical knowledge base.
    </p>

    <div class="mt-4 w-full max-w-md">
      <SuggestedPrompts :prompts="prompts" @select="(q) => emit('select-prompt', q)" />
    </div>
  </div>
</template>
