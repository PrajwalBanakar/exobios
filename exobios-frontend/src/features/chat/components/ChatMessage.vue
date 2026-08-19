<script setup>
import { computed, ref } from 'vue'
import { renderAssistantMarkdown } from '../utils/renderMarkdown'
import CitationList from './CitationList.vue'

const props = defineProps({
  message: { type: Object, required: true },
})

const emit = defineEmits(['retry'])

const isInsufficientEvidence = computed(
  () => props.message.role === 'assistant' && props.message.grounded === false && !props.message.citations?.length,
)

const renderedHtml = computed(() =>
  props.message.role === 'assistant' ? renderAssistantMarkdown(props.message.content) : '',
)

const copied = ref(false)
async function copyContent() {
  try {
    await navigator.clipboard.writeText(props.message.content)
    copied.value = true
    setTimeout(() => (copied.value = false), 1500)
  } catch {
    // Clipboard API unavailable (permissions/insecure context) — fail silently, no user-facing error needed for a convenience action.
  }
}

const feedback = ref(null)
function setFeedback(value) {
  feedback.value = feedback.value === value ? null : value
}

const ERROR_META = {
  network: {
    title: 'Unable to reach Exobios AI',
    body: "We couldn't connect to the Exobios AI service. Check your connection and try again.",
  },
  timeout: {
    title: 'Request timed out',
    body: 'The Exobios AI service is taking longer than expected to respond. Please try again.',
  },
  http: {
    title: 'Exobios AI is temporarily unavailable',
    body: 'The knowledge base service returned an error. Please try again in a moment.',
  },
  invalid: {
    title: 'Unexpected response',
    body: 'Exobios AI returned a response we could not read. Please try again.',
  },
  default: {
    title: 'Something went wrong',
    body: "We couldn't process this request right now. Please try again.",
  },
}

const errorMeta = computed(() => ERROR_META[props.message.code] ?? ERROR_META.default)
</script>

