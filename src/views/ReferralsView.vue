<script setup>
import { ref, computed } from 'vue'
import { useReferralsStore } from '../stores/referrals'
import { useI18n } from '../i18n/index'
import AppShell from '../components/AppShell.vue'

const { t } = useI18n()
const store = useReferralsStore()

const activeFilter = ref('All')
const filters = ['All', 'Pending', 'Accepted', 'Completed', 'Rejected']

const search = ref('')

const filtered = computed(() => {
  let list = activeFilter.value === 'All'
    ? store.items
    : store.items.filter(r => r.status === activeFilter.value)
  if (search.value.trim()) {
    const q = search.value.toLowerCase()
    list = list.filter(r =>
      r.patientName.toLowerCase().includes(q) ||
      r.hospital.toLowerCase().includes(q) ||
      r.ashaWorker.toLowerCase().includes(q)
    )
  }
  return list
})

const summary = computed(() => [
  { labelKey: 'referrals.total',       val: store.items.length,         color: 'bg-blue-600' },
  { labelKey: 'referrals.pending',     val: store.pendingCount,         color: 'bg-orange-400' },
  { labelKey: 'referrals.completed',   val: store.completedCount,       color: 'bg-green-500' },
  { labelKey: 'referrals.successRate', val: store.items.length ? Math.round((store.completedCount / store.items.length) * 100) + '%' : '0%', color: 'bg-purple-500' },
])

const statusClasses = {
  Pending:   'bg-orange-100 text-orange-600',
  Accepted:  'bg-blue-100 text-blue-600',
  Completed: 'bg-green-100 text-green-600',
  Rejected:  'bg-red-100 text-red-600',
}

function statusLabel(s) {
  if (s === 'Pending')   return t('referrals.pending')
  if (s === 'Accepted')  return t('referrals.accepted')
  if (s === 'Completed') return t('referrals.completed')
  if (s === 'Rejected')  return t('referrals.rejected')
  return s
}

const statusOptions = ['Pending', 'Accepted', 'Completed', 'Rejected']
const editingId = ref(null)

function cycleStatus(id) {
  const item = store.items.find(r => r.id === id)
  if (!item) return
  const idx = statusOptions.indexOf(item.status)
  store.updateStatus(id, statusOptions[(idx + 1) % statusOptions.length])
}
</script>

<template>
  <AppShell>
    <template #page-title>{{ t('referrals.title') }}</template>
    <template #page-subtitle>{{ t('referrals.subtitle') }}</template>

    <template #topbar-left>
      <div class="flex items-center gap-3">
        <div class="relative hidden md:block">
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
          <input v-model="search" type="text" :placeholder="t('referrals.searchPlaceholder')"
            class="pl-9 pr-4 py-2 text-sm border border-gray-200 rounded-lg bg-gray-50 w-64 focus:outline-none focus:ring-2 focus:ring-blue-500"/>
        </div>
      </div>
    </template>

    <div class="p-4 md:p-6 space-y-5">

      <!-- Stats -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div v-for="s in summary" :key="s.labelKey"
          class="bg-white rounded-xl border border-gray-100 shadow-sm p-4 flex items-center gap-3">
          <div :class="[s.color, 'w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0']">
            <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>
            </svg>
          </div>
          <div>
            <div class="text-xl font-bold text-gray-900">{{ s.val }}</div>
            <div class="text-xs text-gray-500">{{ t(s.labelKey) }}</div>
          </div>
        </div>
      </div>

      <!-- Table card -->
      <div class="bg-white rounded-xl border border-gray-100 shadow-sm">
        <div class="flex items-center justify-between px-5 py-4 border-b border-gray-100 gap-3 flex-wrap">
          <div class="flex items-center gap-2 flex-wrap">
            <button v-for="f in filters" :key="f"
              :class="['px-3 py-1.5 rounded-full text-xs font-medium transition', activeFilter === f ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200']"
              @click="activeFilter = f">
              {{ f === 'All' ? t('referrals.allFilter') : statusLabel(f) }}
            </button>
          </div>
        </div>

        <!-- Empty state -->
        <div v-if="filtered.length === 0" class="py-16 text-center">
          <svg class="w-12 h-12 text-gray-200 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.2">
            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>
          </svg>
          <p class="text-sm text-gray-500">{{ t('referrals.noReferrals') }}</p>
        </div>

        <!-- Table -->
        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-gray-100 bg-gray-50/50">
                <th class="text-left text-xs font-semibold text-gray-500 px-5 py-3">{{ t('referrals.patient') }}</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">{{ t('referrals.hospital') }}</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">{{ t('referrals.ashaWorker') }}</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">{{ t('referrals.transport') }}</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">{{ t('common.date') }}</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">{{ t('common.status') }}</th>
                <th class="text-left text-xs font-semibold text-gray-500 px-4 py-3">{{ t('common.actions') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in filtered" :key="r.id"
                class="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                <td class="px-5 py-3.5">
                  <div class="flex items-center gap-2.5">
                    <div class="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-xs font-semibold text-blue-600 flex-shrink-0">
                      {{ r.patientName.split(' ').map(n=>n[0]).join('').slice(0,2).toUpperCase() }}
                    </div>
                    <div>
                      <div class="font-medium text-gray-800">{{ r.patientName }}</div>
                      <div v-if="r.notes" class="text-[10px] text-gray-400 truncate max-w-[140px]">{{ r.notes }}</div>
                    </div>
                  </div>
                </td>
                <td class="px-4 py-3.5">
                  <div class="flex items-center gap-1.5">
                    <svg class="w-3.5 h-3.5 text-gray-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/></svg>
                    <span class="text-sm text-gray-700">{{ r.hospital }}</span>
                  </div>
                </td>
                <td class="px-4 py-3.5 text-gray-600 text-sm">{{ r.ashaWorker }}</td>
                <td class="px-4 py-3.5">
                  <span class="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded font-medium">{{ r.transport }}</span>
                </td>
                <td class="px-4 py-3.5 text-gray-500 text-xs">{{ r.date }}</td>
                <td class="px-4 py-3.5">
                  <span :class="[statusClasses[r.status] || 'bg-gray-100 text-gray-600', 'px-2.5 py-1 rounded-full text-xs font-semibold']">
                    {{ statusLabel(r.status) }}
                  </span>
                </td>
                <td class="px-4 py-3.5">
                  <button @click="cycleStatus(r.id)"
                    class="text-xs text-blue-600 hover:underline border border-blue-200 px-2.5 py-1 rounded-lg hover:bg-blue-50 transition">
                    {{ t('referrals.updateStatus') }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Footer count -->
        <div class="px-5 py-3 text-xs text-gray-400 border-t border-gray-50">
          {{ t('common.showing') }} {{ filtered.length }} {{ t('common.of') }} {{ store.items.length }} {{ t('referrals.title').toLowerCase() }}
        </div>
      </div>
    </div>
  </AppShell>
</template>
