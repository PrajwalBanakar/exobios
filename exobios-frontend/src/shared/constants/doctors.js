/**
 * Single source of truth for teleconsult doctor data, previously duplicated with
 * drifting names/specialties across AIResultView and MeasuresView.
 * General-tier doctors are offered for Paramedic-initiated teleconsults; Specialist-tier
 * doctors are offered when a Doctor (MBBS) initiates a referral-avoiding teleconsult.
 */
export const DOCTOR_TIER = { GENERAL: 'GENERAL', SPECIALIST: 'SPECIALIST' }

export const DOCTORS = [
  { id: 'doc-anjali-sharma', name: 'Dr. Anjali Sharma', specialization: 'General Physician', tier: DOCTOR_TIER.GENERAL,    available: true,  phone: '9876500001' },
  { id: 'doc-vivek-singh',   name: 'Dr. Vivek Singh',   specialization: 'Internal Medicine',  tier: DOCTOR_TIER.GENERAL,    available: true,  phone: '9876500002' },
  { id: 'doc-neha-verma',    name: 'Dr. Neha Verma',    specialization: 'Pediatrician',       tier: DOCTOR_TIER.GENERAL,    available: false, phone: '9876500003' },
  { id: 'doc-ramesh-iyer',   name: 'Dr. Ramesh Iyer',   specialization: 'Cardiologist',       tier: DOCTOR_TIER.SPECIALIST, available: true,  phone: '9876500004' },
  { id: 'doc-kavya-rao',     name: 'Dr. Kavya Rao',     specialization: 'Diabetologist',      tier: DOCTOR_TIER.SPECIALIST, available: true,  phone: '9876500005' },
  { id: 'doc-arjun-mehta',   name: 'Dr. Arjun Mehta',   specialization: 'Pulmonologist',      tier: DOCTOR_TIER.SPECIALIST, available: false, phone: '9876500006' },
]

export const getDoctorById    = (id)   => DOCTORS.find(d => d.id === id) || null
export const getDoctorsByTier = (tier) => DOCTORS.filter(d => d.tier === tier)
