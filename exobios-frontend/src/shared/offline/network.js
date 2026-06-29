import { ref, readonly } from 'vue'

const _isOnline = ref(navigator.onLine)

window.addEventListener('online',  () => { _isOnline.value = true  })
window.addEventListener('offline', () => { _isOnline.value = false })

export const isOnline = readonly(_isOnline)

export function useNetwork() {
  return { isOnline }
}
