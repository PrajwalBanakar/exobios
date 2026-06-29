<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '@/shared/components/AppShell.vue'

const router = useRouter()

// ── Connection state ──────────────────────────────────────────────────────
// 'disconnected' | 'scanning' | 'connecting' | 'connected' | 'error'
const connectionState = ref('disconnected')
const connectedDevice = ref(null)
const errorMessage    = ref('')

const MOCK_DEVICES = [
  { id: 'dev-001', name: 'OMRON HEM-7121',       type: 'BP Monitor',      battery: 85, signal: 'strong' },
  { id: 'dev-002', name: 'iHealth Air PO3',       type: 'SpO2 / Pulse',    battery: 62, signal: 'medium' },
  { id: 'dev-003', name: 'AccuCheck Instant',     type: 'Glucometer',      battery: 40, signal: 'strong' },
  { id: 'dev-004', name: 'iHealth Thermometer',   type: 'Thermometer',     battery: 91, signal: 'weak'   },
]

const discoveredDevices = ref([])
const selectedDevice    = ref(null)

function startScan() {
  connectionState.value  = 'scanning'
  discoveredDevices.value = []
  selectedDevice.value    = null
  // Simulate BLE scan discovering devices one by one
  let i = 0
  const interval = setInterval(() => {
    if (i < MOCK_DEVICES.length) {
      discoveredDevices.value.push(MOCK_DEVICES[i])
      i++
    } else {
      clearInterval(interval)
      if (connectionState.value === 'scanning') connectionState.value = 'disconnected'
    }
  }, 600)
}

function selectDevice(dev) { selectedDevice.value = dev }

async function connectDevice() {
  if (!selectedDevice.value) return
  connectionState.value = 'connecting'
  await new Promise(r => setTimeout(r, 1400))
  connectedDevice.value = selectedDevice.value
  connectionState.value = 'connected'
  // Simulate first reading arriving
  startReading()
}

function disconnect() {
  connectionState.value = 'disconnected'
  connectedDevice.value = null
  discoveredDevices.value = []
  selectedDevice.value = null
  readings.bp.systolic = ''; readings.bp.diastolic = ''; readings.spo2 = ''; readings.heartRate = ''
  readings.temperature = ''; readings.glucose = ''
}

// ── Live readings ─────────────────────────────────────────────────────────
const readings = reactive({
  bp:          { systolic: '', diastolic: '' },
  spo2:        '',
  heartRate:   '',
  temperature: '',
  glucose:     '',
})
const readingTimestamp = ref(null)
const readingLoading   = ref(false)

function startReading() {
  readingLoading.value = true
  setTimeout(() => {
    // Mock readings based on device type
    const type = connectedDevice.value?.type || ''
    if (type.includes('BP')) { readings.bp.systolic = '122'; readings.bp.diastolic = '78'; readings.heartRate = '76' }
    if (type.includes('SpO2')) { readings.spo2 = '98'; readings.heartRate = '74' }
    if (type.includes('Gluco')) { readings.glucose = '94' }
    if (type.includes('Thermo')) { readings.temperature = '98.4' }
    readingTimestamp.value = new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true })
    readingLoading.value = false
  }, 1200)
}

function refreshReading() {
  readingLoading.value = true
  setTimeout(() => {
    if (connectedDevice.value?.type.includes('BP')) {
      readings.bp.systolic  = String(118 + Math.floor(Math.random() * 12))
      readings.bp.diastolic = String(74 + Math.floor(Math.random() * 8))
      readings.heartRate    = String(68 + Math.floor(Math.random() * 16))
    }
    if (connectedDevice.value?.type.includes('SpO2')) {
      readings.spo2      = String(96 + Math.floor(Math.random() * 4))
      readings.heartRate = String(68 + Math.floor(Math.random() * 16))
    }
    readingTimestamp.value = new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true })
    readingLoading.value = false
  }, 800)
}

// ── Manual entry fallback ─────────────────────────────────────────────────
const showManualEntry = ref(false)
const manual = reactive({ systolic: '', diastolic: '', spo2: '', heartRate: '', temperature: '', glucose: '' })

function applyManual() {
  if (manual.systolic)    readings.bp.systolic  = manual.systolic
  if (manual.diastolic)   readings.bp.diastolic = manual.diastolic
  if (manual.spo2)        readings.spo2         = manual.spo2
  if (manual.heartRate)   readings.heartRate    = manual.heartRate
  if (manual.temperature) readings.temperature  = manual.temperature
  if (manual.glucose)     readings.glucose      = manual.glucose
  readingTimestamp.value = new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true })
  showManualEntry.value = false
}

