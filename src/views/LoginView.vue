<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth   = useAuthStore()

const loginId  = ref('')
const password = ref('')
const showPass = ref(false)
const remember = ref(false)
const loading  = ref(false)
const error    = ref('')

async function handleLogin() {
  if (!loginId.value || !password.value) { error.value = 'Please enter Login ID and Password.'; return }
  loading.value = true
  error.value = ''
  await new Promise(r => setTimeout(r, 600))
  auth.login({ loginId: loginId.value, password: password.value })
  router.push('/dashboard')
  loading.value = false
}
</script>

<template>
  <div class="min-h-screen flex">
    <!-- Left branding panel -->
    <div class="hidden lg:flex lg:w-[45%] flex-col items-center justify-center relative overflow-hidden"
         style="background: linear-gradient(160deg, #0a1628 0%, #0f1b35 50%, #0a1628 100%)">
      <!-- Wave bg -->
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
        <!-- Logo -->
        <div class="flex items-center justify-center gap-3 mb-10">
          <div class="w-12 h-12 rounded-xl bg-blue-500 flex items-center justify-center">
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L2 7l10 5 10-5-10-5z" stroke="white" stroke-width="2" stroke-linejoin="round"/>
              <path d="M2 17l10 5 10-5" stroke="white" stroke-width="2" stroke-linejoin="round"/>
              <path d="M2 12l10 5 10-5" stroke="white" stroke-width="2" stroke-linejoin="round"/>
            </svg>
          </div>
          <span class="text-white text-3xl font-bold">Exobios</span>
        </div>

        <h2 class="text-white text-4xl font-bold leading-tight mb-4">
          AI Assisted<br>Healthcare Platform
        </h2>
        <div class="w-12 h-1 bg-cyan-400 rounded mx-auto mb-6"></div>
        <p class="text-slate-300 text-base leading-relaxed">
          Smart tools for faster triage,<br>better decisions, and improved care.
        </p>

        <!-- Features -->
        <div class="flex justify-center gap-10 mt-12">
          <div class="flex flex-col items-center gap-2">
            <div class="w-12 h-12 rounded-full border border-cyan-500/30 flex items-center justify-center">
              <svg class="w-6 h-6 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/>
              </svg>
            </div>
            <span class="text-slate-300 text-xs">AI Powered</span>
          </div>
          <div class="flex flex-col items-center gap-2">
            <div class="w-12 h-12 rounded-full border border-cyan-500/30 flex items-center justify-center">
              <svg class="w-6 h-6 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
              </svg>
            </div>
            <span class="text-slate-300 text-xs">Fast Triage</span>
          </div>
          <div class="flex flex-col items-center gap-2">
            <div class="w-12 h-12 rounded-full border border-cyan-500/30 flex items-center justify-center">
              <svg class="w-6 h-6 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
              </svg>
            </div>
            <span class="text-slate-300 text-xs">Better Care</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Right login form -->
    <div class="flex-1 flex items-center justify-center bg-white px-8">
      <div class="w-full max-w-sm">
        <h1 class="text-2xl font-bold text-gray-900 mb-1">Welcome Back</h1>
        <p class="text-sm text-gray-500 mb-8">Access your account</p>

        <form @submit.prevent="handleLogin" class="space-y-4">
          <!-- Login ID -->
          <div class="relative">
            <div class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
              </svg>
            </div>
            <input
              v-model="loginId"
              type="text"
              placeholder="Login ID"
              class="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
            />
          </div>

          <!-- Password -->
          <div class="relative">
            <div class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
              </svg>
            </div>
            <input
              v-model="password"
              :type="showPass ? 'text' : 'password'"
              placeholder="Password"
              class="w-full pl-10 pr-10 py-3 border border-gray-200 rounded-xl text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
            />
            <button type="button" @click="showPass = !showPass"
              class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
              <svg v-if="!showPass" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
              </svg>
              <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                <line x1="1" y1="1" x2="23" y2="23"/>
              </svg>
            </button>
          </div>

          <!-- Remember + Forgot -->
          <div class="flex items-center justify-between">
            <label class="flex items-center gap-2 cursor-pointer">
              <input v-model="remember" type="checkbox" class="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"/>
              <span class="text-sm text-gray-600">Remember me</span>
            </label>
            <a href="#" class="text-sm font-medium text-blue-600 hover:underline">Forgot Password?</a>
          </div>

          <!-- Error -->
          <p v-if="error" class="text-red-500 text-xs">{{ error }}</p>

          <!-- Login btn -->
          <button type="submit"
            class="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl transition flex items-center justify-center gap-2 text-sm"
            :disabled="loading">
            <svg v-if="loading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 0 1 8-8v8H4z"/>
            </svg>
            <span>{{ loading ? 'Logging in…' : 'Login' }}</span>
          </button>

          <!-- Divider -->
          <div class="flex items-center gap-3">
            <div class="flex-1 h-px bg-gray-200"></div>
            <span class="text-xs text-gray-400">or continue with</span>
            <div class="flex-1 h-px bg-gray-200"></div>
          </div>

          <!-- OTP -->
          <button type="button"
            class="w-full py-3 border border-blue-600 text-blue-600 font-semibold rounded-xl hover:bg-blue-50 transition text-sm flex items-center justify-center gap-2">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
              <rect x="5" y="2" width="14" height="20" rx="2" ry="2"/><line x1="12" y1="18" x2="12.01" y2="18"/>
            </svg>
            Login with OTP
          </button>

          <!-- Sign up -->
          <p class="text-center text-sm text-gray-500">
            New to Exobios?
          </p>
          <button type="button"
            class="w-full py-3 border border-gray-200 text-gray-700 font-semibold rounded-xl hover:bg-gray-50 transition text-sm flex items-center justify-center gap-2">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
              <line x1="19" y1="8" x2="19" y2="14"/><line x1="22" y1="11" x2="16" y2="11"/>
            </svg>
            Sign Up
          </button>

          <p class="text-center text-xs text-gray-400">
            By continuing, you agree to our
            <a href="#" class="text-blue-600 hover:underline font-medium">Terms &amp; Privacy Policy</a>
          </p>
        </form>
      </div>
    </div>
  </div>
</template>
