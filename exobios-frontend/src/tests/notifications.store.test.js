import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useNotificationsStore } from '@/features/notifications/stores/notifications'

describe('Notifications Store', () => {
  beforeEach(() => { setActivePinia(createPinia()) })

  it('seeds with sample notifications', () => {
    const store = useNotificationsStore()
    expect(store.items.length).toBeGreaterThan(0)
  })

  it('unreadCount reflects only unread items', () => {
    const store = useNotificationsStore()
    const expected = store.items.filter(n => !n.read).length
    expect(store.unreadCount).toBe(expected)
    expect(store.unreadCount).toBeGreaterThan(0)
  })

  it('markRead() marks a single notification as read and decrements unreadCount', () => {
    const store = useNotificationsStore()
    const unread = store.items.find(n => !n.read)
    const before = store.unreadCount
    store.markRead(unread.id)
    expect(unread.read).toBe(true)
    expect(store.unreadCount).toBe(before - 1)
  })

  it('markRead() on an already-read item is a no-op for the count', () => {
    const store = useNotificationsStore()
    const read = store.items.find(n => n.read)
    const before = store.unreadCount
    store.markRead(read.id)
    expect(store.unreadCount).toBe(before)
  })

  it('markRead() with an unknown id does not throw', () => {
    const store = useNotificationsStore()
    expect(() => store.markRead(999999)).not.toThrow()
  })

  it('markAllRead() clears unreadCount to zero', () => {
    const store = useNotificationsStore()
    store.markAllRead()
    expect(store.unreadCount).toBe(0)
    expect(store.items.every(n => n.read)).toBe(true)
  })
})
