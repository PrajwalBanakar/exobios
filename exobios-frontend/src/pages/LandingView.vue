<script setup>
import exobiosLogo from '@/assets/brand/exobios-logo-dark.png'
import ExobiosChatbot from '@/features/chat/components/ExobiosChatbot.vue'

const INTRO_POINTS = [
  { label: 'AI-assisted assessment', icon: 'M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09Z' },
  { label: 'Evidence-grounded guidance', icon: 'M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25' },
  { label: 'Faster triage & referral', icon: 'M13 2 3 14h9l-1 8 10-12h-9l1-8Z' },
]
</script>

<template>
  <div class="flex min-h-screen flex-col bg-white">
    <!-- Header -->
    <header class="flex shrink-0 items-center justify-between px-5 py-4 sm:px-8">
      <img :src="exobiosLogo" alt="Exobios" class="h-7 w-auto object-contain sm:h-8" />
      <router-link to="/login"
        class="rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm shadow-blue-600/20 transition hover:bg-blue-700">
        Login
      </router-link>
    </header>

    <!-- Hero -->
    <main class="flex flex-1 flex-col items-center px-5 pb-14 pt-4 sm:px-8">
      <div class="w-full max-w-2xl text-center">
        <h1 class="text-[1.75rem] font-bold leading-tight tracking-tight text-navy-900 sm:text-[2.25rem]">
          AI-Assisted Healthcare for Faster, Safer Triage
        </h1>
        <p class="mx-auto mt-3 max-w-xl text-sm leading-relaxed text-slate-500 sm:text-base">
          Clinical decision support designed to help frontline healthcare workers assess patients,
          identify risk and make informed referral decisions.
        </p>

        <div class="mt-5 flex flex-wrap items-center justify-center gap-x-6 gap-y-2">
          <div v-for="p in INTRO_POINTS" :key="p.label" class="flex items-center gap-1.5 text-xs font-medium text-slate-600 sm:text-sm">
            <svg class="h-4 w-4 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
              <path stroke-linecap="round" stroke-linejoin="round" :d="p.icon"/>
            </svg>
            {{ p.label }}
          </div>
        </div>
      </div>

      <!-- Chatbot — main focus of the page -->
      <div class="mt-8 flex w-full justify-center sm:mt-10">
        <ExobiosChatbot />
      </div>
    </main>
  </div>
</template>
