package com.exobios.backend.auth.controller;

import com.exobios.backend.auth.dto.LoginRequest;
import com.exobios.backend.auth.dto.LoginResponse;
import com.exobios.backend.auth.dto.RefreshTokenRequest;
import com.exobios.backend.auth.dto.RefreshTokenResponse;
import com.exobios.backend.auth.service.AuthService;
import com.exobios.backend.testsupport.AbstractControllerTest;
import com.exobios.backend.testsupport.JwtTestSupport;
import com.exobios.backend.users.entity.enums.Role;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;

import java.util.UUID;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(controllers = AuthController.class)
class AuthControllerTest extends AbstractControllerTest {

    @MockBean
    private AuthService authService;

    private LoginResponse sampleLoginResponse() {
        return LoginResponse.builder()
                .accessToken("access-token-abc")
                .refreshToken("refresh-token-xyz")
                .tokenType("Bearer")
                .expiresIn(3600L)
                .user(LoginResponse.UserInfo.builder()
                        .id(UUID.randomUUID()).name("Sunita Devi").phone("9876543210").role(Role.ASHA)
                        .build())
                .build();
    }

    // ── /login — public, no auth required ───────────────────────────────────────

    @Test
    void login_withValidCredentials_returns200AndTokens() throws Exception {
        LoginRequest req = new LoginRequest();
        req.setPhone("9876543210");
        req.setPassword("correct-password");
        when(authService.login(any())).thenReturn(sampleLoginResponse());

        mockMvc.perform(post("/api/v1/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.success").value(true))
                .andExpect(jsonPath("$.data.accessToken").value("access-token-abc"))
                .andExpect(jsonPath("$.data.user.role").value("ASHA"));
    }

    @Test
    void login_isReachableWithoutAnAuthorizationHeader() throws Exception {
        // Sanity check that /login is actually on the permitAll list — every other
        // endpoint in this suite requires a bearer token; this one must not.
        LoginRequest req = new LoginRequest();
        req.setPhone("9876543210");
        req.setPassword("x");
        when(authService.login(any())).thenReturn(sampleLoginResponse());

        mockMvc.perform(post("/api/v1/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isOk());
    }

    @Test
    void login_withMalformedPhone_returns400ValidationError() throws Exception {
        LoginRequest req = new LoginRequest();
        req.setPhone("12345"); // fails the 10-digit Indian-mobile pattern
        req.setPassword("some-password");

        mockMvc.perform(post("/api/v1/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.success").value(false));
    }

    @Test
    void login_withBlankPassword_returns400ValidationError() throws Exception {
        LoginRequest req = new LoginRequest();
        req.setPhone("9876543210");
        req.setPassword("");

        mockMvc.perform(post("/api/v1/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isBadRequest());
    }

    // ── /refresh — public, no auth required ─────────────────────────────────────

    @Test
    void refresh_withValidToken_returns200AndNewAccessToken() throws Exception {
        RefreshTokenRequest req = new RefreshTokenRequest();
        req.setRefreshToken("some-refresh-token");
        when(authService.refresh(any())).thenReturn(
                RefreshTokenResponse.builder().accessToken("new-access-token").tokenType("Bearer").expiresIn(3600L).build());

        mockMvc.perform(post("/api/v1/auth/refresh")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.accessToken").value("new-access-token"));
    }

    @Test
    void refresh_withBlankToken_returns400ValidationError() throws Exception {
        RefreshTokenRequest req = new RefreshTokenRequest();
        req.setRefreshToken("");

        mockMvc.perform(post("/api/v1/auth/refresh")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isBadRequest());
    }

    // ── /logout — requires a valid bearer token ─────────────────────────────────

    @Test
    void logout_withoutAuthorizationHeader_returns401() throws Exception {
        mockMvc.perform(post("/api/v1/auth/logout"))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.success").value(false));
    }

    @Test
    void logout_withMalformedToken_returns401() throws Exception {
        mockMvc.perform(post("/api/v1/auth/logout")
                        .header("Authorization", "Bearer not-a-real-jwt"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void logout_withValidToken_returns200AndInvalidatesRefreshTokenForThatUser() throws Exception {
        UUID userId = UUID.randomUUID();
        String bearer = JwtTestSupport.ashaBearer(jwtTokenProvider, userId, "9876543210");

        mockMvc.perform(post("/api/v1/auth/logout").header("Authorization", bearer))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.success").value(true));

        verify(authService).logout(eq(userId.toString()));
    }
}
