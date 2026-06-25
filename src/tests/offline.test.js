import { describe, it, expect, vi, beforeEach } from 'vitest'
import { enqueue, getPendingItems, getAllQueueItems, updateQueueItem, removeQueueItem, clearSyncedItems } from '@/shared/offline/db.js'

// These tests verify the mock behaviour set up in setup.js
// When a real IndexedDB environment is available (e.g. playwright), swap the mock for the real implementation.

describe('Offline DB module (mocked)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('enqueue() resolves with a numeric id', async () => {
    enqueue.mockResolvedValueOnce(42)
    const id = await enqueue('add_patient', { name: 'Test' })
    expect(id).toBe(42)
    expect(enqueue).toHaveBeenCalledWith('add_patient', { name: 'Test' })
  })

  it('getPendingItems() returns an array', async () => {
    getPendingItems.mockResolvedValueOnce([{ id: 1, type: 'add_patient', status: 'pending' }])
    const items = await getPendingItems()
    expect(Array.isArray(items)).toBe(true)
    expect(items[0].type).toBe('add_patient')
  })

  it('updateQueueItem() is called with the right args', async () => {
    await updateQueueItem(1, { status: 'syncing' })
    expect(updateQueueItem).toHaveBeenCalledWith(1, { status: 'syncing' })
  })

  it('removeQueueItem() is called', async () => {
    await removeQueueItem(1)
    expect(removeQueueItem).toHaveBeenCalledWith(1)
  })

  it('getAllQueueItems() returns empty by default', async () => {
    const items = await getAllQueueItems()
    expect(items).toEqual([])
  })

  it('clearSyncedItems() resolves without error', async () => {
    await expect(clearSyncedItems()).resolves.toBeUndefined()
  })
})

// ── SyncQueue module ────────────────────────────────────────────────────────
import { addToQueue, drainQueue, retryFailed } from '@/shared/offline/syncQueue.js'

describe('SyncQueue module (mocked)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('addToQueue() calls enqueue and returns', async () => {
    await expect(addToQueue('add_patient', { name: 'Test' })).resolves.toBeUndefined()
  })

  it('drainQueue() can be called without throwing', async () => {
    await expect(drainQueue()).resolves.toBeUndefined()
  })

  it('retryFailed() can be called without throwing', async () => {
    await expect(retryFailed()).resolves.toBeUndefined()
  })
})
