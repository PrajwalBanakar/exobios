<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '../components/AppShell.vue'
import { useAuthStore } from '../stores/auth'
import { useI18n } from '../i18n/index'

const router = useRouter()
const auth   = useAuthStore()
const { t }  = useI18n()

const photoInputRef = ref(null)
const profilePhoto  = ref('')
const saved = ref(false)

const form = reactive({
  name:   '',
  role:   '',
  phone:  '',
  ashaId: '',
  area:   '',
  email:  '',
})

onMounted(() => {
  form.name   = auth.user?.name  || 'Sunita Devi'
  form.role   = auth.user?.role  || 'ASHA Worker'
  form.phone  = '9876543210'
  form.ashaId = 'ASHA-2023-00890'
  form.area   = 'Rampur Block, Uttar Pradesh'
  form.email  = 'sunita.devi@asha.gov.in'

  const savedPhoto = localStorage.getItem('exobios_profile_photo')
  if (savedPhoto) profilePhoto.value = savedPhoto
})

const initials = computed(() => {
  const parts = form.name.trim().split(/\s+/).filter(Boolean)
  return parts.length >= 2
    ? (parts[0][0] + parts[1][0]).toUpperCase()
    : (parts[0]?.[0] || 'U').toUpperCase()
})

function triggerPhotoUpload() {
  photoInputRef.value?.click()
}

