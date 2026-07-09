package com.exobios.backend;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.annotation.EnableScheduling;

// @EnableJpaAuditing lives on JpaAuditingConfig (see its Javadoc) rather than here, to
// keep it out of @WebMvcTest slices that use this class as their root configuration.
@SpringBootApplication
@ConfigurationPropertiesScan
@EnableAsync
@EnableScheduling
public class ExobiosApplication {

    public static void main(String[] args) {
        SpringApplication.run(ExobiosApplication.class, args);
    }
}
