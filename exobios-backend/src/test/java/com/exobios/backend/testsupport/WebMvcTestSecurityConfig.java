package com.exobios.backend.testsupport;

import com.exobios.backend.config.CorsProperties;
import com.exobios.backend.security.jwt.JwtProperties;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Bean;

/**
 * Supplies the two {@code @ConfigurationProperties} beans that {@code SecurityConfig}
 * depends on ({@link JwtProperties}, {@link CorsProperties}). These are normally bound
 * automatically via {@code @ConfigurationPropertiesScan} on the main application class,
 * but a {@code @WebMvcTest} slice doesn't pick that up — so controller tests that
 * {@code @Import(SecurityConfig.class)} need this alongside it to build a working
 * security filter chain (real JWT signing/parsing, real {@code @PreAuthorize} enforcement).
 */
@TestConfiguration
public class WebMvcTestSecurityConfig {

    static final String TEST_JWT_SECRET =
            "test-only-secret-key-for-jwt-signing-must-be-at-least-256-bits-long";

    @Bean
    public JwtProperties jwtProperties() {
        JwtProperties props = new JwtProperties();
        props.setSecret(TEST_JWT_SECRET);
        props.setAccessTokenExpiryMs(3_600_000L);
        props.setRefreshTokenExpiryMs(604_800_000L);
        return props;
    }

    @Bean
    public CorsProperties corsProperties() {
        CorsProperties props = new CorsProperties();
        props.setAllowedOrigins("http://localhost:5173");
        return props;
    }
}
