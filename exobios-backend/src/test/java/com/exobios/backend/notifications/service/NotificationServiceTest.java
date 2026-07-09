package com.exobios.backend.notifications.service;

import com.exobios.backend.common.exception.ForbiddenException;
import com.exobios.backend.common.exception.ResourceNotFoundException;
import com.exobios.backend.notifications.dto.NotificationDto;
import com.exobios.backend.notifications.entity.Notification;
import com.exobios.backend.notifications.entity.enums.NotificationType;
import com.exobios.backend.notifications.mapper.NotificationMapper;
import com.exobios.backend.notifications.repository.NotificationRepository;
import com.exobios.backend.security.UserPrincipal;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

import java.time.Instant;
import java.util.Optional;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.lenient;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class NotificationServiceTest {

    @Mock private NotificationRepository notificationRepository;
    @Mock private NotificationMapper     notificationMapper;

    private NotificationService notificationService;

    private final UUID userId = UUID.randomUUID();

    @BeforeEach
    void setUp() {
        notificationService = new NotificationService(notificationRepository, notificationMapper);
        lenient().when(notificationMapper.toDto(any(Notification.class))).thenAnswer(inv -> {
            Notification n = inv.getArgument(0);
            return NotificationDto.builder().id(n.getId()).userId(n.getUserId()).read(n.isRead()).build();
        });
    }

    private UserPrincipal user(UUID id) { return UserPrincipal.fromToken(id.toString(), "9876543210", "ASHA"); }

    private Notification unreadNotification(UUID id, UUID owner) {
        Notification n = new Notification();
        ReflectionTestUtils.setField(n, "id", id);
        n.setUserId(owner);
        n.setType(NotificationType.HIGH_RISK_ALERT);
        n.setTitle("High-Risk Alert");
        n.setMessage("Patient shows critical vitals");
        n.setRead(false);
        return n;
    }

    // ── markAsRead — ownership + idempotency ─────────────────────────────────────

    @Test
    void markAsRead_forAnotherUsersNotification_throwsForbidden() {
        UUID id = UUID.randomUUID();
        when(notificationRepository.findById(id)).thenReturn(Optional.of(unreadNotification(id, UUID.randomUUID())));

        assertThatThrownBy(() -> notificationService.markAsRead(id, user(userId)))
                .isInstanceOf(ForbiddenException.class);
        verify(notificationRepository, never()).save(any());
    }

    @Test
    void markAsRead_forUnknownId_throwsResourceNotFound() {
        UUID id = UUID.randomUUID();
        when(notificationRepository.findById(id)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> notificationService.markAsRead(id, user(userId)))
                .isInstanceOf(ResourceNotFoundException.class);
    }

    @Test
    void markAsRead_forUnreadOwnNotification_setsReadAndPersists() {
        UUID id = UUID.randomUUID();
        Notification notification = unreadNotification(id, userId);
        when(notificationRepository.findById(id)).thenReturn(Optional.of(notification));
        when(notificationRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        NotificationDto result = notificationService.markAsRead(id, user(userId));

        assertThat(result.isRead()).isTrue();
        assertThat(notification.getReadAt()).isNotNull();
        verify(notificationRepository).save(notification);
    }

    @Test
    void markAsRead_whenAlreadyRead_isANoOpAndDoesNotResave() {
        UUID id = UUID.randomUUID();
        Notification notification = unreadNotification(id, userId);
        notification.setRead(true);
        notification.setReadAt(Instant.now().minusSeconds(60));
        when(notificationRepository.findById(id)).thenReturn(Optional.of(notification));

        notificationService.markAsRead(id, user(userId));

        verify(notificationRepository, never()).save(any());
    }

    // ── markAllAsRead / listMyNotifications — delegate correctly ────────────────

    @Test
    void markAllAsRead_delegatesToBulkUpdateAndReturnsCount() {
        when(notificationRepository.markAllReadByUserId(eq(userId), any())).thenReturn(4);

        int updated = notificationService.markAllAsRead(user(userId));

        assertThat(updated).isEqualTo(4);
        verify(notificationRepository, times(1)).markAllReadByUserId(eq(userId), any());
    }

    @Test
    void listMyNotifications_queriesScopedToCallingUser() {
        var pageable = org.springframework.data.domain.PageRequest.of(0, 20);
        when(notificationRepository.findAllByUserId(userId, pageable))
                .thenReturn(new org.springframework.data.domain.PageImpl<>(java.util.List.of()));

        notificationService.listMyNotifications(pageable, user(userId));

        verify(notificationRepository).findAllByUserId(userId, pageable);
    }
}
