/** Returns true if the value is not empty (null / undefined / blank string). */
export function required(value) {
  return value !== null && value !== undefined && String(value).trim().length > 0
}

/** Returns true for a 10-digit Indian mobile number. */
export function phone(value) {
  return /^[6-9]\d{9}$/.test(String(value).trim())
}

/** Returns true for a valid email address. */
export function email(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(value).trim())
}

/** Returns true for a 14-digit ABHA (Ayushman Bharat Health Account) ID. */
export function abhaId(value) {
  return /^\d{14}$/.test(String(value).replace(/[-\s]/g, ''))
}

/** Returns true when age is a positive integer ≤ 120. */
export function age(value) {
  const n = Number(value)
  return Number.isInteger(n) && n > 0 && n <= 120
}
