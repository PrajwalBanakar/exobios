import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'

const STORAGE_KEY = 'exobios.chatThreads.v1'
const MAX_THREADS = 50
const TITLE_MAX_LENGTH = 48
const DEFAULT_TITLE = 'New chat'

function loadThreads() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    const parsed = raw ? JSON.parse(raw) : []
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function makeTitle(text) {
  const trimmed = text.trim().replace(/\s+/g, ' ')
  return trimmed.length > TITLE_MAX_LENGTH ? `${trimmed.slice(0, TITLE_MAX_LENGTH).trimEnd()}…` : trimmed
}

function createEmptyThread() {
  const now = Date.now()
  return {
    id: `${now}-${Math.random().toString(36).slice(2, 8)}`,
    title: DEFAULT_TITLE,
    messages: [],
    createdAt: now,
    updatedAt: now,
  }
}

// Threads persist to localStorage only (no account/device sync) — history
// survives reloads in the same browser but is lost if storage is cleared.
export const useChatThreadsStore = defineStore('chatThreads', () => {
  const threads = ref(loadThreads())

  if (threads.value.length === 0) {
    threads.value.push(createEmptyThread())
  }

  const activeThreadId = ref(threads.value[0].id)

  const sortedThreads = computed(() => [...threads.value].sort((a, b) => b.updatedAt - a.updatedAt))
  const activeThread = computed(() => threads.value.find((t) => t.id === activeThreadId.value) ?? null)

  watch(
    threads,
    (v) => {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(v))
      } catch {
        // Storage full or unavailable (e.g. private browsing) — chat still
        // works, it just won't persist across reloads.
      }
    },
    { deep: true },
  )

  function selectThread(id) {
    if (threads.value.some((t) => t.id === id)) activeThreadId.value = id
  }

  function createThread() {
    const thread = createEmptyThread()
    threads.value.unshift(thread)
    if (threads.value.length > MAX_THREADS) {
      threads.value.splice(MAX_THREADS)
    }
    activeThreadId.value = thread.id
    return thread
  }

  // "New chat" action: reuses the current thread if it's already empty
  // instead of piling up blank entries in the sidebar.
  function newChat() {
    if (activeThread.value && activeThread.value.messages.length === 0) {
      return activeThread.value
    }
    return createThread()
  }

  function deleteThread(id) {
    const idx = threads.value.findIndex((t) => t.id === id)
    if (idx === -1) return
    threads.value.splice(idx, 1)

    if (threads.value.length === 0) {
      threads.value.push(createEmptyThread())
    }
    if (activeThreadId.value === id) {
      activeThreadId.value = sortedThreads.value[0].id
    }
  }

  function appendMessage(threadId, message) {
    const thread = threads.value.find((t) => t.id === threadId)
    if (!thread) return
    thread.messages.push(message)
    thread.updatedAt = Date.now()
    if (thread.title === DEFAULT_TITLE && message.role === 'user') {
      thread.title = makeTitle(message.content)
    }
  }

  function popLastMessage(threadId) {
    const thread = threads.value.find((t) => t.id === threadId)
    if (!thread || thread.messages.length === 0) return
    thread.messages.pop()
  }

  return {
    threads: sortedThreads,
    activeThreadId,
    activeThread,
    selectThread,
    createThread,
    newChat,
    deleteThread,
    appendMessage,
    popLastMessage,
  }
})
