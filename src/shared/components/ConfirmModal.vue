<script setup>
defineProps({
  title:       { type: String, default: 'Confirm' },
  message:     { type: String, default: 'Are you sure?' },
  confirmText: { type: String, default: 'Confirm' },
  cancelText:  { type: String, default: 'Cancel' },
  danger:      { type: Boolean, default: false },
  show:        { type: Boolean, required: true },
})
defineEmits(['confirm', 'cancel'])
</script>

<template>
  <teleport to="body">
    <transition enter-active-class="transition-all duration-200" enter-from-class="opacity-0" leave-active-class="transition-all duration-150" leave-to-class="opacity-0">
      <div v-if="show" class="fixed inset-0 bg-black/50 z-[80] flex items-center justify-center p-4" @click.self="$emit('cancel')">
        <transition enter-active-class="transition-all duration-200" enter-from-class="opacity-0 scale-95" leave-active-class="transition-all duration-150" leave-to-class="opacity-0 scale-95">
          <div v-if="show" class="bg-white rounded-2xl shadow-2xl w-full max-w-sm p-7 text-center">
            <div :class="['w-14 h-14 rounded-full flex items-center justify-center mx-auto mb-4', danger ? 'bg-red-100' : 'bg-blue-100']">
              <svg v-if="danger" :class="['w-7 h-7', danger ? 'text-red-500' : 'text-blue-500']" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4h6v2"/>
              </svg>
              <svg v-else class="w-7 h-7 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
            </div>
            <h3 class="font-bold text-gray-900 text-lg mb-2">{{ title }}</h3>
            <p class="text-sm text-gray-500 mb-6 leading-relaxed">{{ message }}</p>
            <div class="flex gap-3">
              <button @click="$emit('cancel')" class="flex-1 py-2.5 border border-gray-200 text-gray-600 text-sm font-medium rounded-xl hover:bg-gray-50 transition">
                {{ cancelText }}
              </button>
              <button @click="$emit('confirm')" :class="['flex-1 py-2.5 text-white text-sm font-semibold rounded-xl transition', danger ? 'bg-red-600 hover:bg-red-700' : 'bg-blue-600 hover:bg-blue-700']">
                {{ confirmText }}
              </button>
            </div>
          </div>
        </transition>
      </div>
    </transition>
  </teleport>
</template>
