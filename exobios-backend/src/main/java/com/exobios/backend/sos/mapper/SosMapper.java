package com.exobios.backend.sos.mapper;

import com.exobios.backend.sos.dto.SosRecordDto;
import com.exobios.backend.sos.entity.SosRecord;
import org.mapstruct.Mapper;
import org.mapstruct.MappingConstants;
import org.mapstruct.ReportingPolicy;

import java.util.List;

@Mapper(componentModel = MappingConstants.ComponentModel.SPRING,
        unmappedTargetPolicy = ReportingPolicy.ERROR)
public interface SosMapper {

    SosRecordDto toDto(SosRecord sosRecord);

    List<SosRecordDto> toDtoList(List<SosRecord> sosRecords);
}
