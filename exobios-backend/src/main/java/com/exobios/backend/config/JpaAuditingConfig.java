package com.exobios.backend.config;

import com.exobios.backend.common.utils.SecurityUtils;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.domain.AuditorAware;

import java.util.Optional;

@Configuration
public class JpaAuditingConfig {

    @Bean
    public AuditorAware<String> auditorProvider() {
        return () -> Optional.of(SecurityUtils.getCurrentUsername());
    }
}
