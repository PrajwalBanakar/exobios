package com.exobios.backend.testsupport;

import com.exobios.backend.security.UserPrincipal;
import com.exobios.backend.security.jwt.JwtTokenProvider;
import com.exobios.backend.users.entity.enums.Role;

import java.util.UUID;

/**
 * Mints real, validly-signed JWT bearer-token header values for {@code @WebMvcTest}
 * controller tests, using the same {@link JwtTokenProvider} bean the running app uses.
 * Going through a real token (rather than stubbing the SecurityContext directly) means
 * these tests exercise the actual {@code JwtAuthenticationFilter} + {@code @PreAuthorize}
 * pipeline, not a bypass of it.
 */
public final class JwtTestSupport {

    private JwtTestSupport() {}

    public static String ashaBearer(JwtTokenProvider provider, UUID userId, String phone) {
        return bearer(provider, userId, phone, Role.ASHA.name());
    }

    public static String adminBearer(JwtTokenProvider provider, UUID userId, String phone) {
        return bearer(provider, userId, phone, Role.SUPER_ADMIN.name());
    }

    public static String bearer(JwtTokenProvider provider, UUID userId, String phone, String role) {
        UserPrincipal principal = UserPrincipal.fromToken(userId.toString(), phone, role);
        return "Bearer " + provider.generateAccessToken(principal);
    }
}
