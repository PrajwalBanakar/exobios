<script setup>
import { computed, ref, watch, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/features/auth/stores/auth'

const auth   = useAuthStore()
const router = useRouter()

// Countdown for the warning modal
const countdown = ref(300) // 5 minutes
let   timer     = null

watch(() => auth.sessionNearExpiry, (near) => {
  if (near) {
    countdown.value = 300
    timer = setInterval(() => {
      countdown.value--
      if (countdown.value <= 0) clearInterval(timer)
    }, 1000)
  } else {
    clearInterval(timer)
  }
}, { immediate: true })

onUnmounted(() => clearInterval(timer))

const mm = computed(() => String(Math.floor(countdown.value / 60)).padStart(2, '0'))
const ss = computed(() => String(countdown.value % 60).padStart(2, '0'))

function stayLoggedIn() {
  auth.extendSession()
}

function logoutNow() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <!-- Session near-expiry warning -->
  <teleport to="body">
    <transition enter-active-class="transition-all duration-300" enter-from-class="opacity-0" leave-active-class="transition-all duration-200" leave-to-class="opacity-0">
      <div v-if="auth.sessionNearExpiry" class="fixed inset-0 bg-black/50 z-[100] flex items-center justify-center p-4">
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-sm p-7 text-center">
          <div class="w-16 h-16 rounded-full bg-amber-100 flex items-center justify-center mx-auto mb-4">
            <svg class="w-8 h-8 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
          </div>
          <h3 class="font-bold text-slate-900 text-lg mb-1">Session Expiring Soon</h3>
          <p class="text-sm text-slate-500 mb-4">
            Your session will expire in <span class="font-bold text-amber-600">{{ mm }}:{{ ss }}</span>. Stay logged in?
          </p>
          <div class="flex gap-3">
            <button @click="logoutNow" class="flex-1 py-2.5 border border-slate-200 text-slate-600 text-sm rounded-xl hover:bg-slate-50 transition font-medium">
              Log Out
            </button>
            <button @click="stayLoggedIn" class="flex-1 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-xl transition font-semibold">
              Stay Logged In
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- Session expired modal -->
    <transition enter-active-class="transition-all duration-300" enter-from-class="opacity-0" leave-active-class="transition-all duration-200" leave-to-class="opacity-0">
      <div v-if="auth.sessionExpired" class="fixed inset-0 bg-black/60 z-[100] flex items-center justify-center p-4">
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-sm p-7 text-center">
          <div class="w-16 h-16 rounded-full bg-red-100 flex items-center justify-center mx-auto mb-4">
            <svg class="w-8 h-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/><path d="M15 9l-6 6M9 9l6 6"/>
            </svg>
          </div>
          <h3 class="font-bold text-slate-900 text-lg mb-1">Session Expired</h3>
          <p class="text-sm text-slate-500 mb-5">Your session has expired for security. Please log in again to continue.</p>
          <button @click="logoutNow" class="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-xl transition font-semibold">
            Back to Login
          </button>
        </div>
      </div>
    </transition>
  </teleport>
</template>
