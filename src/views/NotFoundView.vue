<script setup>
import { useRouter } from 'vue-router'
import { useI18n } from '../i18n/index'

const router = useRouter()
const { t }  = useI18n()
</script>

<template>
  <div class="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-6">
    <div class="text-center max-w-sm">
      <div class="w-24 h-24 rounded-full bg-blue-100 flex items-center justify-center mx-auto mb-6">
        <svg class="w-12 h-12 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
      </div>
      <h1 class="text-4xl font-bold text-gray-800 mb-2">404</h1>
      <h2 class="text-lg font-semibold text-gray-600 mb-2">{{ t('notFound.title') }}</h2>
      <p class="text-sm text-gray-400 mb-8">{{ t('notFound.message') }}</p>
      <button @click="router.push('/dashboard')"
        class="flex items-center gap-2 mx-auto px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-xl transition">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 5l-7 7 7 7"/></svg>
        {{ t('notFound.back') }}
      </button>
    </div>
  </div>
</template>
