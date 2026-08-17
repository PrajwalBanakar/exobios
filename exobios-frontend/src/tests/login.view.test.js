import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/vue'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import LoginView from '@/features/auth/views/LoginView.vue'
import { useAuthStore } from '@/features/auth/stores/auth'

// LoginView calls useRouter()/router.push('/dashboard') on successful login/signup —
// give it a real (memory-history) router so navigation resolves without touching the
// browser URL bar, and we can assert on the resulting route.
function makeRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', name: 'Login', component: { template: '<div>login-page</div>' } },
      { path: '/dashboard', name: 'Dashboard', component: { template: '<div>dashboard-page</div>' } },
    ],
  })
}

async function renderLogin() {
  const pinia = createPinia()
  setActivePinia(pinia)
  const router = makeRouter()
  await router.push('/')
  const utils = render(LoginView, { global: { plugins: [pinia, router] } })
  return { ...utils, router }
}

describe('LoginView — Login flow', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    localStorage.clear()
  })

  it('shows a validation error when submitting an empty form', async () => {
    const { container } = await renderLogin()
    await fireEvent.submit(container.querySelector('form'))
    expect(await screen.findByText(/enter login id and password/i)).toBeTruthy()
  })

  it('shows an error for invalid credentials', async () => {
    const { container } = await renderLogin()
    await fireEvent.update(screen.getByPlaceholderText('Phone number or worker ID'), 'nobody')
    await fireEvent.update(screen.getByPlaceholderText('Enter your password'), 'wrongpass')
    await fireEvent.submit(container.querySelector('form'))
    await vi.advanceTimersByTimeAsync(700)
    expect(await screen.findByText(/incorrect login id or password/i)).toBeTruthy()
  })

  it('logs in a registered user and navigates to the dashboard', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const auth = useAuthStore()
    auth.registerUser({ name: 'Sunita Devi', phone: '9876500001', ashaId: 'ASHA-001', role: 'ASHA', password: 'secret1' })

    const router = makeRouter()
    await router.push('/')
    const { container } = render(LoginView, { global: { plugins: [pinia, router] } })

    await fireEvent.update(screen.getByPlaceholderText('Phone number or worker ID'), '9876500001')
    await fireEvent.update(screen.getByPlaceholderText('Enter your password'), 'secret1')
    await fireEvent.submit(container.querySelector('form'))
    await vi.advanceTimersByTimeAsync(700)

    await waitFor(() => expect(router.currentRoute.value.name).toBe('Dashboard'))
    expect(useAuthStore().isLoggedIn).toBe(true)
  })

  it('disables the submit button while logging in', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    useAuthStore().registerUser({ name: 'A', phone: '9000000011', ashaId: 'ASHA-011', role: 'ASHA', password: 'pw1234' })
    const router = makeRouter()
    await router.push('/')
    const { container } = render(LoginView, { global: { plugins: [pinia, router] } })

    await fireEvent.update(screen.getByPlaceholderText('Phone number or worker ID'), '9000000011')
    await fireEvent.update(screen.getByPlaceholderText('Enter your password'), 'pw1234')
    await fireEvent.submit(container.querySelector('form'))

    expect(screen.getByText(/signing in/i).closest('button').disabled).toBe(true)
    await vi.advanceTimersByTimeAsync(700)
  })
})

describe('LoginView — Signup flow', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    localStorage.clear()
  })

  // Labels in this form aren't programmatically associated with their inputs (no
  // for/id), so we fill the signup form positionally: Name, Phone, [Role select],
  // ASHA ID, Password, Confirm Password — matching the on-screen field order.
  async function openSignup() {
    const { container } = await renderLogin()
    await fireEvent.click(screen.getByText('Create account'))
    return { container }
  }

  function signupInputs(container) {
    const inputs = container.querySelectorAll('form input')
    return { name: inputs[0], phone: inputs[1], ashaId: inputs[2], password: inputs[3], confirm: inputs[4] }
  }

  it('requires all mandatory fields', async () => {
    const { container } = await openSignup()
    const form = container.querySelector('form')
    await fireEvent.submit(form)
    expect(await screen.findByText(/please fill all required fields/i)).toBeTruthy()
  })

  it('rejects a phone number shorter than 10 digits', async () => {
    const { container } = await openSignup()
    const f = signupInputs(container)
    await fireEvent.update(f.name, 'Kavita Sharma')
    await fireEvent.update(f.phone, '123')
    await fireEvent.update(f.ashaId, 'ASHA-055')
    await fireEvent.update(f.password, 'pw123456')
    await fireEvent.submit(container.querySelector('form'))
    expect(await screen.findByText(/valid 10-digit phone number/i)).toBeTruthy()
  })

  it('rejects mismatched passwords', async () => {
    const { container } = await openSignup()
    const f = signupInputs(container)
    await fireEvent.update(f.name, 'Kavita Sharma')
    await fireEvent.update(f.phone, '9876500002')
    await fireEvent.update(f.ashaId, 'ASHA-056')
    await fireEvent.update(f.password, 'password1')
    await fireEvent.update(f.confirm, 'password2')
    await fireEvent.submit(container.querySelector('form'))
    expect(await screen.findByText(/passwords do not match/i)).toBeTruthy()
  })

  it('registers a new user and shows a success message', async () => {
    const { container } = await openSignup()
    const f = signupInputs(container)
    await fireEvent.update(f.name, 'Kavita Sharma')
    await fireEvent.update(f.phone, '9876500003')
    await fireEvent.update(f.ashaId, 'ASHA-057')
    await fireEvent.update(f.password, 'password1')
    await fireEvent.update(f.confirm, 'password1')
    await fireEvent.submit(container.querySelector('form'))
    await vi.advanceTimersByTimeAsync(900)

    expect(await screen.findByText(/account created/i)).toBeTruthy()
    const registered = useAuthStore().findUser('9876500003', 'password1')
    expect(registered?.name).toBe('Kavita Sharma')
  })

  it('rejects signup with a phone number that is already registered', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    useAuthStore().registerUser({ name: 'Existing', phone: '9876500004', ashaId: 'ASHA-058', role: 'ASHA', password: 'existingpw' })
    const router = makeRouter()
    await router.push('/')
    const { container } = render(LoginView, { global: { plugins: [pinia, router] } })
    await fireEvent.click(screen.getByText('Create account'))

    const f = signupInputs(container)
    await fireEvent.update(f.name, 'Duplicate')
    await fireEvent.update(f.phone, '9876500004')
    await fireEvent.update(f.ashaId, 'ASHA-059')
    await fireEvent.update(f.password, 'anotherpw')
    await fireEvent.update(f.confirm, 'anotherpw')
    await fireEvent.submit(container.querySelector('form'))
    await vi.advanceTimersByTimeAsync(900)

    expect(await screen.findByText(/already registered/i)).toBeTruthy()
  })
})

