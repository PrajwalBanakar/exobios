<script setup>
import { ref, computed, reactive } from 'vue'
import AppShell from '@/shared/components/AppShell.vue'
import { useI18n } from '@/i18n'

const { t } = useI18n()

const FEEDBACK_KEY = 'exobios_feedback'

function loadFeedback() { try { return JSON.parse(localStorage.getItem(FEEDBACK_KEY) || '[]') } catch { return [] } }
function saveFeedback(list) { localStorage.setItem(FEEDBACK_KEY, JSON.stringify(list)) }

const feedbackList = ref(loadFeedback().length ? loadFeedback() : [
  { id: 1, from: 'Sunita Devi',   fromRole: 'ASHA Worker', category: 'Teleconsult',    rating: 5, comment: 'Very helpful and prompt teleconsult experience.', date: '5 Jun 2025', responded: false },
  { id: 2, from: 'Kavita Sharma', fromRole: 'ASHA Worker', category: 'App Usability',  rating: 4, comment: 'Good patient history and vitals recording interface.', date: '4 Jun 2025', responded: false },
  { id: 3, from: 'Meena Kumari',  fromRole: 'ASHA Worker', category: 'Teleconsult',    rating: 3, comment: 'Response from the teleconsult was delayed by a few hours.', date: '3 Jun 2025', responded: true },
])

const showModal = ref(false)
const submitted = ref(false)

const CATEGORIES = ['Teleconsult', 'App Usability', 'Patient Care', 'Training', 'Other']

const form = reactive({ category: 'Teleconsult', rating: 0, comment: '', anonymous: false })

const filtered = computed(() => feedbackList.value)

function openModal() {
  form.category = 'Teleconsult'; form.rating = 0; form.comment = ''; form.anonymous = false
  showModal.value = true
}

function submitFeedback() {
  if (!form.rating || !form.comment.trim()) return
  const dateStr = new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
  feedbackList.value.unshift({
    id: Date.now(),
    from:     form.anonymous ? t('feedback.anonymous') : 'Sunita Devi',
    fromRole: 'ASHA Worker',
    category: form.category, rating: form.rating, comment: form.comment, date: dateStr, responded: false,
  })
  saveFeedback(feedbackList.value)
  showModal.value = false
  submitted.value = true
  setTimeout(() => { submitted.value = false }, 2500)
}

const ratingColor = (r) => r >= 4 ? 'text-green-600' : r === 3 ? 'text-yellow-500' : 'text-red-500'
const avgRating   = computed(() => !feedbackList.value.length ? 0 : (feedbackList.value.reduce((a, f) => a + f.rating, 0) / feedbackList.value.length).toFixed(1))
</script>

