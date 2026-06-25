<script setup>
import SessionExpiryModal from '@/shared/components/SessionExpiryModal.vue'
import ToastContainer     from '@/shared/components/ToastContainer.vue'
</script>

<template>
  <router-view />
  <SessionExpiryModal />
  <ToastContainer />
</template>
