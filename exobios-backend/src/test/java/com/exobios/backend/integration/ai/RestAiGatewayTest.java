package com.exobios.backend.integration.ai;

import com.exobios.backend.assessments.entity.enums.AiResultStatus;
import com.exobios.backend.assessments.entity.enums.ComplaintCategory;
import com.sun.net.httpserver.HttpServer;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Timeout;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.util.UUID;
import java.util.concurrent.TimeUnit;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Regression test for a real bug found during the 2026-08 audit: if
 * exobios-ai ever returns a 2xx with an empty/null body, RestAiGateway's
 * retry loop never incremented `attempts` in that branch (only the
 * RestClientException catch block did) — a null-but-non-exceptional
 * response spun the loop forever instead of retrying/falling through to
 * AiResponse.placeholder(). Uses a real embedded HTTP server (JDK's
 * com.sun.net.httpserver, no new test dependency) rather than a mock, so
 * this exercises the actual RestClient construction/behavior, not a stub.
 */
class RestAiGatewayTest {

    private HttpServer server;

    @AfterEach
    void tearDown() {
        if (server != null) {
            server.stop(0);
        }
    }

    private RestAiGateway gatewayFor(int port) {
        AiConfiguration config = new AiConfiguration();
        config.setBaseUrl("http://localhost:" + port);
        config.setApiKey("test-key");
        config.setConnectTimeoutMs(2000);
        config.setReadTimeoutMs(2000);
        return new RestAiGateway(config);
    }

    private AiRequest sampleRequest() {
        return AiRequest.builder()
                .assessmentId(UUID.randomUUID())
                .patientId(UUID.randomUUID())
                .complaintCategory(ComplaintCategory.FEVER)
                .build();
    }

    @Test
    @Timeout(value = 15, unit = TimeUnit.SECONDS)
    void emptyBodyResponseDoesNotHangForeverAndFallsBackToPlaceholder() throws IOException {
        server = HttpServer.create(new InetSocketAddress("localhost", 0), 0);
        server.createContext("/analyze", exchange -> {
            // 200 with a fully empty body — this is exactly the case that
            // used to spin the retry loop forever.
            exchange.sendResponseHeaders(200, -1);
            exchange.close();
        });
        server.start();

        AiResponse response = gatewayFor(server.getAddress().getPort()).analyzeAssessment(sampleRequest());

        assertThat(response).isNotNull();
        assertThat(response.getStatus()).isEqualTo(AiResultStatus.FAILED);
        assertThat(response.getRiskLevel()).isNull();
        assertThat(response.getConfidenceScore()).isNull();
    }

    @Test
    @Timeout(value = 15, unit = TimeUnit.SECONDS)
    void serverErrorFallsBackToPlaceholderWithoutHanging() throws IOException {
        server = HttpServer.create(new InetSocketAddress("localhost", 0), 0);
        server.createContext("/analyze", exchange -> {
            byte[] body = "{}".getBytes();
            exchange.sendResponseHeaders(500, body.length);
            exchange.getResponseBody().write(body);
            exchange.close();
        });
        server.start();

        AiResponse response = gatewayFor(server.getAddress().getPort()).analyzeAssessment(sampleRequest());

        assertThat(response.getStatus()).isEqualTo(AiResultStatus.FAILED);
    }
}
