# ── Stage 1: Build ────────────────────────────────────────────────────────────
FROM maven:3.9.6-eclipse-temurin-21 AS builder

WORKDIR /build

# Download dependencies as a separate layer so they're cached on re-builds
COPY pom.xml .
RUN mvn dependency:go-offline -B -q

COPY src/ src/
RUN mvn package -DskipTests -B -q

# ── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM eclipse-temurin:21-jre-alpine AS runtime

# Non-root user
RUN addgroup -S exobios && adduser -S exobios -G exobios

WORKDIR /app

COPY --from=builder /build/target/*.jar app.jar

# Local upload storage directory
RUN mkdir -p /app/uploads && chown -R exobios:exobios /app

USER exobios

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD wget -qO- http://localhost:8080/api/actuator/health | grep -q '"status":"UP"' || exit 1

ENTRYPOINT ["java", \
  "-XX:+UseContainerSupport", \
  "-XX:MaxRAMPercentage=75.0", \
  "-Djava.security.egd=file:/dev/./urandom", \
  "-jar", "app.jar"]
