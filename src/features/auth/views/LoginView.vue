<script setup>
import { ref, reactive, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/features/auth/stores/auth'
import { useI18n } from '@/i18n'

const router = useRouter()
const auth   = useAuthStore()
const { t }  = useI18n()

// Modes: login | signup | otp | forgot
const mode = ref('login')

// ─── Login ────────────────────────────────────────────────────────────────────
const loginId  = ref('')
const password = ref('')
const showPass = ref(false)
const remember = ref(false)
const loading  = ref(false)
const error    = ref('')

async function handleLogin() {
  if (!loginId.value || !password.value) { error.value = 'Please enter Login ID and Password.'; return }
  loading.value = true; error.value = ''
  try {
    await new Promise(r => setTimeout(r, 600))
    const found = auth.findUser(loginId.value, password.value)
    if (!found) { error.value = 'Invalid credentials. Please check your Login ID (phone/ASHA ID) and password.'; return }
    auth.login({ loginId: found.phone, name: found.name, role: found.role })
    await router.push('/dashboard')
  } catch {
    error.value = 'Login failed. Please try again.'
  } finally {
    loading.value = false
  }
}

// ─── OTP Login ────────────────────────────────────────────────────────────────
const otpPhone        = ref('')
const otpStep         = ref('phone') // phone | verify
const otpDigits       = ref(['', '', '', '', '', ''])
const otpError        = ref('')
const otpSending      = ref(false)
const otpLoading      = ref(false)
const resendCountdown = ref(0)
const generatedOtp    = ref('')
let resendTimer = null

function startResendCountdown() {
  if (resendTimer) clearInterval(resendTimer)
  resendCountdown.value = 30
  resendTimer = setInterval(() => {
    resendCountdown.value--
    if (resendCountdown.value <= 0) clearInterval(resendTimer)
  }, 1000)
}

// Reset OTP digit inputs when entering the verify step
watch(otpStep, (newStep) => {
  if (newStep === 'verify') {
    otpDigits.value = ['', '', '', '', '', '']
    nextTick(() => {
      for (let i = 0; i < 6; i++) {
        const el = document.getElementById(`otp-${i}`)
        if (el) el.value = ''
      }
      document.getElementById('otp-0')?.focus()
    })
  }
})

async function sendOtp() {
  if (!otpPhone.value || otpPhone.value.length < 10) { otpError.value = 'Enter a valid 10-digit phone number.'; return }
  otpSending.value = true; otpError.value = ''
  await new Promise(r => setTimeout(r, 800))
  const user = auth.findUserByPhone(otpPhone.value)
  otpSending.value = false
  if (!user) { otpError.value = 'This phone number is not registered. Please sign up first.'; return }
  generatedOtp.value = String(Math.floor(100000 + Math.random() * 900000))
  otpStep.value = 'verify'
  startResendCountdown()
}

async function verifyOtp() {
  const code = otpDigits.value.join('')
  if (code.length < 6 || otpDigits.value.some(d => d === '')) { otpError.value = 'Enter all 6 digits.'; return }
  if (otpLoading.value) return
  otpError.value = ''
  otpLoading.value = true
  try {
    await new Promise(r => setTimeout(r, 600))
    if (code !== generatedOtp.value) { otpError.value = 'Incorrect OTP. Please try again.'; return }
    const user = auth.findUserByPhone(otpPhone.value)
    auth.login({ loginId: user.phone, name: user.name, role: user.role })
    await router.push('/dashboard')
  } catch {
    otpError.value = 'Something went wrong. Please try again.'
  } finally {
    otpLoading.value = false
  }
}

function handleOtpInput(idx, e) {
  const val = e.target.value.replace(/\D/g, '').slice(-1)
  e.target.value = val
  otpDigits.value[idx] = val
  if (val && idx < 5) document.getElementById(`otp-${idx + 1}`)?.focus()
  if (!otpLoading.value && otpDigits.value.every(d => d !== '') && otpDigits.value.join('').length === 6) verifyOtp()
}

function handleOtpKeydown(idx, e) {
  if (e.key === 'Backspace') {
    e.preventDefault()
    if (otpDigits.value[idx]) {
      otpDigits.value[idx] = ''
      e.target.value = ''
    } else if (idx > 0) {
      const prev = document.getElementById(`otp-${idx - 1}`)
      if (prev) { prev.focus(); prev.value = ''; otpDigits.value[idx - 1] = '' }
    }
  }
}

function handleOtpPaste(e) {
  e.preventDefault()
  const text   = (e.clipboardData || window.clipboardData).getData('text')
  const digits = text.replace(/\D/g, '').slice(0, 6)
  digits.split('').forEach((digit, i) => {
    otpDigits.value[i] = digit
    const el = document.getElementById(`otp-${i}`)
    if (el) el.value = digit
  })
  document.getElementById(`otp-${Math.min(digits.length, 5)}`)?.focus()
  if (digits.length === 6 && !otpLoading.value) verifyOtp()
}

// ─── Signup ───────────────────────────────────────────────────────────────────
const signup        = reactive({ name: '', phone: '', ashaId: '', role: 'ASHA Worker', password: '', confirm: '' })
const signupShowPass = ref(false)
const signupError   = ref('')
const signupSuccess = ref(false)

async function handleSignup() {
  if (!signup.name || !signup.phone || !signup.ashaId || !signup.password) { signupError.value = 'Please fill all required fields.'; return }
  if (signup.phone.length < 10) { signupError.value = 'Enter a valid 10-digit phone number.'; return }
  if (signup.password.length < 4) { signupError.value = 'Password must be at least 4 characters.'; return }
  if (signup.password !== signup.confirm) { signupError.value = 'Passwords do not match.'; return }
  signupError.value = ''
  loading.value = true
  await new Promise(r => setTimeout(r, 800))
  loading.value = false
  const result = auth.registerUser({ name: signup.name, phone: signup.phone, ashaId: signup.ashaId, role: signup.role, password: signup.password })
  if (!result.success) { signupError.value = result.error; return }
  signupSuccess.value = true
  setTimeout(() => { mode.value = 'login'; signupSuccess.value = false }, 2000)
}

// ─── Forgot Password ──────────────────────────────────────────────────────────
const forgotStep         = ref('phone') // phone | otp | newpass
const forgotPhone        = ref('')
const forgotOtp          = ref(['', '', '', '', '', ''])
const forgotNewPass      = ref('')
const forgotConfirm      = ref('')
const forgotError        = ref('')
const forgotSuccess      = ref(false)
const forgotGeneratedOtp = ref('')

async function sendForgotOtp() {
  if (!forgotPhone.value || forgotPhone.value.length < 10) { forgotError.value = 'Enter a valid phone number.'; return }
  forgotError.value = ''
  loading.value = true
  await new Promise(r => setTimeout(r, 800))
  loading.value = false
  const user = auth.findUserByPhone(forgotPhone.value)
  if (!user) { forgotError.value = 'This phone number is not registered.'; return }
  forgotGeneratedOtp.value = String(Math.floor(100000 + Math.random() * 900000))
  forgotStep.value = 'otp'
}

async function verifyForgotOtp() {
  const code = forgotOtp.value.join('')
  if (code.length < 6) { forgotError.value = 'Enter all 6 digits.'; return }
  if (code !== forgotGeneratedOtp.value) { forgotError.value = 'Incorrect OTP. Please try again.'; return }
  forgotError.value = ''
  forgotStep.value = 'newpass'
}

async function resetPassword() {
  if (!forgotNewPass.value) { forgotError.value = 'Enter a new password.'; return }
  if (forgotNewPass.value.length < 4) { forgotError.value = 'Password must be at least 4 characters.'; return }
  if (forgotNewPass.value !== forgotConfirm.value) { forgotError.value = 'Passwords do not match.'; return }
  loading.value = true
  await new Promise(r => setTimeout(r, 800))
  loading.value = false
  auth.updateUserPassword(forgotPhone.value, forgotNewPass.value)
  forgotSuccess.value = true
  setTimeout(() => { mode.value = 'login'; forgotSuccess.value = false; forgotStep.value = 'phone' }, 2000)
}

function handleForgotOtpInput(idx, e) {
  const val = e.target.value.replace(/\D/g, '').slice(-1)
  forgotOtp.value[idx] = val
  if (val && idx < 5) document.getElementById(`fotp-${idx + 1}`)?.focus()
}

// ─── Terms popup ──────────────────────────────────────────────────────────────
const showTerms = ref(false)
const termsTab  = ref('terms') // terms | privacy

// ─── Contact Us ───────────────────────────────────────────────────────────────
const contactForm    = reactive({ name: '', occupation: '', phone: '', workerId: '', other: '' })
const contactSuccess = ref(false)
const contactError   = ref('')

async function submitContact() {
  if (!contactForm.name || !contactForm.phone) { contactError.value = 'Name and phone number are required.'; return }
  contactError.value = ''
  loading.value = true
  await new Promise(r => setTimeout(r, 700))
  loading.value = false
  contactSuccess.value = true
  Object.assign(contactForm, { name: '', occupation: '', phone: '', workerId: '', other: '' })
  setTimeout(() => { contactSuccess.value = false; mode.value = 'login' }, 2500)
}
</script>

<template>
  <div class="min-h-screen flex">
    <!-- Left branding panel (desktop only) -->
    <div class="hidden lg:flex lg:w-[45%] flex-col items-center justify-center relative overflow-hidden"
         style="background: linear-gradient(160deg, #0a1628 0%, #0f1b35 50%, #0a1628 100%)">
      <div class="absolute inset-0 opacity-20">
        <svg viewBox="0 0 800 600" class="w-full h-full" preserveAspectRatio="xMidYMid slice">
          <defs>
            <radialGradient id="rg1" cx="50%" cy="80%">
              <stop offset="0%" stop-color="#3b82f6" stop-opacity="0.8"/>
              <stop offset="100%" stop-color="#1e3a8f" stop-opacity="0"/>
            </radialGradient>
          </defs>
          <ellipse cx="400" cy="500" rx="600" ry="200" fill="url(#rg1)"/>
        </svg>
      </div>
      <div class="relative z-10 text-center px-12">
        <div class="flex items-center justify-center gap-3 mb-10">
          <div class="w-12 h-12 rounded-xl bg-blue-500 flex items-center justify-center">
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L2 7l10 5 10-5-10-5z" stroke="white" stroke-width="2" stroke-linejoin="round"/>
              <path d="M2 17l10 5 10-5"           stroke="white" stroke-width="2" stroke-linejoin="round"/>
              <path d="M2 12l10 5 10-5"           stroke="white" stroke-width="2" stroke-linejoin="round"/>
            </svg>
          </div>
          <span class="text-white text-3xl font-bold">Exobios</span>
        </div>
        <h2 class="text-white text-4xl font-bold leading-tight mb-4">AI Assisted<br>Healthcare Platform</h2>
        <div class="w-12 h-1 bg-cyan-400 rounded mx-auto mb-6"/>
        <p class="text-slate-300 text-base leading-relaxed">Smart tools for faster triage,<br>better decisions, and improved care.</p>
        <div class="flex justify-center gap-10 mt-12">
          <div v-for="feature in [
            { icon: 'M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83', label: 'AI Powered' },
            { icon: 'M13 2L3 14h9l-1 8 10-12h-9l1-8z', label: 'Fast Triage' },
            { icon: 'M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z', label: 'Better Care' },
          ]" :key="feature.label" class="flex flex-col items-center gap-2">
            <div class="w-12 h-12 rounded-full border border-cyan-500/30 flex items-center justify-center">
              <svg class="w-6 h-6 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path :d="feature.icon"/></svg>
            </div>
            <span class="text-slate-300 text-xs">{{ feature.label }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Right: auth forms -->
    <div class="flex-1 flex items-center justify-center bg-white px-8 py-10 overflow-y-auto">
      <div class="w-full max-w-sm">

        <!-- ── LOGIN ── -->
        <template v-if="mode === 'login'">
          <h1 class="text-2xl font-bold text-gray-900 mb-1">{{ t('login.title') }}</h1>
          <p class="text-sm text-gray-500 mb-8">{{ t('login.subtitle') }}</p>
          <form @submit.prevent="handleLogin" class="space-y-4">
            <div class="relative">
              <div class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
              </div>
              <input v-model="loginId" type="text" :placeholder="t('login.loginId')"
                class="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"/>
            </div>
            <div class="relative">
              <div class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
              </div>
              <input v-model="password" :type="showPass ? 'text' : 'password'" :placeholder="t('login.password')"
                class="w-full pl-10 pr-10 py-3 border border-gray-200 rounded-xl text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"/>
              <button type="button" @click="showPass = !showPass" class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                <svg v-if="!showPass" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
              </button>
            </div>
            <div class="flex items-center justify-between">
              <label class="flex items-center gap-2 cursor-pointer">
                <input v-model="remember" type="checkbox" class="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"/>
                <span class="text-sm text-gray-600">{{ t('login.remember') }}</span>
              </label>
              <button type="button" @click="mode = 'forgot'; forgotStep = 'phone'; forgotError = ''"
                class="text-sm font-medium text-blue-600 hover:underline">{{ t('login.forgot') }}</button>
            </div>
            <p v-if="error" class="text-red-500 text-xs">{{ error }}</p>
            <button type="submit" :disabled="loading"
              class="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white font-semibold rounded-xl transition flex items-center justify-center gap-2 text-sm">
              <svg v-if="loading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 0 1 8-8v8H4z"/></svg>
              {{ loading ? t('login.loggingIn') : t('login.login') }}
            </button>
            <div class="flex items-center gap-3">
              <div class="flex-1 h-px bg-gray-200"/>
              <span class="text-xs text-gray-400">{{ t('login.orContinueWith') }}</span>
              <div class="flex-1 h-px bg-gray-200"/>
            </div>
            <button type="button" @click="mode = 'otp'; otpStep = 'phone'; otpError = ''; otpPhone = ''"
              class="w-full py-3 border border-blue-600 text-blue-600 font-semibold rounded-xl hover:bg-blue-50 transition text-sm flex items-center justify-center gap-2">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><rect x="5" y="2" width="14" height="20" rx="2"/><line x1="12" y1="18" x2="12.01" y2="18"/></svg>
              {{ t('login.loginWithOtp') }}
            </button>
            <p class="text-center text-sm text-gray-500">{{ t('login.newToExobios') }}</p>
            <button type="button" @click="mode = 'signup'; signupError = ''"
              class="w-full py-3 border border-gray-200 text-gray-700 font-semibold rounded-xl hover:bg-gray-50 transition text-sm flex items-center justify-center gap-2">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><line x1="19" y1="8" x2="19" y2="14"/><line x1="22" y1="11" x2="16" y2="11"/></svg>
              {{ t('login.signUp') }}
            </button>
            <p class="text-center text-xs text-gray-400">
              {{ t('login.termsAgree') }}
              <button type="button" @click="showTerms = true; termsTab = 'terms'" class="text-blue-600 hover:underline font-medium">{{ t('login.termsLink') }}</button>
            </p>
            <div class="border-t border-gray-100 pt-4 text-center">
              <button type="button" @click="mode = 'contactUs'; contactError = ''"
                class="text-sm text-gray-500 hover:text-blue-600 transition flex items-center gap-1.5 mx-auto">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                Contact Us / Request Access
              </button>
            </div>
          </form>
        </template>

        <!-- ── OTP LOGIN ── -->
        <template v-else-if="mode === 'otp'">
          <button @click="mode = 'login'; otpStep = 'phone'; otpError = ''" class="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 mb-6">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 5l-7 7 7 7"/></svg>
            {{ t('login.back') }}
          </button>
          <h1 class="text-2xl font-bold text-gray-900 mb-1">{{ t('login.loginWithOtp') }}</h1>

          <!-- Step: Enter phone -->
          <template v-if="otpStep === 'phone'">
            <p class="text-sm text-gray-500 mb-8">{{ t('login.phone') }}</p>
            <div class="space-y-4">
              <div class="relative">
                <div class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><rect x="5" y="2" width="14" height="20" rx="2"/><line x1="12" y1="18" x2="12.01" y2="18"/></svg>
                </div>
                <input v-model="otpPhone" type="tel" :placeholder="t('login.phonePlaceholder')" maxlength="10"
                  class="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"/>
              </div>
              <p v-if="otpError" class="text-red-500 text-xs">{{ otpError }}</p>
              <button @click="sendOtp" :disabled="otpSending"
                class="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white font-semibold rounded-xl transition text-sm flex items-center justify-center gap-2">
                <svg v-if="otpSending" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 0 1 8-8v8H4z"/></svg>
                {{ otpSending ? t('login.sending') : t('login.send') }}
              </button>
            </div>
          </template>

          <!-- Step: Verify OTP -->
          <template v-else>
            <p class="text-sm text-gray-500 mb-1">{{ t('login.otpSent') }} <strong>+91 {{ otpPhone }}</strong></p>
            <p class="text-xs text-gray-400 mb-4">{{ t('login.enterCode') }}</p>
            <p class="text-xs text-blue-700 bg-blue-50 border border-blue-200 rounded-lg px-3 py-2 text-center mb-4">
              Your OTP: <strong class="text-base tracking-widest">{{ generatedOtp }}</strong>
            </p>
            <div class="flex gap-2 sm:gap-3 justify-center mb-4">
              <input v-for="(_, idx) in 6" :key="idx"
                :id="`otp-${idx}`" type="text" inputmode="numeric" maxlength="1" autocomplete="one-time-code"
                @input="handleOtpInput(idx, $event)"
                @keydown="handleOtpKeydown(idx, $event)"
                @paste="handleOtpPaste($event)"
                class="w-10 h-12 text-center border-2 border-gray-200 rounded-lg text-lg font-bold text-gray-800 focus:outline-none focus:border-blue-500 transition"/>
            </div>
            <p v-if="otpError" class="text-red-500 text-xs text-center mb-3">{{ otpError }}</p>
            <button @click="verifyOtp" :disabled="otpLoading"
              class="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white font-semibold rounded-xl transition text-sm flex items-center justify-center gap-2">
              <svg v-if="otpLoading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 0 1 8-8v8H4z"/></svg>
              {{ otpLoading ? t('login.verifying') : t('login.verify') }}
            </button>
            <p class="text-center text-xs text-gray-400 mt-3">
              {{ t('login.didntReceive') }}
              <span v-if="resendCountdown > 0" class="text-gray-400">{{ t('login.resendIn') }} {{ resendCountdown }}s</span>
              <button v-else @click="otpStep = 'phone'; otpError = ''" class="text-blue-600 hover:underline ml-1">{{ t('login.resend') }}</button>
            </p>
          </template>
        </template>

        <!-- ── SIGNUP ── -->
        <template v-else-if="mode === 'signup'">
          <button @click="mode = 'login'" class="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 mb-6">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 5l-7 7 7 7"/></svg>
            {{ t('login.backToLogin') }}
          </button>
          <h1 class="text-2xl font-bold text-gray-900 mb-1">{{ t('login.createAccount') }}</h1>
          <p class="text-sm text-gray-500 mb-6">{{ t('login.registerDesc') }}</p>

          <div v-if="signupSuccess" class="bg-green-50 border border-green-200 text-green-700 rounded-xl px-4 py-3 text-sm text-center mb-4">
            {{ t('login.accountCreated') }}
          </div>

          <form v-else @submit.prevent="handleSignup" class="space-y-3.5">
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1.5">{{ t('login.fullName') }} <span class="text-red-500">*</span></label>
              <input v-model="signup.name" type="text" :placeholder="t('login.fullNamePlaceholder')"
                class="w-full px-3.5 py-3 border border-gray-200 rounded-xl text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"/>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1.5">{{ t('login.phoneNumber') }} <span class="text-red-500">*</span></label>
              <input v-model="signup.phone" type="tel" maxlength="10" :placeholder="t('login.phonePlaceholder')"
                class="w-full px-3.5 py-3 border border-gray-200 rounded-xl text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"/>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1.5">{{ t('login.ashaId') }} <span class="text-red-500">*</span></label>
              <input v-model="signup.ashaId" type="text" :placeholder="t('login.ashaIdPlaceholder')"
                class="w-full px-3.5 py-3 border border-gray-200 rounded-xl text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"/>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1.5">{{ t('login.role') }}</label>
              <select v-model="signup.role"
                class="w-full px-3.5 py-3 border border-gray-200 rounded-xl text-sm text-gray-800 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option>ASHA Worker</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1.5">{{ t('login.password') }} <span class="text-red-500">*</span></label>
              <input v-model="signup.password" :type="signupShowPass ? 'text' : 'password'" :placeholder="t('login.minPassword')"
                class="w-full px-3.5 py-3 border border-gray-200 rounded-xl text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"/>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1.5">{{ t('login.confirmPassword') }} <span class="text-red-500">*</span></label>
              <input v-model="signup.confirm" :type="signupShowPass ? 'text' : 'password'" :placeholder="t('login.confirmPassword')"
                class="w-full px-3.5 py-3 border border-gray-200 rounded-xl text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"/>
            </div>
            <label class="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" v-model="signupShowPass" class="w-4 h-4 rounded border-gray-300 text-blue-600"/>
              <span class="text-xs text-gray-600">{{ t('login.showPassword') }}</span>
            </label>
            <p v-if="signupError" class="text-red-500 text-xs">{{ signupError }}</p>
            <button type="submit" :disabled="loading"
              class="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white font-semibold rounded-xl transition text-sm flex items-center justify-center gap-2">
              <svg v-if="loading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 0 1 8-8v8H4z"/></svg>
              {{ loading ? t('login.creatingAccount') : t('login.createAccount') }}
            </button>
            <p class="text-center text-xs text-gray-400">
              {{ t('login.signupAgree') }}
              <button type="button" @click="showTerms = true; termsTab = 'terms'" class="text-blue-600 hover:underline font-medium">{{ t('login.termsLink') }}</button>
            </p>
          </form>
        </template>

        <!-- ── CONTACT US ── -->
        <template v-else-if="mode === 'contactUs'">
          <button @click="mode = 'login'" class="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 mb-6">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 5l-7 7 7 7"/></svg>
            {{ t('login.backToLogin') }}
          </button>
          <h1 class="text-2xl font-bold text-gray-900 mb-1">Contact Us</h1>
          <p class="text-sm text-gray-500 mb-6">Fill in your details and we'll get back to you.</p>

          <div v-if="contactSuccess" class="bg-green-50 border border-green-200 text-green-700 rounded-xl px-4 py-3 text-sm text-center mb-4">
            Thank you! We'll reach out to you soon.
          </div>

          <form v-else @submit.prevent="submitContact" class="space-y-3.5">
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1.5">Full Name <span class="text-red-500">*</span></label>
              <input v-model="contactForm.name" type="text" placeholder="Your full name"
                class="w-full px-3.5 py-3 border border-gray-200 rounded-xl text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"/>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1.5">Occupation</label>
              <input v-model="contactForm.occupation" type="text" placeholder="e.g. ASHA Worker, Health Official"
                class="w-full px-3.5 py-3 border border-gray-200 rounded-xl text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"/>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1.5">Phone Number <span class="text-red-500">*</span></label>
              <input v-model="contactForm.phone" type="tel" maxlength="10" placeholder="10-digit mobile number"
                class="w-full px-3.5 py-3 border border-gray-200 rounded-xl text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"/>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1.5">ASHA ID / Worker ID</label>
              <input v-model="contactForm.workerId" type="text" placeholder="Your ASHA ID or worker ID"
                class="w-full px-3.5 py-3 border border-gray-200 rounded-xl text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"/>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1.5">Any Other Details</label>
              <textarea v-model="contactForm.other" rows="3" placeholder="Your query, district, sub-center, etc."
                class="w-full px-3.5 py-3 border border-gray-200 rounded-xl text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"/>
            </div>
            <p v-if="contactError" class="text-red-500 text-xs">{{ contactError }}</p>
            <button type="submit" :disabled="loading"
              class="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white font-semibold rounded-xl transition flex items-center justify-center gap-2 text-sm">
              <svg v-if="loading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 0 1 8-8v8H4z"/></svg>
              {{ loading ? 'Sending...' : 'Send Message' }}
            </button>
          </form>
        </template>

        <!-- ── FORGOT PASSWORD ── -->
        <template v-else-if="mode === 'forgot'">
          <button @click="mode = 'login'" class="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 mb-6">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 5l-7 7 7 7"/></svg>
            {{ t('login.backToLogin') }}
          </button>
          <h1 class="text-2xl font-bold text-gray-900 mb-1">{{ t('login.forgotTitle') }}</h1>

          <div v-if="forgotSuccess" class="bg-green-50 border border-green-200 text-green-700 rounded-xl px-4 py-3 text-sm text-center mt-4">
            {{ t('login.passwordResetSuccess') }}
          </div>

          <!-- Step 1: Phone number -->
          <template v-else-if="forgotStep === 'phone'">
            <p class="text-sm text-gray-500 mb-8">{{ t('login.forgotDesc') }}</p>
            <div class="space-y-4">
              <input v-model="forgotPhone" type="tel" maxlength="10" :placeholder="t('login.phonePlaceholder')"
                class="w-full px-3.5 py-3 border border-gray-200 rounded-xl text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"/>
              <p v-if="forgotError" class="text-red-500 text-xs">{{ forgotError }}</p>
              <button @click="sendForgotOtp" :disabled="loading"
                class="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white font-semibold rounded-xl transition text-sm flex items-center justify-center gap-2">
                <svg v-if="loading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 0 1 8-8v8H4z"/></svg>
                {{ loading ? t('login.sending') : t('login.send') }}
              </button>
            </div>
          </template>

          <!-- Step 2: Verify OTP -->
          <template v-else-if="forgotStep === 'otp'">
            <p class="text-sm text-gray-500 mb-2">{{ t('login.otpSent') }} <strong>+91 {{ forgotPhone }}</strong></p>
            <p class="text-xs text-blue-700 bg-blue-50 border border-blue-200 rounded-lg px-3 py-2 text-center mb-4">
              Your OTP: <strong class="text-base tracking-widest">{{ forgotGeneratedOtp }}</strong>
            </p>
            <div class="flex gap-2 sm:gap-3 justify-center mb-4">
              <input v-for="(_, idx) in forgotOtp" :key="idx"
                :id="`fotp-${idx}`" type="text" inputmode="numeric" maxlength="1"
                @input="handleForgotOtpInput(idx, $event)"
                @keydown="(e) => { if(e.key==='Backspace'){ e.preventDefault(); if(forgotOtp[idx]){ forgotOtp[idx]=''; e.target.value='' } else if(idx>0){ const p=document.getElementById('fotp-'+(idx-1)); if(p){p.focus();p.value='';forgotOtp[idx-1]=''} } } }"
                class="w-10 h-12 text-center border-2 border-gray-200 rounded-lg text-lg font-bold text-gray-800 focus:outline-none focus:border-blue-500 transition"/>
            </div>
            <p v-if="forgotError" class="text-red-500 text-xs text-center mb-3">{{ forgotError }}</p>
            <button @click="verifyForgotOtp" class="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl transition text-sm">{{ t('login.verify') }}</button>
          </template>

          <!-- Step 3: New password -->
          <template v-else>
            <p class="text-sm text-gray-500 mb-8">{{ t('login.setNewPassword') }}</p>
            <div class="space-y-4">
              <input v-model="forgotNewPass" type="password" :placeholder="t('login.newPassword')"
                class="w-full px-3.5 py-3 border border-gray-200 rounded-xl text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"/>
              <input v-model="forgotConfirm" type="password" :placeholder="t('login.confirmNewPassword')"
                class="w-full px-3.5 py-3 border border-gray-200 rounded-xl text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"/>
              <p v-if="forgotError" class="text-red-500 text-xs">{{ forgotError }}</p>
              <button @click="resetPassword" :disabled="loading"
                class="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white font-semibold rounded-xl transition text-sm flex items-center justify-center gap-2">
                <svg v-if="loading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 0 1 8-8v8H4z"/></svg>
                {{ loading ? t('login.resetting') : t('login.resetPassword') }}
              </button>
            </div>
          </template>
        </template>
      </div>
    </div>

    <!-- Terms & Privacy Modal -->
    <teleport to="body">
      <div v-if="showTerms" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" @click.self="showTerms = false">
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[80vh] flex flex-col">
          <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
            <div class="flex gap-4">
              <button :class="['text-sm font-semibold pb-1 transition', termsTab === 'terms' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700']" @click="termsTab = 'terms'">Terms of Service</button>
              <button :class="['text-sm font-semibold pb-1 transition', termsTab === 'privacy' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700']" @click="termsTab = 'privacy'">Privacy Policy</button>
            </div>
            <button @click="showTerms = false" class="text-gray-400 hover:text-gray-600 p-1">
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18M6 6l12 12"/></svg>
            </button>
          </div>
          <div class="flex-1 overflow-y-auto px-6 py-5 text-sm text-gray-600 space-y-4 leading-relaxed">
            <template v-if="termsTab === 'terms'">
              <h3 class="font-bold text-gray-800 text-base">Terms of Service</h3>
              <p>Welcome to Exobios. By accessing or using our platform, you agree to be bound by these Terms of Service.</p>
              <h4 class="font-semibold text-gray-700">1. Use of Platform</h4>
              <p>Exobios is intended solely for use by registered healthcare workers including ASHA workers, ANMs, and other certified health enablers. Unauthorized access is strictly prohibited.</p>
              <h4 class="font-semibold text-gray-700">2. AI-Generated Recommendations</h4>
              <p>All clinical suggestions generated by the AI are intended to assist, not replace, professional medical judgment. Final decisions must be made by qualified healthcare professionals.</p>
              <h4 class="font-semibold text-gray-700">3. Patient Data</h4>
              <p>All patient data is confidential. Users are responsible for maintaining the privacy and security of patient information.</p>
              <h4 class="font-semibold text-gray-700">4. Account Responsibility</h4>
              <p>You are responsible for all activities under your account. Do not share your login credentials.</p>
            </template>
            <template v-else>
              <h3 class="font-bold text-gray-800 text-base">Privacy Policy</h3>
              <p>Your privacy is important to us. This policy explains how Exobios collects, uses, and protects your data.</p>
              <h4 class="font-semibold text-gray-700">1. Data Collection</h4>
              <p>We collect information necessary to provide healthcare assessment services, including user registration details and patient health information.</p>
              <h4 class="font-semibold text-gray-700">2. Data Use</h4>
              <p>Collected data is used exclusively to provide clinical decision support and improve patient care. We do not sell data to third parties.</p>
              <h4 class="font-semibold text-gray-700">3. Data Security</h4>
              <p>All data is encrypted in transit and at rest using industry-standard security measures.</p>
              <h4 class="font-semibold text-gray-700">4. Contact</h4>
              <p>For privacy concerns, contact us at privacy@exobios.health</p>
            </template>
          </div>
          <div class="px-6 py-4 border-t border-gray-100 flex justify-end">
            <button @click="showTerms = false"
              class="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-xl transition">
              {{ t('login.iUnderstand') }}
            </button>
          </div>
        </div>
      </div>
    </teleport>
  </div>
</template>
