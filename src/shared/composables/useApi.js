import { ref } from 'vue'
import { api } from '@/shared/services/api'

/**
 * Wraps an API call with standard loading / error state.
 *
 * Usage:
 *   const { data, loading, error, execute } = useApi(() => api.get('/patients'))
 *   await execute()
 *
 * `immediate: true` fires the request on first call automatically.
 */
export function useApi(fn) {
  const data    = ref(null)
  const loading = ref(false)
  const error   = ref(null)

  async function execute(...args) {
    loading.value = true
    error.value   = null
    try {
      data.value = await fn(...args)
    } catch (err) {
      error.value = err
    } finally {
      loading.value = false
    }
    return data.value
  }

  return { data, loading, error, execute }
}
