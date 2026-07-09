package com.exobios.backend.auth.service;

import com.exobios.backend.common.exception.UnauthorizedException;
import com.exobios.backend.security.jwt.JwtProperties;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

/**
 * In-memory refresh token store — one active token per user.
 * Will be replaced with a database-backed store in a later phase.
 */
@Service
@RequiredArgsConstructor
public class RefreshTokenService {

    private final JwtProperties jwtProperties;

    private record TokenEntry(String userId, Instant issuedAt) {}

    private final Map<String, TokenEntry> store = new ConcurrentHashMap<>();

    public String createRefreshToken(String userId) {
        store.entrySet().removeIf(e -> e.getValue().userId().equals(userId));
        String token = UUID.randomUUID().toString();
        store.put(token, new TokenEntry(userId, Instant.now()));
        return token;
    }

    public String validateAndGetUserId(String token) {
        TokenEntry entry = store.get(token);
        if (entry == null) {
            throw new UnauthorizedException("Refresh token is invalid or has expired");
        }
        Instant expiresAt = entry.issuedAt().plusMillis(jwtProperties.getRefreshTokenExpiryMs());
        if (Instant.now().isAfter(expiresAt)) {
            store.remove(token);
            throw new UnauthorizedException("Refresh token is invalid or has expired");
        }
        return entry.userId();
    }

    public void deleteByToken(String token) {
        store.remove(token);
    }

    public void deleteByUserId(String userId) {
        store.entrySet().removeIf(e -> e.getValue().userId().equals(userId));
    }
}
