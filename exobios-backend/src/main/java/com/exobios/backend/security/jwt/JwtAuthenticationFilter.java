package com.exobios.backend.security.jwt;

import com.exobios.backend.common.constants.AppConstants;
import com.exobios.backend.security.UserPrincipal;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.lang.NonNull;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.util.StringUtils;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

/**
 * Not a @Component — registered directly in SecurityConfig to prevent Spring Boot
 * from also registering it as a standalone servlet filter (which would run it twice).
 */
@Slf4j
@RequiredArgsConstructor
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private final JwtTokenProvider tokenProvider;

    @Override
    protected void doFilterInternal(
            @NonNull HttpServletRequest request,
            @NonNull HttpServletResponse response,
            @NonNull FilterChain filterChain) throws ServletException, IOException {
        try {
            String token = extractToken(request);
            if (StringUtils.hasText(token) && tokenProvider.validateToken(token)) {
                String userId = tokenProvider.extractUserId(token);
                String phone  = tokenProvider.extractPhone(token);
                String role   = tokenProvider.extractRole(token);

                UserPrincipal principal = UserPrincipal.fromToken(userId, phone, role);
                UsernamePasswordAuthenticationToken auth =
                        new UsernamePasswordAuthenticationToken(principal, null, principal.getAuthorities());
                auth.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));
                SecurityContextHolder.getContext().setAuthentication(auth);
            }
        } catch (Exception ex) {
            log.error("JWT filter error on {}: {}", request.getRequestURI(), ex.getMessage());
        }
        filterChain.doFilter(request, response);
    }

    private String extractToken(HttpServletRequest request) {
        String header = request.getHeader(AppConstants.AUTHORIZATION_HEADER);
        if (StringUtils.hasText(header) && header.startsWith(AppConstants.BEARER_PREFIX)) {
            return header.substring(AppConstants.BEARER_PREFIX.length());
        }
        return null;
    }
}
