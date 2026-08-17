<script setup>
import { useSyncStatus } from '@/shared/offline/useSyncStatus'
import { useI18n } from '@/i18n'

/**
 * StatusIndicator — compact online/offline + last-synced pill for the app topbar.
 * Backed by the real sync queue state (useSyncStatus) — never a fabricated timestamp.
 */
const { isOnline, formattedLastSync } = useSyncStatus()
const { t } = useI18n()
</script>

<template>
  <div class="hidden items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs md:flex">
    <span class="flex items-center gap-1.5">
      <span :class="['h-2 w-2 rounded-full flex-shrink-0', isOnline ? 'bg-green-500' : 'bg-amber-500 animate-pulse']"/>
      <span :class="['font-medium', isOnline ? 'text-slate-700' : 'text-amber-700']">
        {{ isOnline ? t('topbar.online') : t('sync.offline') }}
      </span>
    </span>
    <template v-if="formattedLastSync">
      <span class="text-slate-300">·</span>
      <span class="text-slate-500">{{ t('topbar.synced') }} {{ formattedLastSync }}</span>
    </template>
  </div>
</template>
