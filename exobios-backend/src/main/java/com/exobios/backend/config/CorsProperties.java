package com.exobios.backend.config;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;

@Getter
@Setter
@ConfigurationProperties(prefix = "app.cors")
public class CorsProperties {

    /** Comma-separated list of allowed origins. Supports wildcards for subdomains in dev. */
    private String allowedOrigins = "http://localhost:5173";
}
