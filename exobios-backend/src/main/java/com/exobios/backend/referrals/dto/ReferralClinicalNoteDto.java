package com.exobios.backend.referrals.dto;

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
public class ReferralClinicalNoteDto {
    private UUID    id;
    private UUID    referralId;
    private String  note;
    private String  createdBy;
    private Instant createdAt;
}
