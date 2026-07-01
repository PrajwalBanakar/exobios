package com.exobios.backend.notifications.dto;

import com.exobios.backend.notifications.entity.enums.NotificationType;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.Instant;
import java.util.UUID;

@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class NotificationDto {
    private UUID             id;
    private UUID             userId;
    private NotificationType type;
    private String           title;
    private String           message;
    private String           referenceType;
    private UUID             referenceId;
    private boolean          read;
    private Instant          readAt;
    private Instant          createdAt;
}
