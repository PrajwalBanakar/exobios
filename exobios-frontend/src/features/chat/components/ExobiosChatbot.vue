<script setup>
import { ref, nextTick } from 'vue'
import { askExobiosAssistant } from '@/shared/services/aiAssistantService'

const KNOWLEDGE_BASE_LABEL = 'Biochemistry'

const SUGGESTED_QUESTIONS = [
  'Explain glycolysis',
  'What are the functions of insulin?',
  'Explain the urea cycle',
  'What causes metabolic acidosis?',
]

// role: 'user' | 'assistant' | 'error'
const messages = ref([])
const input = ref('')
const loading = ref(false)
const textareaEl = ref(null)
const scrollEl = ref(null)

function scrollToBottom() {
  nextTick(() => {
    if (scrollEl.value) scrollEl.value.scrollTop = scrollEl.value.scrollHeight
  })
}

function resizeTextarea() {
  const el = textareaEl.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = `${Math.min(el.scrollHeight, 160)}px`
}

function handleKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

async function sendMessage(question) {
  const text = (question ?? input.value).trim()
  if (!text || loading.value) return

  messages.value.push({ role: 'user', content: text })
  input.value = ''
  nextTick(resizeTextarea)
  scrollToBottom()

  loading.value = true
  try {
    const result = await askExobiosAssistant(text)
    messages.value.push({
      role: 'assistant',
      content: result.answer,
      citations: result.citations ?? [],
      grounded: result.grounded,
    })
  } catch (e) {
    messages.value.push({ role: 'error', content: e.message ?? 'Something went wrong. Please try again.' })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

function clearChat() {
  if (loading.value) return
  messages.value = []
  input.value = ''
  nextTick(resizeTextarea)
}
</script>

<template>
  <div class="flex h-[640px] w-full max-w-3xl flex-col overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-2xl shadow-navy-900/10 sm:h-[680px]">

    <!-- Header -->
    <div class="flex shrink-0 items-center justify-between gap-3 px-5 py-4 sm:px-6"
         style="background: linear-gradient(135deg, #0a1628 0%, #0d1a30 100%)">
      <div class="flex items-center gap-3 min-w-0">
        <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-blue-500/20 ring-1 ring-blue-400/30">
          <svg class="h-5 w-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 0 0-2.456 2.456Z"/>
          </svg>
        </div>
        <div class="min-w-0">
          <h3 class="truncate text-sm font-semibold text-white sm:text-base">Exobios AI Assistant</h3>
          <div class="mt-0.5 flex items-center gap-1.5">
            <span class="h-1.5 w-1.5 rounded-full bg-emerald-400"/>
            <span class="text-xs text-slate-300">Knowledge Base: {{ KNOWLEDGE_BASE_LABEL }}</span>
          </div>
        </div>
      </div>

      <button type="button" @click="clearChat" :disabled="loading || messages.length === 0"
        class="flex shrink-0 items-center gap-1.5 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-xs font-medium text-slate-200 transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-40">
        <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99"/></svg>
        <span class="hidden sm:inline">New chat</span>
      </button>
    </div>

    <!-- Messages -->
    <div ref="scrollEl" class="flex-1 space-y-4 overflow-y-auto bg-slate-50/60 px-4 py-5 sm:px-6">

      <!-- Empty state -->
      <div v-if="messages.length === 0" class="flex h-full flex-col items-center justify-center px-2 text-center">
        <div class="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-50 ring-1 ring-blue-100">
          <svg class="h-7 w-7 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.6">
            <path stroke-linecap="round" stroke-linejoin="round" d="M8.625 12a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H8.25m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H12m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 0 1-2.555-.337A5.972 5.972 0 0 1 5.41 20.97a5.969 5.969 0 0 1-.474-.065 4.48 4.48 0 0 0 .978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25Z"/>
          </svg>
        </div>
        <p class="max-w-xs text-sm text-slate-500">Ask a question from the currently available Exobios medical knowledge base.</p>

        <div class="mt-5 grid w-full max-w-md grid-cols-1 gap-2 sm:grid-cols-2">
          <button v-for="q in SUGGESTED_QUESTIONS" :key="q" type="button" @click="sendMessage(q)"
            class="rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-left text-xs font-medium text-slate-700 shadow-sm transition hover:border-blue-300 hover:bg-blue-50 hover:text-blue-700">
            {{ q }}
          </button>
        </div>
      </div>

      <!-- Message list -->
      <template v-for="(m, i) in messages" :key="i">

        <!-- User bubble -->
        <div v-if="m.role === 'user'" class="flex justify-end">
          <div class="max-w-[85%] rounded-2xl rounded-br-md bg-blue-600 px-4 py-2.5 text-sm text-white shadow-sm sm:max-w-[75%]">
            {{ m.content }}
          </div>
        </div>

        <!-- Assistant bubble -->
        <div v-else-if="m.role === 'assistant'" class="flex justify-start">
          <div class="max-w-[90%] rounded-2xl rounded-bl-md border border-slate-200 bg-white px-4 py-3 text-sm leading-relaxed text-slate-800 shadow-sm sm:max-w-[80%]">
            <p class="whitespace-pre-wrap">{{ m.content }}</p>

            <p v-if="m.grounded === false" class="mt-2.5 flex items-start gap-1.5 rounded-lg bg-amber-50 px-2.5 py-1.5 text-xs text-amber-700">
              <svg class="mt-0.5 h-3.5 w-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="13"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
              This may not be fully grounded in the knowledge base.
            </p>

            <details v-if="m.citations?.length" class="mt-3 border-t border-slate-100 pt-2.5">
              <summary class="cursor-pointer text-xs font-semibold uppercase tracking-wide text-slate-500 hover:text-slate-700">
                Sources ({{ m.citations.length }})
              </summary>
              <div class="mt-2 space-y-2.5">
                <div v-for="c in m.citations" :key="c.chunkId" class="rounded-lg border border-slate-100 bg-slate-50 px-3 py-2 text-xs">
                  <div class="flex flex-wrap items-center gap-x-2 gap-y-0.5 font-medium text-slate-700">
                    <span>{{ KNOWLEDGE_BASE_LABEL }}</span>
                    <span class="text-slate-300">&middot;</span>
                    <span v-if="c.heading">{{ c.heading }}</span>
                    <span class="text-slate-300">&middot;</span>
                    <span>Page {{ c.page }}</span>
                  </div>
                  <p class="mt-1 text-slate-500">{{ c.excerpt }}</p>
                </div>
              </div>
            </details>
          </div>
        </div>

        <!-- Error bubble -->
        <div v-else class="flex justify-start">
          <div class="flex max-w-[85%] items-start gap-2 rounded-2xl rounded-bl-md border border-red-100 bg-red-50 px-4 py-2.5 text-sm text-red-600 sm:max-w-[75%]">
            <svg class="mt-0.5 h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="13"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            <span>{{ m.content }}</span>
          </div>
        </div>
      </template>

      <!-- Typing indicator -->
      <div v-if="loading" class="flex justify-start">
        <div class="flex items-center gap-1.5 rounded-2xl rounded-bl-md border border-slate-200 bg-white px-4 py-3.5 shadow-sm">
          <span class="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400" style="animation-delay: 0ms"/>
          <span class="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400" style="animation-delay: 150ms"/>
          <span class="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400" style="animation-delay: 300ms"/>
        </div>
      </div>
    </div>

    <!-- Input -->
    <div class="shrink-0 border-t border-slate-100 bg-white px-4 py-3 sm:px-6">
      <div class="flex items-end gap-2">
        <textarea
          ref="textareaEl"
          v-model="input"
          rows="1"
          placeholder="Ask about glycolysis, insulin, the urea cycle..."
          @keydown="handleKeydown"
          @input="resizeTextarea"
          class="max-h-40 flex-1 resize-none rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm text-slate-800 placeholder-slate-400 transition focus:border-blue-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/30"
        />
        <button type="button" @click="sendMessage()" :disabled="!input.trim() || loading"
          class="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-blue-600 text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-200 disabled:text-slate-400">
          <svg class="h-4.5 w-4.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 12 3.269 3.126A59.77 59.77 0 0 1 21.485 12 59.77 59.77 0 0 1 3.269 20.874L6 12Zm0 0h7.5"/></svg>
        </button>
      </div>
      <p class="mt-1.5 text-center text-[11px] text-slate-400">Enter to send &middot; Shift+Enter for a new line</p>
    </div>
  </div>
</template>
