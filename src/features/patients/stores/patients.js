import { defineStore } from 'pinia'
import { ref } from 'vue'

const STORAGE_KEY   = 'exobios_patients'
const STORE_VERSION = 'v3' // bump when seed data shape changes
const VERSION_KEY   = 'exobios_patients_ver'

// Calculates age in years from a date string (YYYY-MM-DD or similar)
function calcAge(dob) {
  if (!dob) return null
  const birth = new Date(dob)
  const today = new Date()
  let age = today.getFullYear() - birth.getFullYear()
  const m = today.getMonth() - birth.getMonth()
  if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) age--
  return age
}

const DEFAULT_PATIENTS = [
  {
    id: 1, name: 'Priya Sharma', dob: '1997-03-15', age: 28, gender: 'Female',
    phone: '9876543210', occupation: 'Homemaker', abhaId: '12-3456-7890-0001',
    fatherSpouseName: 'Amit Sharma (Spouse)',
    address: { details: 'House No. 12, Near Temple', village: 'Rampur Village', pincode: '244901', taluk: 'Rampur', district: 'Rampur', state: 'Uttar Pradesh' },
    family: { maritalStatus: 'Married', spouseName: 'Amit Sharma', spouseAge: 32, children: [{ name: 'Riya Sharma', age: 4 }], householdMembers: [], fatherName: '', fatherAge: '', motherName: '', motherAge: '' },
    photo: '', risk: 'High', date: '15 Jun 2025', assessmentTime: '15 Jun 2025, 10:30 AM',
    assessmentHistory: [
      {
        date: '15 Jun 2025', time: '10:30 AM', risk: 'High',
        primaryComplaint: 'High Fever & Body Pain',
        complaints: [{ complaint: 'High Fever', onset: '3 days ago', duration: '3 days', intensity: 8, associatedSymptoms: ['Body Pain', 'Headache', 'Weakness'] }],
        vitals: { bpSystolic: 130, bpDiastolic: 85, heartRate: 98, respiratoryRate: 22, temperature: '102.4', spo2: 96, rbs: '' },
        examForm: { height: '158', weight: '52', dehydration: true, rashes: false, swelling: false, eyeDiscolouration: false, generalOther: 'Mild pallor noted' },
        aiDiagnosis: 'Dengue Fever',
        aiSummary: 'High fever with body pain, headache and mild dehydration. Dengue suspected based on symptom cluster. Platelet count monitoring advised.',
      },
      {
        date: '22 Mar 2025', time: '11:15 AM', risk: 'Moderate',
        primaryComplaint: 'Headache & Dizziness',
        complaints: [{ complaint: 'Persistent Headache', onset: '1 week ago', duration: '7 days', intensity: 6, associatedSymptoms: ['Dizziness', 'Weakness'] }],
        vitals: { bpSystolic: 148, bpDiastolic: 94, heartRate: 82, respiratoryRate: 18, temperature: '98.6', spo2: 99, rbs: '' },
        examForm: { height: '158', weight: '53', dehydration: false, rashes: false, swelling: false, eyeDiscolouration: false, generalOther: '' },
        aiDiagnosis: 'Hypertension',
        aiSummary: 'Elevated BP readings with headache and dizziness. Hypertension assessment recommended. Lifestyle modification advised.',
      },
      {
        date: '10 Jan 2025', time: '09:00 AM', risk: 'Low',
        primaryComplaint: 'Cough & Cold',
        complaints: [{ complaint: 'Cough', onset: '5 days ago', duration: '5 days', intensity: 3, associatedSymptoms: ['Fever', 'Loss of Appetite'] }],
        vitals: { bpSystolic: 118, bpDiastolic: 76, heartRate: 78, respiratoryRate: 18, temperature: '99.1', spo2: 99, rbs: '' },
        examForm: { height: '158', weight: '53', dehydration: false, rashes: false, swelling: false, eyeDiscolouration: false, generalOther: '' },
        aiDiagnosis: 'Viral URTI',
        aiSummary: 'Mild upper respiratory tract infection. Symptomatic treatment recommended. Adequate hydration and rest advised.',
      },
    ],
  },
  {
    id: 2, name: 'Rajesh Kumar', dob: '1980-08-22', age: 45, gender: 'Male',
    phone: '9765432109', occupation: 'Farmer', abhaId: '12-3456-7890-0002',
    fatherSpouseName: 'Savita Kumar (Spouse)',
    address: { details: 'Plot 5, Main Road', village: 'Sitapur Town', pincode: '261001', taluk: 'Sitapur', district: 'Sitapur', state: 'Uttar Pradesh' },
    family: { maritalStatus: 'Married', spouseName: 'Savita Kumar', spouseAge: 40, children: [], householdMembers: [], fatherName: '', fatherAge: '', motherName: '', motherAge: '' },
    photo: '', risk: 'Moderate', date: '14 Jun 2025', assessmentTime: '14 Jun 2025, 02:15 PM',
    assessmentHistory: [
      {
        date: '14 Jun 2025', time: '02:15 PM', risk: 'Moderate',
        primaryComplaint: 'Chest Discomfort',
        complaints: [{ complaint: 'Chest Discomfort', onset: '2 days ago', duration: '2 days', intensity: 6, associatedSymptoms: ['Breathlessness', 'Sweating'] }],
        vitals: { bpSystolic: 152, bpDiastolic: 96, heartRate: 92, respiratoryRate: 20, temperature: '98.4', spo2: 97, rbs: '168' },
        examForm: { height: '172', weight: '78', dehydration: false, rashes: false, swelling: true, eyeDiscolouration: false, generalOther: 'Mild ankle oedema' },
        aiDiagnosis: 'Hypertensive Heart Disease',
        aiSummary: 'Chest discomfort with elevated BP and RBS. Cardiac and diabetic evaluation recommended. ECG and HbA1c advised.',
      },
      {
        date: '05 Feb 2025', time: '10:00 AM', risk: 'Low',
        primaryComplaint: 'Lower Back Pain',
        complaints: [{ complaint: 'Lower Back Pain', onset: '1 week ago', duration: '7 days', intensity: 5, associatedSymptoms: ['Weakness'] }],
        vitals: { bpSystolic: 138, bpDiastolic: 88, heartRate: 80, respiratoryRate: 16, temperature: '98.6', spo2: 99, rbs: '142' },
        examForm: { height: '172', weight: '79', dehydration: false, rashes: false, swelling: false, eyeDiscolouration: false, generalOther: 'Tenderness over lumbar spine' },
        aiDiagnosis: 'Musculoskeletal Back Pain',
        aiSummary: 'Mechanical lower back pain likely from occupational strain. Physiotherapy and analgesics recommended.',
      },
    ],
  },
  {
    id: 3, name: 'Anita Devi', dob: '1993-11-05', age: 32, gender: 'Female',
    phone: '9654321098', occupation: 'Teacher', abhaId: '12-3456-7890-0003',
    fatherSpouseName: 'Ram Prasad (Father)',
    address: { details: 'Village Main, Near School', village: 'Lakhimpur Block', pincode: '262701', taluk: 'Lakhimpur', district: 'Lakhimpur Kheri', state: 'Uttar Pradesh' },
    family: { maritalStatus: 'Unmarried', spouseName: '', spouseAge: '', children: [], householdMembers: [], fatherName: 'Ram Prasad', fatherAge: 60, motherName: 'Kamla Devi', motherAge: 55 },
    photo: '', risk: 'Low', date: '13 Jun 2025', assessmentTime: '13 Jun 2025, 11:00 AM',
    assessmentHistory: [
      {
        date: '13 Jun 2025', time: '11:00 AM', risk: 'Low',
        primaryComplaint: 'Abdominal Pain & Vomiting',
        complaints: [{ complaint: 'Abdominal Pain', onset: 'Yesterday', duration: '1 day', intensity: 5, associatedSymptoms: ['Vomiting', 'Loss of Appetite'] }],
        vitals: { bpSystolic: 112, bpDiastolic: 72, heartRate: 86, respiratoryRate: 18, temperature: '99.2', spo2: 99, rbs: '' },
        examForm: { height: '163', weight: '58', dehydration: false, rashes: false, swelling: false, eyeDiscolouration: false, generalOther: 'Epigastric tenderness' },
        aiDiagnosis: 'Acute Gastritis',
        aiSummary: 'Epigastric pain and vomiting consistent with acute gastritis. Antacids and bland diet recommended. Rule out peptic ulcer.',
      },
      {
        date: '28 Apr 2025', time: '03:30 PM', risk: 'Low',
        primaryComplaint: 'Headache',
        complaints: [{ complaint: 'Headache', onset: '2 days ago', duration: '2 days', intensity: 6, associatedSymptoms: ['Weakness'] }],
        vitals: { bpSystolic: 108, bpDiastolic: 70, heartRate: 74, respiratoryRate: 16, temperature: '98.6', spo2: 100, rbs: '' },
        examForm: { height: '163', weight: '58', dehydration: false, rashes: false, swelling: false, eyeDiscolouration: false, generalOther: '' },
        aiDiagnosis: 'Tension Headache / Migraine',
        aiSummary: 'Recurrent headache without aura. Stress-related tension headache likely. Analgesics and stress management advised.',
      },
    ],
  },
  {
    id: 4, name: 'Mohammed Iqbal', dob: '1958-02-14', age: 67, gender: 'Male',
    phone: '9543210987', occupation: 'Retired', abhaId: '12-3456-7890-0004',
    fatherSpouseName: 'Fatima Iqbal (Spouse)',
    address: { details: 'Mohalla Ansari, Old Town', village: 'Bhira', pincode: '262801', taluk: 'Bhira', district: 'Pilibhit', state: 'Uttar Pradesh' },
    family: { maritalStatus: 'Married', spouseName: 'Fatima Iqbal', spouseAge: 63, children: [{ name: 'Imran Iqbal', age: 35 }], householdMembers: [], fatherName: '', fatherAge: '', motherName: '', motherAge: '' },
    photo: '', risk: 'High', date: '12 Jun 2025', assessmentTime: '12 Jun 2025, 09:45 AM',
    assessmentHistory: [
      {
        date: '12 Jun 2025', time: '09:45 AM', risk: 'High',
        primaryComplaint: 'Breathlessness & Chest Tightness',
        complaints: [{ complaint: 'Breathlessness', onset: 'This morning', duration: '6 hours', intensity: 8, associatedSymptoms: ['Cough', 'Swelling'] }],
        vitals: { bpSystolic: 158, bpDiastolic: 98, heartRate: 104, respiratoryRate: 26, temperature: '98.8', spo2: 93, rbs: '212' },
        examForm: { height: '168', weight: '74', dehydration: false, rashes: false, swelling: true, eyeDiscolouration: false, generalOther: 'Bilateral wheeze on auscultation' },
        aiDiagnosis: 'Asthma Exacerbation',
        aiSummary: 'Acute breathlessness with low SpO2 and wheeze. Asthma exacerbation in known diabetic-hypertensive patient. Immediate bronchodilator and referral advised.',
      },
      {
        date: '15 Mar 2025', time: '02:00 PM', risk: 'Moderate',
        primaryComplaint: 'Fever & Productive Cough',
        complaints: [{ complaint: 'Fever', onset: '4 days ago', duration: '4 days', intensity: 7, associatedSymptoms: ['Cough', 'Breathlessness'] }],
        vitals: { bpSystolic: 145, bpDiastolic: 90, heartRate: 96, respiratoryRate: 22, temperature: '101.2', spo2: 96, rbs: '188' },
        examForm: { height: '168', weight: '74', dehydration: true, rashes: false, swelling: false, eyeDiscolouration: false, generalOther: 'Coarse crepitations in right base' },
        aiDiagnosis: 'Community Acquired Pneumonia',
        aiSummary: 'Fever with productive cough and reduced breath sounds. Pneumonia likely in elderly diabetic patient. Antibiotics and close monitoring required.',
      },
      {
        date: '20 Dec 2024', time: '10:30 AM', risk: 'Low',
        primaryComplaint: 'Routine Checkup — Diabetes Monitoring',
        complaints: [{ complaint: 'Increased thirst and urination', onset: 'Ongoing', duration: 'Chronic', intensity: 3, associatedSymptoms: ['Weakness'] }],
        vitals: { bpSystolic: 138, bpDiastolic: 86, heartRate: 78, respiratoryRate: 16, temperature: '98.4', spo2: 99, rbs: '176' },
        examForm: { height: '168', weight: '75', dehydration: false, rashes: false, swelling: false, eyeDiscolouration: false, generalOther: '' },
        aiDiagnosis: 'Type 2 Diabetes (Controlled)',
        aiSummary: 'Routine diabetes follow-up. RBS moderately elevated. Medication compliance reviewed. HbA1c test recommended. Diet counselling given.',
      },
    ],
  },
  {
    id: 5, name: 'Sunita Verma', dob: '2006-07-30', age: 19, gender: 'Female',
    phone: '9432109876', occupation: 'Student', abhaId: '12-3456-7890-0005',
    fatherSpouseName: 'Suresh Verma (Father)',
    address: { details: 'Near Pond, East Side', village: 'Nanpara Village', pincode: '271865', taluk: 'Nanpara', district: 'Bahraich', state: 'Uttar Pradesh' },
    family: { maritalStatus: 'Unmarried', spouseName: '', spouseAge: '', children: [], householdMembers: [], fatherName: 'Suresh Verma', fatherAge: 48, motherName: 'Meena Verma', motherAge: 44 },
    photo: '', risk: 'Low', date: '11 Jun 2025', assessmentTime: '11 Jun 2025, 04:00 PM',
    assessmentHistory: [
      {
        date: '11 Jun 2025', time: '04:00 PM', risk: 'Low',
        primaryComplaint: 'Fatigue & Loss of Appetite',
        complaints: [{ complaint: 'Generalized Weakness', onset: '2 weeks ago', duration: '14 days', intensity: 4, associatedSymptoms: ['Loss of Appetite', 'Dizziness'] }],
        vitals: { bpSystolic: 100, bpDiastolic: 66, heartRate: 88, respiratoryRate: 18, temperature: '98.4', spo2: 99, rbs: '' },
        examForm: { height: '155', weight: '44', dehydration: false, rashes: false, swelling: false, eyeDiscolouration: true, generalOther: 'Pallor in conjunctiva and nails' },
        aiDiagnosis: 'Iron Deficiency Anaemia',
        aiSummary: 'Pallor, fatigue, and conjunctival pallor suggestive of anaemia in young female. CBC and iron studies advised. Iron supplementation recommended.',
      },
      {
        date: '08 May 2025', time: '11:45 AM', risk: 'Moderate',
        primaryComplaint: 'Skin Rash',
        complaints: [{ complaint: 'Itchy skin rash on arms', onset: '3 days ago', duration: '3 days', intensity: 5, associatedSymptoms: ['Rash', 'Fever'] }],
        vitals: { bpSystolic: 104, bpDiastolic: 68, heartRate: 80, respiratoryRate: 16, temperature: '99.6', spo2: 100, rbs: '' },
        examForm: { height: '155', weight: '44', dehydration: false, rashes: true, swelling: false, eyeDiscolouration: false, generalOther: 'Urticarial rash on forearms' },
        aiDiagnosis: 'Allergic Urticaria',
        aiSummary: 'Urticarial rash with mild fever. Allergic reaction likely. Antihistamines prescribed. Allergen avoidance counselled.',
      },
    ],
  },
]

