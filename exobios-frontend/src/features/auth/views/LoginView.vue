<script setup>
import { ref, reactive, nextTick, watch, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore, PARAMEDIC_ROLES, DOCTOR_ROLES } from '@/features/auth/stores/auth'
import RadioGroup from '@/shared/components/forms/RadioGroup.vue'
import AuthTextField from '@/features/auth/components/AuthTextField.vue'
import AuthButton from '@/features/auth/components/AuthButton.vue'
import AuthBrandPanel from '@/features/auth/components/AuthBrandPanel.vue'
import exobiosLogo from '@/assets/brand/exobios-logo-dark.png'
import { useI18n } from '@/i18n'

// 'ASHA Worker' is the legacy alias kept for backward compatibility (see auth store) —
// hidden here so new signups pick the current role names.
const SIGNUP_ROLE_OPTIONS = [...PARAMEDIC_ROLES.filter(r => r !== 'ASHA Worker'), ...DOCTOR_ROLES]

const router = useRouter()
const auth   = useAuthStore()
const { t }  = useI18n()

// Modes: login | signup | otp | forgot
const mode = ref('login')

// ─── Login ────────────────────────────────────────────────────────────────────
const loginId  = ref('')
const password = ref('')
const remember = ref(false)
const loading  = ref(false)
const error    = ref('')

