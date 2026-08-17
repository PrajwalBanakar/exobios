<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '@/shared/components/AppShell.vue'
import { useNotificationsStore } from '@/features/notifications/stores/notifications'
import { useI18n } from '@/i18n'

const router     = useRouter()
const notifStore = useNotificationsStore()
const { t }      = useI18n()

const typeFilter = ref('All')
const types      = ['All', 'Error', 'Warning', 'Success', 'Info']

const filtered = computed(() => {
  if (typeFilter.value === 'All') return notifStore.items
  return notifStore.items.filter(n => n.type === typeFilter.value.toLowerCase())
})

const typeIcon = {
  error:   { bg: 'bg-red-100',    dot: 'bg-red-500',    text: 'text-red-600'    },
  warning: { bg: 'bg-orange-100', dot: 'bg-orange-400', text: 'text-orange-500' },
  success: { bg: 'bg-green-100',  dot: 'bg-green-500',  text: 'text-green-600'  },
  info:    { bg: 'bg-blue-100',   dot: 'bg-blue-500',   text: 'text-blue-600'   },
}
</script>

<template>
  <AppShell>
    <template #page-title>{{ t('notif.title') }}</template>
    <template #page-subtitle>{{ t('notif.subtitle') }}</template>

    <div class="p-4 md:p-6 space-y-5">
      <!-- Header actions -->
      <div class="flex items-center justify-between flex-wrap gap-3">
        <div class="flex items-center gap-3">
          <button @click="router.back()" class="flex items-center gap-1.5 text-sm text-blue-600 hover:underline">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 5l-7 7 7 7"/></svg>
            {{ t('common.back') }}
          </button>
          <span v-if="notifStore.unreadCount > 0" class="px-2.5 py-1 bg-red-100 text-red-600 text-xs font-semibold rounded-full">
            {{ notifStore.unreadCount }} {{ t('notif.unread') }}
          </span>
        </div>
        <button v-if="notifStore.unreadCount > 0" @click="notifStore.markAllRead()" class="text-xs text-blue-600 hover:underline font-medium">
          {{ t('notif.markAllRead') }}
        </button>
      </div>

      <!-- Type filters -->
      <div class="flex items-center gap-2 flex-wrap">
        <button v-for="tp in types" :key="tp"
          :class="['px-3 py-1.5 rounded-full text-xs font-medium transition', typeFilter === tp ? 'bg-blue-600 text-white' : 'bg-white border border-slate-200 text-slate-600 hover:border-blue-300']"
          @click="typeFilter = tp">
          {{ tp }}
        </button>
      </div>

      <!-- Notifications list -->
      <div class="space-y-3">
        <div v-for="n in filtered" :key="n.id"
          :class="['bg-white rounded-xl border shadow-sm px-4 md:px-5 py-4 flex items-start gap-4 transition cursor-pointer', n.read ? 'border-slate-100' : 'border-blue-200 bg-blue-50/20']"
          @click="notifStore.markRead(n.id)">
          <div :class="[typeIcon[n.type].bg, 'w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5']">
            <svg v-if="n.type==='error'"   class="w-5 h-5 text-red-500"    fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/></svg>
            <svg v-else-if="n.type==='warning'" class="w-5 h-5 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            <svg v-else-if="n.type==='success'" class="w-5 h-5 text-green-500"  fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg>
            <svg v-else class="w-5 h-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-start justify-between gap-3">
              <span class="font-semibold text-slate-800 text-sm">{{ n.title }}</span>
              <div class="flex items-center gap-2 flex-shrink-0">
                <span class="text-xs text-slate-400 hidden sm:block">{{ n.date }}, {{ n.time }}</span>
                <span class="text-xs text-slate-400 sm:hidden">{{ n.time }}</span>
                <span v-if="!n.read" class="w-2 h-2 rounded-full bg-blue-500 flex-shrink-0"/>
              </div>
            </div>
            <p class="text-sm text-slate-600 mt-1 leading-relaxed">{{ n.body }}</p>
          </div>
        </div>

        <div v-if="!filtered.length" class="bg-white rounded-xl border border-slate-100 py-16 text-center">
          <svg class="w-12 h-12 text-slate-200 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
          <p class="text-sm text-slate-500">{{ t('notif.noNotifications') }}</p>
        </div>
      </div>
    </div>
  </AppShell>
</template>
