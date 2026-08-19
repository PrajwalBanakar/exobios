<script setup>
import exobiosLogo from '@/assets/brand/exobios-logo-dark.png'
</script>

<template>
  <header class="shrink-0 border-b border-slate-100">
    <div class="mx-auto flex max-w-6xl items-center justify-between px-5 py-3.5 sm:px-8">
      <img :src="exobiosLogo" alt="Exobios" class="h-6 w-auto object-contain sm:h-7" />
      <router-link
        to="/login"
        class="rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-sm shadow-blue-600/20 transition motion-safe:duration-150 hover:bg-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/40 focus-visible:ring-offset-2"
      >
        Login
      </router-link>
    </div>
  </header>
</template>
