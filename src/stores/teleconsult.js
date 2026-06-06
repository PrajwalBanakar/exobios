import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const SAMPLE = [
  { id: 1, patientId: 1, patientName: 'Ramesh Kumar', doctor: 'Dr. Anjali Sharma', spec: 'General Physician', date: '20 May 2025, 11:00 AM', duration: 18, status: 'Completed', ashaWorker: 'Sunita Devi', advice: 'Paracetamol 650mg TDS, rest and fluids, CBC test advised' },
  { id: 2, patientId: 2, patientName: 'Savitri Devi', doctor: 'Dr. Vivek Singh', spec: 'Physician', date: '20 May 2025, 02:30 PM', duration: null, status: 'Scheduled', ashaWorker: 'Sunita Devi', advice: '' },
  { id: 3, patientId: 4, patientName: 'Pooja Kumari', doctor: 'Dr. Neha Verma', spec: 'General Physician', date: '20 May 2025, 09:45 AM', duration: 12, status: 'Completed', ashaWorker: 'Kavita Sharma', advice: 'Referred to OB-GYN for further evaluation' },
  { id: 4, patientId: 5, patientName: 'Harish Yadav', doctor: 'Dr. Anjali Sharma', spec: 'General Physician', date: '21 May 2025, 10:00 AM', duration: null, status: 'Scheduled', ashaWorker: 'Meena Kumari', advice: '' },
  { id: 5, patientId: 3, patientName: 'Mukesh Singh', doctor: 'Dr. Vivek Singh', spec: 'Physician', date: '18 May 2025, 03:00 PM', duration: 8, status: 'Cancelled', ashaWorker: 'Sunita Devi', advice: '' },
]

export const useTeleconsultStore = defineStore('teleconsult', () => {
  const stored = localStorage.getItem('exobios_teleconsult')
  const items = ref(stored ? JSON.parse(stored) : SAMPLE)

  function persist() {
    localStorage.setItem('exobios_teleconsult', JSON.stringify(items.value))
  }

  function add(data) {
    const newId = items.value.length ? Math.max(...items.value.map(s => s.id)) + 1 : 1
    const now = new Date()
    const dateStr = now.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) +
      ', ' + now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true })
    items.value.unshift({ id: newId, date: dateStr, status: 'Scheduled', duration: null, ...data })
    persist()
    return newId
  }

  function updateStatus(id, status, duration = null) {
    const item = items.value.find(s => s.id === id)
    if (item) {
      item.status = status
      if (duration !== null) item.duration = duration
      persist()
    }
  }

  const scheduledCount  = computed(() => items.value.filter(s => s.status === 'Scheduled').length)
  const completedCount  = computed(() => items.value.filter(s => s.status === 'Completed').length)
  const avgDuration     = computed(() => {
    const done = items.value.filter(s => s.duration)
    return done.length ? Math.round(done.reduce((a, s) => a + s.duration, 0) / done.length) : 0
  })

  return { items, add, updateStatus, scheduledCount, completedCount, avgDuration }
})