function useInAssessment() {
  // Build query params so NewAssessment can pre-fill vitals
  const q = new URLSearchParams()
  if (readings.bp.systolic)  q.set('bp_sys',  readings.bp.systolic)
  if (readings.bp.diastolic) q.set('bp_dia',  readings.bp.diastolic)
  if (readings.spo2)         q.set('spo2',    readings.spo2)
  if (readings.heartRate)    q.set('hr',      readings.heartRate)
  if (readings.temperature)  q.set('temp',    readings.temperature)
  if (readings.glucose)      q.set('rbs',     readings.glucose)
  router.push(`/assessment/new?${q.toString()}`)
}

const signalColor = (s) => s === 'strong' ? 'text-green-500' : s === 'medium' ? 'text-amber-500' : 'text-red-400'
const batteryColor = (b) => b > 60 ? 'text-green-500' : b > 30 ? 'text-amber-500' : 'text-red-500'
const hasAnyReading = computed(() =>
  readings.bp.systolic || readings.spo2 || readings.heartRate || readings.temperature || readings.glucose
)

const IC = 'w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500'
</script>

<template>
  <AppShell>
    <template #page-title>Device Integration</template>
    <template #page-subtitle>Connect a Bluetooth wearable or enter vitals manually</template>

    <div class="p-4 md:p-6 space-y-5 max-w-3xl mx-auto">

      <!-- Notice banner (placeholder) -->
      <div class="flex items-start gap-3 bg-blue-50 border border-blue-100 rounded-xl px-4 py-3.5">
        <svg class="w-4 h-4 text-blue-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="8.01"/><line x1="12" y1="12" x2="12" y2="16"/></svg>
        <p class="text-xs text-blue-700 leading-relaxed">
          <span class="font-semibold">Bluetooth pairing is a UI placeholder.</span>
          Full BLE integration with Web Bluetooth API will be enabled in the next release.
          Device readings shown here are simulated. Use <strong>Manual Entry</strong> to enter real vitals now.
        </p>
      </div>

      <!-- Connection card -->
      <div class="bg-white rounded-xl border border-gray-100 shadow-sm">
        <div class="px-5 py-4 border-b border-gray-100 flex items-center justify-between flex-wrap gap-3">
          <div>
            <h2 class="font-semibold text-gray-900">Bluetooth Device</h2>
            <p class="text-xs text-gray-400 mt-0.5">
              <span v-if="connectionState === 'disconnected'">No device connected</span>
              <span v-else-if="connectionState === 'scanning'" class="text-blue-500">Scanning for nearby devices…</span>
              <span v-else-if="connectionState === 'connecting'" class="text-amber-500">Connecting to {{ selectedDevice?.name }}…</span>
              <span v-else-if="connectionState === 'connected'" class="text-green-600">Connected · {{ connectedDevice?.name }}</span>
            </p>
          </div>
          <div class="flex items-center gap-2">
            <button v-if="connectionState === 'connected'" @click="disconnect"
              class="px-3 py-1.5 text-xs border border-red-200 text-red-600 rounded-lg hover:bg-red-50 transition">
              Disconnect
            </button>
            <button v-if="connectionState !== 'connected' && connectionState !== 'connecting'"
              @click="startScan"
              :disabled="connectionState === 'scanning'"
              class="flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white text-sm font-semibold rounded-lg transition">
              <svg v-if="connectionState === 'scanning'" class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 0 0 4.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 0 1-15.357-2m15.357 2H15"/>
              </svg>
              <svg v-else class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path d="M8.111 16.404a5.5 5.5 0 0 1 7.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0"/>
              </svg>
              {{ connectionState === 'scanning' ? 'Scanning…' : 'Scan for Devices' }}
            </button>
            <button v-if="connectionState === 'connecting'"
              class="flex items-center gap-1.5 px-4 py-2 bg-gray-100 text-gray-500 text-sm rounded-lg cursor-not-allowed">
              <svg class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 0 0 4.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 0 1-15.357-2m15.357 2H15"/>
              </svg>
              Connecting…
            </button>
          </div>
        </div>

        <!-- Discovered devices list -->
        <div v-if="discoveredDevices.length && connectionState !== 'connected'" class="divide-y divide-gray-50">
          <div v-for="dev in discoveredDevices" :key="dev.id"
            :class="['flex items-center gap-4 px-5 py-3.5 cursor-pointer transition hover:bg-gray-50', selectedDevice?.id === dev.id ? 'bg-blue-50' : '']"
            @click="selectDevice(dev)">
            <div class="w-10 h-10 rounded-xl bg-blue-100 flex items-center justify-center flex-shrink-0">
              <svg class="w-5 h-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
                <path d="M8.111 16.404a5.5 5.5 0 0 1 7.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0"/>
              </svg>
            </div>
            <div class="flex-1 min-w-0">
              <div class="text-sm font-semibold text-gray-800">{{ dev.name }}</div>
              <div class="text-xs text-gray-400">{{ dev.type }}</div>
            </div>
            <div class="flex items-center gap-3 text-xs">
              <span :class="['font-medium', signalColor(dev.signal)]">
                {{ dev.signal === 'strong' ? '●●●' : dev.signal === 'medium' ? '●●○' : '●○○' }}
              </span>
              <span :class="batteryColor(dev.battery)">{{ dev.battery }}%</span>
              <div v-if="selectedDevice?.id === dev.id" class="w-4 h-4 rounded-full bg-blue-600 flex items-center justify-center">
                <svg class="w-2.5 h-2.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path d="M20 6L9 17l-5-5"/></svg>
              </div>
            </div>
          </div>

          <div v-if="selectedDevice" class="px-5 py-3 flex justify-end">
            <button @click="connectDevice" class="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-lg transition">
              Connect to {{ selectedDevice.name }}
            </button>
          </div>
        </div>

        <!-- Empty / no devices found -->
        <div v-if="!discoveredDevices.length && connectionState === 'disconnected'" class="py-10 text-center px-5">
          <svg class="w-12 h-12 text-gray-200 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.2">
            <path d="M8.111 16.404a5.5 5.5 0 0 1 7.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0"/>
          </svg>
          <p class="text-sm text-gray-400">No devices paired yet.</p>
          <p class="text-xs text-gray-400 mt-1">Click "Scan for Devices" to discover nearby Bluetooth devices.</p>
        </div>
      </div>

      <!-- Connected device readings -->
      <div v-if="connectionState === 'connected'" class="bg-white rounded-xl border border-gray-100 shadow-sm">
        <div class="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
          <div>
            <h3 class="font-semibold text-gray-900">Live Readings</h3>
            <p v-if="readingTimestamp" class="text-xs text-gray-400">Last read at {{ readingTimestamp }}</p>
          </div>
          <button @click="refreshReading" :disabled="readingLoading"
            class="flex items-center gap-1.5 px-3 py-1.5 border border-gray-200 text-gray-600 text-xs rounded-lg hover:bg-gray-50 transition disabled:opacity-50">
            <svg :class="['w-3.5 h-3.5', readingLoading ? 'animate-spin' : '']" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
              <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 0 0 4.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 0 1-15.357-2m15.357 2H15"/>
            </svg>
            Refresh
          </button>
        </div>

        <div v-if="readingLoading" class="py-10 flex items-center justify-center gap-2 text-sm text-blue-600">
          <svg class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 0 0 4.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 0 1-15.357-2m15.357 2H15"/>
          </svg>
          Reading from device…
        </div>

        <div v-else class="p-5 grid grid-cols-2 sm:grid-cols-3 gap-4">
          <div v-if="readings.bp.systolic" class="bg-red-50 rounded-xl p-4 text-center">
            <div class="text-2xl font-bold text-red-600">{{ readings.bp.systolic }}/{{ readings.bp.diastolic }}</div>
            <div class="text-xs text-red-400 mt-1 font-medium">Blood Pressure (mmHg)</div>
          </div>
          <div v-if="readings.spo2" class="bg-blue-50 rounded-xl p-4 text-center">
            <div class="text-2xl font-bold text-blue-600">{{ readings.spo2 }}<span class="text-base">%</span></div>
            <div class="text-xs text-blue-400 mt-1 font-medium">SpO₂</div>
          </div>
          <div v-if="readings.heartRate" class="bg-pink-50 rounded-xl p-4 text-center">
            <div class="text-2xl font-bold text-pink-600">{{ readings.heartRate }}</div>
            <div class="text-xs text-pink-400 mt-1 font-medium">Heart Rate (bpm)</div>
          </div>
          <div v-if="readings.temperature" class="bg-amber-50 rounded-xl p-4 text-center">
            <div class="text-2xl font-bold text-amber-600">{{ readings.temperature }}<span class="text-base">°F</span></div>
            <div class="text-xs text-amber-400 mt-1 font-medium">Temperature</div>
          </div>
          <div v-if="readings.glucose" class="bg-green-50 rounded-xl p-4 text-center">
            <div class="text-2xl font-bold text-green-600">{{ readings.glucose }}</div>
            <div class="text-xs text-green-400 mt-1 font-medium">Blood Glucose (mg/dL)</div>
          </div>
          <div v-if="!hasAnyReading" class="col-span-full py-6 text-center text-sm text-gray-400">
            Waiting for readings…
          </div>
        </div>

        <div v-if="hasAnyReading && !readingLoading" class="px-5 pb-5">
          <button @click="useInAssessment"
            class="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-xl transition flex items-center justify-center gap-2">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M12 5v14M5 12h14"/></svg>
            Use These Readings in New Assessment
          </button>
        </div>
      </div>

      <!-- Manual Entry Fallback -->
      <div class="bg-white rounded-xl border border-gray-100 shadow-sm">
        <button
          class="w-full flex items-center justify-between px-5 py-4 text-left"
          @click="showManualEntry = !showManualEntry">
          <div>
            <h3 class="font-semibold text-gray-900">Manual Entry</h3>
            <p class="text-xs text-gray-400 mt-0.5">Enter vitals directly without a device</p>
          </div>
          <svg :class="['w-4 h-4 text-gray-400 transition-transform', showManualEntry ? 'rotate-180' : '']"
            fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M19 9l-7 7-7-7"/></svg>
        </button>

        <div v-if="showManualEntry" class="px-5 pb-5 border-t border-gray-100 pt-4 space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1.5">BP Systolic (mmHg)</label>
              <input v-model="manual.systolic" type="number" min="60" max="200" placeholder="e.g. 120" :class="IC"/>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1.5">BP Diastolic (mmHg)</label>
              <input v-model="manual.diastolic" type="number" min="40" max="140" placeholder="e.g. 80" :class="IC"/>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1.5">SpO₂ (%)</label>
              <input v-model="manual.spo2" type="number" min="80" max="100" placeholder="e.g. 98" :class="IC"/>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1.5">Heart Rate (bpm)</label>
              <input v-model="manual.heartRate" type="number" min="40" max="200" placeholder="e.g. 72" :class="IC"/>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1.5">Temperature (°F)</label>
              <input v-model="manual.temperature" type="number" step="0.1" min="94" max="107" placeholder="e.g. 98.6" :class="IC"/>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1.5">Blood Glucose (mg/dL)</label>
              <input v-model="manual.glucose" type="number" min="40" max="600" placeholder="e.g. 90" :class="IC"/>
            </div>
          </div>
          <div class="flex gap-3">
            <button @click="applyManual"
              class="flex-1 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-lg transition">
              Apply Readings
            </button>
            <button @click="useInAssessment"
              class="flex-1 py-2.5 border border-blue-200 text-blue-600 hover:bg-blue-50 text-sm font-semibold rounded-lg transition">
              Use in Assessment
            </button>
          </div>
        </div>
      </div>

      <!-- Supported device types -->
      <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
        <h3 class="font-semibold text-gray-900 mb-4">Supported Devices <span class="text-xs font-normal text-gray-400">(coming soon)</span></h3>
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div v-for="d in [
            { icon: '🩺', label: 'BP Monitor', desc: 'Systolic/diastolic, HR' },
            { icon: '🫀', label: 'Pulse Oximeter', desc: 'SpO₂, Heart Rate' },
            { icon: '🌡', label: 'Thermometer', desc: 'Body temperature' },
            { icon: '🩸', label: 'Glucometer', desc: 'Blood glucose (RBS)' },
          ]" :key="d.label" class="border border-gray-100 rounded-xl p-3 text-center hover:border-blue-200 transition cursor-default">
            <div class="text-2xl mb-1.5">{{ d.icon }}</div>
            <div class="text-xs font-semibold text-gray-800">{{ d.label }}</div>
            <div class="text-[10px] text-gray-400 mt-0.5">{{ d.desc }}</div>
          </div>
        </div>
      </div>

    </div>
  </AppShell>
</template>
