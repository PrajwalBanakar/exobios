package com.exobios.backend.referrals.controller;

import com.exobios.backend.common.dto.PageResponse;
import com.exobios.backend.referrals.dto.CreateReferralRequest;
import com.exobios.backend.referrals.dto.ReferralDto;
import com.exobios.backend.referrals.dto.ReferralStatusUpdateRequest;
import com.exobios.backend.referrals.dto.UpdateReferralRequest;
import com.exobios.backend.referrals.entity.enums.ReferralStatus;
import com.exobios.backend.referrals.service.ReferralService;
import com.exobios.backend.testsupport.AbstractControllerTest;
import com.exobios.backend.testsupport.JwtTestSupport;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.MediaType;

import java.util.List;
import java.util.UUID;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.patch;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(controllers = ReferralController.class)
class ReferralControllerTest extends AbstractControllerTest {

    @MockBean
    private ReferralService referralService;

    private ReferralDto sampleReferral(UUID id, UUID ashaId, ReferralStatus status) {
        return ReferralDto.builder().id(id).assessmentId(UUID.randomUUID()).patientId(UUID.randomUUID())
                .ashaWorkerId(ashaId).referralReason("Needs specialist evaluation").status(status).build();
    }

    @Test
    void createReferral_withoutToken_returns401() throws Exception {
        mockMvc.perform(post("/api/v1/referrals").contentType(MediaType.APPLICATION_JSON).content("{}"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void createReferral_withValidRequest_returns201() throws Exception {
        UUID ashaId = UUID.randomUUID();
        String bearer = JwtTestSupport.ashaBearer(jwtTokenProvider, ashaId, "9876543210");
        when(referralService.createReferral(any(), any()))
                .thenReturn(sampleReferral(UUID.randomUUID(), ashaId, ReferralStatus.PENDING));

        CreateReferralRequest req = new CreateReferralRequest();
        req.setAssessmentId(UUID.randomUUID());
        req.setReferralReason("Needs specialist evaluation");

        mockMvc.perform(post("/api/v1/referrals")
                        .header("Authorization", bearer)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.data.status").value("PENDING"));
    }

    @Test
    void createReferral_withBlankReason_returns400ValidationError() throws Exception {
        String bearer = JwtTestSupport.ashaBearer(jwtTokenProvider, UUID.randomUUID(), "9876543210");
        CreateReferralRequest req = new CreateReferralRequest();
        req.setAssessmentId(UUID.randomUUID());
        req.setReferralReason(""); // @NotBlank

        mockMvc.perform(post("/api/v1/referrals")
                        .header("Authorization", bearer)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isBadRequest());
    }

    @Test
    void getReferralById_returns200() throws Exception {
        UUID ashaId = UUID.randomUUID();
        UUID id = UUID.randomUUID();
        String bearer = JwtTestSupport.ashaBearer(jwtTokenProvider, ashaId, "9876543210");
        when(referralService.getReferralById(any(), any())).thenReturn(sampleReferral(id, ashaId, ReferralStatus.PENDING));

        mockMvc.perform(get("/api/v1/referrals/{id}", id).header("Authorization", bearer))
                .andExpect(status().isOk());
    }

    @Test
    void getReferrals_withStatusFilter_returns200() throws Exception {
        UUID ashaId = UUID.randomUUID();
        String bearer = JwtTestSupport.ashaBearer(jwtTokenProvider, ashaId, "9876543210");
        Page<ReferralDto> page = new PageImpl<>(
                List.of(sampleReferral(UUID.randomUUID(), ashaId, ReferralStatus.ACCEPTED)), PageRequest.of(0, 20), 1);
        when(referralService.getReferrals(any(), any(), any(), any(), any())).thenReturn(PageResponse.of(page));

        mockMvc.perform(get("/api/v1/referrals").param("status", "ACCEPTED").header("Authorization", bearer))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.totalElements").value(1));
    }

    @Test
    void getReferrals_withInvalidStatusEnum_returns500_knownGap() throws Exception {
        // Same known gap as PatientControllerTest#getPatientById_withMalformedUuid_returns500_knownGap:
        // an unparseable @RequestParam enum value hits the generic 500 handler instead of 400.
        String bearer = JwtTestSupport.ashaBearer(jwtTokenProvider, UUID.randomUUID(), "9876543210");

        mockMvc.perform(get("/api/v1/referrals").param("status", "NOT_A_REAL_STATUS").header("Authorization", bearer))
                .andExpect(status().isInternalServerError());
    }

    @Test
    void getAssessmentReferrals_returns200WithList() throws Exception {
        UUID ashaId = UUID.randomUUID();
        String bearer = JwtTestSupport.ashaBearer(jwtTokenProvider, ashaId, "9876543210");
        when(referralService.getAssessmentReferrals(any(), any()))
                .thenReturn(List.of(sampleReferral(UUID.randomUUID(), ashaId, ReferralStatus.PENDING)));

        mockMvc.perform(get("/api/v1/assessments/{assessmentId}/referrals", UUID.randomUUID()).header("Authorization", bearer))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data").isArray());
    }

    @Test
    void getPatientReferrals_returns200WithPage() throws Exception {
        UUID ashaId = UUID.randomUUID();
        String bearer = JwtTestSupport.ashaBearer(jwtTokenProvider, ashaId, "9876543210");
        Page<ReferralDto> page = new PageImpl<>(List.of(), PageRequest.of(0, 20), 0);
        when(referralService.getPatientReferrals(any(), any(), any())).thenReturn(PageResponse.of(page));

        mockMvc.perform(get("/api/v1/patients/{patientId}/referrals", UUID.randomUUID()).header("Authorization", bearer))
                .andExpect(status().isOk());
    }

    @Test
    void updateReferral_withValidRequest_returns200() throws Exception {
        UUID ashaId = UUID.randomUUID();
        UUID id = UUID.randomUUID();
        String bearer = JwtTestSupport.ashaBearer(jwtTokenProvider, ashaId, "9876543210");
        when(referralService.updateReferral(any(), any(), any())).thenReturn(sampleReferral(id, ashaId, ReferralStatus.PENDING));

        UpdateReferralRequest req = new UpdateReferralRequest();
        req.setReferralHospital("City Hospital");

        mockMvc.perform(put("/api/v1/referrals/{id}", id)
                        .header("Authorization", bearer)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isOk());
    }

    @Test
    void updateStatus_withValidRequest_returns200() throws Exception {
        UUID ashaId = UUID.randomUUID();
        UUID id = UUID.randomUUID();
        String bearer = JwtTestSupport.ashaBearer(jwtTokenProvider, ashaId, "9876543210");
        when(referralService.updateStatus(any(), any(), any())).thenReturn(sampleReferral(id, ashaId, ReferralStatus.ACCEPTED));

        ReferralStatusUpdateRequest req = new ReferralStatusUpdateRequest();
        req.setStatus(ReferralStatus.ACCEPTED);

        mockMvc.perform(patch("/api/v1/referrals/{id}/status", id)
                        .header("Authorization", bearer)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.status").value("ACCEPTED"));
    }

    @Test
    void deleteReferral_returns200() throws Exception {
        String bearer = JwtTestSupport.ashaBearer(jwtTokenProvider, UUID.randomUUID(), "9876543210");

        mockMvc.perform(delete("/api/v1/referrals/{id}", UUID.randomUUID()).header("Authorization", bearer))
                .andExpect(status().isOk());
    }
}
