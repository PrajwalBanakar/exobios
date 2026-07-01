package com.exobios.backend.notifications.service;

import com.exobios.backend.common.dto.PageResponse;
import com.exobios.backend.common.exception.ForbiddenException;
import com.exobios.backend.common.exception.ResourceNotFoundException;
import com.exobios.backend.notifications.dto.NotificationDto;
import com.exobios.backend.notifications.entity.Notification;
import com.exobios.backend.notifications.entity.enums.NotificationType;
import com.exobios.backend.notifications.mapper.NotificationMapper;
import com.exobios.backend.notifications.repository.NotificationRepository;
import com.exobios.backend.security.UserPrincipal;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.UUID;

@Slf4j
@Service
@Transactional(readOnly = true)
@RequiredArgsConstructor
public class NotificationService {

    private final NotificationRepository notificationRepository;
    private final NotificationMapper     notificationMapper;

    public PageResponse<NotificationDto> listMyNotifications(Pageable pageable, UserPrincipal principal) {
        return PageResponse.of(
                notificationRepository.findAllByUserId(principal.getId(), pageable)
                        .map(notificationMapper::toDto));
    }

    @Transactional
    public NotificationDto markAsRead(UUID id, UserPrincipal principal) {
        Notification notification = notificationRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Notification", id));

        if (!notification.getUserId().equals(principal.getId())) {
            throw new ForbiddenException("Access denied: this notification belongs to another user");
        }

        if (!notification.isRead()) {
            notification.setRead(true);
            notification.setReadAt(Instant.now());
            notification = notificationRepository.save(notification);
        }
        return notificationMapper.toDto(notification);
    }

    @Transactional
    public int markAllAsRead(UserPrincipal principal) {
        int updated = notificationRepository.markAllReadByUserId(principal.getId(), Instant.now());
        log.info("Marked {} notifications as read for user={}", updated, principal.getId());
        return updated;
    }

    /** Internal — called by other services to deliver a notification. */
    @Transactional
    public Notification createNotification(UUID userId, NotificationType type, String title,
                                           String message, String referenceType, UUID referenceId) {
        Notification n = new Notification();
        n.setUserId(userId);
        n.setType(type);
        n.setTitle(title);
        n.setMessage(message);
        n.setReferenceType(referenceType);
        n.setReferenceId(referenceId);
        n.setRead(false);
        return notificationRepository.save(n);
    }
}
