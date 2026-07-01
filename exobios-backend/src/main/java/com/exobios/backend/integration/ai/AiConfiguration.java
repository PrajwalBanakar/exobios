package com.exobios.backend.integration.ai;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Component
@ConfigurationProperties(prefix = "app.ai")
@Getter
@Setter
public class AiConfiguration {

    private String baseUrl        = "http://localhost:8000";
    private String apiKey         = "";
    private int    connectTimeoutMs = 5000;
    private int    readTimeoutMs    = 30000;
}
