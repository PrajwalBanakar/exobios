package com.exobios.backend.notifications.controller;

import com.exobios.backend.common.dto.PageResponse;
import com.exobios.backend.notifications.dto.NotificationDto;
import com.exobios.backend.notifications.entity.enums.NotificationType;
import com.exobios.backend.notifications.service.NotificationService;
import com.exobios.backend.testsupport.AbstractControllerTest;
import com.exobios.backend.testsupport.JwtTestSupport;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;

import java.util.List;
import java.util.UUID;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.patch;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(controllers = NotificationController.class)
class NotificationControllerTest extends AbstractControllerTest {

    @MockBean
    private NotificationService notificationService;

    private NotificationDto sampleNotification(UUID id, UUID userId, boolean read) {
        return NotificationDto.builder().id(id).userId(userId).type(NotificationType.HIGH_RISK_ALERT)
                .title("High-Risk Alert").message("Patient shows critical vitals").read(read).build();
    }

    @Test
    void listMyNotifications_withoutToken_returns401() throws Exception {
        mockMvc.perform(get("/api/v1/notifications")).andExpect(status().isUnauthorized());
    }

    @Test
    void listMyNotifications_returns200WithPage() throws Exception {
        UUID userId = UUID.randomUUID();
        String bearer = JwtTestSupport.ashaBearer(jwtTokenProvider, userId, "9876543210");
        Page<NotificationDto> page = new PageImpl<>(
                List.of(sampleNotification(UUID.randomUUID(), userId, false)), PageRequest.of(0, 20), 1);
        when(notificationService.listMyNotifications(any(), any())).thenReturn(PageResponse.of(page));

        mockMvc.perform(get("/api/v1/notifications").header("Authorization", bearer))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.content[0].title").value("High-Risk Alert"));
    }

    @Test
    void markAsRead_returns200() throws Exception {
        UUID userId = UUID.randomUUID();
        UUID id = UUID.randomUUID();
        String bearer = JwtTestSupport.ashaBearer(jwtTokenProvider, userId, "9876543210");
        when(notificationService.markAsRead(any(), any())).thenReturn(sampleNotification(id, userId, true));

        mockMvc.perform(patch("/api/v1/notifications/{id}/read", id).header("Authorization", bearer))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.read").value(true));
    }

    @Test
    void markAllAsRead_returns200WithCountInMessage() throws Exception {
        String bearer = JwtTestSupport.ashaBearer(jwtTokenProvider, UUID.randomUUID(), "9876543210");
        when(notificationService.markAllAsRead(any())).thenReturn(3);

        mockMvc.perform(post("/api/v1/notifications/mark-all-read").header("Authorization", bearer))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.message").value("3 notification(s) marked as read"));
    }

    @Test
    void listMyNotifications_asForbiddenRole_returns403() throws Exception {
        String bearer = JwtTestSupport.bearer(jwtTokenProvider, UUID.randomUUID(), "9876500000", "GUEST");

        mockMvc.perform(get("/api/v1/notifications").header("Authorization", bearer))
                .andExpect(status().isForbidden());
    }
}
