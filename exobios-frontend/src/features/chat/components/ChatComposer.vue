<script setup>
import { ref, watch, nextTick } from 'vue'

const props = defineProps({
  modelValue: { type: String, required: true },
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue', 'send'])

const textareaEl = ref(null)

function resize() {
  const el = textareaEl.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = `${Math.min(el.scrollHeight, 160)}px`
}

function onInput(e) {
  emit('update:modelValue', e.target.value)
  resize()
}

function handleKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    send()
  }
}

function send() {
  if (!props.modelValue.trim() || props.loading) return
  emit('send')
}

watch(
  () => props.modelValue,
  (v) => {
    if (v === '') nextTick(resize)
  },
)

defineExpose({ focus: () => textareaEl.value?.focus() })
</script>

<template>
  <div class="shrink-0 border-t border-slate-100 bg-white px-4 py-3 sm:px-6">
    <div
      class="flex items-end gap-2 rounded-2xl border border-slate-200 bg-slate-50 px-2 py-2 transition focus-within:border-blue-500 focus-within:bg-white focus-within:ring-2 focus-within:ring-blue-500/25"
    >
      <label for="exobios-chat-input" class="sr-only">Ask Exobios AI a question about biochemistry</label>
      <textarea
        id="exobios-chat-input"
        ref="textareaEl"
        :value="modelValue"
        rows="1"
        placeholder="Ask Exobios about biochemistry..."
        :disabled="loading"
        @input="onInput"
        @keydown="handleKeydown"
        class="max-h-40 flex-1 resize-none bg-transparent px-2 py-1.5 text-sm text-slate-800 placeholder-slate-400 outline-none disabled:cursor-not-allowed disabled:text-slate-400"
      />
      <button
        type="button"
        @click="send"
        :disabled="!modelValue.trim() || loading"
        aria-label="Send message"
        class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl transition motion-safe:duration-150"
        :class="
          modelValue.trim() && !loading
            ? 'bg-blue-600 text-white hover:bg-blue-700'
            : 'bg-slate-200 text-slate-400'
        "
      >
        <svg v-if="!loading" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M6 12 3.269 3.126A59.77 59.77 0 0 1 21.485 12 59.77 59.77 0 0 1 3.269 20.874L6 12Zm0 0h7.5" />
        </svg>
        <svg v-else class="h-4 w-4 motion-safe:animate-spin" viewBox="0 0 24 24" fill="none">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" />
          <path class="opacity-80" d="M22 12a10 10 0 0 0-10-10" stroke="currentColor" stroke-width="3" stroke-linecap="round" />
        </svg>
      </button>
    </div>
    <p class="mt-1.5 text-center text-[11px] text-slate-400">Enter to send &middot; Shift+Enter for a new line</p>
  </div>
</template>
