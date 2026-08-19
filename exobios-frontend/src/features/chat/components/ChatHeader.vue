<script setup>
defineProps({
  knowledgeBase: { type: String, required: true },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['new-chat', 'toggle-sidebar'])
</script>

<template>
  <div
    class="flex shrink-0 items-center justify-between gap-3 px-5 py-3.5 sm:px-6"
    style="background: linear-gradient(135deg, #0a1628 0%, #0d1a30 100%)"
  >
    <div class="flex min-w-0 items-center gap-3">
      <button
        type="button"
        @click="emit('toggle-sidebar')"
        title="Chat history"
        aria-label="Toggle chat history"
        class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-slate-200 transition motion-safe:duration-150 hover:bg-white/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400/50 sm:hidden"
      >
        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
          <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5M3.75 17.25h16.5" />
        </svg>
      </button>
      <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-blue-500/20 ring-1 ring-blue-400/30">
        <svg class="h-4 w-4 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 0 0-2.456 2.456Z"
          />
        </svg>
      </div>
      <div class="min-w-0">
        <h3 class="truncate text-sm font-semibold text-white sm:text-base">Exobios AI Assistant</h3>
        <div class="mt-0.5 flex flex-wrap items-center gap-x-2 gap-y-0.5">
          <span class="flex items-center gap-1.5 text-xs text-slate-300">
            <span class="h-1.5 w-1.5 rounded-full bg-emerald-400" aria-hidden="true" />
            {{ knowledgeBase }} Knowledge Base
          </span>
          <span class="hidden text-[11px] font-medium text-blue-300/80 sm:inline">&middot; Evidence-grounded</span>
        </div>
      </div>
    </div>

    <button
      type="button"
      @click="emit('new-chat')"
      :disabled="disabled"
      title="Start a new chat"
      aria-label="Start a new chat"
      class="flex shrink-0 items-center gap-1.5 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-xs font-medium text-slate-200 transition motion-safe:duration-150 hover:bg-white/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400/50 disabled:cursor-not-allowed disabled:opacity-40"
    >
      <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99"
        />
      </svg>
      <span class="hidden sm:inline">New chat</span>
    </button>
  </div>
</template>
