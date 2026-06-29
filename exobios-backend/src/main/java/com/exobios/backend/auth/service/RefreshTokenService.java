package com.exobios.backend.auth.service;

import com.exobios.backend.common.exception.UnauthorizedException;
import org.springframework.stereotype.Service;

import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

/**
 * In-memory refresh token store — one active token per user.
 * Will be replaced with a database-backed store in a later phase.
 */
@Service
public class RefreshTokenService {

    private final ConcurrentHashMap<String, String> store = new ConcurrentHashMap<>();

    public String createRefreshToken(String userId) {
        store.entrySet().removeIf(e -> e.getValue().equals(userId));
        String token = UUID.randomUUID().toString();
        store.put(token, userId);
        return token;
    }

    public String validateAndGetUserId(String token) {
        String userId = store.get(token);
        if (userId == null) {
            throw new UnauthorizedException("Refresh token is invalid or has expired");
        }
        return userId;
    }

    public void deleteByToken(String token) {
        store.remove(token);
    }

    public void deleteByUserId(String userId) {
        store.entrySet().removeIf(e -> e.getValue().equals(userId));
    }
}
