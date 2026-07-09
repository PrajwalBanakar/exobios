package com.exobios.backend.testsupport;

import com.exobios.backend.config.JpaAuditingConfig;
import org.springframework.boot.test.autoconfigure.jdbc.AutoConfigureTestDatabase;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.PostgreSQLContainer;

/**
 * Base class for repository integration tests. Boots a real PostgreSQL container via
 * Testcontainers, lets Flyway migrate it exactly as production would, and runs each
 * repository against that real schema — entity mappings, constraints, and native/derived
 * queries are all exercised for real, not against an H2 stand-in.
 *
 * The container uses the manual "singleton container" pattern (started once in a static
 * initializer, wired via {@code @DynamicPropertySource}) rather than {@code @Testcontainers}
 * + {@code @Container}/{@code @ServiceConnection}. The latter only guarantees reuse of a
 * static container *within* one test class's lifecycle — across multiple subclasses in the
 * same JVM it was observed starting a brand-new container per class (visible as distinct
 * container names/ports in `docker ps` between classes), leaving earlier subclasses' Spring
 * contexts pointed at a now-stopped container. Never call {@code POSTGRES.stop()} — cleanup
 * is left to Ryuk / JVM shutdown so the single instance survives for the whole test run.
 *
 * {@link JpaAuditingConfig} (which hosts {@code @EnableJpaAuditing}) must be imported
 * explicitly — {@code @DataJpaTest} doesn't component-scan arbitrary {@code @Configuration}
 * classes, but {@code created_at}/{@code updated_at} are {@code NOT NULL} columns that only
 * get populated when auditing is active.
 */
@DataJpaTest
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
@ActiveProfiles("test")
@Import(JpaAuditingConfig.class)
public abstract class AbstractRepositoryIT {

    static final PostgreSQLContainer<?> POSTGRES = new PostgreSQLContainer<>("postgres:16-alpine");

    static {
        POSTGRES.start();
    }

    @DynamicPropertySource
    static void registerDatasourceProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", POSTGRES::getJdbcUrl);
        registry.add("spring.datasource.username", POSTGRES::getUsername);
        registry.add("spring.datasource.password", POSTGRES::getPassword);
    }
}
