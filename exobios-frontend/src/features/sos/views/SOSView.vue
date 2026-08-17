<script setup>
import { computed } from 'vue'
import AppShell from '@/shared/components/AppShell.vue'
import { useI18n } from '@/i18n'

const { t } = useI18n()

const contacts = computed(() => [
  { name: t('sos.ambulance'),       phone: '108',          icon: 'ambulance', color: 'bg-red-500',   desc: t('sos.ambulanceDesc') },
  { name: t('sos.nearestHospital'), phone: '05952-234567', icon: 'hospital',  color: 'bg-blue-600',  desc: t('sos.hospitalDesc') },
  { name: t('sos.police'),          phone: '100',          icon: 'police',    color: 'bg-slate-700',  desc: t('sos.policeDesc') },
  { name: t('sos.chc'),             phone: '05952-345678', icon: 'hospital2', color: 'bg-green-600', desc: t('sos.chcDesc') },
])

function callNumber(phone) { window.location.href = `tel:${phone}` }
</script>

<template>
  <AppShell>
    <template #page-title>{{ t('nav.sos') }}</template>
    <template #page-subtitle>{{ t('sos.pageSubtitle') }}</template>

    <div class="p-6 flex flex-col items-center gap-8">

      <!-- Alert banner -->
      <div class="w-full max-w-2xl bg-red-50 border border-red-200 rounded-2xl px-6 py-5 flex items-center gap-4">
        <div class="w-12 h-12 rounded-full bg-red-500 flex items-center justify-center flex-shrink-0 animate-pulse">
          <span class="text-white text-sm font-bold leading-none">SOS</span>
        </div>
        <div>
          <div class="font-semibold text-red-800 text-base">{{ t('sos.emergencyAlert') }}</div>
          <div class="text-sm text-red-600 mt-0.5">{{ t('sos.emergencyAlertDesc') }}</div>
        </div>
      </div>

      <!-- Call buttons -->
      <div class="w-full max-w-2xl">
        <h2 class="text-center text-sm font-semibold text-slate-500 uppercase tracking-widest mb-6">{{ t('sos.tapToCall') }}</h2>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-5">
          <button v-for="c in contacts" :key="c.phone"
            @click="callNumber(c.phone)"
            class="group flex flex-col items-center gap-4 bg-white hover:shadow-lg border-2 border-slate-100 hover:border-transparent rounded-2xl px-6 py-8 transition-all duration-200 hover:-translate-y-1 cursor-pointer">
            <div :class="[c.color, 'w-16 h-16 rounded-full flex items-center justify-center shadow-md group-hover:scale-110 transition-transform']">
              <svg v-if="c.icon === 'ambulance'" class="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 13a19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 3.6 2.18h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
              </svg>
              <svg v-else-if="c.icon === 'hospital' || c.icon === 'hospital2'" class="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <rect x="3" y="3" width="18" height="18" rx="2"/><path d="M12 8v8M8 12h8"/>
              </svg>
              <svg v-else-if="c.icon === 'police'" class="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              </svg>
            </div>
            <div class="text-center">
              <div class="font-bold text-slate-900 text-base">{{ c.name }}</div>
              <div class="text-2xl font-mono font-extrabold mt-1" :class="c.color.replace('bg-', 'text-')">{{ c.phone }}</div>
              <div class="text-xs text-slate-400 mt-1">{{ c.desc }}</div>
            </div>
            <div :class="[c.color, 'w-full py-2.5 rounded-xl text-white text-sm font-semibold flex items-center justify-center gap-2 group-hover:opacity-90 transition']">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 13a19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 3.6 2.18h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
              </svg>
              {{ t('sos.callNow') }}
            </div>
          </button>
        </div>
      </div>

      <!-- Instructions -->
      <div class="w-full max-w-2xl bg-amber-50 border border-amber-200 rounded-2xl px-6 py-5">
        <h3 class="font-semibold text-amber-800 mb-3 flex items-center gap-2">
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          {{ t('sos.instructions') }}
        </h3>
        <ul class="space-y-1.5 text-sm text-amber-700">
          <li class="flex items-start gap-2"><span class="mt-1 w-1.5 h-1.5 rounded-full bg-amber-500 flex-shrink-0"/>{{ t('sos.tip1') }}</li>
          <li class="flex items-start gap-2"><span class="mt-1 w-1.5 h-1.5 rounded-full bg-amber-500 flex-shrink-0"/>{{ t('sos.tip2') }}</li>
          <li class="flex items-start gap-2"><span class="mt-1 w-1.5 h-1.5 rounded-full bg-amber-500 flex-shrink-0"/>{{ t('sos.tip3') }}</li>
          <li class="flex items-start gap-2"><span class="mt-1 w-1.5 h-1.5 rounded-full bg-amber-500 flex-shrink-0"/>{{ t('sos.tip4') }}</li>
        </ul>
      </div>

    </div>
  </AppShell>
</template>
