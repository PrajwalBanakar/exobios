package com.exobios.backend.security;

import com.exobios.backend.analytics.controller.AnalyticsController;
import com.exobios.backend.analytics.service.AnalyticsService;
import com.exobios.backend.assessments.controller.AssessmentController;
import com.exobios.backend.assessments.service.AssessmentService;
import com.exobios.backend.auth.controller.AuthController;
import com.exobios.backend.auth.service.AuthService;
import com.exobios.backend.measures.controller.MeasureController;
import com.exobios.backend.measures.service.MeasureService;
import com.exobios.backend.notifications.controller.NotificationController;
import com.exobios.backend.notifications.service.NotificationService;
import com.exobios.backend.patients.controller.PatientController;
import com.exobios.backend.patients.service.PatientService;
import com.exobios.backend.referrals.controller.ReferralController;
import com.exobios.backend.referrals.service.ReferralService;
import com.exobios.backend.sos.controller.SosController;
import com.exobios.backend.sos.service.SosService;
import com.exobios.backend.testsupport.AbstractControllerTest;
import com.exobios.backend.testsupport.JwtTestSupport;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.HttpMethod;

import java.util.UUID;
import java.util.stream.Stream;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.request;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * A consolidated sweep across every protected endpoint on the 8 required controllers,
 * complementing (not duplicating) the per-endpoint 401/403 assertions already embedded in
 * each controller's own test class. Its job is different: catch the case where a *new*
 * endpoint gets added to one of these controllers without inheriting the class-level
 * {@code @PreAuthorize}, or where the security filter chain regresses for the API surface
 * as a whole. Login/refresh are intentionally excluded — they're the two endpoints meant to
 * be public, and are covered by {@code AuthControllerTest}.
 */
@WebMvcTest(controllers = {
        AuthController.class,
        PatientController.class,
        AssessmentController.class,
        MeasureController.class,
        ReferralController.class,
        SosController.class,
        NotificationController.class,
        AnalyticsController.class,
})
class SecurityAccessSweepTest extends AbstractControllerTest {

    @MockBean private AuthService authService;
    @MockBean private PatientService patientService;
    @MockBean private AssessmentService assessmentService;
    @MockBean private MeasureService measureService;
    @MockBean private ReferralService referralService;
    @MockBean private SosService sosService;
    @MockBean private NotificationService notificationService;
    @MockBean private AnalyticsService analyticsService;

    private static final UUID ID = UUID.randomUUID();

