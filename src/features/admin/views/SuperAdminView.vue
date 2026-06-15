<script setup>
import { ref, computed, reactive } from 'vue'
import AppShell from '@/shared/components/AppShell.vue'
import { useI18n } from '@/i18n'
import { useAuthStore } from '@/features/auth/stores/auth'

const { t } = useI18n()
const auth  = useAuthStore()

const USERS_KEY      = 'exobios_admin_users'
const ROLES          = ['ASHA Worker', 'ANM', 'Doctor', 'Supervisor', 'Admin', 'Hospital Staff', 'Super Admin']
const STATUS_OPTIONS = ['Active', 'Inactive', 'Suspended']

function seedUsers() {
  return [
    { id: 1, name: 'Sunita Devi',       email: 'sunita@asha.in',      phone: '9876543210', role: 'ASHA Worker',    status: 'Active',   lastLogin: '8 Jun 2025' },
    { id: 2, name: 'Kavita Sharma',     email: 'kavita@asha.in',      phone: '9876543211', role: 'ASHA Worker',    status: 'Active',   lastLogin: '7 Jun 2025' },
    { id: 3, name: 'Meena Kumari',      email: 'meena@anm.in',        phone: '9876543212', role: 'ANM',            status: 'Active',   lastLogin: '6 Jun 2025' },
    { id: 4, name: 'Dr. Anjali Sharma', email: 'anjali@doctor.in',    phone: '9876543213', role: 'Doctor',         status: 'Active',   lastLogin: '8 Jun 2025' },
    { id: 5, name: 'Dr. Vivek Singh',   email: 'vivek@doctor.in',     phone: '9876543214', role: 'Doctor',         status: 'Active',   lastLogin: '5 Jun 2025' },
    { id: 6, name: 'Rajesh Gupta',      email: 'rajesh@admin.in',     phone: '9876543215', role: 'Admin',          status: 'Active',   lastLogin: '8 Jun 2025' },
    { id: 7, name: 'Priya Singh',       email: 'priya@hospital.in',   phone: '9876543216', role: 'Hospital Staff', status: 'Inactive', lastLogin: '1 Jun 2025' },
    { id: 8, name: 'Vinod Kumar',       email: 'vinod@supervisor.in', phone: '9876543217', role: 'Supervisor',     status: 'Active',   lastLogin: '7 Jun 2025' },
  ]
}

function loadUsers()    { try { const s = localStorage.getItem(USERS_KEY); const p = s ? JSON.parse(s) : null; return p?.length ? p : seedUsers() } catch { return seedUsers() } }
function saveUsers(list){ localStorage.setItem(USERS_KEY, JSON.stringify(list)) }

const users       = ref(loadUsers())
const searchQuery = ref('')
const roleFilter  = ref('All')
const showModal   = ref(false)
const isEditing   = ref(false)
const deleteId    = ref(null)
const toast       = ref('')
const sortKey     = ref('name')
const sortDir     = ref('asc')

const form = reactive({ id: null, name: '', email: '', phone: '', role: 'ASHA Worker', status: 'Active' })

function toggleSort(key) {
  if (sortKey.value === key) sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  else { sortKey.value = key; sortDir.value = 'asc' }
}

const filtered = computed(() => {
  let list = users.value
  if (roleFilter.value !== 'All') list = list.filter(u => u.role === roleFilter.value)
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase()
    list = list.filter(u => u.name.toLowerCase().includes(q) || u.email.toLowerCase().includes(q) || u.phone.includes(q))
  }
  return [...list].sort((a, b) => {
    const va = a[sortKey.value] ?? '', vb = b[sortKey.value] ?? ''
    return sortDir.value === 'asc' ? String(va).localeCompare(String(vb)) : String(vb).localeCompare(String(va))
  })
})

const roleCount = computed(() => Object.fromEntries(ROLES.map(r => [r, users.value.filter(u => u.role === r).length])))

function openAdd()       { isEditing.value = false; Object.assign(form, { id: null, name: '', email: '', phone: '', role: 'ASHA Worker', status: 'Active' }); showModal.value = true }
function openEdit(user)  { isEditing.value = true;  Object.assign(form, { ...user }); showModal.value = true }

function saveUser() {
  if (!form.name.trim() || !form.email.trim()) return
  if (isEditing.value) {
    const idx = users.value.findIndex(u => u.id === form.id)
    if (idx !== -1) users.value[idx] = { ...form }
    showToast('User updated successfully')
  } else {
    const newId = users.value.length ? Math.max(...users.value.map(u => u.id)) + 1 : 1
    users.value.push({ ...form, id: newId, lastLogin: '—' })
    showToast(t('admin.addUser') + ' successful')
  }
  saveUsers(users.value)
  showModal.value = false
}

function confirmDelete(id) { deleteId.value = id }
function deleteUser() {
  users.value = users.value.filter(u => u.id !== deleteId.value)
  saveUsers(users.value)
  deleteId.value = null
  showToast('User deleted')
}
function showToast(msg) { toast.value = msg; setTimeout(() => { toast.value = '' }, 2500) }

