<script setup>
import { useRouter } from 'vue-router'
import AppShell from '@/shared/components/AppShell.vue'

const router = useRouter()
</script>

<template>
  <AppShell>
    <template #page-title>Access Denied</template>

    <div class="flex flex-col items-center justify-center min-h-[70vh] p-8 text-center">
      <div class="w-20 h-20 rounded-full bg-red-100 flex items-center justify-center mb-5">
        <svg class="w-10 h-10 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          <path d="M9 12l2 2 4-4"/>
        </svg>
      </div>
      <h1 class="text-2xl font-bold text-slate-900 mb-2">Access Denied</h1>
      <p class="text-slate-500 text-sm max-w-xs mb-6 leading-relaxed">
        You don't have the required permissions to view this page. Contact your administrator if you think this is a mistake.
      </p>
      <div class="flex gap-3">
        <button @click="router.back()" class="px-5 py-2.5 border border-slate-200 text-slate-600 text-sm font-medium rounded-xl hover:bg-slate-50 transition">
          Go Back
        </button>
        <button @click="router.push('/dashboard')" class="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-xl transition">
          Dashboard
        </button>
      </div>
    </div>
  </AppShell>
</template>
