<script setup>
import LandingHeader from '@/features/landing/components/LandingHeader.vue'
import HeroSection from '@/features/landing/components/HeroSection.vue'
import ExobiosChatbot from '@/features/chat/components/ExobiosChatbot.vue'
</script>

<template>
  <div class="flex min-h-screen flex-col bg-white">
    <LandingHeader />

    <main class="flex flex-1 flex-col items-center px-5 pb-10 pt-6 sm:px-8">
      <HeroSection />

      <!-- Chatbot — main focus of the page -->
      <div class="mt-6 flex w-full justify-center sm:mt-7">
        <ExobiosChatbot />
      </div>

      <p class="mt-4 max-w-xl text-center text-[11px] leading-relaxed text-slate-400">
        Responses are generated from the currently available Exobios knowledge base and are intended for clinical
        decision support, not as a replacement for professional medical judgment.
      </p>
    </main>
  </div>
</template>
