import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const SAMPLE = [
  { id: 1, patientId: 1, patientName: 'Ramesh Kumar', hospital: 'Rampur Community Health Center', transport: 'Ambulance', date: '20 May 2025, 10:45 AM', status: 'Completed', ashaWorker: 'Sunita Devi', notes: 'Dengue suspected, referred urgently' },
  { id: 2, patientId: 2, patientName: 'Savitri Devi', hospital: 'Sharma Hospital', transport: 'Private Vehicle', date: '20 May 2025, 09:55 AM', status: 'Pending', ashaWorker: 'Sunita Devi', notes: 'High fever, possible dengue' },
  { id: 3, patientId: 4, patientName: 'Pooja Kumari', hospital: 'City Care Hospital', transport: 'Govt. Vehicle', date: '20 May 2025, 09:10 AM', status: 'Accepted', ashaWorker: 'Kavita Sharma', notes: '' },
  { id: 4, patientId: 5, patientName: 'Harish Yadav', hospital: 'Rampur Community Health Center', transport: 'Ambulance', date: '19 May 2025, 04:30 PM', status: 'Completed', ashaWorker: 'Meena Kumari', notes: 'Cardiac concern, urgent referral' },
  { id: 5, patientId: 3, patientName: 'Mukesh Singh', hospital: 'Sharma Hospital', transport: 'Private Vehicle', date: '19 May 2025, 11:00 AM', status: 'Rejected', ashaWorker: 'Sunita Devi', notes: 'Low risk, managed at home' },
]

export const useReferralsStore = defineStore('referrals', () => {
  const stored = localStorage.getItem('exobios_referrals')
  const items = ref(stored ? JSON.parse(stored) : SAMPLE)

  function persist() {
    localStorage.setItem('exobios_referrals', JSON.stringify(items.value))
  }

  function add(data) {
    const newId = items.value.length ? Math.max(...items.value.map(r => r.id)) + 1 : 1
    const now = new Date()
    const dateStr = now.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) +
      ', ' + now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true })
    items.value.unshift({ id: newId, date: dateStr, status: 'Pending', ...data })
    persist()
    return newId
  }

  function updateStatus(id, status) {
    const item = items.value.find(r => r.id === id)
    if (item) { item.status = status; persist() }
  }

  const pendingCount   = computed(() => items.value.filter(r => r.status === 'Pending').length)
  const acceptedCount  = computed(() => items.value.filter(r => r.status === 'Accepted').length)
  const completedCount = computed(() => items.value.filter(r => r.status === 'Completed').length)

  return { items, add, updateStatus, pendingCount, acceptedCount, completedCount }
})