<template>
  <AppShell>
    <template #page-title>{{ t('feedback.title') }}</template>
    <template #page-subtitle>{{ t('feedback.subtitle') }}</template>

    <div class="p-4 md:p-6 space-y-5">
      <transition enter-active-class="transition-all duration-300" enter-from-class="opacity-0 -translate-y-2" leave-active-class="transition-all duration-200" leave-to-class="opacity-0">
        <div v-if="submitted" class="bg-green-50 border border-green-200 text-green-700 rounded-xl px-5 py-3 flex items-center gap-2 font-medium text-sm">
          <svg class="w-5 h-5 text-green-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg>
          {{ t('feedback.submitted') }}
        </div>
      </transition>

      <!-- Stats -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div v-for="stat in [
          { label: 'Total Feedback', val: feedbackList.length,                                              color: 'bg-blue-600'   },
          { label: 'This Month',     val: feedbackList.filter(f=>f.date.includes('Jun 2025')).length,       color: 'bg-purple-500' },
          { label: 'Responded',      val: feedbackList.filter(f=>f.responded).length,                       color: 'bg-teal-500'   },
          { label: 'Avg Rating',     val: avgRating + ' ★',                                                 color: 'bg-amber-500'  },
        ]" :key="stat.label"
          class="bg-white rounded-xl border border-gray-100 shadow-sm p-4 flex items-center gap-3">
          <div :class="[stat.color, 'w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0']">
            <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
          </div>
          <div>
            <div class="text-xl font-bold text-gray-900">{{ stat.val }}</div>
            <div class="text-xs text-gray-500">{{ stat.label }}</div>
          </div>
        </div>
      </div>

      <!-- Feedback card -->
      <div class="bg-white rounded-xl border border-gray-100 shadow-sm">
        <div class="flex items-center justify-between px-5 py-4 border-b border-gray-100 gap-3 flex-wrap">
          <h2 class="font-semibold text-gray-900 text-sm">{{ t('feedback.allTypes') }}</h2>
          <button @click="openModal" class="flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-lg transition">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M12 5v14M5 12h14"/></svg>
            {{ t('feedback.giveFeedback') }}
          </button>
        </div>

        <div v-if="filtered.length === 0" class="py-16 text-center">
          <svg class="w-12 h-12 text-gray-200 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
          <p class="text-sm text-gray-500">{{ t('feedback.noFeedback') }}</p>
        </div>

        <div v-else class="divide-y divide-gray-50">
          <div v-for="fb in filtered" :key="fb.id" class="px-5 py-4 hover:bg-gray-50 transition">
            <div class="flex items-start gap-4">
              <div class="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0 text-sm font-semibold text-blue-700">
                {{ fb.from.split(' ').map(n=>n[0]).join('').slice(0,2).toUpperCase() }}
              </div>
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 flex-wrap">
                  <span class="font-medium text-gray-800 text-sm">{{ fb.from }}</span>
                  <span class="bg-blue-100 text-blue-600 px-2 py-0.5 text-xs font-medium rounded">{{ fb.category }}</span>
                </div>
                <div class="flex items-center gap-1 mt-1">
                  <span v-for="s in 5" :key="s" :class="['text-base', s <= fb.rating ? 'text-amber-400' : 'text-gray-200']">★</span>
                  <span :class="[ratingColor(fb.rating), 'text-xs font-semibold ml-1']">{{ fb.rating }}/5</span>
                </div>
                <p class="text-sm text-gray-600 mt-1.5 leading-relaxed">{{ fb.comment }}</p>
                <div class="text-xs text-gray-400 mt-1">{{ fb.date }}</div>
              </div>
              <span v-if="fb.responded" class="text-[10px] px-2 py-1 bg-green-100 text-green-600 rounded font-semibold flex-shrink-0">{{ t('feedback.responded') }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Give Feedback Modal -->
    <teleport to="body">
      <div v-if="showModal" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" @click.self="showModal=false">
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-lg">
          <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
            <h3 class="font-semibold text-gray-900 text-lg">{{ t('feedback.giveFeedback') }}</h3>
            <button @click="showModal=false" class="text-gray-400 hover:text-gray-600 p-1" aria-label="Close">
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18M6 6l12 12"/></svg>
            </button>
          </div>
          <div class="px-6 py-5 space-y-4">
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1.5">{{ t('feedback.type') }}</label>
              <select v-model="form.category" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white">
                <option v-for="c in CATEGORIES" :key="c" :value="c">{{ c }}</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1.5">{{ t('feedback.rating') }} <span class="text-red-500">*</span></label>
              <div class="flex items-center gap-1">
                <button v-for="s in 5" :key="s" @click="form.rating=s" :class="['text-3xl transition-transform hover:scale-110', s <= form.rating ? 'text-amber-400' : 'text-gray-200']">★</button>
                <span class="ml-2 text-sm text-gray-500">{{ form.rating > 0 ? form.rating + '/5' : '' }}</span>
              </div>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1.5">{{ t('feedback.comment') }} <span class="text-red-500">*</span></label>
              <textarea v-model="form.comment" rows="3" :placeholder="t('feedback.commentPlaceholder')"
                class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"/>
            </div>
            <label class="flex items-center gap-2 cursor-pointer">
              <input v-model="form.anonymous" type="checkbox" class="w-4 h-4 rounded border-gray-300 text-blue-600"/>
              <span class="text-sm text-gray-600">{{ t('feedback.anonymous') }}</span>
            </label>
          </div>
          <div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-100">
            <button @click="showModal=false" class="px-4 py-2 text-sm border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50">{{ t('common.cancel') }}</button>
            <button @click="submitFeedback" :disabled="!form.rating || !form.comment.trim()"
              class="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed">
              {{ t('feedback.submit') }}
            </button>
          </div>
        </div>
      </div>
    </teleport>
  </AppShell>
</template>
