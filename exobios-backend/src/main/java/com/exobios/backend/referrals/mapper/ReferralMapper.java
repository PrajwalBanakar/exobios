package com.exobios.backend.referrals.mapper;

import com.exobios.backend.referrals.dto.ReferralDto;
import com.exobios.backend.referrals.entity.Referral;
import org.mapstruct.Mapper;
import org.mapstruct.MappingConstants;
import org.mapstruct.ReportingPolicy;

import java.util.List;

@Mapper(componentModel = MappingConstants.ComponentModel.SPRING,
        unmappedTargetPolicy = ReportingPolicy.ERROR)
public interface ReferralMapper {

    ReferralDto toDto(Referral referral);

    List<ReferralDto> toDtoList(List<Referral> referrals);
}