export const usePatientsStore = defineStore('patients', () => {
  function load() {
    try {
      // If stored data is from an older version, discard it and use fresh seed data
      if (localStorage.getItem(VERSION_KEY) !== STORE_VERSION) {
        localStorage.removeItem(STORAGE_KEY)
        localStorage.setItem(VERSION_KEY, STORE_VERSION)
        return null
      }
      const raw = localStorage.getItem(STORAGE_KEY)
      return raw ? JSON.parse(raw) : null
    } catch { return null }
  }
  function persist(list) { localStorage.setItem(STORAGE_KEY, JSON.stringify(list)) }

  const patients = ref(load() ?? [...DEFAULT_PATIENTS])

  function getById(id)    { return patients.value.find(p => p.id === id) ?? null }

  function add(data) {
    const maxId = patients.value.reduce((m, p) => Math.max(m, p.id), 0)
    const newId = maxId + 1
    const age = data.dob ? calcAge(data.dob) : (data.age ?? null)
    patients.value.unshift({ id: newId, age, assessmentHistory: [], ...data })
    persist(patients.value)
    return newId
  }

  function update(id, data) {
    const idx = patients.value.findIndex(p => p.id === id)
    if (idx !== -1) {
      const age = data.dob ? calcAge(data.dob) : patients.value[idx].age
      patients.value[idx] = { ...patients.value[idx], ...data, age }
      persist(patients.value)
    }
  }

  // Push a completed assessment into a patient's history (newest first)
  function addAssessment(id, assessmentData) {
    const idx = patients.value.findIndex(p => p.id === id)
    if (idx === -1) return
    const patient = patients.value[idx]
    const now = new Date()
    const date = now.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
    const time = now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true })
    const entry = {
      date, time,
      risk: assessmentData.risk || 'Low',
      primaryComplaint: assessmentData.complaints?.[0]?.complaint || 'General Assessment',
      complaints:    assessmentData.complaints    || [],
      pastHistory:   assessmentData.pastHistory   || {},
      familyHistory: assessmentData.familyHistory || {},
      examForm:      assessmentData.examForm      || {},
      vitals:        assessmentData.vitals        || {},
      aiDiagnosis:   assessmentData.aiDiagnosis   || '',
      aiSummary:     assessmentData.aiSummary     || '',
    }
    const history = Array.isArray(patient.assessmentHistory) ? patient.assessmentHistory : []
    patients.value[idx] = {
      ...patient,
      assessmentHistory: [entry, ...history],
      // Mirror latest on patient root for table display
      date, assessmentTime: `${date}, ${time}`,
      risk: entry.risk,
    }
    persist(patients.value)
  }

  function remove(id) {
    patients.value = patients.value.filter(p => p.id !== id)
    persist(patients.value)
  }

  return { patients, getById, add, update, addAssessment, remove, calcAge }
})
