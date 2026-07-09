package com.exobios.backend.referrals.mapper;

import com.exobios.backend.referrals.dto.ReferralClinicalNoteDto;
import com.exobios.backend.referrals.entity.ReferralClinicalNote;
import org.mapstruct.Mapper;
import org.mapstruct.MappingConstants;
import org.mapstruct.ReportingPolicy;

import java.util.List;

@Mapper(componentModel = MappingConstants.ComponentModel.SPRING,
        unmappedTargetPolicy = ReportingPolicy.ERROR)
public interface ReferralClinicalNoteMapper {

    ReferralClinicalNoteDto toDto(ReferralClinicalNote note);

    List<ReferralClinicalNoteDto> toDtoList(List<ReferralClinicalNote> notes);
}
