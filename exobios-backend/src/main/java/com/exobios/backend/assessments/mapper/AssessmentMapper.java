package com.exobios.backend.assessments.mapper;

import com.exobios.backend.assessments.dto.AiAssessmentResultDto;
import com.exobios.backend.assessments.dto.AssessmentDto;
import com.exobios.backend.assessments.dto.ExaminationFindingDto;
import com.exobios.backend.assessments.dto.LegacyInformationDto;
import com.exobios.backend.assessments.dto.MedicalHistoryDto;
import com.exobios.backend.assessments.dto.SymptomDto;
import com.exobios.backend.assessments.dto.VitalsDto;
import com.exobios.backend.assessments.entity.AiAssessmentResult;
import com.exobios.backend.assessments.entity.Assessment;
import com.exobios.backend.assessments.entity.ExaminationFinding;
import com.exobios.backend.assessments.entity.LegacyInformation;
import com.exobios.backend.assessments.entity.MedicalHistory;
import com.exobios.backend.assessments.entity.Symptom;
import com.exobios.backend.assessments.entity.Vitals;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.MappingConstants;
import org.mapstruct.ReportingPolicy;

import java.util.List;

@Mapper(componentModel = MappingConstants.ComponentModel.SPRING,
        unmappedTargetPolicy = ReportingPolicy.ERROR)
public interface AssessmentMapper {

    AssessmentDto toDto(Assessment assessment);

    List<AssessmentDto> toDtoList(List<Assessment> assessments);

    // ── Sub-entity mappers (used automatically by MapStruct for nested fields) ──

    @Mapping(target = "id", source = "id")
    SymptomDto toSymptomDto(Symptom symptom);

    @Mapping(target = "id", source = "id")
    VitalsDto toVitalsDto(Vitals vitals);

    @Mapping(target = "id", source = "id")
    MedicalHistoryDto toMedicalHistoryDto(MedicalHistory medicalHistory);

    @Mapping(target = "id", source = "id")
    ExaminationFindingDto toExaminationFindingDto(ExaminationFinding finding);

    @Mapping(target = "id", source = "id")
    LegacyInformationDto toLegacyInformationDto(LegacyInformation info);

    @Mapping(target = "id", source = "id")
    AiAssessmentResultDto toAiResultDto(AiAssessmentResult result);
}
