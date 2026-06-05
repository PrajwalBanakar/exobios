<script setup>
import AppShell from '../components/AppShell.vue'
</script>

<template>
  <AppShell>
    <template #page-title>Reports</template>
    <template #page-subtitle>Analytics and health reports</template>
    <div class="p-6">
      <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-12 text-center text-gray-400">
        <svg class="w-12 h-12 mx-auto mb-3 text-gray-200" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/>
        </svg>
        <p class="font-medium text-gray-500">Reports & Analytics</p>
        <p class="text-sm mt-1">Patient trends, risk distributions, and field reports.</p>
      </div>
    </div>
  </AppShell>
</template>
