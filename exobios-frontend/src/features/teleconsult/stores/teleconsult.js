import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const SAMPLE_SESSIONS = [
  { id: 1, patientName: 'Priya Sharma',   doctor: 'Dr. Anjali Sharma', spec: 'General Physician', ashaWorker: 'Sunita Devi', status: 'Scheduled', date: '15 Jun 2025, 03:00 PM', duration: null,  advice: '' },
  { id: 2, patientName: 'Rajesh Kumar',   doctor: 'Dr. Vivek Singh',   spec: 'Cardiologist',       ashaWorker: 'Meena Rani',  status: 'Completed', date: '14 Jun 2025, 11:00 AM', duration: 22,   advice: 'Continue medication. Monitor BP daily.' },
  { id: 3, patientName: 'Mohammed Iqbal', doctor: 'Dr. Neha Verma',    spec: 'Diabetologist',      ashaWorker: 'Anita Singh', status: 'Completed', date: '12 Jun 2025, 02:30 PM', duration: 18,   advice: 'Adjust insulin dose as discussed.' },
  { id: 4, patientName: 'Sunita Verma',   doctor: 'Dr. Anjali Sharma', spec: 'General Physician', ashaWorker: 'Sunita Devi', status: 'Cancelled', date: '11 Jun 2025, 10:00 AM', duration: null,  advice: '' },
  { id: 5, patientName: 'Anita Devi',     doctor: 'Dr. Vivek Singh',   spec: 'Cardiologist',       ashaWorker: 'Meena Rani',  status: 'Scheduled', date: '16 Jun 2025, 04:00 PM', duration: null,  advice: '' },
]

export const useTeleconsultStore = defineStore('teleconsult', () => {
  const items = ref([...SAMPLE_SESSIONS])

  const scheduledCount = computed(() => items.value.filter(s => s.status === 'Scheduled').length)
  const completedCount = computed(() => items.value.filter(s => s.status === 'Completed').length)
  const avgDuration    = computed(() => {
    const completed = items.value.filter(s => s.duration)
    return completed.length ? Math.round(completed.reduce((s, i) => s + i.duration, 0) / completed.length) : 0
  })

  function add(data) {
    const maxId = items.value.reduce((m, s) => Math.max(m, s.id), 0)
    items.value.unshift({
      id: maxId + 1,
      date: new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }),
      ...data,
    })
  }

  function updateStatus(id, status) {
    const s = items.value.find(s => s.id === id)
    if (s) s.status = status
  }

  return { items, scheduledCount, completedCount, avgDuration, add, updateStatus }
})
