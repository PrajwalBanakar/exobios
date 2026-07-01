package com.exobios.backend.notifications.mapper;

import com.exobios.backend.notifications.dto.NotificationDto;
import com.exobios.backend.notifications.entity.Notification;
import org.mapstruct.Mapper;
import org.mapstruct.MappingConstants;
import org.mapstruct.ReportingPolicy;

import java.util.List;

@Mapper(componentModel = MappingConstants.ComponentModel.SPRING,
        unmappedTargetPolicy = ReportingPolicy.ERROR)
public interface NotificationMapper {

    NotificationDto toDto(Notification notification);

    List<NotificationDto> toDtoList(List<Notification> notifications);
}
