<script setup>
/**
 * BaseButton — consistent button primitive with variant, size, and loading support.
 *
 * Props:
 *   variant  – 'primary' | 'secondary' | 'danger' | 'ghost'  (default: 'primary')
 *   size     – 'sm' | 'md' | 'lg'                             (default: 'md')
 *   loading  – show a spinner and disable interaction          (default: false)
 *   disabled – native disabled behaviour                       (default: false)
 *   type     – native button type                              (default: 'button')
 */
defineProps({
  variant:  { type: String, default: 'primary' },
  size:     { type: String, default: 'md' },
  loading:  { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
  type:     { type: String, default: 'button' },
})

const VARIANTS = {
  primary:   'bg-blue-600 hover:bg-blue-700 text-white border-transparent',
  secondary: 'bg-white hover:bg-gray-50 text-gray-700 border-gray-200',
  danger:    'bg-red-600 hover:bg-red-700 text-white border-transparent',
  ghost:     'bg-transparent hover:bg-gray-100 text-gray-600 border-transparent',
}

const SIZES = {
  sm: 'px-3 py-1.5 text-xs',
  md: 'px-5 py-2.5 text-sm',
  lg: 'px-7 py-3 text-base',
}
</script>

<template>
  <button
    :type="type"
    :disabled="disabled || loading"
    :class="[
      'inline-flex items-center justify-center gap-2 font-medium rounded-lg border transition focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1',
      'disabled:opacity-60 disabled:cursor-not-allowed',
      VARIANTS[variant],
      SIZES[size],
    ]"
  >
    <!-- Spinner shown while loading -->
    <svg v-if="loading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 0 1 8-8v8H4z"/>
    </svg>
    <slot />
  </button>
</template>
