/**
 * Shared formatting helpers — centralizes display-only formatting so the same
 * conventions (patient ID shape, month comparisons) aren't reimplemented per view.
 */

/** Friendly display ID derived from a patient's real numeric id (e.g. 7 -> "EXO-0007"). */
export function formatPatientId(id) {
  return `EXO-${String(id).padStart(4, '0')}`
}

/** True when a date string/Date falls in the current calendar month and year. */
export function isThisMonth(date) {
  if (!date) return false
  const d = date instanceof Date ? date : new Date(date)
  const now = new Date()
  return !isNaN(d) && d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear()
}
