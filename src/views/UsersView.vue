<script setup>
import AppShell from '../components/AppShell.vue'
</script>

<template>
  <AppShell>
    <template #page-title>Users</template>
    <template #page-subtitle>Manage ASHA workers and health enablers</template>
    <div class="p-6">
      <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-12 text-center text-gray-400">
        <svg class="w-12 h-12 mx-auto mb-3 text-gray-200" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
        </svg>
        <p class="font-medium text-gray-500">User Management</p>
        <p class="text-sm mt-1">Manage ASHA workers, supervisors, and admins.</p>
      </div>
    </div>
  </AppShell>
</template>
