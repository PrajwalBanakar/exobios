import { describe, it, expect, vi, beforeEach } from 'vitest'
import { computed, ref } from 'vue'

// We test the composable's label/color derivation directly by importing it
// The syncQueue and network modules are mocked in setup.js

// Re-export helpers used internally by the composable so we can stub them
vi.mock('@/shared/offline/syncQueue.js', () => {
  const syncStatus   = ref('idle')
  const isSyncing    = ref(false)
  const pendingCount = ref(0)
  const failedCount  = ref(0)
  const lastSync     = ref(null)
  const retryFailed  = vi.fn()
  return { syncStatus, isSyncing, pendingCount, failedCount, lastSync, retryFailed, addToQueue: vi.fn(), drainQueue: vi.fn() }
})

vi.mock('@/shared/offline/network.js', () => {
  const isOnline = ref(true)
  return { isOnline, useNetwork: () => ({ isOnline }) }
})

import { useSyncStatus } from '@/shared/offline/useSyncStatus'
import * as syncQueueModule from '@/shared/offline/syncQueue.js'

describe('useSyncStatus composable', () => {
  beforeEach(() => {
    syncQueueModule.syncStatus.value   = 'idle'
    syncQueueModule.isSyncing.value    = false
    syncQueueModule.pendingCount.value = 0
    syncQueueModule.failedCount.value  = 0
    syncQueueModule.lastSync.value     = null
  })

  it('returns empty label when idle', () => {
    const { label } = useSyncStatus()
    expect(label.value).toBe('')
  })

  it('label is "Saved offline" for saved_offline status', () => {
    syncQueueModule.syncStatus.value = 'saved_offline'
    const { label } = useSyncStatus()
    expect(label.value).toBe('Saved offline')
  })

  it('label is "Syncing…" when syncing', () => {
    syncQueueModule.syncStatus.value = 'syncing'
    const { label } = useSyncStatus()
    expect(label.value).toBe('Syncing…')
  })

  it('label is "Synced" when synced', () => {
    syncQueueModule.syncStatus.value = 'synced'
    const { label } = useSyncStatus()
    expect(label.value).toBe('Synced')
  })

  it('label is "Sync failed" when failed', () => {
    syncQueueModule.syncStatus.value = 'failed'
    const { label } = useSyncStatus()
    expect(label.value).toBe('Sync failed')
  })

  it('showRetry is true only when failed', () => {
    const { showRetry } = useSyncStatus()
    syncQueueModule.syncStatus.value = 'failed'
    expect(showRetry.value).toBe(true)
    syncQueueModule.syncStatus.value = 'synced'
    expect(showRetry.value).toBe(false)
  })

  it('color contains green class when synced', () => {
    syncQueueModule.syncStatus.value = 'synced'
    const { color } = useSyncStatus()
    expect(color.value).toContain('green')
  })

  it('color contains red class when failed', () => {
    syncQueueModule.syncStatus.value = 'failed'
    const { color } = useSyncStatus()
    expect(color.value).toContain('red')
  })
})
