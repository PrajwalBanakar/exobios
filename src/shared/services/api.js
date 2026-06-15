/**
 * Thin HTTP client for the Spring Boot backend.
 *
 * All methods return the parsed JSON body on success, or throw an Error with
 * `{ message, status }` populated from the server's error response.
 *
 * Base URL is read from the VITE_API_BASE_URL environment variable so it can
 * be swapped between local dev, staging, and production without code changes.
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

async function request(method, path, body) {
  const token = localStorage.getItem('exobios_auth')
  const headers = { 'Content-Type': 'application/json' }
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    const error = new Error(err.message ?? `HTTP ${res.status}`)
    error.status = res.status
    throw error
  }

  // 204 No Content — return nothing
  if (res.status === 204) return undefined
  return res.json()
}

export const api = {
  get:    (path)         => request('GET',    path),
  post:   (path, body)   => request('POST',   path, body),
  put:    (path, body)   => request('PUT',    path, body),
  patch:  (path, body)   => request('PATCH',  path, body),
  delete: (path)         => request('DELETE', path),
}
