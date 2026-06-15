<script setup>
import { ref, computed } from 'vue'
import AppShell from '@/shared/components/AppShell.vue'
import { useTeleconsultStore } from '@/features/teleconsult/stores/teleconsult'
import { useI18n } from '@/i18n'

const { t } = useI18n()
const store  = useTeleconsultStore()

const activeFilter = ref('All')
const filters      = ['All', 'Scheduled', 'Completed', 'Cancelled']
const search       = ref('')

const filtered = computed(() => {
  let list = activeFilter.value === 'All' ? store.items : store.items.filter(s => s.status === activeFilter.value)
  if (search.value.trim()) {
    const q = search.value.toLowerCase()
    list = list.filter(s => s.patientName.toLowerCase().includes(q) || s.doctor.toLowerCase().includes(q) || s.ashaWorker.toLowerCase().includes(q))
  }
  return list
})

const summary = computed(() => [
  { labelKey: 'teleconsult.total',       val: store.items.length,                                  color: 'bg-blue-600' },
  { labelKey: 'teleconsult.scheduled',   val: store.scheduledCount,                                color: 'bg-orange-400' },
  { labelKey: 'teleconsult.completed',   val: store.completedCount,                                color: 'bg-green-500' },
  { labelKey: 'teleconsult.avgDuration', val: store.avgDuration + ' ' + t('teleconsult.min'),     color: 'bg-purple-500' },
])

const statusClasses = { Scheduled: 'bg-blue-100 text-blue-600', Completed: 'bg-green-100 text-green-600', Cancelled: 'bg-red-100 text-red-600' }

function statusLabel(s) {
  if (s === 'Scheduled') return t('teleconsult.scheduled')
  if (s === 'Completed') return t('teleconsult.completed')
  if (s === 'Cancelled') return t('teleconsult.cancelled')
  return s
}

function filterLabel(f) { return f === 'All' ? t('teleconsult.allFilter') : statusLabel(f) }
function startVideoCall() { window.open('https://meet.google.com/new', '_blank') }
function markCompleted(id) { store.updateStatus(id, 'Completed') }
function cancelSession(id) { store.updateStatus(id, 'Cancelled') }
</script>