const statusColor = (s) => s === 'Active' ? 'bg-green-100 text-green-700' : s === 'Inactive' ? 'bg-gray-100 text-gray-500' : 'bg-red-100 text-red-600'
const roleColor   = (r) => ({ 'ASHA Worker': 'bg-blue-100 text-blue-700', 'ANM': 'bg-cyan-100 text-cyan-700', 'Doctor': 'bg-purple-100 text-purple-700', 'Supervisor': 'bg-amber-100 text-amber-700', 'Admin': 'bg-orange-100 text-orange-700', 'Hospital Staff': 'bg-teal-100 text-teal-700', 'Super Admin': 'bg-red-100 text-red-700' }[r] || 'bg-gray-100 text-gray-600')
const sortIcon    = (key) => sortKey.value === key ? (sortDir.value === 'asc' ? '↑' : '↓') : '↕'
</script>

<template>
  <AppShell>
    <template #page-title>{{ t('admin.title') }}</template>
    <template #page-subtitle>{{ t('admin.subtitle') }}</template>

    <div class="p-4 md:p-6 space-y-5">

      <!-- Toast -->
      <transition enter-active-class="transition-all duration-300" enter-from-class="opacity-0 -translate-y-2" leave-active-class="transition-all duration-200" leave-to-class="opacity-0">
        <div v-if="toast" class="bg-green-50 border border-green-200 text-green-700 rounded-xl px-5 py-3 flex items-center gap-2 font-medium text-sm">
          <svg class="w-5 h-5 text-green-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg>
          {{ toast }}
        </div>
      </transition>

      <!-- Role summary cards (clickable filter) -->
      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
        <div v-for="role in ROLES.filter(r=>r!=='Super Admin')" :key="role"
          :class="['bg-white rounded-xl border border-gray-100 shadow-sm p-3 flex items-center gap-3 cursor-pointer transition hover:shadow-md', roleFilter===role ? 'ring-2 ring-blue-400' : '']"
          @click="roleFilter = roleFilter === role ? 'All' : role">
          <div class="w-9 h-9 rounded-full bg-gray-100 flex items-center justify-center flex-shrink-0">
            <svg class="w-4 h-4 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/></svg>
          </div>
          <div>
            <div class="text-lg font-bold text-gray-900">{{ roleCount[role] }}</div>
            <div class="text-[11px] text-gray-500 leading-tight">{{ role }}</div>
          </div>
        </div>
      </div>

      <!-- Main table card -->
      <div class="bg-white rounded-xl border border-gray-100 shadow-sm">
        <!-- Toolbar -->
        <div class="flex items-center justify-between gap-3 px-5 py-4 border-b border-gray-100 flex-wrap">
          <div class="flex items-center gap-2 flex-1 min-w-0">
            <div class="relative flex-1 max-w-xs">
              <svg class="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
              <input v-model="searchQuery" type="text" placeholder="Search users…" class="pl-9 pr-3 py-2 w-full text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"/>
            </div>
            <select v-model="roleFilter" class="text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white">
              <option value="All">{{ t('admin.allRoles') }}</option>
              <option v-for="r in ROLES" :key="r" :value="r">{{ r }}</option>
            </select>
          </div>
          <button @click="openAdd" class="flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-lg transition flex-shrink-0">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M12 5v14M5 12h14"/></svg>
            {{ t('admin.addUser') }}
          </button>
        </div>

        <div v-if="filtered.length === 0" class="py-16 text-center">
          <svg class="w-12 h-12 text-gray-200 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.2"><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/></svg>
          <p class="text-sm text-gray-500">No users found</p>
        </div>

        <div v-else class="overflow-x-auto">
          <!-- Desktop table -->
          <table class="w-full text-sm hidden md:table">
            <thead class="bg-gray-50 text-xs text-gray-500 font-medium">
              <tr>
                <th v-for="col in [{ key:'name', label:'Name' }, { key:'email', label:t('admin.email') }, { key:'phone', label:t('admin.phone') }, { key:'role', label:t('admin.roles') }, { key:'status', label:t('admin.status') }, { key:'lastLogin', label:t('admin.lastLogin') }]" :key="col.key"
                  class="px-4 py-3 text-left cursor-pointer hover:text-gray-700 select-none"
                  @click="toggleSort(col.key)">
                  <span class="flex items-center gap-1">{{ col.label }} <span class="text-gray-400">{{ sortIcon(col.key) }}</span></span>
                </th>
                <th class="px-4 py-3 text-left">{{ t('admin.actions') }}</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-50">
              <tr v-for="user in filtered" :key="user.id" class="hover:bg-gray-50 transition">
                <td class="px-4 py-3">
                  <div class="flex items-center gap-2.5">
                    <div class="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-xs font-semibold text-blue-700 flex-shrink-0">
                      {{ user.name.split(' ').map(n=>n[0]).join('').slice(0,2).toUpperCase() }}
                    </div>
                    <span class="font-medium text-gray-800">{{ user.name }}</span>
                  </div>
                </td>
                <td class="px-4 py-3 text-gray-600">{{ user.email }}</td>
                <td class="px-4 py-3 text-gray-600">{{ user.phone }}</td>
                <td class="px-4 py-3"><span :class="[roleColor(user.role), 'px-2 py-0.5 text-xs font-medium rounded-full']">{{ user.role }}</span></td>
                <td class="px-4 py-3"><span :class="[statusColor(user.status), 'px-2 py-0.5 text-xs font-medium rounded-full']">{{ user.status }}</span></td>
                <td class="px-4 py-3 text-gray-500 text-xs">{{ user.lastLogin }}</td>
                <td class="px-4 py-3">
                  <div class="flex items-center gap-2">
                    <button @click="openEdit(user)" class="p-1.5 text-blue-600 hover:bg-blue-50 rounded-lg transition">
                      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                    </button>
                    <button @click="confirmDelete(user.id)" class="p-1.5 text-red-500 hover:bg-red-50 rounded-lg transition">
                      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4h6v2"/></svg>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>

          <!-- Mobile list -->
          <div class="md:hidden divide-y divide-gray-50">
            <div v-for="user in filtered" :key="user.id" class="px-4 py-4">
              <div class="flex items-start gap-3">
                <div class="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-sm font-semibold text-blue-700 flex-shrink-0">
                  {{ user.name.split(' ').map(n=>n[0]).join('').slice(0,2).toUpperCase() }}
                </div>
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2 flex-wrap">
                    <span class="font-medium text-gray-800 text-sm">{{ user.name }}</span>
                    <span :class="[roleColor(user.role), 'px-2 py-0.5 text-xs font-medium rounded-full']">{{ user.role }}</span>
                    <span :class="[statusColor(user.status), 'px-2 py-0.5 text-xs font-medium rounded-full']">{{ user.status }}</span>
                  </div>
                  <div class="text-xs text-gray-500 mt-0.5">{{ user.email }}</div>
                  <div class="text-xs text-gray-400">{{ user.phone }}</div>
                </div>
                <div class="flex gap-1">
                  <button @click="openEdit(user)" class="p-1.5 text-blue-600 hover:bg-blue-50 rounded-lg transition">
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                  </button>
                  <button @click="confirmDelete(user.id)" class="p-1.5 text-red-500 hover:bg-red-50 rounded-lg transition">
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4h6v2"/></svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="filtered.length" class="px-5 py-3 border-t border-gray-100 text-xs text-gray-400">
          Showing {{ filtered.length }} of {{ users.length }} users
        </div>
      </div>
    </div>

    <!-- Add/Edit Modal + Delete Confirm -->
    <teleport to="body">
      <div v-if="showModal" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" @click.self="showModal=false">
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md">
          <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
            <h3 class="font-semibold text-gray-900 text-lg">{{ isEditing ? t('admin.editUser') : t('admin.addUser') }}</h3>
            <button @click="showModal=false" class="text-gray-400 hover:text-gray-600 p-1">
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18M6 6l12 12"/></svg>
            </button>
          </div>
          <div class="px-6 py-5 space-y-4">
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">Name <span class="text-red-500">*</span></label>
              <input v-model="form.name" type="text" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"/>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">{{ t('admin.email') }} <span class="text-red-500">*</span></label>
              <input v-model="form.email" type="email" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"/>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">{{ t('admin.phone') }}</label>
              <input v-model="form.phone" type="tel" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"/>
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">{{ t('admin.roles') }}</label>
                <select v-model="form.role" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white">
                  <option v-for="r in ROLES" :key="r" :value="r">{{ r }}</option>
                </select>
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">{{ t('admin.status') }}</label>
                <select v-model="form.status" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white">
                  <option v-for="s in STATUS_OPTIONS" :key="s" :value="s">{{ s }}</option>
                </select>
              </div>
            </div>
          </div>
          <div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-100">
            <button @click="showModal=false" class="px-4 py-2 text-sm border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50">{{ t('common.cancel') }}</button>
            <button @click="saveUser" :disabled="!form.name.trim() || !form.email.trim()"
              class="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed">
              {{ isEditing ? t('common.save') : t('admin.addUser') }}
            </button>
          </div>
        </div>
      </div>

      <div v-if="deleteId !== null" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" @click.self="deleteId=null">
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-sm p-6 text-center">
          <div class="w-14 h-14 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg class="w-7 h-7 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4h6v2"/></svg>
          </div>
          <h3 class="font-semibold text-gray-900 text-lg mb-1">Delete User</h3>
          <p class="text-sm text-gray-500 mb-5">This action cannot be undone. The user will be permanently removed.</p>
          <div class="flex gap-3">
            <button @click="deleteId=null" class="flex-1 py-2 text-sm border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50">Cancel</button>
            <button @click="deleteUser" class="flex-1 py-2 text-sm bg-red-600 hover:bg-red-700 text-white font-semibold rounded-lg transition">Delete</button>
          </div>
        </div>
      </div>
    </teleport>
  </AppShell>
</template>