async function handleLogin() {
  if (!loginId.value || !password.value) { error.value = 'Please enter Login ID and Password.'; return }
  loading.value = true; error.value = ''
  try {
    await new Promise(r => setTimeout(r, 600))
    const found = auth.findUser(loginId.value, password.value)
    if (!found) { error.value = t('login.authError'); return }
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

onUnmounted(() => {
  if (resendTimer) clearInterval(resendTimer)
})

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
const signup        = reactive({ name: '', phone: '', ashaId: '', role: 'ASHA', password: '', confirm: '' })

// Same dynamic-label pattern as the Contact Us form's workerIdLabel — the ID field
// should ask for the ID that matches whichever role was actually selected.
const signupIdLabel = computed(() => {
  if (signup.role === 'MBBS Doctor') return 'MBBS Doctor Registration ID'
  return signup.role ? `${signup.role} ID` : 'ASHA/ANM/CHO/LHV ID or MBBS Doctor ID'
})
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
const CONTACT_ROLE_OPTIONS = ['ASHA', 'ANM', 'CHO', 'LHV', 'Health Assistant', 'MBBS Doctor']
const contactForm    = reactive({ name: '', occupation: '', phone: '', role: '', workerId: '', other: '' })
const contactSuccess = ref(false)
const contactError   = ref('')

// ID field label switches with the selected role — MBBS Doctor gets a registration-ID
// label, paramedic roles (ASHA/ANM/CHO/LHV/Health Assistant) get "<Role> ID".
const workerIdLabel = computed(() => {
  if (contactForm.role === 'MBBS Doctor') return 'MBBS Doctor Registration ID'
  if (contactForm.role) return `${contactForm.role} ID`
  return 'ASHA/ANM/CHO/LHV ID or MBBS Doctor ID'
})

async function submitContact() {
  if (!contactForm.name || !contactForm.phone) { contactError.value = 'Name and phone number are required.'; return }
  contactError.value = ''
  loading.value = true
  await new Promise(r => setTimeout(r, 700))
  loading.value = false
  contactSuccess.value = true
  Object.assign(contactForm, { name: '', occupation: '', phone: '', role: '', workerId: '', other: '' })
  setTimeout(() => { contactSuccess.value = false; mode.value = 'login' }, 2500)
}
</script>

<template>
  <div class="flex min-h-screen bg-white">
    <!-- Left branding panel (desktop only) -->
    <AuthBrandPanel />

    <!-- Right: auth forms -->
    <div class="flex flex-1 flex-col items-center justify-start overflow-y-auto bg-white px-6 py-10 sm:px-10 lg:justify-center lg:py-12">
      <div class="w-full max-w-[420px]">

        <!-- Compact brand header (mobile / tablet only) -->
        <div class="mb-8 flex flex-col items-center gap-1 lg:hidden">
          <img :src="exobiosLogo" alt="Exobios" class="h-8 w-auto object-contain" />
        </div>

        <!-- ── LOGIN ── -->
        <template v-if="mode === 'login'">
          <h1 class="text-[26px] font-bold tracking-tight text-slate-900">{{ t('login.title') }}</h1>
          <p class="mt-1.5 text-sm text-slate-500">{{ t('login.subtitle') }}</p>

          <form @submit.prevent="handleLogin" class="mt-8 space-y-5" novalidate>
            <AuthTextField
              id="login-id" v-model="loginId" :label="t('login.loginId')"
              :placeholder="t('login.loginIdPlaceholder')" autocomplete="username" required
            >
              <template #icon>
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
              </template>
            </AuthTextField>

            <AuthTextField
              id="login-password" v-model="password" revealable
              :label="t('login.password')" :placeholder="t('login.passwordPlaceholder')" autocomplete="current-password" required
            >
              <template #icon>
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
              </template>
            </AuthTextField>

            <div class="flex items-center justify-between">
              <label class="flex cursor-pointer select-none items-center gap-2">
                <input v-model="remember" type="checkbox" class="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500/40"/>
                <span class="text-sm text-slate-600">{{ t('login.remember') }}</span>
              </label>
              <button type="button" @click="mode = 'forgot'; forgotStep = 'phone'; forgotError = ''"
                class="text-sm font-medium text-blue-600 hover:text-blue-700 hover:underline">{{ t('login.forgot') }}</button>
            </div>

            <div v-if="error" role="alert" class="flex items-start gap-2 rounded-xl border border-red-100 bg-red-50 px-3.5 py-2.5 text-sm text-red-600">
              <svg class="mt-0.5 h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="13"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
              <span>{{ error }}</span>
            </div>

            <AuthButton type="submit" :loading="loading">
              {{ loading ? t('login.loggingIn') : t('login.login') }}
            </AuthButton>

            <div class="flex items-center gap-3 pt-1">
              <div class="h-px flex-1 bg-slate-200"/>
              <span class="text-xs font-medium uppercase tracking-wide text-slate-400">{{ t('login.orContinueWith') }}</span>
              <div class="h-px flex-1 bg-slate-200"/>
            </div>

            <AuthButton type="button" variant="secondary" @click="mode = 'otp'; otpStep = 'phone'; otpError = ''; otpPhone = ''">
              <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><rect x="5" y="2" width="14" height="20" rx="2"/><line x1="12" y1="18" x2="12.01" y2="18"/></svg>
              {{ t('login.loginWithOtp') }}
            </AuthButton>

            <p class="pt-2 text-center text-sm text-slate-500">
              {{ t('login.newToExobios') }}
              <button type="button" @click="mode = 'signup'; signupError = ''" class="font-semibold text-blue-600 hover:underline">{{ t('login.signUp') }}</button>
            </p>

            <p class="text-center text-xs leading-relaxed text-slate-400">
              {{ t('login.termsAgree') }}
              <button type="button" @click="showTerms = true; termsTab = 'terms'" class="font-medium text-blue-600 hover:underline">{{ t('login.termsLink') }}</button>
            </p>

            <div class="border-t border-slate-100 pt-5 text-center">
              <button type="button" @click="mode = 'contactUs'; contactError = ''"
                class="mx-auto flex items-center gap-1.5 text-sm text-slate-500 transition hover:text-blue-600">
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                {{ t('login.requestAccess') }}
              </button>
            </div>
          </form>
        </template>

        <!-- ── OTP LOGIN ── -->
        <template v-else-if="mode === 'otp'">
          <button @click="mode = 'login'; otpStep = 'phone'; otpError = ''" class="mb-6 flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700">
            <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 5l-7 7 7 7"/></svg>
            {{ t('login.back') }}
          </button>
          <h1 class="text-[26px] font-bold tracking-tight text-slate-900">{{ t('login.loginWithOtp') }}</h1>

          <!-- Step: Enter phone -->
          <template v-if="otpStep === 'phone'">
            <p class="mt-1.5 mb-8 text-sm text-slate-500">{{ t('login.phone') }}</p>
            <div class="space-y-5">
              <AuthTextField id="otp-phone" v-model="otpPhone" type="tel" inputmode="numeric" maxlength="10"
                :placeholder="t('login.phonePlaceholder')" autocomplete="tel">
                <template #icon>
                  <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><rect x="5" y="2" width="14" height="20" rx="2"/><line x1="12" y1="18" x2="12.01" y2="18"/></svg>
                </template>
              </AuthTextField>
              <p v-if="otpError" class="text-xs text-red-500">{{ otpError }}</p>
              <AuthButton @click="sendOtp" :loading="otpSending">
                {{ otpSending ? t('login.sending') : t('login.send') }}
              </AuthButton>
            </div>
          </template>

          <!-- Step: Verify OTP -->
          <template v-else>
            <p class="mt-1.5 mb-1 text-sm text-slate-500">{{ t('login.otpSent') }} <strong class="text-slate-700">+91 {{ otpPhone }}</strong></p>
            <p class="mb-4 text-xs text-slate-400">{{ t('login.enterCode') }}</p>
            <p class="mb-4 rounded-lg border border-blue-100 bg-blue-50 px-3 py-2 text-center text-xs text-blue-700">
              Your OTP: <strong class="text-base tracking-widest">{{ generatedOtp }}</strong>
            </p>
            <div class="mb-4 flex justify-center gap-2 sm:gap-3">
              <input v-for="(_, idx) in 6" :key="idx"
                :id="`otp-${idx}`" type="text" inputmode="numeric" maxlength="1" autocomplete="one-time-code"
                @input="handleOtpInput(idx, $event)"
                @keydown="handleOtpKeydown(idx, $event)"
                @paste="handleOtpPaste($event)"
                class="h-12 w-10 rounded-lg border-2 border-slate-200 text-center text-lg font-bold text-slate-800 transition focus:border-blue-500 focus:outline-none"/>
            </div>
            <p v-if="otpError" class="mb-3 text-center text-xs text-red-500">{{ otpError }}</p>
            <AuthButton @click="verifyOtp" :loading="otpLoading">
              {{ otpLoading ? t('login.verifying') : t('login.verify') }}
            </AuthButton>
            <p class="mt-3 text-center text-xs text-slate-400">
              {{ t('login.didntReceive') }}
              <span v-if="resendCountdown > 0" class="text-slate-400">{{ t('login.resendIn') }} {{ resendCountdown }}s</span>
              <button v-else @click="otpStep = 'phone'; otpError = ''" class="ml-1 text-blue-600 hover:underline">{{ t('login.resend') }}</button>
            </p>
          </template>
        </template>

        <!-- ── SIGNUP ── -->
        <template v-else-if="mode === 'signup'">
          <button @click="mode = 'login'" class="mb-6 flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700">
            <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 5l-7 7 7 7"/></svg>
            {{ t('login.backToLogin') }}
          </button>
          <h1 class="text-[26px] font-bold tracking-tight text-slate-900">{{ t('login.createAccount') }}</h1>
          <p class="mt-1.5 mb-6 text-sm text-slate-500">{{ t('login.registerDesc') }}</p>

          <div v-if="signupSuccess" class="mb-4 rounded-xl border border-green-200 bg-green-50 px-4 py-3 text-center text-sm text-green-700">
            {{ t('login.accountCreated') }}
          </div>

          <form v-else @submit.prevent="handleSignup" class="space-y-4">
            <AuthTextField id="signup-name" v-model="signup.name" :label="t('login.fullName')" required
              :placeholder="t('login.fullNamePlaceholder')" autocomplete="name"/>
            <AuthTextField id="signup-phone" v-model="signup.phone" type="tel" inputmode="numeric" maxlength="10" required
              :label="t('login.phoneNumber')" :placeholder="t('login.phonePlaceholder')" autocomplete="tel"/>
            <div>
              <label class="mb-1.5 block text-xs font-medium text-slate-600">{{ t('login.role') }}</label>
              <select v-model="signup.role"
                class="h-12 w-full rounded-xl border border-slate-200 bg-white px-4 text-sm text-slate-800 transition hover:border-slate-300 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/30">
                <option v-for="r in SIGNUP_ROLE_OPTIONS" :key="r" :value="r">{{ r }}</option>
              </select>
            </div>
            <AuthTextField id="signup-worker-id" v-model="signup.ashaId" :label="signupIdLabel" required
              :placeholder="`Your ${signupIdLabel}`"/>
            <AuthTextField id="signup-password" v-model="signup.password" :type="signupShowPass ? 'text' : 'password'" required
              :label="t('login.password')" :placeholder="t('login.minPassword')" autocomplete="new-password"/>
            <AuthTextField id="signup-confirm" v-model="signup.confirm" :type="signupShowPass ? 'text' : 'password'" required
              :label="t('login.confirmPassword')" :placeholder="t('login.confirmPassword')" autocomplete="new-password"/>
            <label class="flex cursor-pointer items-center gap-2">
              <input type="checkbox" v-model="signupShowPass" class="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500/40"/>
              <span class="text-xs text-slate-600">{{ t('login.showPassword') }}</span>
            </label>
            <p v-if="signupError" class="text-xs text-red-500">{{ signupError }}</p>
            <AuthButton type="submit" :loading="loading">
              {{ loading ? t('login.creatingAccount') : t('login.createAccount') }}
            </AuthButton>
            <p class="text-center text-xs leading-relaxed text-slate-400">
              {{ t('login.signupAgree') }}
              <button type="button" @click="showTerms = true; termsTab = 'terms'" class="font-medium text-blue-600 hover:underline">{{ t('login.termsLink') }}</button>
            </p>
          </form>
        </template>

        <!-- ── CONTACT US ── -->
        <template v-else-if="mode === 'contactUs'">
          <button @click="mode = 'login'" class="mb-6 flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700">
            <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 5l-7 7 7 7"/></svg>
            {{ t('login.backToLogin') }}
          </button>
          <h1 class="text-[26px] font-bold tracking-tight text-slate-900">Contact Us</h1>
          <p class="mt-1.5 mb-6 text-sm text-slate-500">Fill in your details and we'll get back to you.</p>

          <div v-if="contactSuccess" class="mb-4 rounded-xl border border-green-200 bg-green-50 px-4 py-3 text-center text-sm text-green-700">
            Thank you! We'll reach out to you soon.
          </div>

          <form v-else @submit.prevent="submitContact" class="space-y-4">
            <AuthTextField id="contact-name" v-model="contactForm.name" label="Full Name" required
              placeholder="Your full name" autocomplete="name"/>
            <AuthTextField id="contact-occupation" v-model="contactForm.occupation" label="Occupation"
              placeholder="e.g. ASHA Worker, Health Official"/>
            <AuthTextField id="contact-phone" v-model="contactForm.phone" type="tel" inputmode="numeric" maxlength="10" required
              label="Phone Number" placeholder="10-digit mobile number" autocomplete="tel"/>
            <div>
              <label class="mb-1.5 block text-xs font-medium text-slate-600">Role</label>
              <RadioGroup v-model="contactForm.role" :options="CONTACT_ROLE_OPTIONS" color="blue" columns="flex flex-wrap gap-2"/>
            </div>
            <AuthTextField id="contact-worker-id" v-model="contactForm.workerId" :label="workerIdLabel"
              :placeholder="`Your ${workerIdLabel}`"/>
            <div>
              <label class="mb-1.5 block text-xs font-medium text-slate-600">Any Other Details</label>
              <textarea v-model="contactForm.other" rows="3" placeholder="Your query, district, sub-center, etc."
                class="w-full resize-none rounded-xl border border-slate-200 px-4 py-3 text-sm text-slate-800 placeholder-slate-400 transition hover:border-slate-300 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/30"/>
            </div>
            <p v-if="contactError" class="text-xs text-red-500">{{ contactError }}</p>
            <AuthButton type="submit" :loading="loading">
              {{ loading ? 'Sending...' : 'Send Message' }}
            </AuthButton>
          </form>
        </template>

        <!-- ── FORGOT PASSWORD ── -->
        <template v-else-if="mode === 'forgot'">
          <button @click="mode = 'login'" class="mb-6 flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700">
            <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 5l-7 7 7 7"/></svg>
            {{ t('login.backToLogin') }}
          </button>
          <h1 class="text-[26px] font-bold tracking-tight text-slate-900">{{ t('login.forgotTitle') }}</h1>

          <div v-if="forgotSuccess" class="mt-4 rounded-xl border border-green-200 bg-green-50 px-4 py-3 text-center text-sm text-green-700">
            {{ t('login.passwordResetSuccess') }}
          </div>

          <!-- Step 1: Phone number -->
          <template v-else-if="forgotStep === 'phone'">
            <p class="mt-1.5 mb-8 text-sm text-slate-500">{{ t('login.forgotDesc') }}</p>
            <div class="space-y-5">
              <AuthTextField id="forgot-phone" v-model="forgotPhone" type="tel" inputmode="numeric" maxlength="10"
                :placeholder="t('login.phonePlaceholder')" autocomplete="tel"/>
              <p v-if="forgotError" class="text-xs text-red-500">{{ forgotError }}</p>
              <AuthButton @click="sendForgotOtp" :loading="loading">
                {{ loading ? t('login.sending') : t('login.send') }}
              </AuthButton>
            </div>
          </template>

          <!-- Step 2: Verify OTP -->
          <template v-else-if="forgotStep === 'otp'">
            <p class="mt-1.5 mb-2 text-sm text-slate-500">{{ t('login.otpSent') }} <strong class="text-slate-700">+91 {{ forgotPhone }}</strong></p>
            <p class="mb-4 rounded-lg border border-blue-100 bg-blue-50 px-3 py-2 text-center text-xs text-blue-700">
              Your OTP: <strong class="text-base tracking-widest">{{ forgotGeneratedOtp }}</strong>
            </p>
            <div class="mb-4 flex justify-center gap-2 sm:gap-3">
              <input v-for="(_, idx) in forgotOtp" :key="idx"
                :id="`fotp-${idx}`" type="text" inputmode="numeric" maxlength="1"
                @input="handleForgotOtpInput(idx, $event)"
                @keydown="(e) => { if(e.key==='Backspace'){ e.preventDefault(); if(forgotOtp[idx]){ forgotOtp[idx]=''; e.target.value='' } else if(idx>0){ const p=document.getElementById('fotp-'+(idx-1)); if(p){p.focus();p.value='';forgotOtp[idx-1]=''} } } }"
                class="h-12 w-10 rounded-lg border-2 border-slate-200 text-center text-lg font-bold text-slate-800 transition focus:border-blue-500 focus:outline-none"/>
            </div>
            <p v-if="forgotError" class="mb-3 text-center text-xs text-red-500">{{ forgotError }}</p>
            <AuthButton @click="verifyForgotOtp">{{ t('login.verify') }}</AuthButton>
          </template>

          <!-- Step 3: New password -->
          <template v-else>
            <p class="mt-1.5 mb-8 text-sm text-slate-500">{{ t('login.setNewPassword') }}</p>
            <div class="space-y-5">
              <AuthTextField id="forgot-new-password" v-model="forgotNewPass" revealable
                :label="t('login.newPassword')" :placeholder="t('login.newPassword')" autocomplete="new-password"/>
              <AuthTextField id="forgot-confirm-password" v-model="forgotConfirm" revealable
                :label="t('login.confirmNewPassword')" :placeholder="t('login.confirmNewPassword')" autocomplete="new-password"/>
              <p v-if="forgotError" class="text-xs text-red-500">{{ forgotError }}</p>
              <AuthButton @click="resetPassword" :loading="loading">
                {{ loading ? t('login.resetting') : t('login.resetPassword') }}
              </AuthButton>
            </div>
          </template>
        </template>
      </div>
    </div>

    <!-- Terms & Privacy Modal -->
    <teleport to="body">
      <div v-if="showTerms" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" @click.self="showTerms = false">
        <div class="flex max-h-[80vh] w-full max-w-lg flex-col rounded-2xl bg-white shadow-2xl">
          <div class="flex items-center justify-between border-b border-slate-100 px-6 py-4">
            <div class="flex gap-4">
              <button :class="['pb-1 text-sm font-semibold transition', termsTab === 'terms' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-slate-500 hover:text-slate-700']" @click="termsTab = 'terms'">Terms of Service</button>
              <button :class="['pb-1 text-sm font-semibold transition', termsTab === 'privacy' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-slate-500 hover:text-slate-700']" @click="termsTab = 'privacy'">Privacy Policy</button>
            </div>
            <button @click="showTerms = false" class="p-1 text-slate-400 hover:text-slate-600" aria-label="Close">
              <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18M6 6l12 12"/></svg>
            </button>
          </div>
          <div class="flex-1 space-y-4 overflow-y-auto px-6 py-5 text-sm leading-relaxed text-slate-600">
            <template v-if="termsTab === 'terms'">
              <h3 class="text-base font-bold text-slate-800">Terms of Service</h3>
              <p>Welcome to Exobios. By accessing or using our platform, you agree to be bound by these Terms of Service.</p>
              <h4 class="font-semibold text-slate-700">1. Use of Platform</h4>
              <p>Exobios is intended solely for use by registered healthcare workers including ASHA workers, ANMs, and other certified health enablers. Unauthorized access is strictly prohibited.</p>
              <h4 class="font-semibold text-slate-700">2. AI-Generated Recommendations</h4>
              <p>All clinical suggestions generated by the AI are intended to assist, not replace, professional medical judgment. Final decisions must be made by qualified healthcare professionals.</p>
              <h4 class="font-semibold text-slate-700">3. Patient Data</h4>
              <p>All patient data is confidential. Users are responsible for maintaining the privacy and security of patient information.</p>
              <h4 class="font-semibold text-slate-700">4. Account Responsibility</h4>
              <p>You are responsible for all activities under your account. Do not share your login credentials.</p>
            </template>
            <template v-else>
              <h3 class="text-base font-bold text-slate-800">Privacy Policy</h3>
              <p>Your privacy is important to us. This policy explains how Exobios collects, uses, and protects your data.</p>
              <h4 class="font-semibold text-slate-700">1. Data Collection</h4>
              <p>We collect information necessary to provide healthcare assessment services, including user registration details and patient health information.</p>
              <h4 class="font-semibold text-slate-700">2. Data Use</h4>
              <p>Collected data is used exclusively to provide clinical decision support and improve patient care. We do not sell data to third parties.</p>
              <h4 class="font-semibold text-slate-700">3. Data Security</h4>
              <p>All data is encrypted in transit and at rest using industry-standard security measures.</p>
              <h4 class="font-semibold text-slate-700">4. Contact</h4>
              <p>For privacy concerns, contact us at privacy@exobios.health</p>
            </template>
          </div>
          <div class="flex justify-end border-t border-slate-100 px-6 py-4">
            <button @click="showTerms = false"
              class="rounded-xl bg-blue-600 px-6 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700">
              {{ t('login.iUnderstand') }}
            </button>
          </div>
        </div>
      </div>
    </teleport>
  </div>
</template>