describe('LoginView — Forgot password flow', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    localStorage.clear()
  })

  it('rejects an unregistered phone number', async () => {
    const { container } = await renderLogin()
    await fireEvent.click(screen.getByText('Forgot password?'))
    await fireEvent.update(screen.getByPlaceholderText('10-digit mobile number'), '9999999999')
    await fireEvent.click(screen.getByText('Send OTP'))
    await vi.advanceTimersByTimeAsync(900)
    expect(await screen.findByText(/not registered/i)).toBeTruthy()
  })

  it('walks a registered user through OTP verification to a new password', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const auth = useAuthStore()
    auth.registerUser({ name: 'Meena Rani', phone: '9876500005', ashaId: 'ASHA-060', role: 'ASHA', password: 'oldpass1' })
    const router = makeRouter()
    await router.push('/')
    const { container } = render(LoginView, { global: { plugins: [pinia, router] } })

    await fireEvent.click(screen.getByText('Forgot password?'))
    await fireEvent.update(screen.getByPlaceholderText('10-digit mobile number'), '9876500005')
    await fireEvent.click(screen.getByText('Send OTP'))
    await vi.advanceTimersByTimeAsync(900)

    // The OTP is displayed directly in the UI (known mock-phase behavior) — read it
    // back from the DOM rather than hardcoding a value, then key it into the 6 boxes.
    const otpText = container.querySelector('.tracking-widest').textContent.trim()
    const digitInputs = container.querySelectorAll('input[id^="fotp-"]')
    expect(digitInputs.length).toBe(6)
    for (let i = 0; i < 6; i++) {
      await fireEvent.update(digitInputs[i], otpText[i])
    }
    await fireEvent.click(screen.getByText('Verify OTP'))

    expect(await screen.findByText(/set your new password/i)).toBeTruthy()

    await fireEvent.update(screen.getByPlaceholderText('New password'), 'brandnew1')
    await fireEvent.update(screen.getByPlaceholderText('Confirm new password'), 'brandnew1')
    await fireEvent.click(screen.getByText('Reset Password'))
    await vi.advanceTimersByTimeAsync(900)

    expect(await screen.findByText(/password reset successful/i)).toBeTruthy()
    expect(auth.findUser('9876500005', 'brandnew1')).toBeTruthy()
    expect(auth.findUser('9876500005', 'oldpass1')).toBeNull()
  })

  it('rejects a new password shorter than 4 characters', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const auth = useAuthStore()
    auth.registerUser({ name: 'Anita Singh', phone: '9876500006', ashaId: 'ASHA-061', role: 'ASHA', password: 'oldpass1' })
    const router = makeRouter()
    await router.push('/')
    const { container } = render(LoginView, { global: { plugins: [pinia, router] } })

    await fireEvent.click(screen.getByText('Forgot password?'))
    await fireEvent.update(screen.getByPlaceholderText('10-digit mobile number'), '9876500006')
    await fireEvent.click(screen.getByText('Send OTP'))
    await vi.advanceTimersByTimeAsync(900)

    const otpText = container.querySelector('.tracking-widest').textContent.trim()
    const digitInputs = container.querySelectorAll('input[id^="fotp-"]')
    for (let i = 0; i < 6; i++) await fireEvent.update(digitInputs[i], otpText[i])
    await fireEvent.click(screen.getByText('Verify OTP'))

    await fireEvent.update(screen.getByPlaceholderText('New password'), 'ab')
    await fireEvent.update(screen.getByPlaceholderText('Confirm new password'), 'ab')
    await fireEvent.click(screen.getByText('Reset Password'))
    expect(await screen.findByText(/at least 4 characters/i)).toBeTruthy()
  })
})
