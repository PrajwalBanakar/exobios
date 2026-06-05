<script setup>
import AppShell from '../components/AppShell.vue'
</script>

<template>
  <AppShell>
    <template #page-title>SOS / Emergency</template>
    <template #page-subtitle>Active emergency cases and alerts</template>
    <div class="p-6">
      <div class="bg-red-50 border border-red-200 rounded-xl p-12 text-center text-red-400">
        <div class="w-16 h-16 rounded-full bg-red-500 flex items-center justify-center mx-auto mb-3">
          <span class="text-white font-bold text-xl">SOS</span>
        </div>
        <p class="font-medium text-red-600">Emergency Management</p>
        <p class="text-sm mt-1 text-red-400">Emergency triage, ambulance dispatch, and alerts.</p>
      </div>
    </div>
  </AppShell>
</template>
