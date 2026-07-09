package com.exobios.backend.assessments.controller;

import com.exobios.backend.assessments.dto.AssessmentDto;
import com.exobios.backend.assessments.dto.CreateAssessmentRequest;
import com.exobios.backend.assessments.dto.UpdateAssessmentRequest;
import com.exobios.backend.assessments.entity.enums.AssessmentStatus;
import com.exobios.backend.assessments.service.AssessmentService;
import com.exobios.backend.common.dto.PageResponse;
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
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.patch;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(controllers = AssessmentController.class)
class AssessmentControllerTest extends AbstractControllerTest {

    @MockBean
    private AssessmentService assessmentService;

    private AssessmentDto sampleAssessment(UUID id, UUID ashaId, AssessmentStatus status) {
        return AssessmentDto.builder()
                .id(id).assessmentNumber("ASMT-2026-000001")
                .patientId(UUID.randomUUID()).ashaWorkerId(ashaId).status(status)
                .build();
    }

    @Test
    void createAssessment_withoutToken_returns401() throws Exception {
        mockMvc.perform(post("/api/v1/assessments")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{}"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void createAssessment_withValidRequest_returns201() throws Exception {
        UUID ashaId = UUID.randomUUID();
        String bearer = JwtTestSupport.ashaBearer(jwtTokenProvider, ashaId, "9876543210");
        when(assessmentService.createAssessment(any(), any()))
                .thenReturn(sampleAssessment(UUID.randomUUID(), ashaId, AssessmentStatus.DRAFT));

        CreateAssessmentRequest req = new CreateAssessmentRequest();
        req.setPatientId(UUID.randomUUID());
        req.setPatientComplaint("Fever for 3 days");

        mockMvc.perform(post("/api/v1/assessments")
                        .header("Authorization", bearer)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.data.status").value("DRAFT"));
    }

    @Test
    void createAssessment_withoutPatientId_returns400ValidationError() throws Exception {
        String bearer = JwtTestSupport.ashaBearer(jwtTokenProvider, UUID.randomUUID(), "9876543210");
        CreateAssessmentRequest req = new CreateAssessmentRequest(); // patientId is @NotNull

        mockMvc.perform(post("/api/v1/assessments")
                        .header("Authorization", bearer)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isBadRequest());
    }

    @Test
    void getAssessmentById_asForbiddenRole_returns403() throws Exception {
        String bearer = JwtTestSupport.bearer(jwtTokenProvider, UUID.randomUUID(), "9876500000", "NURSE");

        mockMvc.perform(get("/api/v1/assessments/{id}", UUID.randomUUID()).header("Authorization", bearer))
                .andExpect(status().isForbidden());
    }

    @Test
    void getAssessmentById_returns200() throws Exception {
        UUID ashaId = UUID.randomUUID();
        UUID id     = UUID.randomUUID();
        String bearer = JwtTestSupport.ashaBearer(jwtTokenProvider, ashaId, "9876543210");
        when(assessmentService.getAssessmentById(any(), any()))
                .thenReturn(sampleAssessment(id, ashaId, AssessmentStatus.SUBMITTED));

        mockMvc.perform(get("/api/v1/assessments/{id}", id).header("Authorization", bearer))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.assessmentNumber").value("ASMT-2026-000001"));
    }

    @Test
    void getPatientAssessments_returns200WithPage() throws Exception {
        UUID ashaId    = UUID.randomUUID();
        UUID patientId = UUID.randomUUID();
        String bearer  = JwtTestSupport.ashaBearer(jwtTokenProvider, ashaId, "9876543210");
        Page<AssessmentDto> page = new PageImpl<>(
                List.of(sampleAssessment(UUID.randomUUID(), ashaId, AssessmentStatus.SUBMITTED)),
                PageRequest.of(0, 20), 1);
        when(assessmentService.getPatientAssessments(any(), any(), any())).thenReturn(PageResponse.of(page));

        mockMvc.perform(get("/api/v1/patients/{patientId}/assessments", patientId).header("Authorization", bearer))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.totalElements").value(1));
    }

    @Test
    void updateAssessment_withValidRequest_returns200() throws Exception {
        UUID ashaId = UUID.randomUUID();
        UUID id     = UUID.randomUUID();
        String bearer = JwtTestSupport.ashaBearer(jwtTokenProvider, ashaId, "9876543210");
        when(assessmentService.updateAssessment(any(), any(), any()))
                .thenReturn(sampleAssessment(id, ashaId, AssessmentStatus.DRAFT));

        UpdateAssessmentRequest req = new UpdateAssessmentRequest();
        req.setPatientComplaint("Updated complaint");

        mockMvc.perform(put("/api/v1/assessments/{id}", id)
                        .header("Authorization", bearer)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isOk());
    }

    @Test
    void submitAssessment_returns200WithSubmittedStatus() throws Exception {
        UUID ashaId = UUID.randomUUID();
        UUID id     = UUID.randomUUID();
        String bearer = JwtTestSupport.ashaBearer(jwtTokenProvider, ashaId, "9876543210");
        when(assessmentService.submitAssessment(any(), any()))
                .thenReturn(sampleAssessment(id, ashaId, AssessmentStatus.SUBMITTED));

        mockMvc.perform(patch("/api/v1/assessments/{id}/submit", id).header("Authorization", bearer))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.status").value("SUBMITTED"));
    }
}
