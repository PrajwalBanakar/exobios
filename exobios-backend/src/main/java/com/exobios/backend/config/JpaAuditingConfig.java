package com.exobios.backend.config;

import com.exobios.backend.common.utils.SecurityUtils;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.domain.AuditorAware;
import org.springframework.data.jpa.repository.config.EnableJpaAuditing;

import java.util.Optional;

/**
 * {@code @EnableJpaAuditing} lives here rather than directly on {@code ExobiosApplication}
 * so that {@code @WebMvcTest} slices (which use the main {@code @SpringBootConfiguration}
 * class as their root config, inheriting any annotations placed directly on it) don't try
 * to instantiate JPA auditing infrastructure that requires an {@code EntityManagerFactory}
 * the web slice never loads.
 */
@Configuration
@EnableJpaAuditing
public class JpaAuditingConfig {

    @Bean
    public AuditorAware<String> auditorProvider() {
        return () -> Optional.of(SecurityUtils.getCurrentUsername());
    }
}
