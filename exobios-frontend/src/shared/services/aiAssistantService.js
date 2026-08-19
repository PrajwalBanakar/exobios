/**
 * Thin HTTP client for the exobios-ai RAG service's /chat endpoint — kept
 * separate from shared/services/api.js because it talks directly to the
 * AI microservice (dev/test only), not the Spring Boot backend, and uses
 * a different base URL / auth header.
 *
 * Base URL and API key are read from Vite env vars so local dev can point
 * at a locally running exobios-ai instance without code changes.
 */

const AI_SERVICE_URL = import.meta.env.VITE_AI_SERVICE_URL ?? 'http://localhost:8000'
const AI_API_KEY = import.meta.env.VITE_AI_API_KEY ?? ''
const DEFAULT_TIMEOUT_MS = 30000

function serviceError(message, code, status) {
  return Object.assign(new Error(message), { code, status })
}

/**
 * @param {string} question
 * @param {Array<{role: 'user'|'assistant', content: string}>} [history] Prior turns of the
 *   same conversation, oldest first, so the backend can resolve follow-up references.
 * @param {{ timeoutMs?: number, signal?: AbortSignal }} [options]
 * @returns {Promise<{ answer: string, citations: Array<{chunkId: string, documentId: string, excerpt: string, heading: string, page: number}>, grounded: boolean }>}
 *
 * Thrown errors carry a `code` ('network' | 'timeout' | 'http' | 'invalid')
 * and, for 'http', a `status`, so the UI can render a specific error state
 * instead of a raw message.
 */
export async function askExobiosAssistant(question, history = [], { timeoutMs = DEFAULT_TIMEOUT_MS, signal } = {}) {
  const controller = new AbortController()
  const onExternalAbort = () => controller.abort()
  signal?.addEventListener('abort', onExternalAbort)
  const timeout = setTimeout(() => controller.abort(), timeoutMs)

  let res
  try {
    res = await fetch(`${AI_SERVICE_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Api-Key': AI_API_KEY,
      },
      body: JSON.stringify({ question, history }),
      signal: controller.signal,
    })
  } catch (e) {
    if (e.name === 'AbortError') {
      throw serviceError('The request took too long and timed out.', 'timeout')
    }
    throw serviceError('Could not reach the Exobios AI service. Is it running?', 'network')
  } finally {
    clearTimeout(timeout)
    signal?.removeEventListener('abort', onExternalAbort)
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw serviceError(err.message ?? `AI service error (HTTP ${res.status})`, 'http', res.status)
  }

  let data
  try {
    data = await res.json()
  } catch {
    throw serviceError('Received an invalid response from the Exobios AI service.', 'invalid')
  }

  if (typeof data.answer !== 'string') {
    throw serviceError('Received an invalid response from the Exobios AI service.', 'invalid')
  }

  return data
}