function handlePhotoChange(e) {
  const file = e.target.files[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = (ev) => {
    profilePhoto.value = ev.target.result
    localStorage.setItem('exobios_profile_photo', ev.target.result)
  }
  reader.readAsDataURL(file)
}

function removePhoto() {
  profilePhoto.value = ''
  localStorage.removeItem('exobios_profile_photo')
  if (photoInputRef.value) photoInputRef.value.value = ''
}

function saveProfile() {
  localStorage.setItem('exobios_profile_data', JSON.stringify({ ...form }))
  saved.value = true
  setTimeout(() => saved.value = false, 2500)
}

const roleOptions = ['ASHA Worker', 'ANM', 'Supervisor', 'Doctor', 'Admin']
</script>

<template>
  <AppShell>
    <template #page-title>{{ t('profile.title') }}</template>
    <template #page-subtitle>Manage your personal information and preferences</template>

    <div class="p-4 md:p-6 max-w-3xl mx-auto space-y-5">
      <!-- Back -->
      <button @click="router.push('/dashboard')"
        class="flex items-center gap-1.5 text-sm text-blue-600 hover:underline">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 5l-7 7 7 7"/></svg>
        {{ t('common.backToDashboard') }}
      </button>

      <!-- Profile photo + name banner -->
      <div class="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <!-- Banner -->
        <div class="h-24 md:h-28" style="background: linear-gradient(135deg, #1d4ed8 0%, #0ea5e9 100%)"></div>

        <div class="px-5 md:px-8 pb-6 relative">
          <!-- Avatar -->
          <div class="relative w-24 h-24 -mt-12 mb-4">
            <div class="w-24 h-24 rounded-full border-4 border-white bg-amber-200 flex items-center justify-center overflow-hidden shadow-md">
              <img v-if="profilePhoto" :src="profilePhoto" class="w-full h-full object-cover" alt="Profile"/>
              <span v-else class="text-2xl font-bold text-amber-700">{{ initials }}</span>
            </div>
            <button @click="triggerPhotoUpload"
              class="absolute bottom-0 right-0 w-8 h-8 bg-blue-600 hover:bg-blue-700 text-white rounded-full flex items-center justify-center shadow-md transition">
              <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>
                <circle cx="12" cy="13" r="4"/>
              </svg>
            </button>
            <input ref="photoInputRef" type="file" accept="image/*" class="hidden" @change="handlePhotoChange"/>
          </div>

          <div class="flex items-start justify-between flex-wrap gap-3">
            <div>
              <h2 class="text-xl font-bold text-gray-900">{{ form.name }}</h2>
              <p class="text-sm text-gray-500">{{ form.role }} · {{ form.area }}</p>
            </div>
            <div class="flex items-center gap-2">
              <button v-if="profilePhoto" @click="removePhoto"
                class="text-xs text-red-500 hover:text-red-700 border border-red-200 px-3 py-1.5 rounded-lg transition">
                Remove Photo
              </button>
              <button @click="triggerPhotoUpload"
                class="text-xs text-blue-600 border border-blue-200 px-3 py-1.5 rounded-lg hover:bg-blue-50 transition">
                {{ t('profile.changePhoto') }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Edit form -->
      <div class="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 md:p-8">
        <h3 class="font-semibold text-gray-800 mb-6 text-base">Personal Information</h3>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">
              {{ t('profile.fullName') }}
            </label>
            <input v-model="form.name" type="text"
              class="w-full border border-gray-200 rounded-xl px-3.5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"/>
          </div>

          <div>
            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">
              {{ t('profile.role') }}
            </label>
            <select v-model="form.role"
              class="w-full border border-gray-200 rounded-xl px-3.5 py-3 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition">
              <option v-for="r in roleOptions" :key="r">{{ r }}</option>
            </select>
          </div>

          <div>
            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">
              {{ t('profile.phone') }}
            </label>
            <input v-model="form.phone" type="tel"
              class="w-full border border-gray-200 rounded-xl px-3.5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition"/>
          </div>

          <div>
            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">
              {{ t('profile.ashaId') }}
            </label>
            <input v-model="form.ashaId" type="text"
              class="w-full border border-gray-200 rounded-xl px-3.5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition"/>
          </div>

          <div class="md:col-span-2">
            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">
              {{ t('profile.area') }}
            </label>
            <input v-model="form.area" type="text"
              class="w-full border border-gray-200 rounded-xl px-3.5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition"/>
          </div>

          <div class="md:col-span-2">
            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">
              {{ t('profile.email') }}
            </label>
            <input v-model="form.email" type="email"
              class="w-full border border-gray-200 rounded-xl px-3.5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition"/>
          </div>
        </div>

        <!-- Save -->
        <div class="mt-8 flex items-center gap-3">
          <button @click="saveProfile"
            class="flex items-center gap-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-xl transition">
            <svg v-if="!saved" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
            <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M20 6L9 17l-5-5"/></svg>
            {{ saved ? t('profile.saved') : t('profile.saveChanges') }}
          </button>
          <button @click="router.push('/dashboard')"
            class="px-5 py-2.5 border border-gray-200 text-gray-600 text-sm font-medium rounded-xl hover:bg-gray-50 transition">
            {{ t('common.cancel') }}
          </button>
        </div>
      </div>

      <!-- Identity card -->
      <div class="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 md:p-8">
        <h3 class="font-semibold text-gray-800 mb-4 text-base">ID Information</h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div class="bg-gray-50 rounded-xl p-4">
            <div class="text-xs text-gray-500 mb-1">ASHA Worker ID</div>
            <div class="text-sm font-bold text-gray-800 font-mono">{{ form.ashaId }}</div>
          </div>
          <div class="bg-gray-50 rounded-xl p-4">
            <div class="text-xs text-gray-500 mb-1">Account Status</div>
            <div class="flex items-center gap-2">
              <span class="w-2 h-2 rounded-full bg-green-500"></span>
              <span class="text-sm font-semibold text-green-600">Active</span>
            </div>
          </div>
          <div class="bg-gray-50 rounded-xl p-4">
            <div class="text-xs text-gray-500 mb-1">Joined</div>
            <div class="text-sm font-semibold text-gray-800">January 2023</div>
          </div>
          <div class="bg-gray-50 rounded-xl p-4">
            <div class="text-xs text-gray-500 mb-1">Last Login</div>
            <div class="text-sm font-semibold text-gray-800">Today, 9:45 AM</div>
          </div>
        </div>
      </div>
    </div>
  </AppShell>
</template>
