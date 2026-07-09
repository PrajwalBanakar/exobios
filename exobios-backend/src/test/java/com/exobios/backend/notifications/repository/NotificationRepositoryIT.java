package com.exobios.backend.notifications.repository;

import com.exobios.backend.notifications.entity.Notification;
import com.exobios.backend.notifications.entity.enums.NotificationType;
import com.exobios.backend.testsupport.AbstractRepositoryIT;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;

import java.time.Instant;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;

class NotificationRepositoryIT extends AbstractRepositoryIT {

    @Autowired
    private NotificationRepository notificationRepository;

    private Notification newNotification(UUID userId, boolean read) {
        Notification n = new Notification();
        n.setUserId(userId);
        n.setType(NotificationType.HIGH_RISK_ALERT);
        n.setTitle("High-Risk Alert");
        n.setMessage("Patient shows critical vitals");
        n.setRead(read);
        if (read) n.setReadAt(Instant.now());
        return n;
    }

    @Test
    void save_persistsAndPopulatesAuditingColumns() {
        Notification saved = notificationRepository.saveAndFlush(newNotification(UUID.randomUUID(), false));

        assertThat(saved.getId()).isNotNull();
        assertThat(saved.getCreatedAt()).isNotNull();
        assertThat(saved.isRead()).isFalse();
    }

    @Test
    void findAllByUserId_returnsOnlyThatUsersNotifications() {
        UUID userA = UUID.randomUUID();
        UUID userB = UUID.randomUUID();
        notificationRepository.saveAndFlush(newNotification(userA, false));
        notificationRepository.saveAndFlush(newNotification(userA, true));
        notificationRepository.saveAndFlush(newNotification(userB, false));

        Page<Notification> page = notificationRepository.findAllByUserId(userA, PageRequest.of(0, 20));

        assertThat(page.getTotalElements()).isEqualTo(2);
    }

    @Test
    void countByUserIdAndReadFalse_countsOnlyUnread() {
        UUID userId = UUID.randomUUID();
        notificationRepository.saveAndFlush(newNotification(userId, false));
        notificationRepository.saveAndFlush(newNotification(userId, false));
        notificationRepository.saveAndFlush(newNotification(userId, true));

        long unread = notificationRepository.countByUserIdAndReadFalse(userId);

        assertThat(unread).isEqualTo(2);
    }

    @Autowired
    private jakarta.persistence.EntityManager entityManager;

    @Test
    void markAllReadByUserId_bulkUpdatesOnlyUnreadNotificationsForThatUser() {
        UUID userA = UUID.randomUUID();
        UUID userB = UUID.randomUUID();
        Notification a1 = notificationRepository.saveAndFlush(newNotification(userA, false));
        Notification a2 = notificationRepository.saveAndFlush(newNotification(userA, false));
        Notification b1 = notificationRepository.saveAndFlush(newNotification(userB, false));

        int updated = notificationRepository.markAllReadByUserId(userA, Instant.now());
        notificationRepository.flush();
        // The @Modifying bulk query writes straight to the DB, bypassing the persistence
        // context, so a1/a2/b1 remain stale in the first-level cache until cleared —
        // clearing here is what makes the re-fetch below actually hit the database.
        entityManager.clear();

        assertThat(updated).isEqualTo(2);
        assertThat(notificationRepository.findById(a1.getId()).orElseThrow().isRead()).isTrue();
        assertThat(notificationRepository.findById(a2.getId()).orElseThrow().isRead()).isTrue();
        // Bulk @Modifying query must stay scoped to the target user — regression guard
        // against it silently marking every user's notifications as read.
        assertThat(notificationRepository.findById(b1.getId()).orElseThrow().isRead()).isFalse();
    }

    @Test
    void markAllReadByUserId_onAlreadyReadNotifications_updatesZeroRows() {
        UUID userId = UUID.randomUUID();
        notificationRepository.saveAndFlush(newNotification(userId, true));

        int updated = notificationRepository.markAllReadByUserId(userId, Instant.now());

        assertThat(updated).isZero();
    }
}
