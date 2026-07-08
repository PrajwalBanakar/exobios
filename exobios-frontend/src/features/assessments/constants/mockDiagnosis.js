/**
 * Placeholder differential-diagnosis data shown on AIResultView and FullAnalysisView.
 * Previously each view hardcoded its own slightly different list (different Typhoid %,
 * FullAnalysisView missing Chikungunya) — a single shared list keeps them consistent
 * until a real backend AI model replaces this entirely.
 */
export const MOCK_DIFFERENTIAL_DIAGNOSIS = [
  { name: 'Dengue Fever', pct: 72, confidence: 'High',   icd: 'A90',    risk: 'High',     color: 'bg-red-500',
    evidence: ['High fever', 'Body aches and joint pain', 'Platelet count concern', 'Rash pattern consistent'] },
  { name: 'Viral Fever',  pct: 18, confidence: 'Medium', icd: 'B34.9',  risk: 'Moderate', color: 'bg-orange-400',
    evidence: ['Elevated temperature', 'Fatigue and weakness', 'Upper respiratory symptoms'] },
  { name: 'Malaria',      pct: 6,  confidence: 'Low',    icd: 'B54',    risk: 'High',     color: 'bg-yellow-400',
    evidence: ['Geographic risk area', 'Periodic fever pattern absent', 'Blood smear needed'] },
  { name: 'Typhoid',      pct: 3,  confidence: 'Low',    icd: 'A01.0',  risk: 'Moderate', color: 'bg-blue-400',
    evidence: ['Rose spots not observed', 'Abdominal tenderness mild', 'Widal test needed'] },
  { name: 'Chikungunya',  pct: 1,  confidence: 'Low',    icd: 'A92.0',  risk: 'Low',      color: 'bg-gray-400',
    evidence: ['Joint pain pattern atypical', 'Rash less prominent'] },
]
