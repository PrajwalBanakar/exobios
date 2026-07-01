package com.exobios.backend.referrals.exception;

import com.exobios.backend.common.exception.ResourceNotFoundException;

import java.util.UUID;

public class ReferralNotFoundException extends ResourceNotFoundException {

    public ReferralNotFoundException(UUID id) {
        super("Referral", id);
    }
}
