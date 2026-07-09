import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const SAMPLE_REFERRALS = [
  { id: 1, patientName: 'Priya Sharma',   hospital: 'Rampur Community Health Center', type: 'Government', transport: 'Ambulance',       status: 'Pending',   ashaWorker: 'Sunita Devi',  date: '15 Jun 2025', notes: 'High fever, possible dengue',
    reviewStage: 'CREATED', assignedDoctorId: null, doctorRecommendation: '', clinicalNotes: [], patientId: 1, assessmentIndex: 0 },
  { id: 2, patientName: 'Rajesh Kumar',   hospital: 'Sharma Hospital',               type: 'Private',    transport: 'Private Vehicle', status: 'Confirmed', ashaWorker: 'Meena Rani',   date: '14 Jun 2025', notes: 'Diabetes follow-up',
    reviewStage: 'ASSIGNED_TO_DOCTOR', assignedDoctorId: 'demo.doctor', doctorRecommendation: '', clinicalNotes: [], patientId: 2, assessmentIndex: 0 },
  { id: 3, patientName: 'Mohammed Iqbal', hospital: 'City Care Hospital',            type: 'Private',    transport: 'Govt. Vehicle',   status: 'Completed', ashaWorker: 'Anita Singh',  date: '12 Jun 2025', notes: 'Cardiac evaluation needed',
    reviewStage: 'UNDER_REVIEW', assignedDoctorId: 'demo.doctor', doctorRecommendation: '',
    clinicalNotes: [{ id: 1, text: 'Reviewed vitals — BP elevated, ordering ECG.', author: 'Demo Doctor', createdAt: '12 Jun 2025, 10:05 AM' }],
    patientId: 4, assessmentIndex: 0 },
  { id: 4, patientName: 'Sunita Verma',   hospital: 'District Hospital Lakhimpur',   type: 'Government', transport: 'Ambulance',       status: 'Pending',   ashaWorker: 'Sunita Devi',  date: '11 Jun 2025', notes: 'Maternal health check-up',
    reviewStage: 'CREATED', assignedDoctorId: null, doctorRecommendation: '', clinicalNotes: [], patientId: 5, assessmentIndex: 0 },
  { id: 5, patientName: 'Anita Devi',     hospital: 'Bhira PHC',                     type: 'Government', transport: 'Walking',         status: 'Confirmed', ashaWorker: 'Meena Rani',   date: '10 Jun 2025', notes: 'Regular follow-up',
    reviewStage: 'CREATED', assignedDoctorId: null, doctorRecommendation: '', clinicalNotes: [], patientId: 3, assessmentIndex: 0 },
]

// Forward-only doctor-review lifecycle — mirrors the backend's ReferralReviewStage
// transition map exactly, so the mock UI can never offer a stage the real API would reject.
const REVIEW_STAGE_TRANSITIONS = {
  ASSIGNED_TO_DOCTOR: 'UNDER_REVIEW',
  UNDER_REVIEW:       'ACTION_TAKEN',
  ACTION_TAKEN:        'CLOSED',
}

export const useReferralsStore = defineStore('referrals', () => {
  const items = ref([...SAMPLE_REFERRALS])

  const govCount     = computed(() => items.value.filter(r => r.type === 'Government').length)
  const privateCount = computed(() => items.value.filter(r => r.type === 'Private').length)

  function getById(id) { return items.value.find(r => r.id === id) ?? null }

  function nextReviewStage(stage) { return REVIEW_STAGE_TRANSITIONS[stage] ?? null }

  function add(data) {
    const maxId = items.value.reduce((m, r) => Math.max(m, r.id), 0)
    items.value.unshift({
      id: maxId + 1,
      type: 'Government',
      status: 'Pending',
      date: new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }),
      reviewStage: 'CREATED',
      assignedDoctorId: null,
      doctorRecommendation: '',
      clinicalNotes: [],
      ...data,
    })
  }

  // Doctor self-claims an unassigned referral.
  function claim(id, doctorLoginId) {
    const r = getById(id)
    if (!r || r.assignedDoctorId) return
    r.assignedDoctorId = doctorLoginId
    r.reviewStage = 'ASSIGNED_TO_DOCTOR'
  }

  // SUPER_ADMIN override — assign/reassign regardless of current state.
  function assign(id, doctorLoginId) {
    const r = getById(id)
    if (!r) return
    r.assignedDoctorId = doctorLoginId
    if (r.reviewStage === 'CREATED') r.reviewStage = 'ASSIGNED_TO_DOCTOR'
  }

  function setReviewStage(id, stage) {
    const r = getById(id)
    if (!r) return
    if (nextReviewStage(r.reviewStage) !== stage) return
    r.reviewStage = stage
  }

  function addNote(id, text, authorName) {
    const r = getById(id)
    if (!r || !text?.trim()) return
    const maxNoteId = r.clinicalNotes.reduce((m, n) => Math.max(m, n.id), 0)
    r.clinicalNotes.unshift({
      id: maxNoteId + 1,
      text: text.trim(),
      author: authorName || 'Doctor',
      createdAt: new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
        + ', ' + new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true }),
    })
  }

  function setRecommendation(id, text) {
    const r = getById(id)
    if (!r) return
    r.doctorRecommendation = text
  }

  return {
    items, govCount, privateCount, add, getById,
    nextReviewStage, claim, assign, setReviewStage, addNote, setRecommendation,
  }
})
