<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import AppShell from '@/shared/components/AppShell.vue'

const router = useRouter()
const route  = useRoute()

const title    = computed(() => route.meta.title    || 'Coming Soon')
const subtitle = computed(() => route.meta.subtitle || 'This feature is under development.')
</script>

<template>
  <AppShell>
    <template #page-title>{{ title }}</template>
    <template #page-subtitle>{{ subtitle }}</template>

    <div class="flex flex-col items-center justify-center min-h-[70vh] p-8 text-center">
      <div class="w-20 h-20 rounded-full bg-blue-100 flex items-center justify-center mb-5">
        <svg class="w-10 h-10 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
          <circle cx="12" cy="12" r="10"/><path d="M12 7v5l3 3"/>
        </svg>
      </div>
      <h1 class="text-2xl font-bold text-gray-900 mb-2">{{ title }}</h1>
      <p class="text-gray-500 text-sm max-w-xs mb-6 leading-relaxed">
        Coming Soon... We're working on bringing this feature to Exobios. Check back later.
      </p>
      <button @click="router.push('/dashboard')" class="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-xl transition">
        Back to Dashboard
      </button>
    </div>
  </AppShell>
</template>