<template>
  <!-- User message -->
  <div v-if="message.role === 'user'" class="flex justify-end">
    <div class="max-w-[85%] rounded-2xl rounded-br-md bg-blue-600 px-4 py-2.5 text-sm text-white shadow-sm sm:max-w-[75%]">
      <p class="whitespace-pre-wrap">{{ message.content }}</p>
    </div>
  </div>

  <!-- Insufficient evidence -->
  <div v-else-if="isInsufficientEvidence" class="flex justify-start">
    <div class="max-w-[92%] rounded-2xl rounded-bl-md border border-slate-200 bg-slate-50 px-4 py-3 sm:max-w-[85%]">
      <div class="flex items-start gap-2.5">
        <svg class="mt-0.5 h-4 w-4 shrink-0 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
          <path stroke-linecap="round" stroke-linejoin="round" d="m21 21-4.35-4.35M11 19a8 8 0 1 1 0-16 8 8 0 0 1 0 16Z" />
        </svg>
        <div>
          <p class="text-sm font-semibold text-slate-700">Insufficient evidence in the current knowledge base</p>
          <p class="mt-1 text-sm leading-relaxed text-slate-500">{{ message.content }}</p>
        </div>
      </div>
    </div>
  </div>

  <!-- Assistant message -->
  <div v-else-if="message.role === 'assistant'" class="flex justify-start">
    <div class="group max-w-[92%] rounded-2xl rounded-bl-md border border-slate-200 bg-white px-4 py-3.5 shadow-sm sm:max-w-[85%]">
      <div class="prose prose-sm max-w-none text-slate-800" v-html="renderedHtml" />

      <p
        v-if="message.grounded === false && message.citations?.length"
        class="mt-2.5 text-xs text-amber-700"
      >
        This answer may only partially reflect the knowledge base.
      </p>

      <CitationList v-if="message.citations?.length" :citations="message.citations" />

      <div class="mt-3 flex items-center gap-1 border-t border-slate-100 pt-2 opacity-0 transition-opacity motion-safe:duration-150 group-hover:opacity-100 group-focus-within:opacity-100">
        <button
          type="button"
          @click="copyContent"
          class="flex items-center gap-1 rounded-lg px-2 py-1 text-[11px] font-medium text-slate-400 transition hover:bg-slate-50 hover:text-slate-600 focus-visible:opacity-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/40"
          :aria-label="copied ? 'Copied to clipboard' : 'Copy response'"
        >
          <svg v-if="!copied" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 17.25v3.375c0 .621-.504 1.125-1.125 1.125h-9.75a1.125 1.125 0 0 1-1.125-1.125V7.875c0-.621.504-1.125 1.125-1.125H6.75a9.06 9.06 0 0 1 1.5.124m7.5 10.376h3.375c.621 0 1.125-.504 1.125-1.125V11.25c0-4.46-3.243-8.161-7.5-8.876a9.06 9.06 0 0 0-1.5-.124H9.375c-.621 0-1.125.504-1.125 1.125v3.5m7.5 10.375H9.375a1.125 1.125 0 0 1-1.125-1.125v-9.25m12 6.625v-1.875a3.375 3.375 0 0 0-3.375-3.375h-1.5a1.125 1.125 0 0 1-1.125-1.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H9.75" />
          </svg>
          <svg v-else class="h-3.5 w-3.5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" />
          </svg>
          {{ copied ? 'Copied' : 'Copy' }}
        </button>

        <span class="mx-1 h-3 w-px bg-slate-200" />

        <button
          type="button"
          @click="setFeedback('up')"
          :aria-pressed="feedback === 'up'"
          aria-label="Mark response as helpful"
          class="rounded-lg p-1.5 transition hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/40"
          :class="feedback === 'up' ? 'text-emerald-600' : 'text-slate-400 hover:text-slate-600'"
        >
          <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6.633 10.5c.806 0 1.533-.446 2.031-1.08a9.041 9.041 0 0 1 2.861-2.4c.723-.384 1.35-.956 1.653-1.715a4.498 4.498 0 0 0 .322-1.672V3a.75.75 0 0 1 .75-.75A2.25 2.25 0 0 1 16.5 4.5c0 1.152-.26 2.243-.723 3.218-.266.558.107 1.282.725 1.282h3.126c1.026 0 1.945.694 2.054 1.715.045.422.068.85.068 1.285a11.95 11.95 0 0 1-2.649 7.521c-.388.482-.987.729-1.605.729H13.48c-.483 0-.964-.078-1.423-.23l-3.114-1.04a4.501 4.501 0 0 0-1.423-.23H5.904M14.25 9h2.25M5.904 18.75c.083.205.173.405.27.602.197.4-.078.898-.523.898h-.908c-.889 0-1.713-.518-1.972-1.368a12 12 0 0 1-.521-3.507c0-1.553.295-3.036.831-4.398C3.387 10.203 4.167 9.75 5 9.75h1.053c.472 0 .745.556.5.96a8.958 8.958 0 0 0-1.302 4.665c0 1.194.232 2.333.654 3.375Z" />
          </svg>
        </button>
        <button
          type="button"
          @click="setFeedback('down')"
          :aria-pressed="feedback === 'down'"
          aria-label="Mark response as not helpful"
          class="rounded-lg p-1.5 transition hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/40"
          :class="feedback === 'down' ? 'text-red-600' : 'text-slate-400 hover:text-slate-600'"
        >
          <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
            <path stroke-linecap="round" stroke-linejoin="round" d="M17.367 13.5c-.806 0-1.533.446-2.031 1.08a9.041 9.041 0 0 1-2.861 2.4c-.723.384-1.35.956-1.653 1.715a4.498 4.498 0 0 0-.322 1.672V21a.75.75 0 0 1-.75.75 2.25 2.25 0 0 1-2.25-2.25c0-1.152.26-2.243.723-3.218.266-.558-.107-1.282-.725-1.282H3.372c-1.026 0-1.945-.694-2.054-1.715a12.137 12.137 0 0 1-.068-1.285c0-2.848.992-5.464 2.649-7.521.388-.482.987-.729 1.605-.729H9.52c.483 0 .964.078 1.423.23l3.114 1.04a4.501 4.501 0 0 0 1.423.23h2.616M9.75 15h-2.25m10.622-9.75c-.083-.205-.173-.405-.27-.602-.197-.4.078-.898.523-.898h.908c.889 0 1.713.518 1.972 1.368.339 1.11.521 2.287.521 3.507 0 1.553-.295 3.036-.831 4.398C20.613 13.797 19.833 14.25 19 14.25h-1.053c-.472 0-.745-.556-.5-.96a8.958 8.958 0 0 0 1.302-4.665c0-1.194-.232-2.333-.654-3.375Z" />
          </svg>
        </button>
      </div>
    </div>
  </div>

  <!-- Error message -->
  <div v-else class="flex justify-start">
    <div class="flex max-w-[85%] items-start gap-2.5 rounded-2xl rounded-bl-md border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-700 sm:max-w-[75%]">
      <svg class="mt-0.5 h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="13" /><line x1="12" y1="16" x2="12.01" y2="16" />
      </svg>
      <div>
        <p class="font-semibold">{{ errorMeta.title }}</p>
        <p class="mt-0.5 text-red-600">{{ errorMeta.body }}</p>
        <button
          type="button"
          @click="emit('retry')"
          class="mt-2 rounded-lg border border-red-200 bg-white px-3 py-1.5 text-xs font-semibold text-red-700 transition hover:bg-red-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-400/50"
        >
          Retry
        </button>
      </div>
    </div>
  </div>
</template>
