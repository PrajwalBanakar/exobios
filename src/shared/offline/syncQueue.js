/**
 * Sync queue: wraps IndexedDB queue items and drives them against the backend.
 * Because the backend doesn't exist yet, "syncing" means applying to the
 * Pinia patients store (localStorage) and marking the item synced.
 * When a real API is ready, replace the applyLocally() calls with fetch().
 */
import { ref, readonly, computed } from 'vue'
import {
  enqueue, getPendingItems, getFailedItems, getAllQueueItems,
  updateQueueItem, removeQueueItem, clearSyncedItems,
} from './db.js'
import { isOnline } from './network.js'

// ── Reactive queue state ───────────────────────────────────────────────────
const _items   = ref([])   // snapshot of all queue items
const _syncing = ref(false)
const _lastSync = ref(localStorage.getItem('exobios_last_sync') || null)

export const syncItems  = readonly(_items)
export const isSyncing  = readonly(_syncing)
export const lastSync   = readonly(_lastSync)

export const pendingCount = computed(() => _items.value.filter(i => i.status === 'pending').length)
export const failedCount  = computed(() => _items.value.filter(i => i.status === 'failed').length)

// ── Sync state label (for the badge) ──────────────────────────────────────
// "saved_offline" | "pending" | "syncing" | "synced" | "failed"
export const syncStatus = computed(() => {
  if (_syncing.value)                    return 'syncing'
  if (failedCount.value > 0)             return 'failed'
  if (pendingCount.value > 0 && !isOnline.value) return 'saved_offline'
  if (pendingCount.value > 0)            return 'pending'
  if (_lastSync.value)                   return 'synced'
  return 'idle'
})

async function refreshItems() {
  _items.value = await getAllQueueItems()
}

// ── Add to queue ───────────────────────────────────────────────────────────
export async function addToQueue(type, payload) {
  await enqueue(type, payload)
  await refreshItems()
  if (isOnline.value) drainQueue()
}

// ── Apply locally (simulates API call until backend exists) ────────────────
async function applyLocally(item) {
  const { usePatientsStore } = await import('@/features/patients/stores/patients')
  const store = usePatientsStore()

  switch (item.type) {
    case 'add_patient':
      store.add(item.payload)
      break
    case 'update_patient':
      store.update(item.payload.id, item.payload.data)
      break
    case 'add_assessment':
      store.addAssessment(item.payload.patientId, item.payload.data)
      break
    case 'add_measures':
      // Measures are already committed by MeasuresView.submitMeasures()
      // so nothing to apply; just mark synced
      break
  }
}

// ── Drain the queue ────────────────────────────────────────────────────────
export async function drainQueue() {
  if (_syncing.value || !isOnline.value) return
  const pending = await getPendingItems()
  if (!pending.length) return

  _syncing.value = true
  await refreshItems()

  for (const item of pending) {
    try {
      await updateQueueItem(item.id, { status: 'syncing' })
      await applyLocally(item)
      await removeQueueItem(item.id)
    } catch {
      const attempts = (item.attempts || 0) + 1
      await updateQueueItem(item.id, {
        status:   attempts >= 3 ? 'failed' : 'pending',
        attempts,
      })
    }
  }

  _lastSync.value = new Date().toISOString()
  localStorage.setItem('exobios_last_sync', _lastSync.value)
  await clearSyncedItems()
  await refreshItems()
  _syncing.value = false
}

// ── Retry failed items ─────────────────────────────────────────────────────
export async function retryFailed() {
  const failed = await getFailedItems()
  for (const item of failed) {
    await updateQueueItem(item.id, { status: 'pending', attempts: 0 })
  }
  await refreshItems()
  drainQueue()
}

// ── Init: refresh on load + when coming back online ───────────────────────
refreshItems()

// Re-run drain each time we come back online
window.addEventListener('online', () => {
  refreshItems()
  drainQueue()
})
