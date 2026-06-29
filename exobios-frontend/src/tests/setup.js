import { vi } from 'vitest'

// Mock IndexedDB (idb) since jsdom doesn't have it
vi.mock('@/shared/offline/db.js', () => ({
  getDb:           vi.fn(),
  saveDraft:       vi.fn().mockResolvedValue(undefined),
  loadDraft:       vi.fn().mockResolvedValue(null),
  deleteDraft:     vi.fn().mockResolvedValue(undefined),
  enqueue:         vi.fn().mockResolvedValue(1),
  getPendingItems: vi.fn().mockResolvedValue([]),
  getFailedItems:  vi.fn().mockResolvedValue([]),
  getAllQueueItems: vi.fn().mockResolvedValue([]),
  updateQueueItem: vi.fn().mockResolvedValue(undefined),
  removeQueueItem: vi.fn().mockResolvedValue(undefined),
  clearSyncedItems: vi.fn().mockResolvedValue(undefined),
}))

// Mock syncQueue at module level so stores don't need a real DB
vi.mock('@/shared/offline/syncQueue.js', () => ({
  addToQueue:   vi.fn().mockResolvedValue(undefined),
  drainQueue:   vi.fn().mockResolvedValue(undefined),
  retryFailed:  vi.fn().mockResolvedValue(undefined),
  syncItems:    { value: [] },
  isSyncing:    { value: false },
  lastSync:     { value: null },
  pendingCount: { value: 0 },
  failedCount:  { value: 0 },
  syncStatus:   { value: 'idle' },
}))

// Stub localStorage
const store = {}
global.localStorage = {
  getItem:    vi.fn((k) => store[k] ?? null),
  setItem:    vi.fn((k, v) => { store[k] = v }),
  removeItem: vi.fn((k) => { delete store[k] }),
  clear:      vi.fn(() => { Object.keys(store).forEach(k => delete store[k]) }),
}

// Stub navigator.onLine
Object.defineProperty(navigator, 'onLine', { get: () => true, configurable: true })
