<script setup>
import AppShell from '../components/AppShell.vue'
</script>

<template>
  <AppShell>
    <template #page-title>Patients</template>
    <template #page-subtitle>Manage and view all patients</template>
    <div class="p-6">
      <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-12 text-center text-gray-400">
        <svg class="w-12 h-12 mx-auto mb-3 text-gray-200" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
          <path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
        </svg>
        <p class="font-medium text-gray-500">Patient Management</p>
        <p class="text-sm mt-1">Full patient list, search, and filters coming here.</p>
      </div>
    </div>
  </AppShell>
</template>
