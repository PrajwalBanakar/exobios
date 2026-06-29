import { ref } from 'vue'

/**
 * Lightweight toast notification composable.
 *
 * Usage in a component:
 *   const { toasts, showToast } = useToast()
 *   showToast('Saved!', 'success')
 *
 * Then render <div v-for="t in toasts"> in a fixed overlay in AppShell.
 *
 * Types: 'success' | 'error' | 'warning' | 'info'
 */

const toasts = ref([])
let nextId = 0

export function useToast() {
  function showToast(message, type = 'info', duration = 3000) {
    const id = nextId++
    toasts.value.push({ id, message, type })
    setTimeout(() => {
      toasts.value = toasts.value.filter(t => t.id !== id)
    }, duration)
  }

  function removeToast(id) {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }

  return { toasts, showToast, removeToast }
}
