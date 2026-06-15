/**
 * Format a Date or ISO string into a human-readable date string.
 * Uses the en-IN locale by default to match the project's Indian context.
 *
 * @param {Date|string} date
 * @param {Intl.DateTimeFormatOptions} [options]
 * @returns {string}
 */
export function formatDate(date, options = { day: 'numeric', month: 'short', year: 'numeric' }) {
  const d = date instanceof Date ? date : new Date(date)
  return d.toLocaleDateString('en-IN', options)
}

/**
 * Format a Date or ISO string into a short time string (e.g. "02:30 PM").
 *
 * @param {Date|string} date
 * @returns {string}
 */
export function formatTime(date) {
  const d = date instanceof Date ? date : new Date(date)
  return d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true })
}

/**
 * Returns a combined date-time string like "15 Jun 2025, 02:30 PM".
 *
 * @param {Date|string} date
 * @returns {string}
 */
export function formatDateTime(date) {
  return `${formatDate(date)}, ${formatTime(date)}`
}
