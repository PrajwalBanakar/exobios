package com.exobios.backend.doctor.service;

import com.exobios.backend.doctor.dto.DoctorDashboardDto;
import com.exobios.backend.referrals.entity.enums.ReferralReviewStage;
import com.exobios.backend.referrals.repository.ReferralRepository;
import com.exobios.backend.security.UserPrincipal;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional(readOnly = true)
@RequiredArgsConstructor
public class DoctorService {

    private final ReferralRepository referralRepository;

    public DoctorDashboardDto getDashboard(UserPrincipal principal) {
        return DoctorDashboardDto.builder()
                .assignedCount(referralRepository.countByAssignedDoctorIdAndReviewStage(
                        principal.getId(), ReferralReviewStage.ASSIGNED_TO_DOCTOR))
                .underReviewCount(referralRepository.countByAssignedDoctorIdAndReviewStage(
                        principal.getId(), ReferralReviewStage.UNDER_REVIEW))
                .actionTakenCount(referralRepository.countByAssignedDoctorIdAndReviewStage(
                        principal.getId(), ReferralReviewStage.ACTION_TAKEN))
                .closedCount(referralRepository.countByAssignedDoctorIdAndReviewStage(
                        principal.getId(), ReferralReviewStage.CLOSED))
                .unassignedInboxCount(referralRepository.countByReviewStageAndAssignedDoctorIdIsNull(
                        ReferralReviewStage.CREATED))
                .build();
    }
}
