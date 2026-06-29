import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const SAMPLE_REFERRALS = [
  { id: 1, patientName: 'Priya Sharma',   hospital: 'Rampur Community Health Center', type: 'Government', transport: 'Ambulance',       status: 'Pending',   ashaWorker: 'Sunita Devi',  date: '15 Jun 2025', notes: 'High fever, possible dengue' },
  { id: 2, patientName: 'Rajesh Kumar',   hospital: 'Sharma Hospital',               type: 'Private',    transport: 'Private Vehicle', status: 'Confirmed', ashaWorker: 'Meena Rani',   date: '14 Jun 2025', notes: 'Diabetes follow-up' },
  { id: 3, patientName: 'Mohammed Iqbal', hospital: 'City Care Hospital',            type: 'Private',    transport: 'Govt. Vehicle',   status: 'Completed', ashaWorker: 'Anita Singh',  date: '12 Jun 2025', notes: 'Cardiac evaluation needed' },
  { id: 4, patientName: 'Sunita Verma',   hospital: 'District Hospital Lakhimpur',   type: 'Government', transport: 'Ambulance',       status: 'Pending',   ashaWorker: 'Sunita Devi',  date: '11 Jun 2025', notes: 'Maternal health check-up' },
  { id: 5, patientName: 'Anita Devi',     hospital: 'Bhira PHC',                     type: 'Government', transport: 'Walking',         status: 'Confirmed', ashaWorker: 'Meena Rani',   date: '10 Jun 2025', notes: 'Regular follow-up' },
]

export const useReferralsStore = defineStore('referrals', () => {
  const items = ref([...SAMPLE_REFERRALS])

  const govCount     = computed(() => items.value.filter(r => r.type === 'Government').length)
  const privateCount = computed(() => items.value.filter(r => r.type === 'Private').length)

  function add(data) {
    const maxId = items.value.reduce((m, r) => Math.max(m, r.id), 0)
    items.value.unshift({
      id: maxId + 1,
      type: 'Government',
      status: 'Pending',
      date: new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }),
      ...data,
    })
  }

  return { items, govCount, privateCount, add }
})
