<script setup>
import { useI18n } from '@/i18n'
import exobiosLogo from '@/assets/brand/exobios-logo-dark.png'

const { t } = useI18n()

const FEATURES = [
  { titleKey: 'login.feature1Title', icon: 'M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z' },
  { titleKey: 'login.feature2Title', icon: 'M12 3v2.25m6.364.386-1.591 1.591M21 12h-2.25m-.386 6.364-1.591-1.591M12 18.75V21m-6.364-2.386 1.591-1.591M3 12h2.25m.386-6.364 1.591 1.591M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6Z' },
  { titleKey: 'login.feature3Title', icon: 'M13 2 3 14h9l-1 8 10-12h-9l1-8Z' },
]
</script>

<template>
  <div class="relative hidden overflow-hidden lg:flex lg:w-[44%] lg:flex-col lg:justify-between"
       style="background: linear-gradient(165deg, #0a1628 0%, #0d1a30 45%, #060e1f 100%)">

    <!-- Subtle network / grid backdrop -->
    <svg class="pointer-events-none absolute inset-0 h-full w-full opacity-[0.07]" preserveAspectRatio="xMidYMid slice" viewBox="0 0 800 900">
      <defs>
        <pattern id="grid" width="46" height="46" patternUnits="userSpaceOnUse">
          <path d="M46 0H0V46" fill="none" stroke="#7fb3ff" stroke-width="0.6"/>
        </pattern>
      </defs>
      <rect width="800" height="900" fill="url(#grid)"/>
    </svg>
    <svg class="pointer-events-none absolute inset-0 h-full w-full opacity-25" preserveAspectRatio="xMidYMid slice" viewBox="0 0 800 900">
      <defs>
        <radialGradient id="rg1" cx="50%" cy="100%" r="70%">
          <stop offset="0%" stop-color="#2f6fed" stop-opacity="0.55"/>
          <stop offset="100%" stop-color="#0a1628" stop-opacity="0"/>
        </radialGradient>
      </defs>
      <ellipse cx="400" cy="900" rx="520" ry="380" fill="url(#rg1)"/>
    </svg>

    <!-- Logo -->
    <div class="relative z-10 px-12 pt-12">
      <div class="inline-flex items-center rounded-2xl bg-white/95 px-5 py-3 shadow-lg shadow-black/20">
        <img :src="exobiosLogo" alt="Exobios" class="h-7 w-auto object-contain" />
      </div>
    </div>

    <!-- Headline + features -->
    <div class="relative z-10 px-12 py-10">
      <h1 class="max-w-md text-[2rem] font-bold leading-[1.2] text-white">{{ t('login.heroTitle') }}</h1>
      <div class="my-6 h-1 w-12 rounded-full bg-blue-500"/>
      <p class="max-w-sm text-[15px] leading-relaxed text-slate-300">{{ t('login.heroSupport') }}</p>

      <div class="mt-10 space-y-4">
        <div v-for="f in FEATURES" :key="f.titleKey" class="flex items-center gap-3.5">
          <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-white/10 bg-white/5">
            <svg class="h-[18px] w-[18px] text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.6"><path stroke-linecap="round" stroke-linejoin="round" :d="f.icon"/></svg>
          </div>
          <span class="text-sm font-medium text-slate-200">{{ t(f.titleKey) }}</span>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <div class="relative z-10 border-t border-white/10 px-12 py-6">
      <p class="text-xs text-slate-500">© {{ new Date().getFullYear() }} Exobios. Built for frontline healthcare teams.</p>
    </div>
  </div>
</template>
