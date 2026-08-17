package com.exobios.backend.integration.ai;

import com.exobios.backend.assessments.entity.enums.AiResultStatus;
import com.exobios.backend.assessments.entity.enums.RiskLevel;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.json.JsonTest;

import java.math.BigDecimal;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Contract test between exobios-ai's POST /analyze response shape
 * (app/schemas/response.py::AssessmentResponse) and this backend's
 * AiResponse DTO.
 *
 * Uses @JsonTest so {@code objectMapper} is the SAME autoconfigured Jackson
 * instance (respecting application.yml's spring.jackson.* settings, and
 * critically the ParameterNamesModule Spring Boot registers automatically)
 * that RestAiGateway's RestClient uses at runtime — a bare `new
 * ObjectMapper()` does NOT register ParameterNamesModule and cannot
 * construct AiResponse at all (it has no explicit no-args/all-args
 * constructor, only Lombok's implicit @Builder-generated one), which would
 * make a hand-rolled-ObjectMapper test give a false negative.
 *
 * If exobios-ai's response shape ever changes incompatibly, this is the
 * test that should catch it — update SAMPLE_ANALYZE_RESPONSE to match
 * schemas/response.py and re-verify these assertions still hold.
 */
@JsonTest
class AiResponseContractTest {

    @Autowired
    private ObjectMapper objectMapper;

    // Mirrors AssessmentResponse.from_state()'s actual output shape as of the
    // 2026-08 contract-alignment pass — camelCase top-level legacy fields
    // plus the full rich per-stage detail alongside them.
    private static final String SAMPLE_ANALYZE_RESPONSE = """
            {
              "assessmentId": "11111111-1111-1111-1111-111111111111",
              "status": "COMPLETED",
              "summary": "Top differential: Dengue Fever (HIGH confidence). Risk level: HIGH. 2 candidate(s) considered.",
              "riskLevel": "HIGH",
              "confidenceScore": 0.82,
              "redFlags": "SPO2_LOW (90-93%)",
              "recommendations": "Administer ORS; Refer if warning signs develop",
              "modelVersion": "llama-3.3-70b-versatile",
              "source": "exobios-ai-langgraph",
              "deterministicFlags": {
                "flags": [{"code": "SPO2_LOW", "severity": "HIGH", "value": 92, "threshold": "90-93%"}],
                "riskFloor": "HIGH"
              },
              "diagnosis": {
                "candidates": [
                  {
                    "diseaseName": "Dengue Fever",
                    "confidenceScore": 0.82,
                    "confidenceLabel": "HIGH",
                    "supportingEvidence": ["thrombocytopenia", "high fever"],
                    "citations": [{"chunkId": "c1", "documentId": "d1", "excerpt": "...", "heading": "Dengue", "page": 12}],
                    "reasoning": "Consistent with classic dengue presentation."
                  }
                ],
                "queryUsed": "high fever thrombocytopenia",
                "insufficientEvidence": false
              },
              "investigation": {"tests": [], "basedOnDiagnosis": ["Dengue Fever"]},
              "treatmentProtocol": {"steps": [], "basedOnDiagnosis": ["Dengue Fever"], "patientFactorsConsidered": [], "regimenSpecificityFlag": false},
              "planOfAction": {"immediateMeasures": [], "warningSigns": [], "riskLevel": "HIGH", "riskFloorConflict": false, "referralAdvice": null},
              "validationFlags": []
            }
            """;

    @Test
    void analyzeResponseDeserializesIntoAiResponseWithoutError() throws Exception {
        AiResponse response = objectMapper.readValue(SAMPLE_ANALYZE_RESPONSE, AiResponse.class);

        assertThat(response.getStatus()).isEqualTo(AiResultStatus.COMPLETED);
        assertThat(response.getRiskLevel()).isEqualTo(RiskLevel.HIGH);
        assertThat(response.getConfidenceScore()).isEqualByComparingTo(BigDecimal.valueOf(0.82));
        assertThat(response.getRedFlags()).isEqualTo("SPO2_LOW (90-93%)");
        assertThat(response.getRecommendations()).contains("ORS");
        assertThat(response.getModelVersion()).isEqualTo("llama-3.3-70b-versatile");
        assertThat(response.getSource()).isEqualTo("exobios-ai-langgraph");
        assertThat(response.getSummary()).contains("Dengue Fever");
    }

    @Test
    void legacyContractFieldsAreAllPopulatedNotSilentlyEmpty() throws Exception {
        AiResponse response = objectMapper.readValue(SAMPLE_ANALYZE_RESPONSE, AiResponse.class);

        assertThat(response.getSummary()).isNotBlank();
        assertThat(response.getRiskLevel()).isNotNull();
        assertThat(response.getConfidenceScore()).isNotNull();
        assertThat(response.getModelVersion()).isNotBlank();
        assertThat(response.getSource()).isNotBlank();
    }

    @Test
    void oldSnakeCaseShapeWouldHaveDeserializedWithEmptyClinicalContent() throws Exception {
        // Documents, empirically, the exact failure mode the contract fix
        // closes. The PRE-FIX exobios-ai response (snake_case, no top-level
        // legacy fields at all — assessment_id/deterministic_flags/etc. only)
        // does NOT throw a deserialization exception — fail-on-unknown-
        // properties=false means Jackson silently builds an AiResponse with
        // status=COMPLETED (matched by pure coincidence, since "COMPLETED" is
        // a valid enum literal on both sides) and every clinical field null.
        // That is worse than an exception: RestAiGateway's retry/placeholder
        // fallback only triggers on a thrown exception, so this would have
        // reached AssessmentService as an apparently-successful, empty
        // result — never retried, never flagged. Kept as a named example of
        // the bug, not something to reproduce going forward.
        String oldShape = """
                {
                  "assessment_id": "11111111-1111-1111-1111-111111111111",
                  "status": "COMPLETED",
                  "deterministic_flags": {"flags": [], "risk_floor": "LOW"},
                  "diagnosis": {"candidates": [], "query_used": "x", "insufficient_evidence": true},
                  "investigation": {"tests": [], "based_on_diagnosis": []},
                  "treatment_protocol": {"steps": [], "based_on_diagnosis": [], "patient_factors_considered": [], "regimen_specificity_flag": false},
                  "plan_of_action": {"immediate_measures": [], "warning_signs": [], "risk_level": "LOW", "risk_floor_conflict": false, "referral_advice": null},
                  "validation_flags": []
                }
                """;

        AiResponse response = objectMapper.readValue(oldShape, AiResponse.class);

        assertThat(response.getStatus()).isEqualTo(AiResultStatus.COMPLETED); // matched by coincidence, not by design
        assertThat(response.getSummary()).isNull();        // silently empty, not an error
        assertThat(response.getRiskLevel()).isNull();       // silently empty, not an error
        assertThat(response.getConfidenceScore()).isNull(); // silently empty, not an error
    }
}
