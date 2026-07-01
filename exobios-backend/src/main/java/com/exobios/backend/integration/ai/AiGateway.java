package com.exobios.backend.integration.ai;

public interface AiGateway {

    AiResponse analyzeAssessment(AiRequest request);

    boolean health();
}
