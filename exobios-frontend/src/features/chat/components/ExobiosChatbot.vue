<script setup>
import { ref, computed, nextTick } from 'vue'
import { storeToRefs } from 'pinia'
import { askExobiosAssistant } from '@/shared/services/aiAssistantService'
import { useChatThreadsStore } from '../stores/chatThreads'
import ChatHeader from './ChatHeader.vue'
import ChatSidebar from './ChatSidebar.vue'
import ChatEmptyState from './ChatEmptyState.vue'
import ChatMessage from './ChatMessage.vue'
import ChatLoadingIndicator from './ChatLoadingIndicator.vue'
import ChatComposer from './ChatComposer.vue'

const KNOWLEDGE_BASE_LABEL = 'Biochemistry'
const HISTORY_TURNS_SENT = 12

const SUGGESTED_QUESTIONS = [
  'Explain glycolysis',
  'What are the functions of insulin?',
  'Explain the urea cycle',
  'What causes metabolic acidosis?',
]

const chatStore = useChatThreadsStore()
const { threads, activeThreadId, activeThread } = storeToRefs(chatStore)

// role: 'user' | 'assistant' | 'error'
const messages = computed(() => activeThread.value?.messages ?? [])

const input = ref('')
const loading = ref(false)
const lastFailedQuestion = ref('')
const scrollEl = ref(null)
const isNearBottom = ref(true)
const sidebarOpen = ref(false)

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

function buildHistoryPayload() {
  return messages.value
    .filter((m) => m.role === 'user' || m.role === 'assistant')
    .slice(-HISTORY_TURNS_SENT)
    .map((m) => ({ role: m.role, content: m.content }))
}

async function sendMessage(question) {
  const text = (question ?? input.value).trim()
  if (!text || loading.value) return

  // Captured up front so the response lands in the thread the request was
  // sent from, even if the user switches threads while it's in flight.
  const threadId = activeThreadId.value
  const history = buildHistoryPayload()
  chatStore.appendMessage(threadId, { role: 'user', content: text })
  input.value = ''
  scrollToBottom(true)

  loading.value = true
  const willAutoScroll = isNearBottom.value
  try {
    const result = await askExobiosAssistant(text, history)
    chatStore.appendMessage(threadId, {
      role: 'assistant',
      content: result.answer,
      citations: result.citations ?? [],
      grounded: result.grounded,
    })
    lastFailedQuestion.value = ''
  } catch (e) {
    lastFailedQuestion.value = text
    chatStore.appendMessage(threadId, {
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
  if (last?.role === 'error') chatStore.popLastMessage(activeThreadId.value)
  sendMessage(lastFailedQuestion.value)
}

function resetComposer() {
  input.value = ''
  lastFailedQuestion.value = ''
  isNearBottom.value = true
}

function newChat() {
  if (loading.value) return
  chatStore.newChat()
  resetComposer()
  sidebarOpen.value = false
}

function selectThread(id) {
  if (loading.value) return
  chatStore.selectThread(id)
  resetComposer()
  sidebarOpen.value = false
  scrollToBottom(true)
}

function deleteThread(id) {
  if (loading.value) return
  chatStore.deleteThread(id)
  resetComposer()
  scrollToBottom(true)
}
</script>

<template>
  <div
    class="relative flex h-[min(78vh,660px)] w-full max-w-[1100px] overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-lg shadow-navy-900/5"
  >
    <ChatSidebar
      class="hidden sm:flex"
      :threads="threads"
      :active-thread-id="activeThreadId"
      :disabled="loading"
      @select="selectThread"
      @new-chat="newChat"
      @delete="deleteThread"
    />

    <Transition name="fade">
      <div v-if="sidebarOpen" class="absolute inset-0 z-20 flex sm:hidden">
        <ChatSidebar
          class="flex"
          :threads="threads"
          :active-thread-id="activeThreadId"
          :disabled="loading"
          @select="selectThread"
          @new-chat="newChat"
          @delete="deleteThread"
        />
        <button
          type="button"
          class="flex-1 bg-slate-900/30"
          aria-label="Close chat history"
          @click="sidebarOpen = false"
        />
      </div>
    </Transition>

    <div class="flex min-w-0 flex-1 flex-col">
      <ChatHeader
        :knowledge-base="KNOWLEDGE_BASE_LABEL"
        :disabled="loading || messages.length === 0"
        @new-chat="newChat"
        @toggle-sidebar="sidebarOpen = !sidebarOpen"
      />

      <div ref="scrollEl" @scroll="handleScroll" class="flex-1 space-y-4 overflow-y-auto bg-slate-50/60 px-4 py-5 sm:px-6">
        <ChatEmptyState v-if="messages.length === 0" :prompts="SUGGESTED_QUESTIONS" @select-prompt="sendMessage" />

        <template v-for="(m, i) in messages" :key="i">
          <ChatMessage :message="m" @retry="retryLast" />
        </template>

        <ChatLoadingIndicator v-if="loading" />
      </div>

      <ChatComposer v-model="input" :loading="loading" @send="() => sendMessage()" />
    </div>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
