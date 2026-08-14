package com.exobios.backend.integration.ai;

import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

import java.time.Duration;

@Slf4j
@Component
public class RestAiGateway implements AiGateway {

    private final RestClient restClient;

    public RestAiGateway(AiConfiguration config) {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(Duration.ofMillis(config.getConnectTimeoutMs()));
        factory.setReadTimeout(Duration.ofMillis(config.getReadTimeoutMs()));

        this.restClient = RestClient.builder()
                .baseUrl(config.getBaseUrl())
                .requestFactory(factory)
                .defaultHeader("X-Api-Key", config.getApiKey())
                .defaultHeader("Content-Type", MediaType.APPLICATION_JSON_VALUE)
                .build();
    }

    @Override
    public AiResponse analyzeAssessment(AiRequest request) {
        int attempts = 0;
        int maxRetries = 2;

        while (attempts <= maxRetries) {
            try {
                AiResponse response = restClient.post()
                        .uri("/analyze")
                        .body(request)
                        .retrieve()
                        .body(AiResponse.class);

                if (response != null) {
                    log.debug("AI gateway responded for assessment {}", request.getAssessmentId());
                    return response;
                }
                // A 2xx with a null/empty body isn't a RestClientException, so it
                // wasn't caught below — but `attempts` still has to advance here,
                // or a null-body response makes this loop spin forever instead of
                // retrying/falling through to the placeholder like any other
                // failure mode does.
                attempts++;
                log.warn("AI gateway returned an empty body for assessment {} (attempt {}/{})",
                        request.getAssessmentId(), attempts, maxRetries);
            } catch (RestClientException e) {
                attempts++;
                if (attempts > maxRetries) {
                    log.warn("AI service unavailable after {} attempt(s) for assessment {}: {}",
                            attempts, request.getAssessmentId(), e.getMessage());
                } else {
                    log.debug("AI gateway attempt {}/{} failed, retrying…", attempts, maxRetries);
                }
            }
        }

        return AiResponse.placeholder();
    }

    @Override
    public boolean health() {
        try {
            restClient.get()
                    .uri("/health")
                    .retrieve()
                    .toBodilessEntity();
            return true;
        } catch (RestClientException e) {
            log.debug("AI service health check failed: {}", e.getMessage());
            return false;
        }
    }
}
