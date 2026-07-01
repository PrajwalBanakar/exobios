package com.exobios.backend.measures.mapper;

import com.exobios.backend.measures.dto.MeasureDto;
import com.exobios.backend.measures.entity.Measure;
import org.mapstruct.Mapper;
import org.mapstruct.MappingConstants;
import org.mapstruct.ReportingPolicy;

import java.util.List;

@Mapper(componentModel = MappingConstants.ComponentModel.SPRING,
        unmappedTargetPolicy = ReportingPolicy.ERROR)
public interface MeasureMapper {

    MeasureDto toDto(Measure measure);

    List<MeasureDto> toDtoList(List<Measure> measures);
}
