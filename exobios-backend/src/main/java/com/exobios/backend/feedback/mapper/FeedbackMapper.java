package com.exobios.backend.feedback.mapper;

import com.exobios.backend.feedback.dto.FeedbackDto;
import com.exobios.backend.feedback.entity.Feedback;
import org.mapstruct.Mapper;
import org.mapstruct.MappingConstants;
import org.mapstruct.ReportingPolicy;

import java.util.List;

@Mapper(componentModel = MappingConstants.ComponentModel.SPRING,
        unmappedTargetPolicy = ReportingPolicy.ERROR)
public interface FeedbackMapper {

    FeedbackDto toDto(Feedback feedback);

    List<FeedbackDto> toDtoList(List<Feedback> feedbacks);
}
