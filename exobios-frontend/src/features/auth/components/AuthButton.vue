<script setup>
defineProps({
  variant:  { type: String, default: 'primary' }, // primary | secondary | ghost
  loading:  { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
  type:     { type: String, default: 'button' },
})

const VARIANTS = {
  primary:   'bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white border-transparent shadow-sm shadow-blue-600/20',
  secondary: 'bg-white hover:bg-blue-50 text-blue-600 border-blue-200 hover:border-blue-300',
  ghost:     'bg-white hover:bg-slate-50 text-slate-700 border-slate-200',
}
</script>

<template>
  <button
    :type="type"
    :disabled="disabled || loading"
    :class="[
      'inline-flex h-12 w-full items-center justify-center gap-2 rounded-xl border text-sm font-semibold',
      'transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:ring-offset-1',
      'disabled:opacity-60 disabled:cursor-not-allowed',
      VARIANTS[variant],
    ]"
  >
    <svg v-if="loading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 0 1 8-8v8H4z"/>
    </svg>
    <slot />
  </button>
</template>
