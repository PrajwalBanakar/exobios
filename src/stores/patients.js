import { defineStore } from 'pinia'
import { ref } from 'vue'

const DEFAULT_PATIENTS = [
  { id: 1, initials: 'RK', name: 'Ramesh Kumar',  age: 45, gender: 'Male',   phone: '9876543210', location: 'Rampur, Uttar Pradesh - 244901', village: 'Rampur', risk: 'High',     date: '20 May 2025, 10:30 AM', assessmentTime: '20 May 2025, 10:30 AM', abhaId: '' },
  { id: 2, initials: 'SD', name: 'Savitri Devi',  age: 32, gender: 'Female', phone: '9876543211', location: 'Bhelwa, Uttar Pradesh - 244925', village: 'Bhelwa', risk: 'High',     date: '20 May 2025, 09:45 AM', assessmentTime: '20 May 2025, 09:45 AM', abhaId: '' },
  { id: 3, initials: 'MS', name: 'Mukesh Singh',  age: 60, gender: 'Male',   phone: '9876543212', location: 'Rampur, Uttar Pradesh - 244901', village: 'Rampur', risk: 'Low',      date: '20 May 2025, 09:20 AM', assessmentTime: '20 May 2025, 09:20 AM', abhaId: '' },
  { id: 4, initials: 'PK', name: 'Pooja Kumari',  age: 28, gender: 'Female', phone: '9876543213', location: 'Bhelwa, Uttar Pradesh - 244925', village: 'Bhelwa', risk: 'Moderate', date: '20 May 2025, 08:50 AM', assessmentTime: '20 May 2025, 08:50 AM', abhaId: '' },
  { id: 5, initials: 'HY', name: 'Harish Yadav',  age: 50, gender: 'Male',   phone: '9876543214', location: 'Rampur, Uttar Pradesh - 244901', village: 'Rampur', risk: 'High',     date: '20 May 2025, 08:15 AM', assessmentTime: '20 May 2025, 08:15 AM', abhaId: '' },
]

export const usePatientsStore = defineStore('patients', () => {
  const saved = localStorage.getItem('exobios_patients')
  const patients = ref(saved ? JSON.parse(saved) : DEFAULT_PATIENTS)

  function persist() {
    localStorage.setItem('exobios_patients', JSON.stringify(patients.value))
  }

  function getById(id) {
    return patients.value.find(p => p.id === Number(id)) || null
  }

  function update(id, data) {
    const idx = patients.value.findIndex(p => p.id === Number(id))
    if (idx !== -1) {
      patients.value[idx] = { ...patients.value[idx], ...data }
      persist()
    }
  }

  function remove(id) {
    patients.value = patients.value.filter(p => p.id !== Number(id))
    persist()
  }

  function add(data) {
    const newId = patients.value.length ? Math.max(...patients.value.map(p => p.id)) + 1 : 1
    const words = (data.name || '').trim().split(/\s+/).filter(Boolean)
    const initials = words.length >= 2
      ? (words[0][0] + words[1][0]).toUpperCase()
      : (words[0]?.[0] || 'P').toUpperCase()
    const now = new Date()
    const dateStr = now.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) +
      ', ' + now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true })
    const newPatient = { id: newId, initials, risk: 'Moderate', date: dateStr, ...data }
    patients.value.unshift(newPatient)
    persist()
    return newId
  }

  return { patients, getById, update, remove, add }
})
