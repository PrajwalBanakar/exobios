package com.exobios.backend.auth.service;

import com.exobios.backend.auth.dto.LoginRequest;
import com.exobios.backend.auth.dto.LoginResponse;
import com.exobios.backend.auth.dto.RefreshTokenRequest;
import com.exobios.backend.auth.dto.RefreshTokenResponse;
import com.exobios.backend.auth.exception.InvalidCredentialsException;
import com.exobios.backend.security.UserPrincipal;
import com.exobios.backend.security.jwt.JwtProperties;
import com.exobios.backend.security.jwt.JwtTokenProvider;
import com.exobios.backend.users.entity.User;
import com.exobios.backend.users.entity.enums.UserStatus;
import com.exobios.backend.users.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.DisabledException;
import org.springframework.security.authentication.LockedException;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.stereotype.Service;

import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class AuthService {

    private final AuthenticationManager authenticationManager;
    private final UserRepository        userRepository;
    private final JwtTokenProvider      tokenProvider;
    private final JwtProperties         jwtProperties;
    private final RefreshTokenService   refreshTokenService;

    public LoginResponse login(LoginRequest request) {
        try {
            Authentication authentication = authenticationManager.authenticate(
                    new UsernamePasswordAuthenticationToken(request.getPhone(), request.getPassword())
            );
            UserPrincipal principal = (UserPrincipal) authentication.getPrincipal();
            User user = userRepository.findById(principal.getId())
                    .orElseThrow(InvalidCredentialsException::new);

            String accessToken  = tokenProvider.generateAccessToken(principal);
            String refreshToken = refreshTokenService.createRefreshToken(principal.getId().toString());

            log.info("Login: id={} role={}", principal.getId(), principal.getRole());
            return buildResponse(accessToken, refreshToken, user);

        } catch (BadCredentialsException | DisabledException | LockedException e) {
            throw new InvalidCredentialsException();
        }
    }

    public RefreshTokenResponse refresh(RefreshTokenRequest request) {
        String userId = refreshTokenService.validateAndGetUserId(request.getRefreshToken());
        User user = userRepository.findById(UUID.fromString(userId))
                .orElseThrow(InvalidCredentialsException::new);

        if (user.getStatus() != UserStatus.ACTIVE) {
            refreshTokenService.deleteByToken(request.getRefreshToken());
            throw new InvalidCredentialsException();
        }

        UserPrincipal principal = UserPrincipal.from(
                user.getId(), user.getPhone(), null, user.getRole().name(), true);
        String newAccessToken = tokenProvider.generateAccessToken(principal);

        return RefreshTokenResponse.builder()
                .accessToken(newAccessToken)
                .tokenType("Bearer")
                .expiresIn(jwtProperties.getAccessTokenExpiryMs() / 1000)
                .build();
    }

    public void logout(String userId) {
        refreshTokenService.deleteByUserId(userId);
        log.info("Logout: id={}", userId);
    }

    private LoginResponse buildResponse(String accessToken, String refreshToken, User user) {
        return LoginResponse.builder()
                .accessToken(accessToken)
                .refreshToken(refreshToken)
                .tokenType("Bearer")
                .expiresIn(jwtProperties.getAccessTokenExpiryMs() / 1000)
                .user(LoginResponse.UserInfo.builder()
                        .id(user.getId())
                        .name(user.getName())
                        .phone(user.getPhone())
                        .role(user.getRole())
                        .build())
                .build();
    }
}
