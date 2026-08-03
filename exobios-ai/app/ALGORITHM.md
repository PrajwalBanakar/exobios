# ALGORITHM.md

Pipeline logic for `POST /analyze`. This document covers the "what runs and
in what order" — see `README.md` for code layout.

## 1. Overview

One request → one `AssessmentState` object → one deterministic step → four
LangGraph nodes in fixed sequence → persisted per-stage → response shaped
from final state.

```
request → rule_engine → diagnosis → validate → investigation → validate
                                   → treatment → validate → plan_of_action
                                   → validate → response
```

Validation runs after every generation node (one reusable node, not four
separate ones).

## 2. State object

`AssessmentState` (`schemas/state.py`) is the single object threaded through
every node. Nodes read what they need off it, write their output back to it.
Fields accumulate — nothing is overwritten by a later node.

```
assessment_id
patient_input              # AiRequest, from frontend
deterministic_flags        # RuleEngineResult — set once, pre-graph, read-only after
diagnosis                  # + diagnosis_chunks
investigation               # + investigation_chunks
treatment                    # + treatment_chunks
plan_of_action                 # no chunks — synthesis only, no retrieval
validation_flags               # appended to by the validation node, per stage
```

Retrieved chunks are stored per stage, not discarded after generation —
needed for citation display and the eventual full-context chat feature.

## 3. Pre-graph: deterministic rule engine

Plain Python, no LLM, no retrieval. Runs before the graph starts. Evaluates
hard thresholds against `patient_input.vitals` (SpO2, BP, respiratory rate,
etc. — see clinical scope doc for exact thresholds). Produces:

```
deterministic_flags: {
  flags: [{code, severity, value}],
  risk_floor: LOW | MEDIUM | HIGH | CRITICAL
}
```

`risk_floor` is a hard floor. No downstream node may lower it. Plan-of-action
node must escalate to at least `risk_floor`, never below it.

## 4. Node 1 — diagnosis

- Input: `state.patient_input`
- Query: vitals + symptoms → natural language string
- Filter: `complaint_category` (from patient_input, not yet from an LLM
  classification — this is the request's stated category)
- Retrieval: `retrieve_and_rerank(query, filters, top_k=10)`
- Generation: LLM call, forced structured output, grounded strictly in
  retrieved chunks + `deterministic_flags`. Must return `insufficient_evidence`
  rather than guess when retrieval is thin.
- Writes: `state.diagnosis`, `state.diagnosis_chunks`
- Persist: one row in `assessment_stages` (stage_name="diagnosis")

## 5. Node 2 — recommended investigation

- Input: `state.diagnosis` (disease name/keywords), `state.patient_input`
- Query: `"{disease} diagnostic test confirmation method"` — built from the
  diagnosis output, not from raw patient symptoms. This is a materially
  different query than node 1's, targeting confirmatory-test content
  (RDT, blood smear, PCR-type chunks) rather than symptom-matching content.
- Retrieval: `retrieve_and_rerank`, same tool, new query/filters
- Generation: LLM call, grounded in these new chunks + the diagnosis
- Writes: `state.investigation`, `state.investigation_chunks`
- Persist: stage_name="investigation"

## 6. Node 3 — treatment protocol

- Input: `state.diagnosis`, patient-specific factors (age, pregnancy status,
  `deterministic_flags` severity) — these change *which* regimen applies,
  not just whether one exists
- Query: `"{disease} treatment dosage regimen {patient factors}"` — must
  include patient factors, not diagnosis alone, or retrieval returns
  generically-scoped treatment content that may not fit this patient
  (e.g. adult dosing surfaced for a pediatric case)
- Retrieval: `retrieve_and_rerank`
- Generation: LLM explicitly instructed to flag uncertainty if retrieved
  chunks don't clearly address the patient's specific factors, rather than
  confidently selecting a regimen that may not apply
- Writes: `state.treatment`, `state.treatment_chunks`, uncertainty flag if
  regimen specificity is unclear
- Persist: stage_name="treatment"

## 7. Node 4 — plan of action

- Input: `state.diagnosis`, `state.investigation`, `state.treatment`,
  `state.deterministic_flags` — no new field from outside state
- No retrieval. No query construction. No hybrid search / rerank / top-k.
  This node synthesizes; it does not search the corpus.
- Generation: LLM synthesizes a plan from the three prior outputs +
  deterministic flags. Explicit instruction: deterministic flags override
  any conclusion the LLM would otherwise reach — if `risk_floor == CRITICAL`,
  output must recommend immediate referral/escalation regardless of what
  node 3 suggested.
- Writes: `state.plan_of_action`, conflict flag if LLM synthesis disagreed
  with `deterministic_flags` (should not happen; logged if it does)
- Persist: stage_name="plan_of_action"

## 8. Validation node (reused after every generation node)

Runs after diagnosis, investigation, treatment, and plan_of_action, each
time, same logic:

- Every citation in the stage's output must trace to a chunk actually
  present in that stage's retrieved chunks (or, for plan_of_action, to
  facts already in state) — reject/flag hallucinated citations.
- `risk_floor` from `deterministic_flags` must never be contradicted or
  downgraded by generated output. If violated, override the output's risk
  field back to `risk_floor` and append to `state.validation_flags`.
- On failure, append to `state.validation_flags`; does not halt the graph
  unless failure is severe (citation to a nonexistent chunk on a CRITICAL
  case) — exact halt condition TBD.

## 9. Shared retrieval tool

`graph/tools/retrieval.py::retrieve_and_rerank(query_text, filters, top_k)`

```
embed query_text → embedding_service
search Qdrant (hybrid dense + sparse) → qdrant_service, filtered by metadata
rerank results → reranker_service
return top_k RetrievedChunk objects
```

Called by nodes 1–3 with different `query_text`/`filters` each time. Node 4
does not call this tool.

## 10. Persistence

Each node writes its own row to `assessment_stages` (Postgres/Supabase) at
the end of its execution — not batched at the end of the whole graph. Row
shape: `assessment_id`, `stage_name`, `input_snapshot`, `output`,
`chunks_retrieved`, `created_at`. Enables reopening/re-running any individual
stage later without replaying the whole graph, and gives a full audit trail
per citation.

## 11. Open items

- Exact halt condition for validation failures (currently: log and
  continue, except severe CRITICAL-case citation failures)
- Rate limiting / idempotency checks at the API layer — not yet built
- LangGraph checkpointer for mid-run failure recovery — not yet wired,
  explicit `persistence_service` writes cover the "resume/reopen" need
  independently