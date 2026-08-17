package com.exobios.backend.integration.ai;

import com.exobios.backend.assessments.entity.enums.AiResultStatus;
import com.exobios.backend.assessments.entity.enums.ComplaintCategory;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.util.List;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.api.Assumptions.assumeTrue;

/**
 * Live contract check between {@link RestAiGateway} and a real running
 * exobios-ai instance (LangGraph pipeline, not the AI-1 stub). Not part of
 * the default unit test run: it talks to a real HTTP service (and, through
 * it, real Qdrant/MongoDB/HF/Groq), so it self-skips via JUnit assumptions
 * when that service isn't reachable at AI_LIVE_TEST_URL (default
 * http://localhost:8000).
 *
 * Run explicitly once exobios-ai (and its Qdrant/Mongo dependencies) are up:
 *   mvn -Dtest=RestAiGatewayLiveIT -DfailIfNoTests=false test
 *
 * Unlike the pre-2026-08 version of this file, this does NOT assert a fixed
 * stub response — the real pipeline's output depends on what's ingested
 * into Qdrant. It asserts the *contract* (shape, valid enum values, no
 * silent-empty-success) rather than specific clinical content. See
 * AiResponseContractTest for the network-free version of this check.
 */
class RestAiGatewayLiveIT {

    private static final String BASE_URL =
            System.getenv().getOrDefault("AI_LIVE_TEST_URL", "http://localhost:8000");
    private static final String API_KEY =
            System.getenv().getOrDefault("AI_LIVE_TEST_KEY", "local-dev-key-12345");

    private RestAiGateway newGateway() {
        AiConfiguration config = new AiConfiguration();
        config.setBaseUrl(BASE_URL);
        config.setApiKey(API_KEY);
        config.setConnectTimeoutMs(5000);
        config.setReadTimeoutMs(30000);
        return new RestAiGateway(config);
    }

    @Test
    void health_reportsUpWhenServiceRunning() {
        assumeAiServiceReachable();
        assertThat(newGateway().health()).isTrue();
    }

    @Test
    void analyzeAssessment_returnsContractCompliantResponse() {
        assumeAiServiceReachable();

        AiRequest request = AiRequest.builder()
                .assessmentId(UUID.randomUUID())
                .patientId(UUID.randomUUID())
                .patientComplaint("Fever for 3 days")
                .complaintCategory(ComplaintCategory.FEVER)
                .symptoms(List.of(
                        AiRequest.SymptomSummary.builder()
                                .name("cough")
                                .duration("3 days")
                                .severity("mild")
                                .build()))
                .vitals(AiRequest.VitalsSummary.builder()
                        .heartRate(88)
                        .spo2(BigDecimal.valueOf(97.5))
                        // Fahrenheit — see docs/api/ai-service-contract.md's Temperature Unit
                        // section. 100.8F is a real, plausible mild-fever value.
                        .temperature(BigDecimal.valueOf(100.8))
                        .bloodPressureSystolic(120)
                        .bloodPressureDiastolic(80)
                        .respiratoryRate(18)
                        .build())
                .pastIllnesses("None")
                .currentMedications("None")
                .allergies("None")
                .build();

        AiResponse response = newGateway().analyzeAssessment(request);

        assertThat(response).isNotNull();
        // Never PENDING/PROCESSING from a synchronous call — either it produced
        // a real result (COMPLETED, possibly with insufficient_evidence baked
        // into the summary/null confidence) or it genuinely failed (FAILED).
        assertThat(response.getStatus()).isIn(AiResultStatus.COMPLETED, AiResultStatus.FAILED);
        assertThat(response.getSummary()).isNotBlank();
        assertThat(response.getSource()).isNotBlank();
        assertThat(response.getModelVersion()).isNotBlank();

        if (response.getStatus() == AiResultStatus.COMPLETED) {
            // A real completed result must not be indistinguishable from the
            // placeholder/failure path — this is the exact silent-empty-success
            // bug the contract fix closes.
            assertThat(response.getSource()).isNotEqualTo("exobios-ai-unavailable");
            assertThat(response.getModelVersion()).isNotEqualTo("unavailable");
        } else {
            assertThat(response.getRiskLevel()).isNull();
            assertThat(response.getConfidenceScore()).isNull();
        }
    }

    private void assumeAiServiceReachable() {
        boolean reachable;
        try {
            reachable = newGateway().health();
        } catch (Exception e) {
            reachable = false;
        }
        assumeTrue(reachable, "exobios-ai service not reachable at " + BASE_URL + " — skipping live test");
    }
}
