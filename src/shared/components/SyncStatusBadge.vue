<script setup>
import { useSyncStatus } from '@/shared/offline/useSyncStatus'

defineProps({
  // 'bar' = horizontal strip | 'chip' = inline pill (default)
  variant: { type: String, default: 'chip' },
})

const { syncStatus, label, color, dotColor, showRetry, formattedLastSync, retryFailed, isSyncing } = useSyncStatus()
</script>

<template>
  <!-- Chip variant -->
  <div v-if="variant === 'chip' && syncStatus !== 'idle'" :class="['inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-medium select-none', color]">
    <span :class="['w-1.5 h-1.5 rounded-full flex-shrink-0', dotColor]"/>
    <span>{{ label }}</span>
    <svg v-if="isSyncing" class="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
      <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 0 0 4.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 0 1-15.357-2m15.357 2H15"/>
    </svg>
    <button v-if="showRetry" @click.stop="retryFailed" class="ml-0.5 underline text-[11px] font-semibold">Retry</button>
    <span v-if="syncStatus === 'synced' && formattedLastSync" class="text-[10px] opacity-70">· {{ formattedLastSync }}</span>
  </div>

  <!-- Bar variant -->
  <div v-else-if="variant === 'bar' && syncStatus !== 'idle'" :class="['flex items-center gap-2 px-4 py-2 border-b text-xs font-medium', color]">
    <span :class="['w-2 h-2 rounded-full flex-shrink-0', dotColor]"/>
    <span class="flex-1">{{ label }}</span>
    <svg v-if="isSyncing" class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
      <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 0 0 4.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 0 1-15.357-2m15.357 2H15"/>
    </svg>
    <button v-if="showRetry" @click.stop="retryFailed" class="underline font-semibold">Retry</button>
    <span v-if="syncStatus === 'synced' && formattedLastSync" class="opacity-70">Last synced {{ formattedLastSync }}</span>
  </div>
</template>
