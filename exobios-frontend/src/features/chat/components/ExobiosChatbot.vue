<script setup>
import { ref, nextTick } from 'vue'
import { askExobiosAssistant } from '@/shared/services/aiAssistantService'
import ChatHeader from './ChatHeader.vue'
import ChatEmptyState from './ChatEmptyState.vue'
import ChatMessage from './ChatMessage.vue'
import ChatLoadingIndicator from './ChatLoadingIndicator.vue'
import ChatComposer from './ChatComposer.vue'

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
const lastFailedQuestion = ref('')
const scrollEl = ref(null)
const isNearBottom = ref(true)

function handleScroll() {
  const el = scrollEl.value
  if (!el) return
  isNearBottom.value = el.scrollHeight - el.scrollTop - el.clientHeight < 96
}

function scrollToBottom(force = false) {
  nextTick(() => {
    const el = scrollEl.value
    if (!el) return
    if (force || isNearBottom.value) el.scrollTop = el.scrollHeight
  })
}

async function sendMessage(question) {
  const text = (question ?? input.value).trim()
  if (!text || loading.value) return

  messages.value.push({ role: 'user', content: text })
  input.value = ''
  scrollToBottom(true)

  loading.value = true
  const willAutoScroll = isNearBottom.value
  try {
    const result = await askExobiosAssistant(text)
    messages.value.push({
      role: 'assistant',
      content: result.answer,
      citations: result.citations ?? [],
      grounded: result.grounded,
    })
    lastFailedQuestion.value = ''
  } catch (e) {
    lastFailedQuestion.value = text
    messages.value.push({
      role: 'error',
      content: e.message ?? 'Something went wrong. Please try again.',
      code: e.code ?? 'default',
    })
  } finally {
    loading.value = false
    scrollToBottom(willAutoScroll)
  }
}

function retryLast() {
  if (!lastFailedQuestion.value) return
  // Drop the trailing error bubble before retrying so the conversation doesn't accumulate stale failures.
  const last = messages.value[messages.value.length - 1]
  if (last?.role === 'error') messages.value.pop()
  sendMessage(lastFailedQuestion.value)
}

function clearChat() {
  if (loading.value) return
  messages.value = []
  input.value = ''
  lastFailedQuestion.value = ''
  isNearBottom.value = true
}
</script>

<template>
  <div
    class="flex h-[min(72vh,620px)] w-full max-w-[960px] flex-col overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-lg shadow-navy-900/5"
  >
    <ChatHeader :knowledge-base="KNOWLEDGE_BASE_LABEL" :disabled="loading || messages.length === 0" @new-chat="clearChat" />

    <div ref="scrollEl" @scroll="handleScroll" class="flex-1 space-y-4 overflow-y-auto bg-slate-50/60 px-4 py-5 sm:px-6">
      <ChatEmptyState v-if="messages.length === 0" :prompts="SUGGESTED_QUESTIONS" @select-prompt="sendMessage" />

      <template v-for="(m, i) in messages" :key="i">
        <ChatMessage :message="m" @retry="retryLast" />
      </template>

      <ChatLoadingIndicator v-if="loading" />
    </div>

    <ChatComposer v-model="input" :loading="loading" @send="() => sendMessage()" />
  </div>
</template>
