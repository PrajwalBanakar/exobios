<script setup>
import { useToast } from '@/shared/composables/useToast'

const { toasts, removeToast } = useToast()

const colorMap = {
  success: 'bg-green-600',
  error:   'bg-red-600',
  warning: 'bg-amber-500',
  info:    'bg-blue-600',
}

const iconMap = {
  success: 'M20 6L9 17l-5-5',
  error:   'M18 6 6 18M6 6l12 12',
  warning: 'M12 9v4M12 17h.01',
  info:    'M12 16v-4M12 8h.01',
}
</script>

<template>
  <teleport to="body">
    <div class="fixed top-4 right-4 z-[200] flex flex-col gap-2 max-w-xs w-full">
      <transition-group
        enter-active-class="transition-all duration-300"
        enter-from-class="opacity-0 translate-x-8"
        leave-active-class="transition-all duration-200"
        leave-to-class="opacity-0 translate-x-8"
        tag="div"
        class="flex flex-col gap-2"
      >
        <div
          v-for="t in toasts"
          :key="t.id"
          :class="['flex items-start gap-3 px-4 py-3 rounded-xl shadow-lg text-white text-sm font-medium cursor-pointer select-none', colorMap[t.type] || 'bg-gray-800']"
          @click="removeToast(t.id)"
        >
          <svg class="w-4 h-4 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
            <path :d="iconMap[t.type] || iconMap.info"/>
          </svg>
          <span class="flex-1 leading-snug">{{ t.message }}</span>
          <button class="text-white/70 hover:text-white ml-1" @click.stop="removeToast(t.id)" aria-label="Dismiss notification">
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M18 6 6 18M6 6l12 12"/></svg>
          </button>
        </div>
      </transition-group>
    </div>
  </teleport>
</template>
