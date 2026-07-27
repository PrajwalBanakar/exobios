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
 * Live contract check between {@link RestAiGateway} and a real running exobios-ai
 * instance (AI-1 stub). Not part of the default unit test run: it talks to a real
 * HTTP service, so it self-skips via JUnit assumptions when that service isn't
 * reachable at AI_LIVE_TEST_URL (default http://localhost:8000).
 *
 * Run explicitly once exobios-ai is up, e.g.:
 *   mvn -Dtest=RestAiGatewayLiveIT -DfailIfNoTests=false test
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
    void analyzeAssessment_deserializesStubResponseWithinContract() {
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
                        .temperature(BigDecimal.valueOf(38.2))
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
        assertThat(response.getStatus()).isEqualTo(AiResultStatus.PENDING);
        assertThat(response.getRiskLevel()).isNull();
        assertThat(response.getConfidenceScore()).isEqualByComparingTo(BigDecimal.ZERO);
        assertThat(response.getRedFlags()).isEmpty();
        assertThat(response.getRecommendations()).isEmpty();
        assertThat(response.getModelVersion()).isEqualTo("stub-v0.1.0");
        assertThat(response.getSource()).isEqualTo("exobios-ai-stub");
        assertThat(response.getSummary()).containsIgnoringCase("not implemented");
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