    /** Every protected endpoint across the 8 required controllers. */
    static Stream<Arguments> protectedEndpoints() {
        return Stream.of(
                Arguments.of(HttpMethod.POST, "/api/v1/auth/logout"),

                Arguments.of(HttpMethod.GET, "/api/v1/patients"),
                Arguments.of(HttpMethod.GET, "/api/v1/patients/" + ID),
                Arguments.of(HttpMethod.POST, "/api/v1/patients"),
                Arguments.of(HttpMethod.PUT, "/api/v1/patients/" + ID),
                Arguments.of(HttpMethod.PATCH, "/api/v1/patients/" + ID + "/status"),

                Arguments.of(HttpMethod.POST, "/api/v1/assessments"),
                Arguments.of(HttpMethod.GET, "/api/v1/assessments/" + ID),
                Arguments.of(HttpMethod.GET, "/api/v1/patients/" + ID + "/assessments"),
                Arguments.of(HttpMethod.PUT, "/api/v1/assessments/" + ID),
                Arguments.of(HttpMethod.PATCH, "/api/v1/assessments/" + ID + "/submit"),

                Arguments.of(HttpMethod.POST, "/api/v1/measures"),
                Arguments.of(HttpMethod.GET, "/api/v1/measures/" + ID),
                Arguments.of(HttpMethod.GET, "/api/v1/measures"),
                Arguments.of(HttpMethod.GET, "/api/v1/assessments/" + ID + "/measures"),
                Arguments.of(HttpMethod.PUT, "/api/v1/measures/" + ID),
                Arguments.of(HttpMethod.DELETE, "/api/v1/measures/" + ID),

                Arguments.of(HttpMethod.POST, "/api/v1/referrals"),
                Arguments.of(HttpMethod.GET, "/api/v1/referrals/" + ID),
                Arguments.of(HttpMethod.GET, "/api/v1/referrals"),
                Arguments.of(HttpMethod.GET, "/api/v1/assessments/" + ID + "/referrals"),
                Arguments.of(HttpMethod.GET, "/api/v1/patients/" + ID + "/referrals"),
                Arguments.of(HttpMethod.PUT, "/api/v1/referrals/" + ID),
                Arguments.of(HttpMethod.PATCH, "/api/v1/referrals/" + ID + "/status"),
                Arguments.of(HttpMethod.DELETE, "/api/v1/referrals/" + ID),

                Arguments.of(HttpMethod.POST, "/api/v1/sos"),
                Arguments.of(HttpMethod.GET, "/api/v1/sos/" + ID),
                Arguments.of(HttpMethod.GET, "/api/v1/sos"),
                Arguments.of(HttpMethod.PATCH, "/api/v1/sos/" + ID + "/status"),

                Arguments.of(HttpMethod.GET, "/api/v1/notifications"),
                Arguments.of(HttpMethod.PATCH, "/api/v1/notifications/" + ID + "/read"),
                Arguments.of(HttpMethod.POST, "/api/v1/notifications/mark-all-read"),

                Arguments.of(HttpMethod.GET, "/api/v1/analytics/dashboard"),
                Arguments.of(HttpMethod.GET, "/api/v1/analytics/asha-performance"),
                Arguments.of(HttpMethod.GET, "/api/v1/analytics/risk-summary"),
                Arguments.of(HttpMethod.GET, "/api/v1/analytics/referral-summary"),
                Arguments.of(HttpMethod.GET, "/api/v1/analytics/village-summary"),
                Arguments.of(HttpMethod.GET, "/api/v1/analytics/export/asha-performance.csv")
        );
    }

    /** SUPER_ADMIN-only endpoints — ASHA must be forbidden, not merely unauthenticated. */
    static Stream<Arguments> superAdminOnlyGetEndpoints() {
        return Stream.of(
                Arguments.of(HttpMethod.GET, "/api/v1/analytics/dashboard"),
                Arguments.of(HttpMethod.GET, "/api/v1/analytics/asha-performance"),
                Arguments.of(HttpMethod.GET, "/api/v1/analytics/risk-summary"),
                Arguments.of(HttpMethod.GET, "/api/v1/analytics/referral-summary"),
                Arguments.of(HttpMethod.GET, "/api/v1/analytics/village-summary"),
                Arguments.of(HttpMethod.GET, "/api/v1/analytics/export/asha-performance.csv")
        );
    }

    @ParameterizedTest(name = "{0} {1} without any Authorization header returns 401")
    @MethodSource("protectedEndpoints")
    void withoutToken_returnsUnauthorized(HttpMethod method, String path) throws Exception {
        mockMvc.perform(request(method, path))
                .andExpect(status().isUnauthorized());
    }

    @ParameterizedTest(name = "{0} {1} with a malformed bearer token returns 401")
    @MethodSource("protectedEndpoints")
    void withMalformedToken_returnsUnauthorized(HttpMethod method, String path) throws Exception {
        mockMvc.perform(request(method, path).header("Authorization", "Bearer not-a-real-jwt"))
                .andExpect(status().isUnauthorized());
    }

    @ParameterizedTest(name = "{0} {1} as ASHA returns 403 (SUPER_ADMIN only)")
    @MethodSource("superAdminOnlyGetEndpoints")
    void ashaRole_isForbiddenFromSuperAdminOnlyEndpoints(HttpMethod method, String path) throws Exception {
        mockMvc.perform(request(method, path)
                        .header("Authorization", JwtTestSupport.ashaBearer(jwtTokenProvider, UUID.randomUUID(), "9876500001")))
                .andExpect(status().isForbidden());
    }
}
