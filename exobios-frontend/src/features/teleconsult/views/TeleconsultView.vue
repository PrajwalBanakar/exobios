<script setup>
import { ref, computed } from 'vue'
import AppShell from '@/shared/components/AppShell.vue'
import StatCard from '@/shared/components/StatCard.vue'
import PatientAvatar from '@/shared/components/PatientAvatar.vue'
import StatusBadge from '@/shared/components/StatusBadge.vue'
import EmptyState from '@/shared/components/EmptyState.vue'
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
  { labelKey: 'teleconsult.total',       val: store.items.length,                              tone: 'blue'  },
  { labelKey: 'teleconsult.scheduled',   val: store.scheduledCount,                             tone: 'amber' },
  { labelKey: 'teleconsult.completed',   val: store.completedCount,                             tone: 'green' },
  { labelKey: 'teleconsult.avgDuration', val: store.avgDuration + ' ' + t('teleconsult.min'),   tone: 'blue'  },
])

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
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
          <input v-model="search" type="text" :placeholder="t('teleconsult.searchPlaceholder')"
            class="pl-9 pr-4 py-2 text-sm border border-slate-200 rounded-xl bg-slate-50 w-64 focus:outline-none focus:ring-2 focus:ring-blue-500"/>
        </div>
      </div>
    </template>

    <div class="p-4 md:p-6 space-y-5">

      <!-- Stats -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard v-for="s in summary" :key="s.labelKey" :label="t(s.labelKey)" :value="s.val" :tone="s.tone">
          <template #icon>
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2"/></svg>
          </template>
        </StatCard>
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
        <button @click="startVideoCall()" class="px-4 py-2 bg-white text-blue-600 text-xs font-semibold rounded-xl hover:bg-blue-50 transition flex-shrink-0">{{ t('teleconsult.join') }}</button>
      </div>

      <!-- Table -->
      <div class="bg-white rounded-xl border border-slate-100 shadow-sm">
        <div class="flex items-center justify-between px-5 py-4 border-b border-slate-100 gap-3 flex-wrap">
          <div class="flex items-center gap-2 flex-wrap">
            <button v-for="f in filters" :key="f"
              :class="['px-3 py-1.5 rounded-full text-xs font-medium transition', activeFilter === f ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200']"
              @click="activeFilter = f">
              {{ filterLabel(f) }}
            </button>
          </div>
        </div>

        <EmptyState v-if="filtered.length === 0" icon="folder" :title="t('teleconsult.noSessions')" message="Sessions created from an assessment's plan of action will appear here."/>

        <template v-else>
          <!-- Desktop table -->
          <div class="hidden overflow-x-auto md:block">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-slate-100 bg-slate-50/50">
                  <th scope="col" class="text-left text-xs font-semibold text-slate-500 px-5 py-3">{{ t('teleconsult.patient') }}</th>
                  <th scope="col" class="text-left text-xs font-semibold text-slate-500 px-4 py-3">{{ t('teleconsult.doctor') }}</th>
                  <th scope="col" class="text-left text-xs font-semibold text-slate-500 px-4 py-3">{{ t('referrals.ashaWorker') }}</th>
                  <th scope="col" class="text-left text-xs font-semibold text-slate-500 px-4 py-3">{{ t('common.date') }}</th>
                  <th scope="col" class="text-left text-xs font-semibold text-slate-500 px-4 py-3">{{ t('teleconsult.duration') }}</th>
                  <th scope="col" class="text-left text-xs font-semibold text-slate-500 px-4 py-3">{{ t('common.status') }}</th>
                  <th scope="col" class="text-left text-xs font-semibold text-slate-500 px-4 py-3">{{ t('common.actions') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="s in filtered" :key="s.id" class="border-b border-slate-50 hover:bg-slate-50 transition-colors">
                  <td class="px-5 py-3.5">
                    <div class="flex items-center gap-2.5">
                      <PatientAvatar :name="s.patientName" size="sm"/>
                      <span class="font-medium text-slate-800">{{ s.patientName }}</span>
                    </div>
                  </td>
                  <td class="px-4 py-3.5">
                    <div class="flex items-center gap-2">
                      <div class="w-7 h-7 rounded-full bg-amber-100 flex items-center justify-center flex-shrink-0">
                        <svg class="w-3.5 h-3.5 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                      </div>
                      <div>
                        <div class="text-sm font-medium text-slate-800">{{ s.doctor }}</div>
                        <div class="text-[10px] text-slate-500">{{ s.spec }}</div>
                      </div>
                    </div>
                  </td>
                  <td class="px-4 py-3.5 text-slate-600 text-sm">{{ s.ashaWorker }}</td>
                  <td class="px-4 py-3.5 text-slate-500 text-xs">{{ s.date }}</td>
                  <td class="px-4 py-3.5 text-slate-600 text-sm">{{ s.duration ? s.duration + ' ' + t('teleconsult.min') : '—' }}</td>
                  <td class="px-4 py-3.5"><StatusBadge :status="statusLabel(s.status)" :tone="s.status === 'Scheduled' ? 'blue' : s.status === 'Completed' ? 'green' : 'red'"/></td>
                  <td class="px-4 py-3.5">
                    <div class="flex items-center gap-1">
                      <button v-if="s.status === 'Scheduled'" @click="startVideoCall()" class="flex items-center gap-1 px-2.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-xl transition">
                        <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2"/></svg>
                        {{ t('teleconsult.join') }}
                      </button>
                      <button v-if="s.status === 'Scheduled'" @click="markCompleted(s.id)" class="p-1.5 text-green-600 hover:bg-green-50 rounded transition" :title="t('teleconsult.completed')" :aria-label="`Mark session with ${s.patientName} completed`">
                        <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M20 6L9 17l-5-5"/></svg>
                      </button>
                      <button v-if="s.status === 'Scheduled'" @click="cancelSession(s.id)" class="p-1.5 text-red-400 hover:bg-red-50 rounded transition" :title="t('teleconsult.cancelled')" :aria-label="`Cancel session with ${s.patientName}`">
                        <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18M6 6l12 12"/></svg>
                      </button>
                      <span v-if="s.status !== 'Scheduled'" class="text-xs text-slate-400">
                        {{ s.status === 'Completed' ? (s.advice ? s.advice.slice(0,30)+'…' : '—') : '—' }}
                      </span>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Mobile cards -->
          <div class="divide-y divide-slate-100 md:hidden">
            <div v-for="s in filtered" :key="s.id" class="p-4">
              <div class="flex items-start justify-between gap-3">
                <div class="flex min-w-0 items-center gap-3">
                  <PatientAvatar :name="s.patientName"/>
                  <div class="min-w-0">
                    <div class="truncate font-semibold text-slate-800">{{ s.patientName }}</div>
                    <div class="truncate text-xs text-slate-400">{{ s.doctor }} · {{ s.spec }}</div>
                  </div>
                </div>
                <StatusBadge :status="statusLabel(s.status)" :tone="s.status === 'Scheduled' ? 'blue' : s.status === 'Completed' ? 'green' : 'red'"/>
              </div>
              <div class="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500">
                <span>{{ s.date }}</span>
                <span>{{ s.duration ? s.duration + ' ' + t('teleconsult.min') : '—' }}</span>
              </div>
              <div v-if="s.status === 'Scheduled'" class="mt-3 flex gap-2">
                <button @click="startVideoCall()" class="flex flex-1 items-center justify-center gap-1.5 rounded-xl bg-blue-600 py-2 text-xs font-semibold text-white transition hover:bg-blue-700">
                  <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2"/></svg>
                  {{ t('teleconsult.join') }}
                </button>
                <button @click="markCompleted(s.id)" class="rounded-xl border border-green-200 px-3 py-2 text-green-600 transition hover:bg-green-50" :aria-label="`Mark session with ${s.patientName} completed`">
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M20 6L9 17l-5-5"/></svg>
                </button>
                <button @click="cancelSession(s.id)" class="rounded-xl border border-red-200 px-3 py-2 text-red-400 transition hover:bg-red-50" :aria-label="`Cancel session with ${s.patientName}`">
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18M6 6l12 12"/></svg>
                </button>
              </div>
              <p v-else-if="s.advice" class="mt-3 text-xs text-slate-500">{{ s.advice }}</p>
            </div>
          </div>

          <div class="px-5 py-3 text-xs text-slate-400 border-t border-slate-50">
            {{ t('common.showing') }} {{ filtered.length }} {{ t('common.of') }} {{ store.items.length }} {{ t('teleconsult.title').toLowerCase() }}
          </div>
        </template>
      </div>
    </div>
  </AppShell>
</template>
