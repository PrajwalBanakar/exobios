/**
 * Single source of truth for hospital/facility data, previously duplicated with
 * drifting names and details across AIResultView, MeasuresView, and ReferralsView.
 * `distance` is a static placeholder string today; kept as a plain field so it can
 * later be replaced by a live GPS-computed value without changing the shape.
 */
export const HOSPITAL_TYPE = { GOVERNMENT: 'Government', PRIVATE: 'Private' }

export const HOSPITALS = [
  { id: 'gov-chc-rampur',     name: 'Community Health Center, Rampur',   type: HOSPITAL_TYPE.GOVERNMENT, govt: true,  distance: '2.3 km', location: 'CHC Rampur, Uttar Pradesh',            phone: '05952-234567', availableServices: ['General Medicine', 'Emergency'] },
  { id: 'gov-dh-pilibhit',    name: 'District Hospital, Pilibhit',       type: HOSPITAL_TYPE.GOVERNMENT, govt: true,  distance: '14 km',  location: 'District Hospital, Pilibhit, UP',      phone: '05882-223344', availableServices: ['General Medicine', 'Surgery', 'Emergency'] },
  { id: 'gov-phc-shahabad',   name: 'PHC Shahabad',                      type: HOSPITAL_TYPE.GOVERNMENT, govt: true,  distance: '6.8 km', location: 'PHC Shahabad, UP',                      phone: '',             availableServices: ['General Medicine'] },
  { id: 'gov-chc-bhelwa',     name: 'CHC Bhelwa',                        type: HOSPITAL_TYPE.GOVERNMENT, govt: true,  distance: '9.2 km', location: 'CHC Bhelwa, UP',                        phone: '',             availableServices: ['General Medicine', 'Maternal Health'] },
  { id: 'gov-sdh-bareilly',   name: 'Sub-District Hospital, Bareilly',   type: HOSPITAL_TYPE.GOVERNMENT, govt: true,  distance: '18 km',  location: 'Sub-District Hospital, Bareilly, UP',  phone: '',             availableServices: ['General Medicine', 'Surgery'] },
  { id: 'gov-aiims-bareilly', name: 'AIIMS Bareilly',                    type: HOSPITAL_TYPE.GOVERNMENT, govt: true,  distance: '22 km',  location: 'AIIMS Bareilly, UP',                    phone: '',             availableServices: ['Tertiary Care', 'Specialist Referral'] },
  { id: 'pvt-sharma',         name: 'Sharma Multi-Specialty Hospital',   type: HOSPITAL_TYPE.PRIVATE,    govt: false, distance: '4.6 km', location: 'Sharma Hospital, Rampur, UP',           phone: '05952-345678', availableServices: ['General Medicine', 'Cardiology'] },
  { id: 'pvt-citycare',       name: 'City Care Hospital',                type: HOSPITAL_TYPE.PRIVATE,    govt: false, distance: '6.1 km', location: 'City Care Hospital, Rampur, UP',        phone: '05952-456789', availableServices: ['General Medicine', 'Pediatrics'] },
  { id: 'pvt-apollo',         name: 'Apollo Clinic, Rampur',              type: HOSPITAL_TYPE.PRIVATE,    govt: false, distance: '7.5 km', location: 'Apollo Clinic, Rampur, UP',             phone: '',             availableServices: ['General Medicine'] },
  { id: 'pvt-medanta',        name: 'Medanta Clinic',                    type: HOSPITAL_TYPE.PRIVATE,    govt: false, distance: '10 km',  location: 'Medanta Clinic, UP',                   phone: '',             availableServices: ['Specialist Consultation'] },
]

export const getHospitalById      = (id)   => HOSPITALS.find(h => h.id === id) || null
export const getHospitalsByType   = (type) => HOSPITALS.filter(h => h.type === type)
export const getGovernmentHospitals = ()   => HOSPITALS.filter(h => h.govt)

// Distance strings are "<number> km" placeholders; parseFloat extracts a sortable number
// until real GPS-based distances replace them.
export const sortByDistance = (list = HOSPITALS) =>
  [...list].sort((a, b) => parseFloat(a.distance) - parseFloat(b.distance))
