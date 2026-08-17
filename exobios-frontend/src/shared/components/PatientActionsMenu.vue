<script setup>
import { ref, onUnmounted } from 'vue'
import { useI18n } from '@/i18n'

/**
 * PatientActionsMenu — three-dot overflow menu for a patient row/card.
 * Purely presentational: emits intent, the parent owns routing and the
 * delete-confirmation flow.
 */
defineProps({
  patientName: { type: String, default: '' },
})

const emit = defineEmits(['view', 'assess', 'edit', 'delete'])
const { t } = useI18n()

const open = ref(false)

function handleOutsideClick(e) {
  if (!e.target.closest('[data-patient-menu]')) open.value = false
}
function handleEscape(e) {
  if (e.key === 'Escape') open.value = false
}

function toggle(e) {
  e.stopPropagation()
  open.value = !open.value
  if (open.value) {
    document.addEventListener('click', handleOutsideClick)
    document.addEventListener('keydown', handleEscape)
  } else {
    document.removeEventListener('click', handleOutsideClick)
    document.removeEventListener('keydown', handleEscape)
  }
}

function act(fn, e) {
  e.stopPropagation()
  open.value = false
  document.removeEventListener('click', handleOutsideClick)
  document.removeEventListener('keydown', handleEscape)
  fn()
}

onUnmounted(() => {
  document.removeEventListener('click', handleOutsideClick)
  document.removeEventListener('keydown', handleEscape)
})
</script>

<template>
  <div class="relative" data-patient-menu>
    <button
      type="button"
      class="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 transition hover:bg-slate-100 hover:text-slate-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/40"
      :aria-label="`More actions for ${patientName}`"
      aria-haspopup="menu"
      :aria-expanded="open"
      @click="toggle"
    >
      <svg class="h-4.5 w-4.5" width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="5" r="1.5"/><circle cx="12" cy="12" r="1.5"/><circle cx="12" cy="19" r="1.5"/>
      </svg>
    </button>

    <div
      v-if="open"
      role="menu"
      class="absolute right-0 top-full z-20 mt-1.5 w-48 overflow-hidden rounded-xl border border-slate-100 bg-white py-1 shadow-lg"
    >
      <button role="menuitem" class="flex w-full items-center gap-2.5 px-3.5 py-2.5 text-left text-sm text-slate-700 transition hover:bg-slate-50" @click="act(() => emit('view'), $event)">
        <svg class="h-4 w-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
        {{ t('dashboard.viewPatient') }}
      </button>
      <button role="menuitem" class="flex w-full items-center gap-2.5 px-3.5 py-2.5 text-left text-sm text-slate-700 transition hover:bg-slate-50" @click="act(() => emit('assess'), $event)">
        <svg class="h-4 w-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M9 12h6m-3-3v6m9-6a9 9 0 1 1-18 0 9 9 0 0 1 18 0z"/></svg>
        {{ t('dashboard.newAssessment') }}
      </button>
      <button role="menuitem" class="flex w-full items-center gap-2.5 px-3.5 py-2.5 text-left text-sm text-slate-700 transition hover:bg-slate-50" @click="act(() => emit('edit'), $event)">
        <svg class="h-4 w-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
        {{ t('dashboard.editPatient') }}
      </button>
      <div class="my-1 border-t border-slate-100"/>
      <button role="menuitem" class="flex w-full items-center gap-2.5 px-3.5 py-2.5 text-left text-sm text-red-600 transition hover:bg-red-50" @click="act(() => emit('delete'), $event)">
        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4h6v2"/></svg>
        {{ t('dashboard.deletePatient') }}
      </button>
    </div>
  </div>
</template>
