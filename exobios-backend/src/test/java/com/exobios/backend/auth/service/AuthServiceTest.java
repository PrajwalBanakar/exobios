package com.exobios.backend.auth.service;

import com.exobios.backend.auth.dto.LoginRequest;
import com.exobios.backend.auth.dto.LoginResponse;
import com.exobios.backend.auth.dto.RefreshTokenRequest;
import com.exobios.backend.auth.dto.RefreshTokenResponse;
import com.exobios.backend.auth.exception.InvalidCredentialsException;
import com.exobios.backend.common.exception.UnauthorizedException;
import com.exobios.backend.security.UserPrincipal;
import com.exobios.backend.security.jwt.JwtProperties;
import com.exobios.backend.security.jwt.JwtTokenProvider;
import com.exobios.backend.users.entity.User;
import com.exobios.backend.users.entity.enums.Role;
import com.exobios.backend.users.entity.enums.UserStatus;
import com.exobios.backend.users.repository.UserRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.DisabledException;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.test.util.ReflectionTestUtils;

import java.util.Optional;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class AuthServiceTest {

    @Mock private AuthenticationManager authenticationManager;
    @Mock private UserRepository        userRepository;
    @Mock private JwtTokenProvider      tokenProvider;
    @Mock private RefreshTokenService   refreshTokenService;

    private JwtProperties jwtProperties;
    private AuthService   authService;

    private final UUID userId = UUID.randomUUID();

    @BeforeEach
    void setUp() {
        jwtProperties = new JwtProperties();
        jwtProperties.setAccessTokenExpiryMs(3_600_000L);
        authService = new AuthService(authenticationManager, userRepository, tokenProvider, jwtProperties, refreshTokenService);
    }

    private User activeUser() {
        User user = new User();
        ReflectionTestUtils.setField(user, "id", userId);
        user.setPhone("9876543210");
        user.setName("Sunita Devi");
        user.setRole(Role.ASHA);
        user.setStatus(UserStatus.ACTIVE);
        return user;
    }

    // ── login() ──────────────────────────────────────────────────────────────────

    @Test
    void login_withValidCredentials_returnsTokensAndUserInfo() {
        LoginRequest request = new LoginRequest();
        request.setPhone("9876543210");
        request.setPassword("correct-password");

        UserPrincipal principal = UserPrincipal.from(userId, "9876543210", "hash", "ASHA", true);
        Authentication auth = new UsernamePasswordAuthenticationToken(principal, null, principal.getAuthorities());
        when(authenticationManager.authenticate(any())).thenReturn(auth);
        when(userRepository.findById(userId)).thenReturn(Optional.of(activeUser()));
        when(tokenProvider.generateAccessToken(principal)).thenReturn("access-token");
        when(refreshTokenService.createRefreshToken(userId.toString())).thenReturn("refresh-token");

        LoginResponse response = authService.login(request);

        assertThat(response.getAccessToken()).isEqualTo("access-token");
        assertThat(response.getRefreshToken()).isEqualTo("refresh-token");
        assertThat(response.getExpiresIn()).isEqualTo(3600L);
        assertThat(response.getUser().getId()).isEqualTo(userId);
        assertThat(response.getUser().getRole()).isEqualTo(Role.ASHA);
    }

    @Test
    void login_withBadCredentials_throwsInvalidCredentialsException() {
        LoginRequest request = new LoginRequest();
        request.setPhone("9876543210");
        request.setPassword("wrong-password");
        when(authenticationManager.authenticate(any())).thenThrow(new BadCredentialsException("bad"));

        assertThatThrownBy(() -> authService.login(request))
                .isInstanceOf(InvalidCredentialsException.class);
    }

    @Test
    void login_withDisabledAccount_throwsInvalidCredentialsException() {
        LoginRequest request = new LoginRequest();
        request.setPhone("9876543210");
        request.setPassword("x");
        when(authenticationManager.authenticate(any())).thenThrow(new DisabledException("disabled"));

        assertThatThrownBy(() -> authService.login(request))
                .isInstanceOf(InvalidCredentialsException.class);
    }

    @Test
    void login_whenPrincipalUserNoLongerExists_throwsInvalidCredentialsException() {
        LoginRequest request = new LoginRequest();
        request.setPhone("9876543210");
        request.setPassword("x");
        UserPrincipal principal = UserPrincipal.from(userId, "9876543210", "hash", "ASHA", true);
        Authentication auth = new UsernamePasswordAuthenticationToken(principal, null, principal.getAuthorities());
        when(authenticationManager.authenticate(any())).thenReturn(auth);
        when(userRepository.findById(userId)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> authService.login(request))
                .isInstanceOf(InvalidCredentialsException.class);
    }

    // ── refresh() ────────────────────────────────────────────────────────────────

    @Test
    void refresh_withValidToken_returnsNewAccessToken() {
        RefreshTokenRequest request = new RefreshTokenRequest();
        request.setRefreshToken("valid-refresh-token");
        when(refreshTokenService.validateAndGetUserId("valid-refresh-token")).thenReturn(userId.toString());
        when(userRepository.findById(userId)).thenReturn(Optional.of(activeUser()));
        when(tokenProvider.generateAccessToken(any())).thenReturn("new-access-token");

        RefreshTokenResponse response = authService.refresh(request);

        assertThat(response.getAccessToken()).isEqualTo("new-access-token");
        assertThat(response.getExpiresIn()).isEqualTo(3600L);
    }

    @Test
    void refresh_withExpiredOrUnknownToken_propagatesUnauthorizedException() {
        RefreshTokenRequest request = new RefreshTokenRequest();
        request.setRefreshToken("bad-token");
        when(refreshTokenService.validateAndGetUserId("bad-token"))
                .thenThrow(new UnauthorizedException("Refresh token is invalid or has expired"));

        assertThatThrownBy(() -> authService.refresh(request))
                .isInstanceOf(UnauthorizedException.class);
    }

    @Test
    void refresh_forInactiveUser_deletesTokenAndThrowsInvalidCredentials() {
        RefreshTokenRequest request = new RefreshTokenRequest();
        request.setRefreshToken("valid-refresh-token");
        User inactiveUser = activeUser();
        inactiveUser.setStatus(UserStatus.SUSPENDED);
        when(refreshTokenService.validateAndGetUserId("valid-refresh-token")).thenReturn(userId.toString());
        when(userRepository.findById(userId)).thenReturn(Optional.of(inactiveUser));

        assertThatThrownBy(() -> authService.refresh(request))
                .isInstanceOf(InvalidCredentialsException.class);

        verify(refreshTokenService).deleteByToken("valid-refresh-token");
    }

    // ── logout() ─────────────────────────────────────────────────────────────────

    @Test
    void logout_invalidatesAllRefreshTokensForThatUser() {
        authService.logout(userId.toString());

        verify(refreshTokenService).deleteByUserId(userId.toString());
    }
}
