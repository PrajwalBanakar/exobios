<script setup>
/**
 * EmptyState — shown when a list or table has no items to display.
 *
 * Props:
 *   title   – primary heading
 *   message – supporting description
 *   icon    – 'folder' | 'search' | 'users' (default: 'folder')
 */
defineProps({
  title:   { type: String, required: true },
  message: { type: String, default: '' },
  icon:    { type: String, default: 'folder' },
})
</script>

<template>
  <div class="flex flex-col items-center justify-center py-16 text-center">
    <!-- Folder icon -->
    <svg v-if="icon === 'folder'" class="w-14 h-14 text-gray-300 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.2">
      <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
    </svg>
    <!-- Search icon -->
    <svg v-else-if="icon === 'search'" class="w-14 h-14 text-gray-300 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.2">
      <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
    </svg>
    <!-- Users icon -->
    <svg v-else class="w-14 h-14 text-gray-300 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.2">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
      <path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
    </svg>

    <h3 class="text-base font-semibold text-gray-700 mb-1">{{ title }}</h3>
    <p v-if="message" class="text-sm text-gray-400 max-w-xs">{{ message }}</p>

    <slot />
  </div>
</template>
