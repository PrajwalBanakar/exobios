package com.exobios.backend.assessments.dto;

import jakarta.validation.ConstraintViolation;
import jakarta.validation.Validation;
import jakarta.validation.Validator;
import jakarta.validation.ValidatorFactory;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.util.Set;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * VitalsRequest.temperature used to be validated as Celsius (30.0-45.0, with
 * "°C" messages) while every other part of the product — the frontend
 * (labeled "(°F)" throughout) and exobios-ai's rule engine (104/102
 * thresholds) — treats it as Fahrenheit. A real Fahrenheit body temperature
 * like 100.8 would have FAILED this validation outright. See the 2026-08
 * audit's Priority 2 for the full cross-service trace.
 */
class VitalsRequestTest {

    private static ValidatorFactory factory;
    private static Validator validator;

    @BeforeAll
    static void setUp() {
        factory = Validation.buildDefaultValidatorFactory();
        validator = factory.getValidator();
    }

    @AfterAll
    static void tearDown() {
        factory.close();
    }

    private VitalsRequest requestWithTemperature(double temperature) {
        VitalsRequest req = new VitalsRequest();
        req.setTemperature(BigDecimal.valueOf(temperature));
        return req;
    }

    @Test
    void acceptsARealFahrenheitFeverValue() {
        // 100.8F — a real, plausible mild-fever reading. Previously rejected
        // outright by the old 30.0-45.0 Celsius bound.
        Set<ConstraintViolation<VitalsRequest>> violations = validator.validate(requestWithTemperature(100.8));
        assertThat(violations).isEmpty();
    }

    @Test
    void acceptsNormalBodyTemperature() {
        Set<ConstraintViolation<VitalsRequest>> violations = validator.validate(requestWithTemperature(98.6));
        assertThat(violations).isEmpty();
    }

    @Test
    void rejectsAValueThatWasOnlyValidUnderTheOldCelsiusBound() {
        // 38.2 was a real value used by this codebase's own prior test
        // fixtures under the old (wrong) Celsius bound — it must now be
        // rejected, since 38.2F is not a physiologically real body
        // temperature for a living patient.
        Set<ConstraintViolation<VitalsRequest>> violations = validator.validate(requestWithTemperature(38.2));
        assertThat(violations).isNotEmpty();
    }

    @Test
    void rejectsBelowFahrenheitFloor() {
        Set<ConstraintViolation<VitalsRequest>> violations = validator.validate(requestWithTemperature(85.9));
        assertThat(violations).isNotEmpty();
    }

    @Test
    void rejectsAboveFahrenheitCeiling() {
        Set<ConstraintViolation<VitalsRequest>> violations = validator.validate(requestWithTemperature(113.1));
        assertThat(violations).isNotEmpty();
    }

    @Test
    void acceptsExactBoundaryValues() {
        assertThat(validator.validate(requestWithTemperature(86.0))).isEmpty();
        assertThat(validator.validate(requestWithTemperature(113.0))).isEmpty();
    }
}
