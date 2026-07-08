import { defineStore } from 'pinia'
import { reactive, computed } from 'vue'

/**
 * Single source of truth for a patient's post-assessment plan of action.
 *
 * Previously AIResultView and MeasuresView each kept their own independent copies of
 * "referral decision", "hospital chosen", "teleconsult decision", "doctor chosen" and
 * "action taken" state, with no link between them — so a decision made while reviewing
 * the AI result could silently diverge from what got recorded in Measures. This store
 * is written to by AIResultView (initial plan) and read/updated by MeasuresView
 * (outcome), so both views operate on the same record instead of duplicating it.
 *
 * referral.status / teleconsult.status use the same vocabulary as the AIResultView UI:
 * '' (undecided) | 'yes' | 'no', plus 'completed' once MeasuresView finalizes it.
 */
function defaultPlan() {
  return {
    immediateMeasures: [],
    referral: { hospitalId: null, status: '' },
    teleconsult: { doctorId: null, status: '' },
    outcome: '',
    notes: '',
  }
}

export const useActionPlanStore = defineStore('actionPlan', () => {
  const plans = reactive({})

  function getPlan(patientId) {
    if (!plans[patientId]) plans[patientId] = defaultPlan()
    return plans[patientId]
  }

  function setImmediateMeasures(patientId, measures) {
    getPlan(patientId).immediateMeasures = measures
  }

  function setReferral(patientId, patch) {
    Object.assign(getPlan(patientId).referral, patch)
  }

  function setTeleconsult(patientId, patch) {
    Object.assign(getPlan(patientId).teleconsult, patch)
  }

  function setOutcome(patientId, outcome) {
    getPlan(patientId).outcome = outcome
  }

  function setNotes(patientId, notes) {
    getPlan(patientId).notes = notes
  }

  // Patients whose plan calls for a referral that hasn't been finalized in Measures yet —
  // consumed by ReferralsView to surface referrals originating from the assessment flow.
  const pendingReferrals = computed(() =>
    Object.entries(plans)
      .filter(([, plan]) => plan.referral.status === 'yes')
      .map(([patientId, plan]) => ({ patientId: Number(patientId), hospitalId: plan.referral.hospitalId }))
  )

  return {
    plans, getPlan,
    setImmediateMeasures, setReferral, setTeleconsult, setOutcome, setNotes,
    pendingReferrals,
  }
})