<template>
  <AppShell>
    <template #page-title>{{ t('teleconsult.title') }}</template>
    <template #page-subtitle>{{ t('teleconsult.subtitle') }}</template>

    <template #topbar-left>
      <div class="flex items-center gap-3">
        <div class="relative hidden md:block">
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
          <input v-model="search" type="text" :placeholder="t('teleconsult.searchPlaceholder')"
            class="pl-9 pr-4 py-2 text-sm border border-gray-200 rounded-lg bg-gray-50 w-64 focus:outline-none focus:ring-2 focus:ring-blue-500"/>
        </div>
      </div>
    </template>

    <div class="p-4 md:p-6 space-y-5">

      <!-- Stats -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div v-for="s in summary" :key="s.labelKey" class="bg-white rounded-xl border border-gray-100 shadow-sm p-4 flex items-center gap-3">
          <div :class="[s.color, 'w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0']">
            <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2"/></svg>
          </div>
          <div>
            <div class="text-xl font-bold text-gray-900">{{ s.val }}</div>
            <div class="text-xs text-gray-500">{{ t(s.labelKey) }}</div>
          </div>
        </div>
      </div>

      <!-- Scheduled banner -->
      <div v-if="store.scheduledCount > 0" class="bg-blue-600 rounded-xl p-4 flex items-center gap-4">
        <div class="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center flex-shrink-0">
          <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2"/></svg>
        </div>
        <div class="flex-1">
          <div class="text-white font-semibold text-sm">{{ store.scheduledCount }} {{ t('teleconsult.scheduledSessions') }}</div>
          <div class="text-blue-200 text-xs mt-0.5">{{ t('teleconsult.joinPrompt') }}</div>
        </div>
        <button @click="startVideoCall()" class="px-4 py-2 bg-white text-blue-600 text-xs font-semibold rounded-lg hover:bg-blue-50 transition flex-shrink-0">{{ t('teleconsult.join') }}</button>
      </div>

      <!-- Table -->
      <div class="bg-white rounded-xl border border-gray-100 shadow-sm">
        <div class="flex items-center justify-between px-5 py-4 border-b border-gray-100 gap-3 flex-wrap">
          <div class="flex items-center gap-2 flex-wrap">
            <button v-for="f in filters" :key="f"
              :class="['px-3 py-1.5 rounded-full text-xs font-medium transition', activeFilter === f ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200']"
              @click="activeFilter = f">
              {{ filterLabel(f) }}
            </button>
          </div>
        </div>

        <div v-if="filtered.length === 0" class="py-16 text-center">
          <svg class="w-12 h-12 text-gray-200 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.2"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2"/></svg>
          <p class="text-sm text-gray-500">{{ t('teleconsult.noSessions') }}</p>
        </div>

        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-gray-100 bg-gray-50/50">
                <th class="text-left text-xs font-semibold text-gray-500 px-5 py-3">{{ t('teleconsult.patient') }}</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">{{ t('teleconsult.doctor') }}</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">{{ t('referrals.ashaWorker') }}</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">{{ t('common.date') }}</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">{{ t('teleconsult.duration') }}</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">{{ t('common.status') }}</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">{{ t('common.actions') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="s in filtered" :key="s.id" class="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                <td class="px-5 py-3.5">
                  <div class="flex items-center gap-2.5">
                    <div class="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-xs font-semibold text-blue-600 flex-shrink-0">
                      {{ s.patientName.split(' ').map(n=>n[0]).join('').slice(0,2).toUpperCase() }}
                    </div>
                    <span class="font-medium text-gray-800">{{ s.patientName }}</span>
                  </div>
                </td>
                <td class="px-4 py-3.5">
                  <div class="flex items-center gap-2">
                    <div class="w-7 h-7 rounded-full bg-amber-100 flex items-center justify-center flex-shrink-0">
                      <svg class="w-3.5 h-3.5 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                    </div>
                    <div>
                      <div class="text-sm font-medium text-gray-800">{{ s.doctor }}</div>
                      <div class="text-[10px] text-gray-500">{{ s.spec }}</div>
                    </div>
                  </div>
                </td>
                <td class="px-4 py-3.5 text-gray-600 text-sm">{{ s.ashaWorker }}</td>
                <td class="px-4 py-3.5 text-gray-500 text-xs">{{ s.date }}</td>
                <td class="px-4 py-3.5 text-gray-600 text-sm">{{ s.duration ? s.duration + ' ' + t('teleconsult.min') : '—' }}</td>
                <td class="px-4 py-3.5">
                  <span :class="[statusClasses[s.status] || 'bg-gray-100 text-gray-600', 'px-2.5 py-1 rounded-full text-xs font-semibold']">{{ statusLabel(s.status) }}</span>
                </td>
                <td class="px-4 py-3.5">
                  <div class="flex items-center gap-1">
                    <button v-if="s.status === 'Scheduled'" @click="startVideoCall()" class="flex items-center gap-1 px-2.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg transition">
                      <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2"/></svg>
                      {{ t('teleconsult.join') }}
                    </button>
                    <button v-if="s.status === 'Scheduled'" @click="markCompleted(s.id)" class="p-1.5 text-green-600 hover:bg-green-50 rounded transition" :title="t('teleconsult.completed')">
                      <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M20 6L9 17l-5-5"/></svg>
                    </button>
                    <button v-if="s.status === 'Scheduled'" @click="cancelSession(s.id)" class="p-1.5 text-red-400 hover:bg-red-50 rounded transition" :title="t('teleconsult.cancelled')">
                      <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18M6 6l12 12"/></svg>
                    </button>
                    <span v-if="s.status !== 'Scheduled'" class="text-xs text-gray-400">
                      {{ s.status === 'Completed' ? (s.advice ? s.advice.slice(0,30)+'…' : '—') : '—' }}
                    </span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="px-5 py-3 text-xs text-gray-400 border-t border-gray-50">
          {{ t('common.showing') }} {{ filtered.length }} {{ t('common.of') }} {{ store.items.length }} {{ t('teleconsult.title').toLowerCase() }}
        </div>
      </div>
    </div>
  </AppShell>
</template>
