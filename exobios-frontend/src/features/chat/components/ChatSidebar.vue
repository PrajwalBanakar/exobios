<script setup>
defineProps({
  threads: { type: Array, required: true },
  activeThreadId: { type: String, default: null },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['select', 'new-chat', 'delete'])
</script>

<template>
  <div class="flex h-full w-64 shrink-0 flex-col border-r border-slate-200 bg-slate-50/80">
    <div class="shrink-0 p-3">
      <button
        type="button"
        @click="emit('new-chat')"
        :disabled="disabled"
        class="flex w-full items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 shadow-sm transition motion-safe:duration-150 hover:border-blue-300 hover:bg-blue-50 hover:text-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/40 disabled:cursor-not-allowed disabled:opacity-40"
      >
        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
        </svg>
        New chat
      </button>
    </div>

    <div class="flex-1 space-y-1 overflow-y-auto px-2 pb-3">
      <p v-if="threads.length === 0" class="px-2 py-4 text-center text-xs text-slate-400">No chats yet</p>

      <div
        v-for="t in threads"
        :key="t.id"
        class="group flex items-center gap-1 rounded-lg"
        :class="t.id === activeThreadId ? 'bg-blue-50' : 'hover:bg-slate-100'"
      >
        <button
          type="button"
          @click="emit('select', t.id)"
          :disabled="disabled"
          :title="t.title"
          class="min-w-0 flex-1 truncate rounded-lg px-2.5 py-2 text-left text-xs font-medium disabled:cursor-not-allowed"
          :class="t.id === activeThreadId ? 'text-blue-700' : 'text-slate-600'"
        >
          {{ t.title }}
        </button>
        <button
          type="button"
          @click="emit('delete', t.id)"
          :disabled="disabled"
          aria-label="Delete chat"
          class="mr-1 shrink-0 rounded-md p-1.5 text-slate-400 opacity-0 transition hover:bg-red-50 hover:text-red-600 focus-visible:opacity-100 focus-visible:outline-none disabled:cursor-not-allowed group-hover:opacity-100"
        >
          <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0"
            />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>
