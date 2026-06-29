package com.exobios.backend.common.utils;

import com.exobios.backend.common.constants.AppConstants;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;

public final class SecurityUtils {

    private SecurityUtils() {}

    /**
     * Returns the username of the currently authenticated user,
     * or {@code SYSTEM} if no authenticated user exists in the security context.
     * Will delegate to the real JWT principal once auth is implemented.
     */
    public static String getCurrentUsername() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth == null || !auth.isAuthenticated() || isAnonymous(auth)) {
            return AppConstants.SYSTEM_USER;
        }
        return auth.getName();
    }

    public static boolean isAuthenticated() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        return auth != null && auth.isAuthenticated() && !isAnonymous(auth);
    }

    private static boolean isAnonymous(Authentication auth) {
        return "anonymousUser".equals(auth.getPrincipal());
    }
}
