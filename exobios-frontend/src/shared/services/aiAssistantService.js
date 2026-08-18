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

/**
 * @param {string} question
 * @returns {Promise<{ answer: string, citations: Array<{chunkId: string, documentId: string, excerpt: string, heading: string, page: number}>, grounded: boolean }>}
 */
export async function askExobiosAssistant(question) {
  let res
  try {
    res = await fetch(`${AI_SERVICE_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Api-Key': AI_API_KEY,
      },
      body: JSON.stringify({ question }),
    })
  } catch {
    throw new Error('Could not reach the Exobios AI service. Is it running?')
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.message ?? `AI service error (HTTP ${res.status})`)
  }

  return res.json()
}
