import { openDB } from 'idb'

const DB_NAME    = 'exobios_offline'
const DB_VERSION = 1

let _db = null

export async function getDb() {
  if (_db) return _db
  _db = await openDB(DB_NAME, DB_VERSION, {
    upgrade(db) {
      // Pending sync operations queue
      if (!db.objectStoreNames.contains('syncQueue')) {
        const sq = db.createObjectStore('syncQueue', { keyPath: 'id', autoIncrement: true })
        sq.createIndex('by_type',   'type')
        sq.createIndex('by_status', 'status')
      }
      // Offline drafts keyed by a string key (e.g. "patient_new", "assessment_42")
      if (!db.objectStoreNames.contains('drafts')) {
        db.createObjectStore('drafts', { keyPath: 'key' })
      }
    },
  })
  return _db
}

// ── Drafts ─────────────────────────────────────────────────────────────────
export async function saveDraft(key, data) {
  const db = await getDb()
  await db.put('drafts', { key, data, savedAt: Date.now() })
}

export async function loadDraft(key) {
  const db  = await getDb()
  const rec = await db.get('drafts', key)
  return rec?.data ?? null
}

export async function deleteDraft(key) {
  const db = await getDb()
  await db.delete('drafts', key)
}

// ── Sync queue ─────────────────────────────────────────────────────────────
export async function enqueue(type, payload) {
  const db = await getDb()
  return db.add('syncQueue', {
    type,
    payload,
    status:    'pending',  // pending | syncing | failed
    attempts:  0,
    createdAt: Date.now(),
    updatedAt: Date.now(),
  })
}

export async function getPendingItems() {
  const db = await getDb()
  return db.getAllFromIndex('syncQueue', 'by_status', 'pending')
}

export async function getFailedItems() {
  const db = await getDb()
  return db.getAllFromIndex('syncQueue', 'by_status', 'failed')
}

export async function updateQueueItem(id, patch) {
  const db   = await getDb()
  const item = await db.get('syncQueue', id)
  if (!item) return
  await db.put('syncQueue', { ...item, ...patch, updatedAt: Date.now() })
}

export async function removeQueueItem(id) {
  const db = await getDb()
  await db.delete('syncQueue', id)
}

export async function getAllQueueItems() {
  const db = await getDb()
  return db.getAll('syncQueue')
}

export async function clearSyncedItems() {
  const db    = await getDb()
  const all   = await db.getAll('syncQueue')
  const synced = all.filter(i => i.status === 'synced')
  for (const item of synced) await db.delete('syncQueue', item.id)
}
