/**
 * Composable: exposes sync state + helpers for use in Vue components.
 */
import { computed } from 'vue'
import { syncStatus, isSyncing, pendingCount, failedCount, lastSync, retryFailed } from './syncQueue.js'
import { isOnline } from './network.js'

export function useSyncStatus() {
  const label = computed(() => {
    switch (syncStatus.value) {
      case 'saved_offline': return 'Saved offline'
      case 'pending':       return 'Pending sync'
      case 'syncing':       return 'Syncing…'
      case 'synced':        return 'Synced'
      case 'failed':        return 'Sync failed'
      default:              return ''
    }
  })

  const color = computed(() => {
    switch (syncStatus.value) {
      case 'saved_offline': return 'text-amber-600 bg-amber-50 border-amber-200'
      case 'pending':       return 'text-blue-600 bg-blue-50 border-blue-200'
      case 'syncing':       return 'text-blue-600 bg-blue-50 border-blue-200'
      case 'synced':        return 'text-green-600 bg-green-50 border-green-200'
      case 'failed':        return 'text-red-600 bg-red-50 border-red-200'
      default:              return 'text-gray-500 bg-gray-50 border-gray-200'
    }
  })

  const dotColor = computed(() => {
    switch (syncStatus.value) {
      case 'saved_offline': return 'bg-amber-400'
      case 'pending':       return 'bg-blue-400 animate-pulse'
      case 'syncing':       return 'bg-blue-500 animate-pulse'
      case 'synced':        return 'bg-green-500'
      case 'failed':        return 'bg-red-500'
      default:              return 'bg-gray-300'
    }
  })

  const showRetry = computed(() => syncStatus.value === 'failed')

  const formattedLastSync = computed(() => {
    if (!lastSync.value) return null
    const d = new Date(lastSync.value)
    return d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true })
  })

  return {
    syncStatus,
    isSyncing,
    pendingCount,
    failedCount,
    lastSync,
    formattedLastSync,
    isOnline,
    label,
    color,
    dotColor,
    showRetry,
    retryFailed,
  }
}
